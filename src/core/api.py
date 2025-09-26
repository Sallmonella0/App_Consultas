# src/core/api.py
import requests
import json
import logging
from src.core.cache import CacheManager 
from src.core.exceptions import APIConnectionError, APIAuthError, APIClientError, APIServerError, APIResponseError, ConsultaAPIException # NOVO: Importa exceções customizadas

def sanitizar_dados(data):
# ... (restante da função sanitizar_dados) ...
    if not isinstance(data, list): return []
    dados_limpos = []
    for item in data:
        if isinstance(item, dict):
            # Garante que DATAHORA existe
            if 'DATAHORA' not in item: item['DATAHORA'] = None
            
            # NOVO: Sanitização robusta para IDMENSAGEM (garante que seja int ou None)
            id_msg = item.get('IDMENSAGEM')
            if id_msg is not None:
                try:
                    # Tenta converter para inteiro, caso seja uma string
                    item['IDMENSAGEM'] = int(id_msg)
                except (ValueError, TypeError):
                    logging.warning(f"IDMENSAGEM com formato inválido ('{id_msg}'). Definido como None.")
                    item['IDMENSAGEM'] = None # Define como None em caso de falha
            
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
# ... (restante da função _fazer_requisicao) ...
        try:
            response = requests.post(self.base_url, auth=self.auth, json=payload, timeout=15)
            
            # CORREÇÃO: Tratamento de exceções mais detalhado (Error 2)
            if response.status_code == 401:
                raise APIAuthError()
            elif 400 <= response.status_code < 500:
                # Trata 4xx (exceto 401)
                raise APIClientError(response.status_code, response.text)
            elif 500 <= response.status_code < 600:
                # Trata 5xx
                raise APIServerError(response.status_code, response.text)
            
            response.raise_for_status() # Levanta exceções para outros erros 4xx e 5xx

            # Tenta converter para JSON
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
            # Captura outros erros de requisição
            logging.error(f"Falha na comunicação com a API: {e}")
            raise APIConnectionError(f"Erro de comunicação não especificado: {e}")
        except json.JSONDecodeError:
            raise APIResponseError("Resposta da API não é um JSON válido.")
        except ConsultaAPIException:
            raise # Lança as exceções customizadas já capturadas acima
            
    def buscar_todos(self, force_refresh=False):
# ... (restante da função buscar_todos) ...
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
        # CORREÇÃO: Remoção da validação redundante 'or not id_mensagem.isdigit()'.
        # A GUI é responsável por garantir que o ID seja um número válido antes de chamar.
        if not id_mensagem: return [] 
        
        logging.info(f"Consultando API pelo IDMENSAGEM: {id_mensagem}")
        
        # O int() levantará um ValueError se a entrada for inválida (ex: 'abc'), 
        # mas a GUI deve lidar com isso antes.
        payload = {"IDMENSAGEM": int(id_mensagem)} 
        return self._fazer_requisicao(payload)