# src/core/api.py

import requests
import logging

from src.core.cache import CacheManager
from src.core.exceptions import ConsultaAPIException

# --- CONSTANTES ---
API_TIMEOUT_SEGUNDOS = 60

class ConsultaAPI:
    """
    Classe reescrita para usar autenticação HTTP Basic em cada pedido POST,
    de acordo com o exemplo do Postman.
    """
    def __init__(self, url, user, password):
        self.url = url
        self.user = user
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.cache = CacheManager()
        logging.info("Instância de ConsultaAPI criada com o novo método de autenticação.")

    def _executar_requisicao(self, payload):
        """
        Método centralizado para executar requisições POST com autenticação Basic.
        """
        logging.info(f"Executando requisição POST para: {self.url} com payload: {payload}")
        
        try:
            response = self.session.post(
                self.url,
                json=payload,
                auth=(self.user, self.password),
                timeout=API_TIMEOUT_SEGUNDOS
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            msg = f"Erro {e.response.status_code} ao acessar {self.url}."
            logging.error(f"{msg} Resposta: {e.response.text}")
            raise ConsultaAPIException(msg)
        except requests.exceptions.Timeout:
            msg = f"A requisição para {self.url} excedeu o tempo limite de {API_TIMEOUT_SEGUNDOS} segundos."
            logging.error(msg)
            raise ConsultaAPIException(msg)
        except requests.exceptions.RequestException as e:
            msg = f"Erro de conexão ao tentar acessar {self.url}: {e}"
            logging.error(msg)
            raise ConsultaAPIException(msg)
        except Exception as e:
            msg = f"Ocorreu um erro inesperado na requisição: {e}"
            logging.error(msg)
            raise ConsultaAPIException(msg)

    def buscar_todos(self, force_refresh=False):
        """
        Busca todos os registros enviando IDMENSAGEM = 0.
        """
        if not force_refresh:
            # --- ALTERAÇÃO AQUI ---
            dados_cache = self.cache.get_cached_data()
            if dados_cache:
                logging.info("Retornando dados do cache.")
                return dados_cache

        logging.info("Buscando dados frescos da API...")
        payload = {"IDMENSAGEM": 0}
        dados = self._executar_requisicao(payload)
        
        if dados:
            # --- ALTERAÇÃO AQUI ---
            self.cache.set_cached_data(dados)
            logging.info("Dados salvos no cache.")
            
        return dados

    def consultar(self, id_mensagem):
        """
        Consulta um registro específico pelo IDMENSAGEM.
        """
        payload = {"IDMENSAGEM": int(id_mensagem)}
        return self._executar_requisicao(payload)

    def consultar_by_trackid(self, track_id):
        """
        Consulta o último registro de um cliente pelo TrackID.
        """
        payload = {"TrackID": track_id}
        return self._executar_requisicao(payload)