# src/core/api.py
import requests
import json
import logging
from src.core.cache import CacheManager 
from src.core.exceptions import APIConnectionError, APIAuthError, APIClientError, APIServerError, APIResponseError, ConsultaAPIException
# CORREÇÃO: Importa utilitário para ordenação por data
from src.utils.data_utils import chave_de_ordenacao_segura

def sanitizar_dados(data):
    if not isinstance(data, list): return []
    dados_limpos = []
    for item in data:
        if isinstance(item, dict):
            if 'DATAHORA' not in item: item['DATAHORA'] = None
            
            id_msg = item.get('IDMENSAGEM')
            if id_msg is not None:
                try:
                    item['IDMENSAGEM'] = int(id_msg)
                except (ValueError, TypeError):
                    logging.warning(f"IDMENSAGEM com formato inválido ('{id_msg}'). Definido como None.")
                    item['IDMENSAGEM'] = None
            
            dados_limpos.append(item)
    return dados_limpos

class ConsultaAPI:
    def __init__(self, url, user, password):
        self.base_url = url
        self.auth = (user, password)
        self.headers = {'Content-Type': 'application/json'}
        self.cache_manager = CacheManager() 
        logging.info("Instância de ConsultaAPI criada.")
        
    def _fazer_requisicao(self, payload):
        logging.debug(f"Payload enviado: {payload}")
        try:
            response = requests.post(self.base_url, auth=self.auth, json=payload, timeout=15)
            
            if response.status_code == 401:
                raise APIAuthError()
            elif 400 <= response.status_code < 500:
                raise APIClientError(response.status_code, response.text)
            elif 500 <= response.status_code < 600:
                raise APIServerError(response.status_code, response.text)
            
            response.raise_for_status()

            dados_brutos = response.json()
            if not isinstance(dados_brutos, list):
                 raise APIResponseError("Resposta JSON inesperada. Esperava-se uma lista de registos.")
                 
            dados_sanitizados = sanitizar_dados(dados_brutos)
            return dados_sanitizados
        
        except requests.exceptions.Timeout:
            raise APIConnectionError("Timeout de requisição.")
        except requests.exceptions.ConnectionError:
            raise APIConnectionError("Falha de conexão com a API.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Falha na comunicação com a API: {e}")
            raise APIConnectionError(f"Erro de comunicação não especificado: {e}")
        except json.JSONDecodeError:
            raise APIResponseError("Resposta da API não é um JSON válido.")
        except ConsultaAPIException:
            raise
        except Exception as e:
            logging.error(f"Erro inesperado durante a requisição: {e}")
            raise ConsultaAPIException(f"Erro inesperado: {e}")
            
    def buscar_todos(self, force_refresh=False):
        if not force_refresh:
            cached_data = self.cache_manager.get_cached_data() 
            if cached_data:
                return sanitizar_dados(cached_data)
        
        logging.info("Buscando dados frescos da API...")
        payload = {"IDMENSAGEM": 0}
        fresh_data = self._fazer_requisicao(payload)
        
        if fresh_data:
            self.cache_manager.set_cached_data(fresh_data)
            
        return fresh_data
        
    def consultar(self, id_mensagem):
        if not id_mensagem: return [] 
        
        logging.info(f"Consultando API pelo IDMENSAGEM: {id_mensagem}")
        
        payload = {"IDMENSAGEM": int(id_mensagem)} 
        return self._fazer_requisicao(payload)

    # CORREÇÃO: Retorna apenas o registo mais recente
    def consultar_by_trackid(self, track_id):
        """
        Consulta a API pelo TrackID e retorna o registo mais recente.
        """
        if not track_id:
            return None

        logging.info(f"Consultando API pelo TrackID: {track_id}")

        payload = {"TrackID": track_id} 
        dados = self._fazer_requisicao(payload)

        if not dados:
            return None

        # Encontra o registo com a DATAHORA mais recente
        registo_mais_recente = max(dados, key=lambda item: chave_de_ordenacao_segura(item, 'DATAHORA'))
        
        return registo_mais_recente