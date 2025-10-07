# src/main.py

import logging
from dotenv import load_dotenv
import os
import sys
from PyQt6.QtWidgets import QApplication

from src.gui.app_gui_pyqt import AppGUI
from src.core.api import ConsultaAPI
from src.utils import logger_config

# Configura o sistema de logging
logger_config.setup_logging()
logging.info("Aplicação iniciada.")

# Carregar variáveis de ambiente
load_dotenv()
URL_API = os.getenv("API_URL")
USER = os.getenv("API_USER")
PASSWORD = os.getenv("API_PASSWORD")


if __name__ == "__main__":
    if not all([URL_API, USER, PASSWORD]):
        logging.error("Credenciais da API não encontradas...")
        sys.exit("Erro: Credenciais não configuradas.")

    # Lógica de arranque do PyQt
    app = QApplication(sys.argv)

    api = ConsultaAPI(URL_API, USER, PASSWORD)
    main_window = AppGUI(api)
    main_window.show()

    sys.exit(app.exec())