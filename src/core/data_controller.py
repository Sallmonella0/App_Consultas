# src/core/data_controller.py
import math
from datetime import datetime, timedelta
import logging

# Tenta importar as dependências que o Controller precisa da GUI/Utils.
# Se falhar (como em testes unitários sem a estrutura completa), usa fallbacks.
try:
    from src.gui.tabela import chave_de_ordenacao_segura
    from src.utils.settings_manager import ITENS_POR_PAGINA
    from src.utils.datetime_utils import parse_api_datetime_to_date
except ImportError as e:
    logging.warning(f"Dependências do DataController não encontradas: {e}. Usando fallbacks.")
    # Fallbacks para garantir que a classe é funcional
    def chave_de_ordenacao_segura(item, coluna): return item.get(coluna)
    ITENS_POR_PAGINA = 50
    def parse_api_datetime_to_date(dt_str): 
        if dt_str: 
            try: return datetime.strptime(dt_str.split(' ')[0], '%Y-%m-%d').date()
            except: return None
        return None
# ----------------------------------------------------------------------------


class DataController:
    """
    Controla a lógica de negócios para filtragem, ordenação e paginação.
    Desacopla a AppGUI dessas responsabilidades.
    """
    def __init__(self, colunas):
        self._dados_completos = []
        self._dados_filtrados = []
        self.colunas = colunas
        self.coluna_ordenacao = "DATAHORA"
        self.ordem_desc = True
        self.termo_filtro = ""
        self.coluna_filtro = "PLACA"
        self.data_inicio_filtro = None
        self.data_fim_filtro_exclusiva = None

    @property
    def dados_completos(self):
        return self._dados_completos

    @dados_completos.setter
    def dados_completos(self, novos_dados):
        """Atualiza a fonte de dados e dispara a filtragem/ordenação."""
        self._dados_completos = novos_dados
        self.aplicar_filtro() # Aplica filtro automaticamente

    def set_filtro_texto(self, termo, coluna):
        self.termo_filtro = termo.lower()
        self.coluna_filtro = coluna

    def set_filtro_data(self, data_inicio_str, data_fim_str):
        """Define os filtros de data e valida o formato (se a UI falhar)."""
        self.data_inicio_filtro = None
        self.data_fim_filtro_exclusiva = None
        
        try:
            if data_inicio_str:
                self.data_inicio_filtro = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            
            if data_fim_str:
                data_fim_date = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
                # O limite superior é o dia seguinte para ser inclusivo
                self.data_fim_filtro_exclusiva = data_fim_date + timedelta(days=1) 
        except ValueError:
            logging.warning("Tentativa de definir filtro de data com formato inválido. Revertendo para None.")
            raise # Sinaliza para a UI que a data é inválida

    def ordenar(self, coluna):
        """Define a coluna e a ordem de ordenação."""
        if self.coluna_ordenacao == coluna:
            self.ordem_desc = not self.ordem_desc
        else:
            self.coluna_ordenacao = coluna
            self.ordem_desc = True
        # A ordenação será aplicada no próximo 'aplicar_filtro'

    def aplicar_filtro(self, re_sort_only=False):
        """Aplica os filtros atuais à lista de dados completos e reordena."""
        # 1. Filtragem 
        if not re_sort_only:
            dados_filtrados = self._dados_completos
            
            # 1.1 Filtro de Texto
            if self.termo_filtro:
                if self.coluna_filtro == "TODAS":
                    dados_filtrados = [
                        item for item in dados_filtrados 
                        if self.termo_filtro in ' '.join(map(str, item.values())).lower()
                    ]
                else:
                    dados_filtrados = [item for item in dados_filtrados if self.termo_filtro in str(item.get(self.coluna_filtro, "")).lower()]

            # 1.2 Filtro de Data
            if self.data_inicio_filtro or self.data_fim_filtro_exclusiva:
                def filter_date(item):
                    item_date = parse_api_datetime_to_date(item.get("DATAHORA"))
                    if not item_date: return False 
                    
                    if self.data_inicio_filtro and item_date < self.data_inicio_filtro: return False
                    if self.data_fim_filtro_exclusiva and item_date >= self.data_fim_filtro_exclusiva: return False
                    return True
                
                dados_filtrados = [item for item in dados_filtrados if filter_date(item)]
            
            self._dados_filtrados = dados_filtrados

        # 2. Ordenação
        self._dados_filtrados = sorted(self._dados_filtrados, 
                                       key=lambda item: chave_de_ordenacao_segura(item, self.coluna_ordenacao), 
                                       reverse=self.ordem_desc)

    # --- Propriedades e Métodos de Paginação ---

    @property
    def total_registos(self):
        return len(self._dados_filtrados)

    @property
    def total_paginas(self):
        return math.ceil(self.total_registos / ITENS_POR_PAGINA) if self.total_registos else 1

    def get_dados_pagina(self, numero_pagina):
        """Retorna os dados para a página solicitada."""
        total_paginas = self.total_paginas
        
        # Garante que o número da página é válido
        numero_pagina = max(1, min(numero_pagina, total_paginas))
        
        inicio = (numero_pagina - 1) * ITENS_POR_PAGINA
        fim = inicio + ITENS_POR_PAGINA
        
        # Retorna o número da página corrigido e os dados
        return numero_pagina, self._dados_filtrados[inicio:fim]
        
    def get_dados_para_exportar(self, linhas_selecionadas=None):
        """Retorna os dados filtrados ou apenas os selecionados para exportação."""
        if linhas_selecionadas:
            return linhas_selecionadas
        return self._dados_filtrados