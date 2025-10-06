# exportar.py
import pandas as pd
from tkinter import filedialog, messagebox
import threading
import logging

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

class Exportar:
    def __init__(self, app, colunas):
        self.app = app
        self.colunas = colunas

    def _salvar_arquivo(self, dados, file_type, extension, callback):
        if not dados:
            logging.warning("Tentativa de exportação sem dados.")
            self.app.after(0, lambda: messagebox.showwarning("Atenção", "Não há dados para exportar."))
            self.app.after(0, callback)
            return

        caminho = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[(f"Ficheiros {file_type}", f"*{extension}"), ("Todos os ficheiros", "*.*")],
            title=f"Salvar como {file_type}"
        )

        if not caminho:
            logging.info("Exportação cancelada pelo utilizador.")
            self.app.after(0, callback)
            return

        try:
            df = pd.DataFrame(dados)
            df = df.reindex(columns=self.colunas)

            if file_type == "Excel":
                if xlsxwriter:
                    writer = pd.ExcelWriter(caminho, engine='xlsxwriter')
                    df.to_excel(writer, index=False, sheet_name='Dados')
                    for i, column in enumerate(df):
                        column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
                        writer.sheets['Dados'].set_column(i, i, column_width)
                    writer.close()
                else:
                    df.to_excel(caminho, index=False)
            elif file_type == "CSV":
                df.to_csv(caminho, index=False, sep=';', encoding='utf-8-sig')

            logging.info(f"Dados exportados com sucesso para {caminho}")
            self.app.after(0, lambda: messagebox.showinfo("Sucesso", f"Dados exportados para {caminho}"))

        except Exception as e:
            logging.error(f"Falha na exportação para {caminho}: {e}")
            self.app.after(0, lambda err=e: messagebox.showerror("Erro na Exportação", f"Ocorreu um erro: {err}"))
        finally:
            self.app.after(0, callback)

    def salvar_csv_async(self, dados, callback):
        threading.Thread(target=self._salvar_arquivo, args=(dados, "CSV", ".csv", callback), daemon=True).start()

    def salvar_excel_async(self, dados, callback):
        threading.Thread(target=self._salvar_arquivo, args=(dados, "Excel", ".xlsx", callback), daemon=True).start()