# settings_manager.py
import configparser

# Cria um objeto de configuração
config = configparser.ConfigParser()
config.read('settings.ini')

# --- Seção [App] ---
ITENS_POR_PAGINA = config.getint('App', 'itens_por_pagina', fallback=100)
AUTO_REFRESH_MINUTES = config.getint('App', 'auto_refresh_minutes', fallback=10)

# --- Seção [Cache] ---
CACHE_DURATION_MINUTES = config.getint('Cache', 'duration_minutes', fallback=15)