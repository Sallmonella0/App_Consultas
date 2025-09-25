import customtkinter as ctk
from tkinter import ttk

class Tabela(ctk.CTkFrame):
    def __init__(self, master, colunas, **kwargs):
        super().__init__(master, **kwargs)

        self.colunas = colunas
        self.dados_originais = []  # sempre guarda os dados completos da API

        # Entrada de filtro
        self.filtro_var = ctk.StringVar()
        filtro_frame = ctk.CTkFrame(self)
        filtro_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(filtro_frame, text="Filtro:").pack(side="left", padx=5)
        filtro_entry = ctk.CTkEntry(filtro_frame, textvariable=self.filtro_var)
        filtro_entry.pack(side="left", fill="x", expand=True, padx=5)
        filtro_entry.bind("<KeyRelease>", self._aplicar_filtro)

        # Frame da tabela
        tabela_frame = ctk.CTkFrame(self)
        tabela_frame.pack(fill="both", expand=True)

        # Treeview (sem scrollbar horizontal)
        self.tree = ttk.Treeview(
            tabela_frame,
            columns=self.colunas,
            show="headings",
            selectmode="browse",
            height=15
        )

        for col in self.colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=120)

        self.tree.pack(side="left", fill="both", expand=True)

        # Scrollbar vertical (ao lado)
        scrollbar = ttk.Scrollbar(
            tabela_frame,
            orient="vertical",
            command=self.tree.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

    def atualizar(self, dados):
        """Atualiza a tabela com novos dados"""
        self.dados_originais = dados  # guarda todos os dados recebidos
        self._popular_tabela(dados)

    def _popular_tabela(self, dados):
        """Preenche a Treeview"""
        self.tree.delete(*self.tree.get_children())
        for linha in dados:
            valores = [linha.get(col, "") for col in self.colunas]
            self.tree.insert("", "end", values=valores)

    def _aplicar_filtro(self, event=None):
        """Aplica filtro sempre sobre os dados originais"""
        texto = self.filtro_var.get().lower()
        if not texto:
            dados_filtrados = self.dados_originais
        else:
            dados_filtrados = [
                item for item in self.dados_originais
                if any(texto in str(valor).lower() for valor in item.values())
            ]
        self._popular_tabela(dados_filtrados)
