import requests
import base64
import json

class ConsultaAPI:
    def __init__(self, url, user, password):
        self.url = url
        # Codifica user:password em Base64
        credentials = f"{user}:{password}"
        token_bytes = base64.b64encode(credentials.encode("utf-8"))
        self.token = token_bytes.decode("utf-8")

    def consultar(self, id_mensagem):
        payload = json.dumps({"IDMENSAGEM": id_mensagem})
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.token}"
        }
        try:
            response = requests.post(self.url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()  # Levanta erro para códigos >=400
            return response.json()  # Retorna os dados já em formato dict/list
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Erro na API: {e}")
        
    
    def buscar_todos(self):
        """Retorna todos os registros da API"""
        try:
            response = requests.get(f"{self.base_url}/todos")  # ajuste para sua rota real
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Erro ao buscar todos os dados: {e}")
            return []  # retorna lista vazia se der erro