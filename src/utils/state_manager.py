# src/utils/state_manager.py
import json
import os
import logging

STATE_FILE = 'app_state.json'

def save_state(state_data):
    """Salva o estado da aplicação (dicionário) num ficheiro JSON."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state_data, f, indent=4)
        logging.info(f"Estado da aplicação salvo em {STATE_FILE}.")
    except IOError as e:
        logging.error(f"Não foi possível salvar o estado da aplicação: {e}")

def load_state():
    """Carrega o estado da aplicação a partir do ficheiro JSON."""
    if not os.path.exists(STATE_FILE):
        logging.warning(f"Ficheiro de estado '{STATE_FILE}' não encontrado. A usar configurações padrão.")
        return {} # Retorna um dicionário vazio se o ficheiro não existir
    
    try:
        with open(STATE_FILE, 'r') as f:
            state_data = json.load(f)
        logging.info(f"Estado da aplicação carregado de {STATE_FILE}.")
        return state_data
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Não foi possível carregar o estado da aplicação: {e}")
        return {}