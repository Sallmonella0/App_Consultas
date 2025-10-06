# src/utils/data_utils.py
from datetime import datetime
import logging

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
        if isinstance(valor, str) and valor.strip():
            try:
                # Trata o formato esperado da API: 'AAAA-MM-DDTHH:MM:SS'
                return datetime.strptime(valor, '%Y-%m-%dT%H:%M:%S')
            except (ValueError, TypeError):
                logging.warning(f"Formato de data inválido: '{valor}'. Esperado 'AAAA-MM-DDTHH:MM:SS'.")
                return datetime.min
        return datetime.min
    
    # Ordena como string (case-insensitive) para todos os outros campos
    return str(valor or "").lower()