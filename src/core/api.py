# api.py
import requests
import json
from core import cache
import logging

def sanitizar_dados(data):
    if not isinstance(data, list):
        return []
    dados_limpos = []
    for item in data:
        if isinstance(item, dict):
            if 'DATAHORA' not in item:
                item['DATAHORA'] = None
            dados_limpos.append(item)
    return dados_limpos

class ConsultaAPI:
    def __init__(self, url, user, password):
        self.base_url = url
        self.auth = (user, password)
        self.headers = {'Content-Type': 'application/json'}
        logging.info("Instância de ConsultaAPI criada.")

    def _fazer_requisicao(self, payload):
        try:
            response = requests.post(self.base_url, auth=self.auth, json=payload, timeout=15)
            response.raise_for_status()
            dados_brutos = response.json()
            dados_sanitizados = sanitizar_dados(dados_brutos)
            return dados_sanitizados
        except requests.exceptions.RequestException as e:
            logging.error(f"Falha na comunicação com a API: {e}")
            raise Exception(f"Erro de comunicação com a API: {e}")

    def buscar_todos(self, force_refresh=False):
        if not force_refresh:
            cached_data = cache.get_cached_data()
            if cached_data:
                return sanitizar_dados(cached_data)
        
        logging.info("Buscando dados frescos da API...")
        payload = {"IDMENSAGEM": 0}
        fresh_data = self._fazer_requisicao(payload)
        
        if fresh_data:
            cache.set_cached_data(fresh_data)
            
        return fresh_data

    def consultar(self, id_mensagem):
        if not id_mensagem or not id_mensagem.isdigit():
            return []
        logging.info(f"Consultando API pelo IDMENSAGEM: {id_mensagem}")
        payload = {"IDMENSAGEM": int(id_mensagem)}
        return self._fazer_requisicao(payload)