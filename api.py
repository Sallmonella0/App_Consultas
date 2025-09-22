import requests

class ConsultaAPI:
    def __init__(self, url, token):
        """
        Inicializa a classe com a URL da API e o token de autenticação (Basic Auth codificado).
        """
        self.url = url
        self.token = token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.token}"
        }

    def consultar(self, id_msg=0, filtro_coluna=None, filtro_valor=None):
        """
        Consulta a API.

        id_msg: int -> IDMENSAGEM para filtrar a consulta (0 retorna todos)
        filtro_coluna: str -> Nome da coluna para filtro opcional
        filtro_valor: str -> Valor do filtro opcional
        """
        payload = {"IDMENSAGEM": int(id_msg)}

        # Adiciona filtro somente se informado
        if filtro_coluna and filtro_valor and filtro_valor.strip() != "":
            payload["FILTRO"] = {filtro_coluna: filtro_valor.strip()}

        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload,
                timeout=10  # evita travamento
            )
            response.raise_for_status()  # levanta erro para códigos != 2xx
            return response.json()  # retorna lista/dicionário
        except requests.exceptions.HTTPError as errh:
            print("HTTP Error:", errh)
            return []
        except requests.exceptions.ConnectionError as errc:
            print("Connection Error:", errc)
            return []
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
            return []
        except requests.exceptions.RequestException as err:
            print("Erro inesperado:", err)
            return []
