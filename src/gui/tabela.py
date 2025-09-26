# src/gui/tabela.py
import customtkinter as ctk
from tkinter import ttk
from datetime import datetime
import math
import logging
from src.utils.settings_manager import ITENS_POR_PAGINA

def chave_de_ordenacao_data_segura(item):
    """
    Função à prova de falhas para ordenar por data.
    Lida com chaves em falta, valores None, e formatos de data incorretos.
    """
    if not isinstance(item, dict):
        return datetime.min

    data_str = item.get("DATAHORA")

    if isinstance(data_str, str):
        try:
            return datetime.strptime(data_str, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            # Adiciona um log para diagnosticar dados mal formatados
            logging.debug(f"Formato de data inválido encontrado: '{data_str}'")
            return datetime.min
            
    return datetime.min

class Tabela(ctk.CTkFrame):
    def __init__(self, master, colunas, **kwargs):
        super().__init__(master, **kwargs)
        self.colunas = colunas
        self.dados_completos = []
        self.dados_exibidos = []
        self.pagina_atual = 1
        self.itens_por_pagina = ITENS_POR_PAGINA
        self.total_paginas = 1
        self.style = ttk.Style()
        self.configure(fg_color="transparent")
        self.tree = ttk.Treeview(self, columns=self.colunas, show="headings", selectmode="browse")
        for col in self.colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=140, stretch=True)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def mostrar_mensagem(self, mensagem):
        self.tree.delete(*self.tree.get_children())
        self.tree.insert("", "end", values=(mensagem,), tags=('mensagem',))
        self.tree.tag_configure('mensagem', anchor='center')

    def atualizar_dados_internos(self, dados):
        """APENAS atualiza a lista de dados. Não filtra nem reordena."""
        self.dados_completos = dados

    def renderizar_tabela(self, termo="", coluna="PLACA", ordem_desc=True):
        """Filtra, ordena e desenha os dados na tabela."""
        self.master.configure(cursor="watch")
        self.master.update_idletasks()
        try:
            if termo.strip():
                termo = termo.lower()
                dados_filtrados = [ item for item in self.dados_completos if termo in str(item.get(coluna, "")).lower() ]
            else:
                dados_filtrados = self.dados_completos

            dados_ordenados = sorted(
                dados_filtrados,
                key=chave_de_ordenacao_data_segura,
                reverse=ordem_desc
            )

            self.dados_exibidos = dados_ordenados
            self.total_paginas = math.ceil(len(self.dados_exibidos) / self.itens_por_pagina) if self.dados_exibidos else 1
            self.ir_para_pagina(1)

        finally:
            self.master.configure(cursor="")

    def _popular_tabela(self, dados_pagina):
        self.tree.delete(*self.tree.get_children())
        if not dados_pagina and self.pagina_atual == 1:
             self.mostrar_mensagem("Nenhum dado encontrado.")
        else:
            for linha in dados_pagina:
                valores = [linha.get(col, "") for col in self.colunas]
                self.tree.insert("", "end", values=valores)

    def ir_para_pagina(self, numero_pagina):
        if not self.dados_exibidos:
            self._popular_tabela([])
            return 1, 1
        if numero_pagina < 1: numero_pagina = 1
        if numero_pagina > self.total_paginas: numero_pagina = self.total_paginas
        self.pagina_atual = numero_pagina
        inicio = (self.pagina_atual - 1) * self.itens_por_pagina
        fim = inicio + self.itens_por_pagina
        dados_da_pagina = self.dados_exibidos[inicio:fim]
        self._popular_tabela(dados_da_pagina)
        return self.pagina_atual, self.total_paginas

    def atualizar_cores(self, cores):
        self.style.theme_use("default")
        self.style.configure("Treeview", background=cores["alt_bg"], foreground=cores["fg"], fieldbackground=cores["alt_bg"], borderwidth=0)
        self.style.map('Treeview', background=[('selected', cores["selected_bg"])], foreground=[('selected', cores["selected_fg"])])
        self.style.configure("Treeview.Heading", background=cores["button_bg"], foreground=cores["selected_fg"], relief="flat", font=('Arial', 10, 'bold'))
        self.style.map("Treeview.Heading", background=[('active', cores["button_hover"])])