# src/core/cache.py
import sqlite3
import json
from datetime import datetime, timedelta
import logging
# --- IMPORTAÇÃO CORRIGIDA ---
from src.utils.settings_manager import CACHE_DURATION_MINUTES

# ... (o resto do ficheiro permanece o mesmo)
CACHE_DB = 'cache.db'
def init_db():
    with sqlite3.connect(CACHE_DB) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS api_cache (id INTEGER PRIMARY KEY, data TEXT NOT NULL, timestamp DATETIME NOT NULL)''')
        conn.commit()
def get_cached_data():
    try:
        with sqlite3.connect(CACHE_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data, timestamp FROM api_cache ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                data_json, timestamp_str = row
                timestamp = datetime.fromisoformat(timestamp_str)
                if datetime.now() - timestamp < timedelta(minutes=CACHE_DURATION_MINUTES):
                    logging.info("Cache válido encontrado. A carregar dados do cache.")
                    return json.loads(data_json)
                else:
                    logging.warning("Cache expirado.")
    except (sqlite3.Error, json.JSONDecodeError) as e:
        logging.error(f"Erro ao ler o cache: {e}")
    return None
def set_cached_data(data):
    try:
        with sqlite3.connect(CACHE_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM api_cache")
            data_json = json.dumps(data)
            timestamp = datetime.now().isoformat()
            cursor.execute("INSERT INTO api_cache (data, timestamp) VALUES (?, ?)", (data_json, timestamp))
            conn.commit()
            logging.info("Dados salvos no cache.")
    except sqlite3.Error as e:
        logging.error(f"Erro ao salvar no cache: {e}")
init_db()