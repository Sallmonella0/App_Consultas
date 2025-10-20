# src/main.py

import logging
import json # Adicionar import
import sys
from PyQt6.QtWidgets import QApplication

from src.gui.app_gui_pyqt import AppGUI
from src.core.api import ConsultaAPI
from src.utils import logger_config

# Configura o sistema de logging
logger_config.setup_logging()
logging.info("Aplicação iniciada.")

# --- CARREGAMENTO DOS CLIENTES ---
def carregar_clientes():
    """Carrega a configuração dos clientes a partir de clientes.json."""
    try:
        with open('clientes.json', 'r', encoding='utf-8') as f:
            clientes = json.load(f)
        if not clientes:
            logging.error("O ficheiro clientes.json está vazio.")
            sys.exit("Erro: O ficheiro clientes.json está vazio.")
        return clientes
    except FileNotFoundError:
        logging.error("O ficheiro clientes.json não foi encontrado.")
        sys.exit("Erro: Ficheiro de configuração de clientes não encontrado.")
    except json.JSONDecodeError:
        logging.error("Erro ao descodificar o ficheiro clientes.json.")
        sys.exit("Erro: Formato inválido no ficheiro clientes.json.")

if __name__ == "__main__":
    clientes = carregar_clientes()

    # Lógica de arranque do PyQt
    app = QApplication(sys.argv)

    # A API será inicializada dentro da GUI
    main_window = AppGUI(clientes) # Passar a lista de clientes para a GUI
    main_window.show()

    sys.exit(app.exec())