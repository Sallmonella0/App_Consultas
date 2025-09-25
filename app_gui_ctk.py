# app_gui_ctk.py
import customtkinter as ctk
from tkinter import messagebox
from tabela import Tabela
from api import buscar_todos

# Temas fornecidos
TEMAS = {
    "dark_green": {
        "bg": "#111111",
        "alt_bg": "#1C1C1C",
        "fg": "#D0F0C0",
        "selected_bg": "#66FF66",
        "selected_fg": "#111111",
        "button_bg": "#33CC33",
        "button_hover": "#22AA22",
        "entry_bg": "#222222",
        "placeholder": "#88CC88"
    },
    "light_green": {
        "bg": "#D3D3D3",
        "alt_bg": "#FFFAFA",
        "fg": "#111111",
        "selected_bg": "#80EF80",  # Corrigi "##80EF80"
        "selected_fg": "#000000",
        "button_bg": "#80EF80",
        "button_hover": "#80EF80",
        "entry_bg": "#FFFAFA",
        "placeholder": "#80EF80"
    }
}

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuração da janela
        self.title("App Consultas")
        self.geometry("1000x600")

        # Estado do tema
        self.tema_atual = "dark_green"
        self.aplicar_tema()

        # Frame superior com botões
        top_frame = ctk.CTkFrame(self, fg_color=self.cores["alt_bg"])
        top_frame.pack(fill="x", padx=10, pady=10)

        self.btn_buscar = ctk.CTkButton(
            top_frame,
            text="Buscar Todos",
            command=self.carregar_dados,
            fg_color=self.cores["button_bg"],
            hover_color=self.cores["button_hover"],
            text_color=self.cores["fg"]
        )
        self.btn_buscar.pack(side="left", padx=5)

        self.btn_tema = ctk.CTkButton(
            top_frame,
            text="Alternar Tema",
            command=self.alternar_tema,
            fg_color=self.cores["button_bg"],
            hover_color=self.cores["button_hover"],
            text_color=self.cores["fg"]
        )
        self.btn_tema.pack(side="left", padx=5)

        # Frame da tabela
        table_frame = ctk.CTkFrame(self, fg_color=self.cores["alt_bg"])
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Criar tabela
        colunas = ["DATAHORA", "IDMENSAGEM", "LATITUDE", "LONGITUDE", "PLACA", "TrackID"]
        self.tabela = Tabela(table_frame, colunas=colunas, cores=self.cores)
        self.tabela.pack(fill="both", expand=True)

        # Cache de dados para filtro
        self.dados_cache = []

    def aplicar_tema(self):
        """Aplica o tema atual aos elementos principais"""
        self.cores = TEMAS[self.tema_atual]
        self.configure(fg_color=self.cores["bg"])

    def alternar_tema(self):
        """Alterna entre tema claro e escuro"""
        self.tema_atual = "light_green" if self.tema_atual == "dark_green" else "dark_green"
        self.aplicar_tema()
        self.tabela.atualizar_cores(self.cores)

        # Atualiza botões também
        self.btn_buscar.configure(fg_color=self.cores["button_bg"],
                                  hover_color=self.cores["button_hover"],
                                  text_color=self.cores["fg"])
        self.btn_tema.configure(fg_color=self.cores["button_bg"],
                                hover_color=self.cores["button_hover"],
                                text_color=self.cores["fg"])

    def carregar_dados(self):
        """Carrega todos os dados da API"""
        try:
            dados = buscar_todos()
            if not dados:
                messagebox.showinfo("Info", "Nenhum dado encontrado.")
                return

            # Guardar cópia para filtro
            self.dados_cache = dados

            # Preencher tabela
            self.tabela.preencher(dados)

        except Exception as err:
            self.after(0, lambda e=err: messagebox.showerror("Erro", f"Falha ao carregar dados:\n{e}"))


if __name__ == "__main__":
    app = App()
    app.mainloop()
