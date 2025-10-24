# SDR Elite IA - Desafio Verzel

Este projeto é a implementação de um SDR (Sales Development Representative) Automatizado, conforme proposto no "Desafio Elite Dev IA" da Verzel.

O agente é um chatbot que utiliza a API de Assistentes da OpenAI para conduzir uma conversa natural, qualificar um lead, e agendar uma reunião (via mock de API), registrando todo o processo em um funil do Pipefy.

---

## 🚀 Funcionalidades (MVP)

* **Conversa Natural:** Conduz uma conversa passo a passo (perguntas progressivas) para coletar dados do lead.
* **Coleta de Dados:** Coleta Nome, E-mail, Empresa e Necessidade/Dor.
* **Qualificação (Gatilho):** Identifica a confirmação explícita de interesse do lead.
* **Agendamento:** Oferece horários (mockados) e confirma o agendamento.
* **Integração Pipefy:** Cria um card no Pipefy com os dados do lead e, após o agendamento, atualiza o mesmo card com o link e a data da reunião.
* **Webchat:** Interface de chat simples (Flask + HTML/CSS/JS) com indicador de "Digitando...".

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python 3
* **Servidor:** Flask
* **IA (Core):** OpenAI Assistants API (gpt-4o)
* **CRM:** Pipefy (API GraphQL)
* **Dependências:** `openai`, `requests`, `flask`, `python-dotenv`

---

## ⚙️ Configuração do Ambiente (Obrigatório)

Siga estes passos para configurar e executar o projeto localmente.

### 1. Pré-requisitos

* Python 3.8 ou superior
* Uma conta paga da API da OpenAI (com créditos)
* Uma conta Pipefy (nível gratuito é suficiente)

### 2. Clonar e Instalar

```bash
# Clone o repositório (substitua pela URL do seu repo)
git clone [https://github.com/LuisMassuchini/SDR-Elite-IA---Desafio-Verzel.git](https://github.com/LuisMassuchini/SDR-Elite-IA---Desafio-Verzel.git)
cd sdr-ia-minimal

# Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate  # No Linux/macOS
# venv\Scripts\activate   # No Windows

# Instale as dependências
pip install -r requirements.txt