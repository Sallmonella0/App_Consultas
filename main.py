# main.py
from app_gui_ctk import AppGUI
from api import ConsultaAPI

URL_API = "http://85.209.93.16/api/data"
TOKEN = "dmlwOjgzMTE0ZDhmYzMxNjRkZTRlODViNGU2ZWU4YTA0YmJk"

api = ConsultaAPI(URL_API, TOKEN)  # ✅ somente url e token
app = AppGUI(api)
app.mainloop()
