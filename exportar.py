# exportar.py
import pandas as pd
from tkinter import filedialog, messagebox

class Exportar:
    def __init__(self, tabela, colunas):
        self.tabela = tabela
        self.colunas = colunas

    def salvar_csv(self):
        dados = self.tabela.get_dados()
        if not dados:
            messagebox.showwarning("Aviso", "Nenhum dado para exportar.")
            return
        df = pd.DataFrame(dados, columns=self.colunas)
        caminho = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
        if caminho:
            df.to_csv(caminho, index=False)
            messagebox.showinfo("Sucesso", f"Arquivo CSV salvo em:\n{caminho}")

    def salvar_excel(self):
        dados = self.tabela.get_dados()
        if not dados:
            messagebox.showwarning("Aviso", "Nenhum dado para exportar.")
            return
        df = pd.DataFrame(dados, columns=self.colunas)
        caminho = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx")])
        if caminho:
            df.to_excel(caminho, index=False)
            messagebox.showinfo("Sucesso", f"Arquivo Excel salvo em:\n{caminho}")
