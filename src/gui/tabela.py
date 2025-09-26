# src/gui/tabela.py
import customtkinter as ctk
from tkinter import ttk
from datetime import datetime
import logging

def chave_de_ordenacao_segura(item, coluna):
    """
    Função de ordenação genérica e segura.
    Ordena por data se a coluna for 'DATAHORA', caso contrário, ordena como string.
    """
    if not isinstance(item, dict):
        return "" if coluna != "DATAHORA" else datetime.min

    valor = item.get(coluna)

    if coluna == "DATAHORA":
        if isinstance(valor, str) and valor.strip():
            try:
                return datetime.strptime(valor, '%Y-%m-%dT%H:%M:%S')
            except (ValueError, TypeError):
                logging.warning(f"Formato de data inválido: '{valor}'. Esperado 'AAAA-MM-DDTHH:MM:SS'.")
                return datetime.min
        return datetime.min
    
    return str(valor or "").lower()


class Tabela(ctk.CTkFrame):
    def __init__(self, master, colunas, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.colunas = colunas
        self.dados_pagina_atual = []
        self.configure(fg_color="transparent")
        
        # Configuração para seleção múltipla
        self.tree = ttk.Treeview(self, columns=self.colunas, show="headings", selectmode="extended")
        
        for col in self.colunas:
            # O comando 'lambda c=col:' garante que o valor de 'col' correto seja passado no momento do clique
            self.tree.heading(col, text=col, anchor="w", command=lambda c=col: self.master.ordenar_por_coluna(c))
            self.tree.column(col, anchor="w", width=140, stretch=True)
            
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.style = ttk.Style()
        self.style.theme_use("default")

    def mostrar_mensagem(self, mensagem):
        self.limpar_tabela()
        self.tree.insert("", "end", values=(mensagem,), tags=('mensagem',))
        self.tree.tag_configure('mensagem', anchor='center')
        
    def limpar_tabela(self):
        self.tree.delete(*self.tree.get_children())

    def atualizar_tabela(self, dados_pagina):
        self.limpar_tabela()
        self.dados_pagina_atual = dados_pagina
        if not dados_pagina:
             self.mostrar_mensagem("Nenhum dado encontrado.")
        else:
            for linha in dados_pagina:
                valores = [linha.get(col, "") for col in self.colunas]
                self.tree.insert("", "end", values=valores)
                
    def get_itens_selecionados(self):
        """Retorna os dados completos dos itens selecionados na Treeview."""
        indices_selecionados = self.tree.selection()
        if not indices_selecionados:
            return []
        
        dados_selecionados = []
        # Mapeia o ID do item da treeview para o índice na lista de dados da página
        for item_id in indices_selecionados:
            index = self.tree.index(item_id)
            if index < len(self.dados_pagina_atual):
                dados_selecionados.append(self.dados_pagina_atual[index])
        return dados_selecionados

    def atualizar_indicador_ordenacao(self, coluna_ordenada, ordem_desc):
        """Adiciona uma seta ▲ ou ▼ no cabeçalho da coluna para indicar a ordenação."""
        seta = ' ▼' if ordem_desc else ' ▲'
        for col in self.colunas:
            texto_cabecalho = col
            if col == coluna_ordenada:
                texto_cabecalho += seta
            self.tree.heading(col, text=texto_cabecalho)

    def atualizar_cores(self, cores):
        self.style.configure("Treeview", background=cores["alt_bg"], foreground=cores["fg"], fieldbackground=cores["alt_bg"], borderwidth=0)
        self.style.map('Treeview', background=[('selected', cores["selected_bg"])], foreground=[('selected', cores["selected_fg"])])
        self.style.configure("Treeview.Heading", background=cores["button_bg"], foreground=cores["selected_fg"], relief="flat", font=('Arial', 10, 'bold'))
        self.style.map("Treeview.Heading", background=[('active', cores["button_hover"])])