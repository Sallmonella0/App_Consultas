# src/utils/data_utils.py
from datetime import datetime
import logging
# CORREÇÃO: Importa a função de parsing unificada
from src.utils.datetime_utils import parse_api_datetime_to_date

def chave_de_ordenacao_segura(item, coluna):
    """
    Função de ordenação genérica e segura.
    Ordena por data se a coluna for 'DATAHORA', caso contrário, ordena como string.
    Movida de src/gui/tabela.py para desacoplar a lógica de ordenação da GUI.
    """
    if not isinstance(item, dict):
        # Trata items não-dict que podem aparecer (e.g., None)
        return "" if coluna != "DATAHORA" else datetime.min

    valor = item.get(coluna)

    if coluna == "DATAHORA":
        # CORREÇÃO: Usa a função de parsing centralizada para consistência.
        # `parse_api_datetime_to_date` já retorna um objeto `date` ou `None`.
        parsed_date = parse_api_datetime_to_date(valor)
        # Retorna uma data mínima se o parsing falhar, garantindo que valores inválidos
        # fiquem no início ou no fim da ordenação de forma consistente.
        return parsed_date if parsed_date else datetime.min

    # Ordena como string (case-insensitive) para todos os outros campos
    return str(valor or "").lower()