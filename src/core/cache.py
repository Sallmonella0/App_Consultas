# src/core/cache.py
import sqlite3
import json
from datetime import datetime, timedelta
import logging
# --- IMPORTAÇÃO CORRIGIDA ---
from src.utils.settings_manager import CACHE_DURATION_MINUTES

CACHE_DB = 'cache.db'
CACHE_ID = 1 # Chave fixa para o cache de linha única

class CacheManager:
    """Gerencia a leitura e escrita de dados de cache usando SQLite."""
    
    def __init__(self):
        """Inicializa o banco de dados ao criar a instância."""
        self._init_db()

    def _init_db(self):
        """Inicializa a tabela de cache, se ainda não existir."""
        try:
            with sqlite3.connect(CACHE_DB) as conn:
                cursor = conn.cursor()
                # Adiciona CACHE_ID como chave primária
                cursor.execute('''CREATE TABLE IF NOT EXISTS api_cache (
                                    id INTEGER PRIMARY KEY, 
                                    data TEXT NOT NULL, 
                                    timestamp DATETIME NOT NULL)''')
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Erro ao inicializar o banco de dados de cache: {e}")

    def get_cached_data(self):
        """Recupera os dados de cache válidos (não expirados)."""
        try:
            with sqlite3.connect(CACHE_DB) as conn:
                cursor = conn.cursor()
                # Busca pelo ID fixo
                cursor.execute("SELECT data, timestamp FROM api_cache WHERE id = ?", (CACHE_ID,))
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

    def set_cached_data(self, data):
        """Salva os dados no cache usando INSERT OR REPLACE para upsert atômico."""
        try:
            with sqlite3.connect(CACHE_DB) as conn:
                cursor = conn.cursor()
                data_json = json.dumps(data)
                timestamp = datetime.now().isoformat()
                
                # CORREÇÃO: Usar INSERT OR REPLACE INTO para upsert atômico (Error 4)
                cursor.execute("""
                    INSERT OR REPLACE INTO api_cache (id, data, timestamp) 
                    VALUES (?, ?, ?)
                    """, (CACHE_ID, data_json, timestamp))
                
                conn.commit()
                logging.info("Dados salvos no cache.")
        except sqlite3.Error as e:
            logging.error(f"Erro ao salvar no cache: {e}")