from tkinter import ttk

class Tabela(ttk.Treeview):
    def __init__(self, parent, colunas, **kwargs):
        super().__init__(parent, columns=colunas, show="headings")
        self.colunas = colunas

        # ===== Cabeçalho =====
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading",
                        background="#33CC33",  # verde claro
                        foreground="#111111",
                        font=("Arial", 11, "bold"))
        style.configure("Treeview",
                        background="#1C1C1C",   # fundo geral
                        foreground="#D0F0C0",   # texto
                        fieldbackground="#1C1C1C",
                        rowheight=25)
        style.map('Treeview', background=[('selected', '#66FF66')], foreground=[('selected', '#111111')])

        # ===== Colunas =====
        for col in colunas:
            self.heading(col, text=col)
            self.column(col, width=120, anchor="center")

        # ===== Dados =====
        self.dados_completos = []
        self.dados_restantes = []
        self.bloco = 50  # linhas por bloco

        # ===== Alternância de cores nas linhas =====
        self.tag_configure('oddrow', background="#1C1C1C")   # cinza escuro
        self.tag_configure('evenrow', background="#222222")  # cinza médio

    def atualizar(self, dados):
        """Atualiza a tabela em blocos."""
        self.delete(*self.get_children())
        self.dados_completos = dados
        self.dados_restantes = list(dados)
        self._inserir_bloco()

    def _inserir_bloco(self):
        for _ in range(min(self.bloco, len(self.dados_restantes))):
            item = self.dados_restantes.pop(0)
            index = len(self.get_children())
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.insert("", "end", values=[item.get(col, "") for col in self.colunas], tags=(tag,))
        if self.dados_restantes:
            self.after(10, self._inserir_bloco)

    def filtrar(self, termo, coluna):
        termo = termo.lower()
        filtrados = [item for item in self.dados_completos if termo in str(item.get(coluna, "")).lower()]
        self.atualizar(filtrados)
