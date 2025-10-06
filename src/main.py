# src/main.py
import logging
from dotenv import load_dotenv 
import os 

# --- IMPORTAÇÕES CORRIGIDAS ---
from src.gui.app_gui_ctk import AppGUI
from src.core.api import ConsultaAPI
from src.utils import logger_config

# Configura o sistema de logging
logger_config.setup_logging()
logging.info("Aplicação iniciada.")

# --- CORREÇÃO DE SEGURANÇA: Carregar variáveis de ambiente do .env ---
load_dotenv()
URL_API = os.getenv("API_URL")
USER = os.getenv("API_USER")
PASSWORD = os.getenv("API_PASSWORD")

if __name__ == "__main__":
    if not all([URL_API, USER, PASSWORD]):
        logging.error("Credenciais da API não encontradas. Certifique-se de que o arquivo .env está configurado corretamente (API_URL, API_USER, API_PASSWORD).")
        # Em uma aplicação real, você pode querer adicionar uma mensagem de erro na tela antes de encerrar.
    
    api = ConsultaAPI(URL_API, USER, PASSWORD)
    app = AppGUI(api)
    app.mainloop()