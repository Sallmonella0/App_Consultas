import customtkinter as ctk
from tkinter import messagebox
import threading
from tabela import Tabela
from exportar import Exportar
from config import COLUNAS

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class AppGUI(ctk.CTk):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self.title("Consulta API por IDMENSAGEM")
        self.geometry("1000x600")
        self.minsize(900, 500)
        self.configure(padx=20, pady=20, fg_color="#111111")

        # === Entrada IDMENSAGEM ===
        frame_top = ctk.CTkFrame(self, fg_color="#1C1C1C")
        frame_top.pack(fill="x", pady=10)

        self.label_id = ctk.CTkLabel(frame_top, text="Digite o IDMENSAGEM:", font=("Arial", 12), text_color="#D0F0C0")
        self.label_id.pack(side="left", padx=(0, 10))

        self.entry_id = ctk.CTkEntry(frame_top, width=200, fg_color="#222222", text_color="#D0F0C0", placeholder_text_color="#88CC88")
        self.entry_id.pack(side="left", padx=(0, 10))

        self.btn_consultar = ctk.CTkButton(frame_top, text="Consultar API", fg_color="#33CC33", hover_color="#22AA22", text_color="#111111", command=self.consultar_api_async)
        self.btn_consultar.pack(side="left")

        # === Tabela ===
        frame_table = ctk.CTkFrame(self, fg_color="#111111")
        frame_table.pack(fill="both", expand=True, pady=10)

        self.tabela = Tabela(frame_table, COLUNAS)
        self.tabela.pack(fill="both", expand=True)

        # === Exportar ===
        frame_export = ctk.CTkFrame(self, fg_color="#1C1C1C")
        frame_export.pack(fill="x", pady=5)

        self.exportar = Exportar(self.tabela, COLUNAS)

        self.btn_csv = ctk.CTkButton(frame_export, text="Salvar CSV", fg_color="#33CC33", hover_color="#22AA22", text_color="#111111", command=self.exportar.salvar_csv)
        self.btn_csv.pack(side="left", padx=10)

        self.btn_excel = ctk.CTkButton(frame_export, text="Salvar Excel", fg_color="#33CC33", hover_color="#22AA22", text_color="#111111", command=self.exportar.salvar_excel)
        self.btn_excel.pack(side="left", padx=10)

        # === Filtro ===
        frame_filtro = ctk.CTkFrame(self, fg_color="#1C1C1C")
        frame_filtro.pack(fill="x", pady=5)

        self.label_filtro = ctk.CTkLabel(frame_filtro, text="Filtrar:", font=("Arial", 11), text_color="#D0F0C0")
        self.label_filtro.pack(side="left", padx=(0,5))

        self.entry_filtro = ctk.CTkEntry(frame_filtro, width=150, fg_color="#222222", text_color="#D0F0C0", placeholder_text_color="#88CC88")
        self.entry_filtro.pack(side="left", padx=5)

        # Debounce do filtro
        self.filtro_job = None
        self.entry_filtro.bind("<KeyRelease>", self.debounce_filtro)

        self.combo_coluna = ctk.CTkComboBox(frame_filtro, values=COLUNAS, width=150, fg_color="#222222", text_color="#D0F0C0", button_color="#33CC33", button_hover_color="#22AA22")
        self.combo_coluna.set("PLACA")
        self.combo_coluna.pack(side="left", padx=5)

        self.btn_filtrar = ctk.CTkButton(frame_filtro, text="Aplicar filtro", fg_color="#33CC33", hover_color="#22AA22", text_color="#111111", command=self.aplicar_filtro_thread)
        self.btn_filtrar.pack(side="left", padx=5)

    # === Consulta assíncrona ===
    def consultar_api_async(self):
        thread = threading.Thread(target=self.consultar_api)
        thread.daemon = True
        thread.start()

    def consultar_api(self):
        id_msg = self.entry_id.get().strip()
        if not id_msg.isdigit():
            self.after(0, lambda: messagebox.showwarning("Atenção", "IDMENSAGEM inválido!"))
            return

        self.after(0, lambda: self.btn_consultar.configure(state="disabled", text="Consultando..."))

        try:
            dados = self.api.consultar(int(id_msg))
            self.tabela.dados_completos = dados
            self.after(0, lambda: self.tabela.atualizar(dados))
            if not dados:
                self.after(0, lambda: messagebox.showinfo("Aviso", "Nenhum dado encontrado para esse IDMENSAGEM."))
        except Exception as e:
            self.after(0, lambda e=e: messagebox.showerror("Erro", f"Falha ao consultar API:\n{e}"))
        finally:
            self.after(0, lambda: self.btn_consultar.configure(state="normal", text="Consultar API"))

    # === Debounce do filtro ===
    def debounce_filtro(self, event):
        if self.filtro_job:
            self.after_cancel(self.filtro_job)
        self.filtro_job = self.after(300, self.aplicar_filtro_thread)

    # === Filtro em thread ===
    def aplicar_filtro_thread(self):
        thread = threading.Thread(target=self.aplicar_filtro)
        thread.daemon = True
        thread.start()

    def aplicar_filtro(self):
        termo = self.entry_filtro.get().strip()
        coluna = self.combo_coluna.get()
        if termo == "":
            self.after(0, lambda: self.tabela.atualizar(self.tabela.dados_completos))
        else:
            self.after(0, lambda: self.tabela.filtrar(termo, coluna))
