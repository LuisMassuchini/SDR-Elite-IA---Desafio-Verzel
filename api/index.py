import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from api.pipefy_service import registrar_lead_pipefy, atualizar_card_pipefy # MUDANÇA VERCEL: path
from flask import Flask, request, jsonify, render_template, session

load_dotenv()
client = OpenAI()
app = Flask(__name__, template_folder='../templates') # MUDANÇA VERCEL: Aponta para a pasta /templates

# ---
# ### MUDANÇA VERCEL 1: CHAVE SECRETA ###
# A chave secreta NÃO PODE ser aleatória (os.urandom) em um ambiente serverless.
# Ela precisa ser uma string estática lida das variáveis de ambiente.
# Adicione FLASK_SECRET_KEY ao seu .env e ao Vercel.
app.secret_key = os.getenv('FLASK_SECRET_KEY')
if not app.secret_key:
    raise ValueError("FLASK_SECRET_KEY não definida nas variáveis de ambiente.")
# ---

# ---
# ### MUDANÇA VERCEL 2: VARIÁVEL GLOBAL REMOVIDA ###
# 'thread_card_map = {}' foi REMOVIDA. Usaremos a 'session' do Flask.
# ---

ASSISTANT_ID = None

# --- FERRAMENTAS DO ASSISTANT (FUNÇÕES) ---

def oferecer_horarios_agenda() -> str:
    """
    Busca 2-3 horários disponíveis nos próximos 7 dias.
    Simulação simples para economizar tempo.
    """
    horarios = [
        "Amanhã, 10h30 (Brasília)",
        "Sexta-feira, 14h00 (Brasília)",
        "Próxima Segunda-feira, 09h00 (Brasília)"
    ]
    return f"Nossos próximos horários disponíveis são: {', '.join(horarios)}. Qual você prefere?"

def agendar_reuniao(horario_escolhido: str, nome: str, email: str, card_id: str) -> str:
    """
    Agenda a reunião no horário escolhido e retorna o link e a data/hora confirmada.
    """
    if not card_id:
        return "Erro: Não foi possível localizar o ID do lead para agendar."

    meeting_link = f"https://meet.link/verzel-ia/{card_id}"
    print(f"Agendando para {nome} em {horario_escolhido}. Link: {meeting_link}")
    
    atualizar_card_pipefy(card_id, meeting_link, horario_escolhido)
    
    return f"Reunião confirmada para **{horario_escolhido}**! Você pode acessar pelo link: **{meeting_link}**. Um convite será enviado para o seu e-mail ({email})."


def registrar_lead(nome: str, email: str, empresa: str, necessidade: str, interesse_confirmado: bool = False) -> str:
    """Registra o lead no Pipefy e retorna o ID do card criado."""
    thread_id = session.get('thread_id')
    card_id = registrar_lead_pipefy(nome, email, empresa, necessidade, interesse_confirmado)
    
    if card_id:
        # ---
        # ### MUDANÇA VERCEL 3: SALVAR NA SESSÃO ###
        # Em vez de 'thread_card_map', salvamos no cookie da sessão.
        session['card_id'] = card_id
        # ---
        return f"Lead registrado no sistema com sucesso. ID do Card: {card_id}"
    
    return "Houve um erro ao registrar o lead, mas continuaremos a conversa."


# --- ORQUESTRADOR DE FUNÇÕES ---
def call_assistant_function(tool_call):
    """Executa a função solicitada pelo Assistant e retorna o resultado."""
    function_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    if function_name in ['agendar_reuniao']:
        # ---
        # ### MUDANÇA VERCEL 3 (LEITURA): LER DA SESSÃO ###
        arguments['card_id'] = session.get('card_id')
        # ---

    print(f"Executando Função: {function_name} com args: {arguments}")

    if function_name == "registrar_lead":
        return registrar_lead(**arguments)
    elif function_name == "oferecer_horarios_agenda":
        return oferecer_horarios_agenda()
    elif function_name == "agendar_reuniao":
        return agendar_reuniao(**arguments)
    else:
        raise ValueError(f"Função desconhecida: {function_name}")


