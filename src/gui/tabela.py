# src/gui/tabela.py
import customtkinter as ctk
from tkinter import ttk
# datetime e logging removidos pois chave_de_ordenacao_segura foi movida para src/utils/data_utils.py

class Tabela(ctk.CTkFrame):
    # ALTERAÇÃO: Recebe colunas_completas e colunas_visiveis_iniciais
    def __init__(self, master, colunas_completas, colunas_visiveis_iniciais, on_sort_command, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.colunas_completas = colunas_completas  # Lista completa de todas as colunas possíveis
        self.visible_colunas = colunas_visiveis_iniciais  # Lista de colunas atualmente visíveis
        self.on_sort_command = on_sort_command # ARMAZENA O COMANDO DE ORDENAÇÃO NA INSTÂNCIA

        self.configure(fg_color="transparent")
        
        # Configuração para seleção múltipla
        # A Treeview é criada com TODAS as colunas possíveis
        self.tree = ttk.Treeview(self, columns=self.colunas_completas, show="headings", selectmode="extended")
        
        # Cria e empacota a barra de rolagem e a treeview
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.style = ttk.Style()
        self.style.theme_use("default")

        # Chamada inicial para configurar as colunas visíveis
        self.reconstruir_colunas(self.visible_colunas, self.on_sort_command)

    def reconstruir_colunas(self, novas_colunas_visiveis, on_sort_command):
        """
        Reconfigura a Treeview para mostrar apenas as colunas especificadas.
        Isto é feito manipulando o displaycolumns e a largura das colunas.
        """
        self.visible_colunas = novas_colunas_visiveis
        
        # 1. Oculta todas as colunas e zera a largura
        for col in self.colunas_completas:
            # CORREÇÃO: Usa command="" para remover a função de ordenação (necessário para Tkinter/Tcl)
            self.tree.heading(col, text=col, anchor="w", command="") 
            # Define largura para 0 e stretch para False para ocultar
            self.tree.column(col, width=0, stretch=False) 

        # 2. Define as colunas a serem exibidas
        self.tree.config(displaycolumns=self.visible_colunas)
        
        # 3. Reestabelece a largura, o stretch e o comando de ordenação para as colunas visíveis
        for col in self.visible_colunas:
            # Reestabelece o comando de ordenação usando a função passada no __init__
            self.tree.heading(col, text=col, anchor="w", command=lambda c=col: on_sort_command(c))
            # Define largura e stretch para as colunas visíveis
            self.tree.column(col, anchor="w", width=140, stretch=True)
        
        # Garante que a GUI é re-renderizada com a nova estrutura da tabela
        # Note: self.master.renderizar_dados() pode causar um loop se chamado aqui, 
        # mas neste caso, é necessário para redesenhar a tabela corretamente após a mudança estrutural.
        if self.master:
            self.master.renderizar_dados() 
        
    def mostrar_mensagem(self, mensagem):
        self.limpar_tabela()
        # Garante que a mensagem ocupa o espaço da primeira coluna visível
        num_cols_visiveis = len(self.visible_colunas)
        if num_cols_visiveis > 0:
            # Coloca a mensagem na coluna que seria a primeira a aparecer
            dummy_values = ["" for _ in range(len(self.colunas_completas))]
            # Encontra o índice da primeira coluna visível
            primeira_coluna_index = self.colunas_completas.index(self.visible_colunas[0])
            dummy_values[primeira_coluna_index] = mensagem
            
            self.tree.insert("", "end", values=dummy_values, tags=('mensagem',))
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
                # Usa todas as colunas completas para mapear os valores, a Treeview decide quais mostrar
                valores = [linha.get(col, "") for col in self.colunas_completas]
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
        seta = ' ▼' if ordem_desc else ' ▲'
        for col in self.visible_colunas: 
            texto_cabecalho = col
            if col == coluna_ordenada:
                texto_cabecalho += seta
            self.tree.heading(col, text=texto_cabecalho)

    def atualizar_cores(self, cores):
        # ... (Mantém a lógica de cores)
        self.style.configure("Treeview", background=cores["alt_bg"], foreground=cores["fg"], fieldbackground=cores["alt_bg"], borderwidth=0)
        self.style.map('Treeview', background=[('selected', cores["selected_bg"])], foreground=[('selected', cores["selected_fg"])])
        self.style.configure("Treeview.Heading", background=cores["button_bg"], foreground=cores["selected_fg"], relief="flat", font=('Arial', 10, 'bold'))
        self.style.map("Treeview.Heading", background=[('active', cores["button_hover"])])