# src/core/data_controller.py

import logging
from datetime import datetime
import math

# --- IMPORTAÇÕES CORRIGIDAS ---
from src.utils.data_utils import chave_de_ordenacao_segura

class DataController:
    """
    Controla o estado dos dados da aplicação, incluindo ordenação,
    filtragem e paginação.
    """
    def __init__(self, todas_as_colunas, itens_por_pagina):
        self.dados_completos = []
        self.dados_filtrados = []
        
        self.todas_as_colunas = todas_as_colunas
        self.itens_por_pagina = itens_por_pagina
        
        # Estado de ordenação
        self.coluna_ordenacao = "DATAHORA"
        self.ordem_desc = True
        
        # Estado de filtragem
        self.termo_filtro = ""
        self.coluna_filtro = "TODAS"
        self.data_inicio_filtro = None
        self.data_fim_filtro = None
        
        # Estado de paginação
        self.total_registos = 0
        self.total_paginas = 1

    def set_filtro_texto(self, termo, coluna):
        """Define os parâmetros para o filtro de texto."""
        self.termo_filtro = termo.strip().lower() if termo else ""
        self.coluna_filtro = coluna

    def set_filtro_data(self, data_inicio, data_fim):
        """Define os parâmetros para o filtro de data."""
        self.data_inicio_filtro = data_inicio
        self.data_fim_filtro = data_fim
    
    def aplicar_filtro(self, re_sort_only=False):
        """
        Aplica os filtros de texto e data aos dados.
        Se re_sort_only for True, apenas reordena os dados já filtrados.
        """
        if not re_sort_only:
            dados_a_filtrar = self.dados_completos
            
            # 1. Filtro por data
            dados_filtrados_data = []
            if self.data_inicio_filtro and self.data_fim_filtro:
                for item in dados_a_filtrar:
                    try:
                        # Assumindo formato 'YYYY-MM-DD HH:MM:SS'
                        data_item_str = item.get("DATAHORA", "").split(" ")[0]
                        data_item = datetime.strptime(data_item_str, '%Y-%m-%d').date()
                        if self.data_inicio_filtro <= data_item <= self.data_fim_filtro:
                            dados_filtrados_data.append(item)
                    except (ValueError, IndexError):
                        continue # Ignora formatos de data inválidos
            else:
                dados_filtrados_data = dados_a_filtrar

            # 2. Filtro por texto
            if self.termo_filtro:
                if self.coluna_filtro == "TODAS":
                    dados_filtrados_texto = [
                        item for item in dados_filtrados_data
                        if any(str(value).lower().find(self.termo_filtro) != -1 
                               for value in item.values())
                    ]
                else:
                    dados_filtrados_texto = [
                        item for item in dados_filtrados_data
                        if str(item.get(self.coluna_filtro, "")).lower().find(self.termo_filtro) != -1
                    ]
            else:
                dados_filtrados_texto = dados_filtrados_data
                
            self.dados_filtrados = dados_filtrados_texto
        
        # 3. Ordenação
        self.dados_filtrados.sort(
            key=lambda item: chave_de_ordenacao_segura(item, self.coluna_ordenacao),
            reverse=self.ordem_desc
        )
        
        # 4. Atualizar contadores de paginação
        self.total_registos = len(self.dados_filtrados)
        self.total_paginas = math.ceil(self.total_registos / self.itens_por_pagina) if self.total_registos > 0 else 1

    def ordenar(self, coluna):
        """Define a coluna de ordenação e inverte a ordem se a mesma coluna for clicada."""
        if self.coluna_ordenacao == coluna:
            self.ordem_desc = not self.ordem_desc
        else:
            self.coluna_ordenacao = coluna
            self.ordem_desc = True # Padrão para novas colunas é descendente

    def get_dados_pagina(self, numero_pagina):
        """Retorna os dados correspondentes a uma página específica."""
        if not self.dados_filtrados:
            return 1, []

        numero_pagina = max(1, min(numero_pagina, self.total_paginas))
        
        inicio = (numero_pagina - 1) * self.itens_por_pagina
        fim = inicio + self.itens_por_pagina
        
        return numero_pagina, self.dados_filtrados[inicio:fim]

    def get_record_by_id(self, record_id):
        """Encontra e retorna um registo completo pelo seu IDMENSAGEM."""
        try:
            record_id_int = int(record_id)
            for record in self.dados_completos:
                if record.get('IDMENSAGEM') == record_id_int:
                    return record
        except (ValueError, TypeError):
            pass
        return None