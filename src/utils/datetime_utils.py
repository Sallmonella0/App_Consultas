# src/utils/datetime_utils.py
from datetime import datetime

# Formato de data de entrada para os campos de filtro da UI
UI_DATE_FORMAT = '%Y-%m-%d'

def parse_api_datetime_to_date(datetime_str):
    """
    Converte a string de data/hora da API (ex: YYYY-MM-DDTHH:MM:SS...) 
    para um objeto date para facilitar a comparação.
    """
    if not datetime_str:
        return None
    try:
        # A API retorna um formato ISO que pode ser simplificado para parsing
        # Ex: "2025-09-25T14:30:00"
        return datetime.fromisoformat(datetime_str.replace("Z", "").replace("T", " ")).date()
    except (ValueError, TypeError):
        # Em caso de erro de parsing, retorna None
        return None

def is_valid_ui_date(date_str):
    """Verifica se a string de data da UI está no formato AAAA-MM-DD."""
    if not date_str:
        return True # Campo vazio é considerado válido (ignorado no filtro)
    try:
        datetime.strptime(date_str, UI_DATE_FORMAT)
        return True
    except ValueError:
        return False