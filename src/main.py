# main.py
from gui.app_gui_ctk import AppGUI
from core.api import ConsultaAPI
from utils import logger_config

# Configura o sistema de logging ANTES de qualquer outra coisa
logger_config.setup_logging()

URL_API = "http://85.209.93.16/api/data"
USER = "vip"
PASSWORD = "83114d8fc3164de4e85b4e6ee8a04bbd"

if __name__ == "__main__":
    api = ConsultaAPI(URL_API, USER, PASSWORD)
    app = AppGUI(api)
    app.mainloop()
    