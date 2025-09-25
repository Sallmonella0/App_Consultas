# app_gui_ctk.py
import customtkinter as ctk
from tkinter import messagebox
import threading
import logging
from datetime import datetime
from gui.tabela import Tabela
from utils.exportar import Exportar
from utils.config import COLUNAS
from utils.settings_manager import AUTO_REFRESH_MINUTES

TEMAS = {
    "dark_green": {
        "bg": "#111111", "alt_bg": "#1C1C1C", "fg": "#D0F0C0",
        "selected_bg": "#66FF66", "selected_fg": "#111111",
        "button_bg": "#33CC33", "button_hover": "#22AA22",
        "entry_bg": "#222222", "placeholder": "#88CC88"
    },
    "light_green": {
        "bg": "#D3D3D3", "alt_bg": "#FFFAFA", "fg": "#111111",
        "selected_bg": "#80EF80", "selected_fg": "#000000",
        "button_bg": "#80EF80", "button_hover": "#80EF80",
        "entry_bg": "#FFFAFA", "placeholder": "#80EF80"
    }
}

class AppGUI(ctk.CTk):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self.tema_atual = "dark_green"
        self.title("App de Consulta Avançada")
        self.geometry("1200x650") # Aumentado para acomodar a barra de status
        self.minsize(900, 500)
        self._debounce_id = None
        self.ordem_desc = True

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.frame_top = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.frame_table = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_table.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.frame_bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_bottom.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 0))
        
        # --- NOVA BARRA DE STATUS ---
        self.status_bar = ctk.CTkFrame(self, height=25)
        self.status_bar.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        self.status_label = ctk.CTkLabel(self.status_bar, text="Bem-vindo!", anchor="w")
        self.status_label.pack(side="left", padx=10)
        self.last_updated_label = ctk.CTkLabel(self.status_bar, text="", anchor="e")
        self.last_updated_label.pack(side="right", padx=10)

        # ... (Widgets do frame_top e frame_bottom, sem alterações na criação)
        self.label_id = ctk.CTkLabel(self.frame_top, text="IDMENSAGEM:")
        self.label_id.pack(side="left", padx=(0, 5))
        self.entry_id = ctk.CTkEntry(self.frame_top, width=150)
        self.entry_id.pack(side="left")
        self.entry_id.bind("<Return>", lambda e: self.consultar_api_async())
        self.btn_consultar = ctk.CTkButton(self.frame_top, text="Consultar", width=100, command=lambda: self.consultar_api_async())
        self.btn_consultar.pack(side="left", padx=5)
        self.btn_alternar_tema = ctk.CTkButton(self.frame_top, text="Alternar Tema", command=lambda: self.alternar_tema())
        self.btn_alternar_tema.pack(side="right", padx=5)
        self.btn_alternar_ordem = ctk.CTkButton(self.frame_top, text="Ordem: Recentes", command=lambda: self.alternar_ordem())
        self.btn_alternar_ordem.pack(side="right")
        self.tabela = Tabela(self.frame_table, COLUNAS)
        self.tabela.pack(fill="both", expand=True)
        self.label_filtro = ctk.CTkLabel(self.frame_bottom, text="Filtrar:")
        self.label_filtro.pack(side="left", padx=(0, 5))
        self.entry_filtro = ctk.CTkEntry(self.frame_bottom, placeholder_text="Digite para filtrar...")
        self.entry_filtro.pack(side="left", padx=5)
        self.entry_filtro.bind("<KeyRelease>", self.aplicar_filtro_debounce)
        self.combo_coluna = ctk.CTkComboBox(self.frame_bottom, values=COLUNAS, width=150)
        self.combo_coluna.set("PLACA")
        self.combo_coluna.pack(side="left")
        self.frame_paginacao = ctk.CTkFrame(self.frame_bottom, fg_color="transparent")
        self.frame_paginacao.pack(side="left", expand=True)
        self.btn_anterior = ctk.CTkButton(self.frame_paginacao, text="< Anterior", width=100, command=lambda: self.pagina_anterior())
        self.btn_anterior.pack(side="left", padx=5)
        self.label_pagina = ctk.CTkLabel(self.frame_paginacao, text="Página 1 / 1")
        self.label_pagina.pack(side="left", padx=10)
        self.btn_proximo = ctk.CTkButton(self.frame_paginacao, text="Próximo >", width=100, command=lambda: self.proxima_pagina())
        self.btn_proximo.pack(side="left", padx=5)
        self.exportar = Exportar(self, COLUNAS)
        self.btn_excel = ctk.CTkButton(self.frame_bottom, text="Salvar Excel", command=self.exportar_excel)
        self.btn_excel.pack(side="right", padx=5)
        self.btn_csv = ctk.CTkButton(self.frame_bottom, text="Salvar CSV", command=self.exportar_csv)
        self.btn_csv.pack(side="right")

        self.aplicar_tema_completo()
        threading.Thread(target=self.carregar_dados_iniciais_com_cache, daemon=True).start()
        self.schedule_auto_refresh()

    def update_status(self, message, clear_after_ms=0):
        """Atualiza a mensagem na barra de status."""
        self.status_label.configure(text=message)
        if clear_after_ms > 0:
            self.after(clear_after_ms, lambda: self.status_label.configure(text=""))

    def schedule_auto_refresh(self):
        """Agenda a próxima atualização automática."""
        if AUTO_REFRESH_MINUTES > 0:
            logging.info(f"A agendar próxima atualização automática em {AUTO_REFRESH_MINUTES} minutos.")
            # Converte minutos para milissegundos
            self.after(AUTO_REFRESH_MINUTES * 60 * 1000, self.auto_refresh_data)

    def auto_refresh_data(self):
        """Executa a atualização automática e agenda a próxima."""
        logging.info("A iniciar atualização automática de dados...")
        self.update_status("A atualizar dados em segundo plano...")
        # Cria uma nova thread para a atualização para não congelar a UI
        threading.Thread(target=self.carregar_dados_iniciais_com_cache, args=(True,), daemon=True).start()
        # Agenda a próxima execução
        self.schedule_auto_refresh()

    def carregar_dados_iniciais_com_cache(self, is_auto_refresh=False):
        try:
            if not is_auto_refresh:
                self.update_status("A carregar dados do cache...")
                dados_iniciais = self.api.buscar_todos(force_refresh=False)
                if dados_iniciais:
                    self.after(0, self.tabela.atualizar, dados_iniciais)
                    self.after(0, self.atualizar_label_pagina)
                    self.update_status(f"{len(dados_iniciais)} registos carregados do cache.")
                else:
                    self.after(0, self.tabela.mostrar_mensagem, "Buscando dados da API...")
                    self.update_status("Cache vazio. A buscar dados da API...")

            dados_frescos = self.api.buscar_todos(force_refresh=True)
            if dados_frescos and dados_frescos != self.tabela.dados_completos:
                logging.info("Dados atualizados encontrados. A atualizar a interface.")
                self.after(0, self.tabela.atualizar, dados_frescos)
                self.after(0, self.atualizar_label_pagina)
                self.update_status(f"Dados atualizados. Total de {len(dados_frescos)} registos.")
            elif is_auto_refresh:
                 self.update_status("Nenhum dado novo encontrado.")

            # Atualiza o rótulo de "última atualização"
            now = datetime.now().strftime("%H:%M:%S")
            self.last_updated_label.configure(text=f"Última verificação: {now}")

        except Exception as e:
            logging.error(f"Falha ao carregar dados: {e}")
            self.update_status(f"Erro ao carregar dados: {e}", clear_after_ms=5000)

    def atualizar_label_pagina(self):
        pag_atual = self.tabela.pagina_atual
        pag_total = self.tabela.total_paginas
        self.label_pagina.configure(text=f"Página {pag_atual} / {max(1, pag_total)}")

    # ... (O resto do ficheiro permanece o mesmo, com pequenas alterações nos callbacks)
    def gerir_estado_exportacao(self, exportando):
        estado = "disabled" if exportando else "normal"
        if exportando:
            self.update_status("A exportar dados... Por favor, aguarde.")
        else:
            self.update_status("Exportação concluída.", clear_after_ms=5000)
            
        self.btn_excel.configure(state=estado)
        self.btn_csv.configure(state=estado)
        
    def exportar_excel(self):
        self.gerir_estado_exportacao(exportando=True)
        dados_completos = self.tabela.dados_exibidos
        self.exportar.salvar_excel_async(dados_completos, callback=lambda: self.gerir_estado_exportacao(exportando=False))

    def exportar_csv(self):
        self.gerir_estado_exportacao(exportando=True)
        dados_completos = self.tabela.dados_exibidos
        self.exportar.salvar_csv_async(dados_completos, callback=lambda: self.gerir_estado_exportacao(exportando=False))
            
    def aplicar_tema_completo(self):
        cores = TEMAS[self.tema_atual]
        self.configure(fg_color=cores["bg"])
        self.status_bar.configure(fg_color=cores["button_bg"])
        self.status_label.configure(text_color=cores["selected_fg"])
        self.last_updated_label.configure(text_color=cores["selected_fg"])
        botoes = [self.btn_consultar, self.btn_csv, self.btn_excel, self.btn_alternar_tema, self.btn_alternar_ordem, self.btn_anterior, self.btn_proximo]
        entries = [self.entry_id, self.entry_filtro]
        labels = [self.label_id, self.label_filtro, self.label_pagina]
        combos = [self.combo_coluna]
        for btn in botoes:
            btn.configure(fg_color=cores["button_bg"], hover_color=cores["button_hover"], text_color=cores["selected_fg"])
        for entry in entries:
            entry.configure(fg_color=cores["entry_bg"], text_color=cores["fg"], border_color=cores["button_hover"], placeholder_text_color=cores["placeholder"])
        for lbl in labels:
            lbl.configure(text_color=cores["fg"])
        for combo in combos:
             combo.configure(fg_color=cores["entry_bg"], text_color=cores["fg"], border_color=cores["button_hover"],
                             button_color=cores["button_bg"], button_hover_color=cores["button_hover"],
                             dropdown_fg_color=cores["alt_bg"], dropdown_hover_color=cores["button_hover"])
        self.tabela.atualizar_cores(cores)

    def alternar_tema(self):
        self.tema_atual = "light_green" if self.tema_atual == "dark_green" else "dark_green"
        self.aplicar_tema_completo()

    def pagina_anterior(self):
        self.tabela.ir_para_pagina(self.tabela.pagina_atual - 1)
        self.atualizar_label_pagina()

    def proxima_pagina(self):
        self.tabela.ir_para_pagina(self.tabela.pagina_atual + 1)
        self.atualizar_label_pagina()

    def consultar_api_async(self):
        threading.Thread(target=self.consultar_api, daemon=True).start()

    def consultar_api(self):
        id_msg = self.entry_id.get().strip()
        if not id_msg.isdigit():
            self.after(0, lambda: messagebox.showwarning("Atenção", "IDMENSAGEM deve ser um número!"))
            return
        self.after(0, lambda: self.btn_consultar.configure(state="disabled", text="Buscando..."))
        self.update_status(f"A buscar IDMENSAGEM {id_msg}...")
        try:
            dados = self.api.consultar(id_msg)
            self.after(0, self.tabela.atualizar, dados)
            self.after(0, self.atualizar_label_pagina)
            self.update_status(f"{len(dados)} registos encontrados para o ID {id_msg}.", clear_after_ms=5000)
        except Exception as e:
            self.after(0, lambda err=e: messagebox.showerror("Erro de API", f"Falha na consulta:\n{err}"))
            self.update_status(f"Erro na consulta do ID {id_msg}.", clear_after_ms=5000)
        finally:
            self.after(0, lambda: self.btn_consultar.configure(state="normal", text="Consultar"))

    def aplicar_filtro_debounce(self, event=None):
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(300, self.aplicar_filtro)

    def aplicar_filtro(self):
        termo = self.entry_filtro.get()
        coluna = self.combo_coluna.get()
        self.tabela.filtrar(termo, coluna, ordem_desc=self.ordem_desc)
        self.atualizar_label_pagina()
        self.update_status(f"{len(self.tabela.dados_exibidos)} registos correspondem ao filtro.")

    def alternar_ordem(self):
        self.ordem_desc = not self.ordem_desc
        texto = "Recentes" if self.ordem_desc else "Antigos"
        self.btn_alternar_ordem.configure(text=f"Ordem: {texto}")
        self.aplicar_filtro()