# cache.py
import sqlite3
import json
import os

class CacheLocal:
    def __init__(self, arquivo="cache.db"):
        # Cria banco no diretório do projeto
        self.conn = sqlite3.connect(arquivo, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                id_mensagem INTEGER PRIMARY KEY,
                dados TEXT
            )
        """)
        self.conn.commit()

    def salvar(self, id_mensagem, dados):
        self.conn.execute(
            "REPLACE INTO cache (id_mensagem, dados) VALUES (?, ?)",
            (id_mensagem, json.dumps(dados))
        )
        self.conn.commit()

    def carregar(self, id_mensagem):
        cursor = self.conn.execute(
            "SELECT dados FROM cache WHERE id_mensagem = ?",
            (id_mensagem,)
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None
