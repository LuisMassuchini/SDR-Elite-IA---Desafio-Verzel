# pipefy_service.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

PIPEFY_URL = "https://api.pipefy.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {os.getenv('PIPEFY_ACCESS_TOKEN')}",
    "Content-Type": "application/json"
}
PIPE_ID = os.getenv('PIPEFY_PIPE_ID')

def get_field_id(field_name):
    """Mapeia nomes de campos amigáveis para IDs do Pipefy (a ser ajustado)."""
    
    mapping = {
        "nome": "nome",
        "email": "e_mail",
        "empresa": "empresa",
        "necessidade": "necessidade",
        "interesse_confirmado": "interesse_confirmado",
        "meeting_link": "meeting_link",
        "meeting_datetime": "meeting_datetime"
    }
    return mapping.get(field_name, field_name)

def registrar_lead_pipefy(nome: str, email: str, empresa: str, necessidade: str, interesse_confirmado: bool = False, meeting_link: str = None, meeting_datetime: str = None) -> str:
    """
    Cria um novo card no funil de Pré-vendas do Pipefy.
    Retorna o ID do card criado.
    """
    if not PIPE_ID:
        print("Erro: PIPE_ID não configurado.")
        return "CARD_MOCK_123"

    fields = [
        {"field_id": get_field_id("nome"), "value": nome},
        {"field_id": get_field_id("email"), "value": email},
        {"field_id": get_field_id("empresa"), "value": empresa},
        {"field_id": get_field_id("necessidade"), "value": necessidade},
        {"field_id": get_field_id("interesse_confirmado"), "value": "Sim" if interesse_confirmado else "Não"},
    ]

    if meeting_link and meeting_datetime:
        fields.append({"field_id": get_field_id("meeting_link"), "value": meeting_link})
        fields.append({"field_id": get_field_id("meeting_datetime"), "value": meeting_datetime})

    query = f"""
    mutation {{
      createCard(input: {{
        pipe_id: "{PIPE_ID}",
        fields_attributes: {str(fields).replace("'", '"')}
      }}) {{
        card {{
          id
          title
        }}
      }}
    }}
    """
    
  

    response = requests.post(PIPEFY_URL, headers=HEADERS, json={'query': query})
    
    if response.status_code == 200 and 'createCard' in response.json().get('data', {}):
        card_id = response.json()['data']['createCard']['card']['id']
        print(f"Card Pipefy criado: {card_id}")
        return card_id
    else:
        print(f"Erro ao criar card no Pipefy: {response.text}")
        return "CARD_MOCK_ERROR"

def atualizar_card_pipefy(card_id: str, meeting_link: str, meeting_datetime: str):
    """Atualiza um card existente no Pipefy com o link da reunião."""
    if card_id.startswith("CARD_MOCK"):
        print(f"Ignorando atualização de card mock: {card_id}")
        return True

    fields = [
        {"field_id": get_field_id("meeting_link"), "value": meeting_link},
        {"field_id": get_field_id("meeting_datetime"), "value": meeting_datetime},
        {"field_id": get_field_id("interesse_confirmado"), "value": "Sim"},
    ]

    query = f"""
    mutation {{
      updateCard(input: {{
        id: "{card_id}",
        fields_attributes: {str(fields).replace("'", '"')}
      }}) {{
        card {{
          id
        }}
      }}
    }}
    """

    response = requests.post(PIPEFY_URL, headers=HEADERS, json={'query': query})
    if response.status_code == 200 and 'updateCard' in response.json().get('data', {}):
        print(f"Card Pipefy {card_id} atualizado com sucesso.")
        return True
    else:
        print(f"Erro ao atualizar card {card_id}: {response.text}")
        return False