# --- SETUP DO ASSISTANT (VERSÃO CORRIGIDA) ---
def setup_assistant():
    """Cria ou ATUALIZA o Assistant para o desafio."""
    global ASSISTANT_ID
    
    ASSISTANT_NAME = "Verzel SDR Elite IA"
    ASSISTANT_ID = os.getenv('OPENAI_ASSISTANT_ID') # Opcional: para acelerar

    instrucoes_sdr = """Você é o SDR da Verzel. Seu objetivo é qualificar leads interessados em consultoria de Implementação de IA para Vendas.
Mantenha um tom profissional, amigável e empático.

Seu fluxo de conversa DEVE seguir estas etapas, UMA DE CADA VEZ:

1. **Boas-vindas e Nome**: Comece se apresentando (Ex: "Olá! Sou o SDR da Verzel.") e perguntando APENAS o nome do cliente.
2. **Coleta da Empresa**: Após obter o nome, pergunte APENAS o nome da empresa.
3. **Coleta do E-mail**: Após obter a empresa, peça o e-mail corporativo para contato.
4. **Coleta da Dor/Necessidade**: Após o e-mail, pergunte qual a principal necessidade ou dor que o cliente enfrenta.
5. **Registro no Pipefy**: Assim que tiver (nome, email, empresa, necessidade), chame a função `registrar_lead`. NÃO avise o usuário que está registrando, apenas prossiga para a próxima etapa.
6. **Pergunta de Gatilho (Interesse)**: Após registrar, pergunte DIRETAMENTE sobre o interesse em agendar: "Ótimo, [Nome do Cliente]! Para iniciarmos o projeto, gostaria de seguir com uma conversa de 30 minutos com um de nossos especialistas para detalhar sua necessidade e dar o primeiro passo na sua automação?"
7. **Agendamento**: SOMENTE SE o cliente confirmar explicitamente, chame `oferecer_horarios_agenda`.
8. **Confirmação**: Após o cliente escolher o horário, chame `agendar_reuniao` para confirmar e enviar o link.
9. **Encerramento (Sem Interesse)**: Se o cliente disser que não tem interesse (na etapa 6), apenas agradeça e encerre cordialmente.
"""

    tools_list = [
        {"type": "function", "function": {
            "name": "registrar_lead",
            "description": "Registra ou atualiza um lead no Pipefy com informações básicas. Use assim que tiver nome, email, empresa e necessidade.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string", "description": "Nome completo do lead."},
                    "email": {"type": "string", "description": "E-mail do lead."},
                    "empresa": {"type": "string", "description": "Nome da empresa do lead."},
                    "necessidade": {"type": "string", "description": "A principal necessidade ou dor que motivou o contato."},
                    "interesse_confirmado": {"type": "boolean", "description": "Define como 'False' no registro inicial."}
                },
                "required": ["nome", "email", "empresa", "necessidade"]
            }
        }},
        {"type": "function", "function": {
            "name": "oferecer_horarios_agenda",
            "description": "Busca 2-3 horários disponíveis para agendamento nos próximos 7 dias. Use somente se o cliente CONFIRMAR o interesse.",
            "parameters": {"type": "object", "properties": {}}
        }},
        {"type": "function", "function": {
            "name": "agendar_reuniao",
            "description": "Confirma o agendamento da reunião no horário escolhido e obtém o link e data/hora para o cliente. Use o nome e e-mail coletados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "horario_escolhido": {"type": "string", "description": "Horário exato escolhido pelo cliente (ex: 'Sexta, 14h00')."},
                    "nome": {"type": "string", "description": "Nome completo do lead para o agendamento."},
                    "email": {"type": "string", "description": "E-mail do lead para o agendamento."}
                },
                "required": ["horario_escolhido", "nome", "email"]
            }
        }}
    ]
    
    # Busca por ID de assistente na var de ambiente primeiro
    if ASSISTANT_ID:
        try:
            assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
            print(f"Assistant existente (via ENV) encontrado: {ASSISTANT_ID}. Atualizando...")
            client.beta.assistants.update(
                ASSISTANT_ID,
                instructions=instrucoes_sdr,
                model="gpt-4o",
                tools=tools_list
            )
            print("Assistant atualizado com sucesso.")
            return
        except Exception:
            print("ID de assistente (ENV) inválido. Procurando por nome...")
            ASSISTANT_ID = None # Limpa para a próxima verificação

    # Se não, busca por nome
    for assistant in client.beta.assistants.list(order="desc", limit="10"):
        if assistant.name == ASSISTANT_NAME:
            ASSISTANT_ID = assistant.id
            print(f"Assistant existente (via NOME) encontrado: {ASSISTANT_ID}. Atualizando...")
            client.beta.assistants.update(
                ASSISTANT_ID,
                instructions=instrucoes_sdr,
                model="gpt-4o",
                tools=tools_list
            )
            print("Assistant atualizado com sucesso.")
            return

    # Se não existe, cria um novo
    print("Nenhum assistente encontrado. Criando um novo...")
    assistant = client.beta.assistants.create(
        name=ASSISTANT_NAME,
        instructions=instrucoes_sdr,
        model="gpt-4o",
        tools=tools_list
    )
    ASSISTANT_ID = assistant.id
    print(f"Assistant criado: {ASSISTANT_ID}")


