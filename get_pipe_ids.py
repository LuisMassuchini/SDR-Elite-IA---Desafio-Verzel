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
query = f"""
query {{
  pipe(id: "{PIPE_ID}") {{
    start_form_fields {{
        id
        label
    }}
  }}
}}
"""
# -------------------------

if not PIPE_ID or not os.getenv('PIPEFY_ACCESS_TOKEN'):
    print("ERRO: Verifique se PIPE_ID e PIPEFY_ACCESS_TOKEN estão corretos no seu .env")
else:
    response = requests.post(PIPEFY_URL, headers=HEADERS, json={'query': query})
    if response.status_code == 200:
        data = response.json()
        print("\n--- IDs ENCONTRADOS NO SEU PIPEFY (Formulário Inicial) ---")
        
       
        if data.get('data') and data['data'].get('pipe') and data['data']['pipe'].get('start_form_fields'):
             fields_list = data['data']['pipe']['start_form_fields']
             if not fields_list:
                 print("\nERRO: Nenhum campo encontrado no Formulário Inicial.")
                 print("Verifique se você salvou os campos no Pipefy (Nome, E-mail, etc.)")
             
             for field in fields_list:
                 print(f"  Label: {field['label']:<25} ID: {field['id']}")
        # -------------------------
        else:
            print("Erro na Query ou ID do Pipe incorreto.")
            print(f"Resposta da API: {data}")
    else:
        print(f"Erro de Conexão. Status: {response.status_code}")
        print(response.text)