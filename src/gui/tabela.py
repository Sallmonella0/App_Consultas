# src/gui/tabela.py
import customtkinter as ctk
from tkinter import ttk
import logging
from src.utils.data_utils import chave_de_ordenacao_segura # Presume-se que a utilidade de ordenação está aqui ou é importada.

class Tabela(ctk.CTkFrame):
    """
    Componente de Tabela usando ttk.Treeview dentro de um CTkFrame,
    com suporte a CustomTkinter Scrollbars.
    """
    # NOVO: on_rebuild_command adicionado para injetar o método renderizar_dados da AppGUI
    def __init__(self, master, all_colunas, visible_colunas, on_sort_command, on_rebuild_command):
        super().__init__(master)
        self.master = master
        self.all_colunas = all_colunas
        self.visible_colunas = visible_colunas
        self.on_sort_command = on_sort_command
        self.on_rebuild_command = on_rebuild_command # FIX: Salva o callback
        
        # Larguras padrão das colunas
        self.column_widths = {
            "IDMENSAGEM": 100, "DATAHORA": 150, "PLACA": 80, 
            "LATITUDE": 100, "LONGITUDE": 100, "TrackID": 150
        }
        
        self.tree = None
        self.mensagem_label = None 
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Cria a tabela e dispara a primeira renderização via callback
        self.reconstruir_colunas(self.visible_colunas, self.on_sort_command)

    def reconstruir_colunas(self, novas_colunas_visiveis, on_sort_command):
        """Destrói e recria a Treeview para aplicar uma nova lista de colunas."""
        # 1. Destruir Treeview e Scrollbars antigos, se existirem
        if self.tree:
            self.tree.destroy()
            self.vsb.destroy()
            self.hsb.destroy()
        
        self.visible_colunas = novas_colunas_visiveis
        
        # 2. Criação da nova Treeview
        self.tree = ttk.Treeview(self, 
                                 columns=self.visible_colunas, 
                                 show='headings', 
                                 selectmode='extended')

        # 3. Criar Scrollbars
        self.vsb = ctk.CTkScrollbar(self, command=self.tree.yview)
        self.hsb = ctk.CTkScrollbar(self, orientation="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        # 4. Posicionar Treeview e Scrollbars
        self.tree.grid(row=0, column=0, sticky='nsew')
        self.vsb.grid(row=0, column=1, sticky='ns')
        self.hsb.grid(row=1, column=0, sticky='ew')
        
        # 5. Configurar Cabeçalhos e Colunas
        for col_name in self.visible_colunas:
            width = self.column_widths.get(col_name, 120)
            self.tree.heading(col_name, text=col_name, command=lambda c=col_name: on_sort_command(c))
            self.tree.column(col_name, width=width, anchor='w')
            
        # 6. Label de Mensagem (Carregando...)
        self.mensagem_label = ctk.CTkLabel(self, text="", fg_color="transparent")
        self.mensagem_label.grid(row=0, column=0, sticky='nsew')
        self.mensagem_label.grid_remove()

        # 7. Disparar a re-renderização dos dados na AppGUI (CHAMADA CORRIGIDA)
        self.on_rebuild_command() 

    def atualizar_tabela(self, dados):
        """Insere os dados da página atual na Treeview."""
        # 1. Limpar tabela existente
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 2. Ocultar mensagem de carregamento
        if self.mensagem_label:
            self.mensagem_label.grid_remove()
            
        # 3. Inserir novos dados
        for item in dados:
            # Usa o iid=IDMENSAGEM para identificação
            item_id = item.get('IDMENSAGEM')
            values = [item.get(col, "") for col in self.visible_colunas]
            self.tree.insert('', 'end', values=values, iid=item_id)

    def mostrar_mensagem(self, mensagem):
        """Exibe uma mensagem na área da tabela (e.g., 'Carregando...')."""
        if self.mensagem_label:
            self.mensagem_label.configure(text=mensagem)
            self.mensagem_label.grid(row=0, column=0, sticky='nsew')
            
    def atualizar_indicador_ordenacao(self, coluna_ordenacao, ordem_desc):
        """Adiciona setas ao cabeçalho da coluna atualmente ordenada."""
        for col_name in self.visible_colunas:
            text = col_name
            if col_name == coluna_ordenacao:
                text += " " + ("↓" if ordem_desc else "↑")
            self.tree.heading(col_name, text=text)

    def get_itens_selecionados(self):
        """
        Retorna uma lista de dicionários contendo os valores visíveis
        das linhas selecionadas.
        """
        selecionados = []
        for item_id in self.tree.selection():
            item_values = self.tree.item(item_id, 'values')
            # Mapeia os valores de volta para um dicionário (apenas com colunas visíveis)
            data_dict = dict(zip(self.visible_colunas, item_values))
            selecionados.append(data_dict)
            
        return selecionados

    def atualizar_cores(self, cores):
        """Atualiza cores de elementos CustomTkinter (Treeview via ttk não é totalmente suportada)."""
        # Aplica cores ao frame da tabela e ao label de mensagem
        self.configure(fg_color=cores["alt_bg"])
        if self.mensagem_label:
            self.mensagem_label.configure(fg_color=cores["alt_bg"], text_color=cores["fg"])

        # Nota: Cores da ttk.Treeview (linhas e cabeçalho) dependem do tema do sistema,
        # e a CustomTkinter não fornece controle direto sobre elas.