# --- SETUP DO ASSISTANT (CHAMADA ÚNICA) ---
# O Vercel executa este código na "inicialização fria" da função
setup_assistant()


# --- ENDPOINTS DO FLASK ---

@app.route('/')
def home():
    """Servir o HTML do Webchat."""
    if 'thread_id' not in session:
        thread = client.beta.threads.create()
        session['thread_id'] = thread.id
        print(f"Nova thread criada: {thread.id}")

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="assistant",
            content="Olá! Sou o SDR da Verzel. Para começarmos, qual é o seu nome?"
        )
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint para processar as mensagens do usuário."""
    if 'thread_id' not in session:
        return jsonify({"response": "Erro de sessão. Por favor, recarregue a página."}), 400

    user_message = request.json.get('message')
    thread_id = session['thread_id']

    runs = client.beta.threads.runs.list(thread_id=thread_id, order="desc", limit=1)
    if runs.data and runs.data[0].status in ["queued", "in_progress", "requires_action"]:
        return jsonify({"response": "Aguarde o processamento anterior terminar antes de enviar uma nova mensagem."}), 429

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID
    )

    while run.status in ['queued', 'in_progress', 'requires_action']:
        time.sleep(1) 
        run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        
        if run.status == 'requires_action':
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                output = call_assistant_function(tool_call)
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": output
                })
            
            run = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )

    print(f"Run finalizado com status: {run.status}")
    
    if run.status == 'failed':
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("O RUN FALHOU. DETALHES DO ERRO:")
        print(run.last_error)
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        
        error_message = f"Desculpe, ocorreu um erro interno (Code: {run.last_error.code})."
        if run.last_error.code == 'insufficient_quota':
            error_message = "Erro: Saldo insuficiente na OpenAI para completar a ação."
            
        return jsonify({"response": error_message})

    # 4. Obter a última resposta (Polling de Steps)
    start_time = time.time()
    max_wait_time = 15 
    
    assistant_response = "Desculpe, ocorreu um erro ao processar a resposta."
    
    if run.status == 'completed':
        while time.time() - start_time < max_wait_time:
            try:
                run_steps = client.beta.threads.runs.steps.list(
                    thread_id=thread_id,
                    run_id=run.id,
                    order="desc",
                    limit=1
                )
                
                if run_steps.data and run_steps.data[0].step_details.type == 'message_creation':
                    step_details = run_steps.data[0].step_details
                    message_id = step_details.message_creation.message_id
                    
                    message = client.beta.threads.messages.retrieve(
                        thread_id=thread_id,
                        message_id=message_id
                    )
                    assistant_response = message.content[0].text.value
                    print(f"Resposta encontrada via Step: {message_id}")
                    break 
                else:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Erro ao buscar steps: {e}")
                time.sleep(1)
    else:
        print(f"Run falhou ou status inesperado ({run.status}). Não foi possível obter resposta.")

    return jsonify({"response": assistant_response})

