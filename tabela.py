# tabela.py
import customtkinter as ctk
from tkinter import ttk, messagebox

class Tabela:
    def __init__(self, parent, colunas, bg="#111111", fg="#D0F0C0",
                 alt_bg="#1C1C1C", selected_bg="#66FF66", selected_fg="#111111"):
        self.parent = parent
        self.colunas = colunas
        self.bg = bg
        self.fg = fg
        self.alt_bg = alt_bg
        self.selected_bg = selected_bg
        self.selected_fg = selected_fg

        # Dados originais da tabela
        self.dados_master = []

        # Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background=self.bg,
                        foreground=self.fg,
                        fieldbackground=self.bg,
                        rowheight=25)
        style.map("Treeview",
                  background=[('selected', self.selected_bg)],
                  foreground=[('selected', self.selected_fg)])

        self.tree = ttk.Treeview(parent, columns=self.colunas, show="headings")
        for col in self.colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor="center")

        self.tree.pack(fill="both", expand=True)

        # Configura cores alternadas
        self.tree.tag_configure("oddrow", background=self.bg)
        self.tree.tag_configure("evenrow", background=self.alt_bg)

    def atualizar(self, dados):
        """Atualiza a tabela com novos dados."""
        if dados is None:
            return
        self.dados_master = dados.copy() if isinstance(dados, list) else []
        self._carregar_tabela(self.dados_master)

    def filtrar(self, termo, coluna):
        """Filtra os dados de acordo com o termo e coluna."""
        if not termo:
            # Se termo vazio, mostra todos os dados
            self._carregar_tabela(self.dados_master)
            return

        termo = str(termo).lower()
        resultados = []

        for row in self.dados_master:
            valor = str(row.get(coluna, "")).lower()
            if termo in valor:
                resultados.append(row)

        if resultados:
            self._carregar_tabela(resultados)
        else:
            # Nenhum resultado encontrado
            self._carregar_tabela([])
            messagebox.showinfo("Filtro", "Nenhum dado encontrado.")

    def _carregar_tabela(self, dados):
        """Carrega uma lista de dicionários na Treeview."""
        # Limpa tabela
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insere dados
        for i, row in enumerate(dados):
            valores = [row.get(col, "") for col in self.colunas]
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=valores, tags=(tag,))
