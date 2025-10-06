# src/gui/app_gui_ctk.py
import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk
import threading
import logging
from datetime import datetime, timedelta
import math
from queue import Queue
import concurrent.futures

# --- IMPORTAÇÕES CORE ---
from src.core.data_controller import DataController
from src.core.exceptions import ConsultaAPIException
# -------------------------

from src.gui.tabela import Tabela

from src.utils.exportar import Exportar
from src.utils.config import COLUNAS
from src.utils.settings_manager import AUTO_REFRESH_MINUTES, ITENS_POR_PAGINA
from src.utils.state_manager import load_state, save_state
from src.utils.datetime_utils import is_valid_ui_date

# --- PALETA DE CORES ---
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
        "placeholder": "#88CC88",
        "error_color": "#E74C3C"
    },
    "light_green": {
        "bg": "#D3D3D3",
        "alt_bg": "#FFFAFA",
        "fg": "#111111",
        "selected_bg": "#80EF80",
        "selected_fg": "#000000",
        "button_bg": "#80EF80",
        "button_hover": "#80EF80",
        "entry_bg": "#FFFAFA",
        "placeholder": "#80EF80",
        "error_color": "#CC3333"
    }
}
# --- FIM PALETA DE CORES ---


# --- CLASSES DE UTILIDADE ---

class ColumnSettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, all_columns, current_visible_columns, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Configurar Colunas Visíveis")
        self.transient(master)
        self.master_app = master
        self.grab_set()
        self.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkScrollableFrame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.checkbox_vars = {}
        for col in all_columns:
            var = ctk.BooleanVar(value=(col in current_visible_columns))
            chk = ctk.CTkCheckBox(frame, text=col, variable=var)
            chk.pack(anchor="w", pady=2)
            self.checkbox_vars[col] = var

        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=10, pady=(0, 10))
        btn_aplicar = ctk.CTkButton(frame_botoes, text="Aplicar", command=self._aplicar_configuracao)
        btn_aplicar.pack(side="right", padx=5)
        btn_cancelar = ctk.CTkButton(frame_botoes, text="Cancelar", command=self.destroy)
        btn_cancelar.pack(side="right", padx=5)

    def _aplicar_configuracao(self):
        selected_columns = [col for col, var in self.checkbox_vars.items() if var.get()]
        if not selected_columns:
            messagebox.showerror("Erro", "Pelo menos uma coluna deve ser selecionada.")
            return
        self.master_app.aplicar_novas_colunas(selected_columns, self.master_app.frames["Consultas"].tabela)
        self.destroy()


# --- CLASSES DE ECRÃ (SCREENS) ---
class ConsultaScreen(ctk.CTkFrame):
    def __init__(self, master, controller, api, main_app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.master_app = main_app
        self.controller = controller
        self.api = api
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._criar_widgets()

    def _criar_widgets(self):
        # --- 1. Cabeçalho Superior ---
        self.frame_top = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.label_id = ctk.CTkLabel(self.frame_top, text="IDMENSAGEM:")
        self.label_id.pack(side="left", padx=(0, 5))
        self.entry_id = ctk.CTkEntry(self.frame_top, width=150)
        self.entry_id.pack(side="left")
        self.entry_id.bind("<Return>", lambda e: self.master_app.consultar_api_async())
        self.btn_consultar = ctk.CTkButton(self.frame_top, text="Consultar", width=100, command=self.master_app.consultar_api_async)
        self.btn_consultar.pack(side="left", padx=5)
        self.btn_refresh = ctk.CTkButton(self.frame_top, text="Refresh", width=100, command=self.master_app.refresh_data_async)
        self.btn_refresh.pack(side="left", padx=5)
        self.btn_config_colunas = ctk.CTkButton(self.frame_top, text="Colunas", width=100, command=self._abrir_configuracao_colunas)
        self.btn_config_colunas.pack(side="left", padx=15)

        # --- 2. Filtros ---
        self.frame_filtros = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_filtros.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        self.label_filtro = ctk.CTkLabel(self.frame_filtros, text="Filtro Termo:")
        self.label_filtro.pack(side="left", padx=(0, 5))
        self.entry_filtro = ctk.CTkEntry(self.frame_filtros, placeholder_text="Digite para filtrar...")
        self.entry_filtro.pack(side="left", padx=5, expand=True, fill="x")
        self.entry_filtro.bind("<KeyRelease>", self.master_app.aplicar_filtro_debounce)
        self.combo_coluna = ctk.CTkComboBox(self.frame_filtros, values=["TODAS"] + COLUNAS, width=150)
        self.combo_coluna.set("PLACA")
        self.combo_coluna.pack(side="left")
        self.btn_limpar_filtro = ctk.CTkButton(self.frame_filtros, text="Limpar", width=80, command=self.master_app.limpar_filtro)
        self.btn_limpar_filtro.pack(side="left", padx=5)
        self.label_data_inicio = ctk.CTkLabel(self.frame_filtros, text="De:")
        self.label_data_inicio.pack(side="left", padx=(10, 5))
        self.entry_data_inicio = ctk.CTkEntry(self.frame_filtros, placeholder_text="AAAA-MM-DD", width=120)
        self.entry_data_inicio.pack(side="left")
        self.entry_data_inicio.bind("<KeyRelease>", self.master_app.aplicar_filtro_debounce)
        self.entry_data_inicio.bind("<FocusIn>", lambda e: self.master_app._reset_date_border(self.entry_data_inicio))
        self.label_data_fim = ctk.CTkLabel(self.frame_filtros, text="Até:")
        self.label_data_fim.pack(side="left", padx=(10, 5))
        self.entry_data_fim = ctk.CTkEntry(self.frame_filtros, placeholder_text="AAAA-MM-DD", width=120)
        self.entry_data_fim.pack(side="left")
        self.entry_data_fim.bind("<KeyRelease>", self.master_app.aplicar_filtro_debounce)
        self.entry_data_fim.bind("<FocusIn>", lambda e: self.master_app._reset_date_border(self.entry_data_fim))

        # --- 3. Tabela ---
        self.frame_table = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_table.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.frame_table.grid_rowconfigure(0, weight=1)
        self.frame_table.grid_columnconfigure(0, weight=1)
        self.tabela = Tabela(self.frame_table, COLUNAS, self.master_app.colunas_visiveis,
                             on_sort_command=self.master_app.ordenar_por_coluna,
                             on_rebuild_command=self.master_app.renderizar_dados)
        self.tabela.grid(row=0, column=0, sticky="nsew")

        # --- 4. Rodapé ---
        self.frame_bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_bottom.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        self.frame_paginacao = ctk.CTkFrame(self.frame_bottom, fg_color="transparent")
        self.frame_paginacao.pack(side="left", expand=True, fill="x")
        self.btn_primeira = ctk.CTkButton(self.frame_paginacao, text="<<", width=50, command=self.master_app.primeira_pagina)
        self.btn_primeira.pack(side="left", padx=(0, 5))
        self.btn_anterior = ctk.CTkButton(self.frame_paginacao, text="<", width=50, command=self.master_app.pagina_anterior)
        self.btn_anterior.pack(side="left", padx=5)
        self.label_pagina = ctk.CTkLabel(self.frame_paginacao, text="Página 1 / 1")
        self.label_pagina.pack(side="left", padx=10)
        self.btn_proximo = ctk.CTkButton(self.frame_paginacao, text=">", width=50, command=self.master_app.proxima_pagina)
        self.btn_proximo.pack(side="left", padx=5)
        self.btn_ultima = ctk.CTkButton(self.frame_paginacao, text=">>", width=50, command=self.master_app.ultima_pagina)
        self.btn_ultima.pack(side="left", padx=5)
        self.btn_excel = ctk.CTkButton(self.frame_bottom, text="Excel", command=self.master_app.exportar_excel)
        self.btn_excel.pack(side="right", padx=5)
        self.btn_csv = ctk.CTkButton(self.frame_bottom, text="CSV", command=self.master_app.exportar_csv)
        self.btn_csv.pack(side="right")
        
        self.widgets_interativos = [
            self.entry_id, self.btn_consultar, self.btn_refresh, self.btn_config_colunas,
            self.entry_filtro, self.combo_coluna, self.btn_limpar_filtro,
            self.entry_data_inicio, self.entry_data_fim,
            self.btn_primeira, self.btn_anterior, self.btn_proximo, self.btn_ultima,
            self.btn_excel, self.btn_csv
        ]

    def _abrir_configuracao_colunas(self):
        ColumnSettingsWindow(self.master_app, COLUNAS, self.master_app.colunas_visiveis)

    def atualizar_elementos(self):
        self.master_app.atualizar_label_pagina(self.label_pagina)
        self.tabela.atualizar_indicador_ordenacao(self.controller.coluna_ordenacao, self.controller.ordem_desc)

    def aplicar_tema(self, cores):
        for frame in [self, self.frame_top, self.frame_filtros, self.frame_table, self.frame_bottom, self.frame_paginacao]:
            frame.configure(fg_color="transparent")

        for entry in [self.entry_id, self.entry_filtro, self.entry_data_inicio, self.entry_data_fim]:
            entry.configure(fg_color=cores["entry_bg"], text_color=cores["fg"], border_color=cores["placeholder"], placeholder_text_color=cores["placeholder"])
        
        for label in [self.label_id, self.label_filtro, self.label_data_inicio, self.label_data_fim, self.label_pagina]:
            label.configure(text_color=cores["fg"])

        self.combo_coluna.configure(fg_color=cores["entry_bg"], text_color=cores["fg"], border_color=cores["placeholder"],
                                    button_color=cores["button_bg"], button_hover_color=cores["button_hover"],
                                    dropdown_fg_color=cores["alt_bg"], dropdown_hover_color=cores["button_hover"])
        
        for btn in self.widgets_interativos:
            if isinstance(btn, ctk.CTkButton):
                btn.configure(fg_color=cores["button_bg"], hover_color=cores["button_hover"], text_color=cores["selected_fg"])
        
        self.tabela.atualizar_cores(cores)


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, master, client_status_ref, main_app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.master_app = main_app
        self.client_status_ref = client_status_ref
        self.status_labels = {}
        self.current_ids = set()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._criar_widgets()
        self._after_id = None

    def _criar_widgets(self):
        self.header_frame = ctk.CTkFrame(self, height=80, corner_radius=10)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 5))
        self.header_frame.grid_columnconfigure(1, weight=1)
        self.title_label = ctk.CTkLabel(self.header_frame, text="Dashboard de Status do Cliente", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.grid(row=0, column=0, sticky="w", padx=15, pady=15)
        self.status_summary_label = ctk.CTkLabel(self.header_frame, text="Monitorando 0 clientes | Última atualização: N/A")
        self.status_summary_label.grid(row=0, column=1, sticky="e", padx=15, pady=15)
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Status por TrackID")
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 10))
        self.interval_label = ctk.CTkLabel(self.footer_frame, text="Próxima Verificação em: N/A", anchor="w")
        self.interval_label.pack(side="left", padx=10)
        self.aplicar_tema(TEMAS[self.master_app.tema_atual])

    def update_display(self, *args):
        new_ids = set(self.client_status_ref.keys())
        if new_ids != self.current_ids:
            self.current_ids = new_ids
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.status_labels = {}
            self._build_labels(sorted(list(new_ids)))
        else:
            self._update_labels_only(sorted(list(new_ids)))
        total_clientes = len(self.current_ids)
        ok_count = sum(1 for status in self.client_status_ref.values() if status.get('status') == 'OK')
        now = datetime.now().strftime("%H:%M:%S")
        self.status_summary_label.configure(text=f"Monitorando {total_clientes} clientes ({ok_count} OK) | Última: {now}")
        app = self.master_app
        if hasattr(app, '_last_monitoring_start') and app._last_monitoring_start > 0:
            time_elapsed = datetime.now().timestamp() * 1000 - app._last_monitoring_start
            time_remaining_ms = max(0, app.monitoring_interval_ms - time_elapsed)
            seconds_remaining = math.ceil(time_remaining_ms / 1000)
            self.interval_label.configure(text=f"Próxima Verificação em: {seconds_remaining}s")

    def _build_labels(self, sorted_ids):
        cores = TEMAS[self.master_app.tema_atual]
        for i, track_id in enumerate(sorted_ids):
            frame = ctk.CTkFrame(self.scrollable_frame, fg_color=cores["alt_bg"], border_color=cores["placeholder"], border_width=1, corner_radius=5)
            frame.grid(row=i, column=0, sticky="ew", pady=5, padx=5)
            frame.grid_columnconfigure(1, weight=1)
            id_label = ctk.CTkLabel(frame, text=f"TrackID: {track_id}", text_color=cores["fg"], font=ctk.CTkFont(weight="bold"))
            id_label.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")
            status_label = ctk.CTkLabel(frame, text="AGUARDANDO", anchor="w")
            status_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            self.status_labels[track_id] = status_label
        self._update_labels_only(sorted_ids)

    def _update_labels_only(self, sorted_ids):
        cores = TEMAS[self.master_app.tema_atual]
        for track_id in sorted_ids:
            status_info = self.client_status_ref.get(track_id, {})
            label = self.status_labels.get(track_id)
            if not label: continue
            
            status_text = status_info.get('status', 'AGUARDANDO')
            last_message_time_str = status_info.get('last_message_time')
            status_message = status_info.get('message', '')

            display_text = status_text
            if status_text == "OK":
                if last_message_time_str:
                    try:
                        dt_obj = datetime.fromisoformat(last_message_time_str)
                        display_text = f"OK ({dt_obj.strftime('%d/%m/%Y %H:%M:%S')})"
                    except (ValueError, TypeError):
                        display_text = f"OK ({last_message_time_str})" # Fallback
                elif status_message:
                     display_text = f"OK ({status_message})"
                else:
                    display_text = "OK"

            elif status_text in ["ERRO", "PROCESSANDO"]:
                 check_time = status_info.get('timestamp', datetime.now())
                 display_text = f"{status_text} ({check_time.strftime('%H:%M:%S')})"

            color_map = {"OK": cores["selected_bg"], "ERRO": cores["error_color"], "PROCESSANDO": "#F1C40F"}
            color = color_map.get(status_text, cores["fg"])
            label.configure(text=display_text, text_color=color)
            if status_text == "ERRO":
                label.unbind("<Button-1>")
                label.bind("<Button-1>", lambda e, id=track_id, msg=status_message: messagebox.showerror(f"Erro - TrackID {id}", msg))
            else:
                label.unbind("<Button-1>")

    def start_periodic_update(self):
        self.stop_periodic_update()
        self.update_display()
        self._after_id = self.after(1000, self.start_periodic_update)

    def stop_periodic_update(self):
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
    
    def aplicar_tema(self, cores):
        self.header_frame.configure(fg_color=cores["alt_bg"])
        self.title_label.configure(text_color=cores["fg"])
        self.status_summary_label.configure(text_color=cores["placeholder"])
        self.scrollable_frame.configure(fg_color=cores["alt_bg"], label_text_color=cores["fg"])
        self.interval_label.configure(text_color=cores["fg"])
        self.update_display()


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, master, main_app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.master_app = main_app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._criar_widgets()

    def _criar_widgets(self):
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.aplicar_tema(TEMAS[self.master_app.tema_atual])

    def _create_setting_card(self, title, row, cores, elements):
        card = ctk.CTkFrame(self.scrollable_frame, fg_color=cores["alt_bg"], border_color=cores["placeholder"], border_width=1, corner_radius=10)
        card.grid(row=row, column=0, sticky="ew", pady=10, padx=5)
        card.grid_columnconfigure(1, weight=1)
        title_label = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color=cores["fg"])
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))
        for i, element in enumerate(elements):
            if isinstance(element, tuple):
                label_text, widget = element
                lbl = ctk.CTkLabel(card, text=label_text, anchor="w", text_color=cores["fg"])
                lbl.grid(row=i+1, column=0, sticky="w", padx=15, pady=5)
                widget.configure(text_color=cores["fg"], fg_color=cores["entry_bg"], border_color=cores["placeholder"])
                widget.grid(row=i+1, column=1, sticky="ew", padx=15, pady=5)
            elif isinstance(element, ctk.CTkCheckBox):
                widget.configure(text_color=cores["fg"])
                widget.grid(row=i+1, column=0, columnspan=2, sticky="w", padx=15, pady=5)
    
    def aplicar_tema(self, cores):
        self.scrollable_frame.configure(fg_color="transparent", label_text_color=cores["fg"], label_text="Configurações do Sistema")
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        sections = {
            "Monitoramento": [("Intervalo (min):", ctk.CTkEntry(self.scrollable_frame, placeholder_text="10"))],
            "Interface": [("Itens por Página:", ctk.CTkComboBox(self.scrollable_frame, values=["50", "100", "200"]))],
        }
        for i, (title, elements) in enumerate(sections.items()):
            self._create_setting_card(title, i, cores, elements)
        
        footer = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        footer.grid(row=len(sections), column=0, sticky="ew", pady=(15, 0), padx=5)
        btn_salvar = ctk.CTkButton(footer, text="Salvar", fg_color=cores["button_bg"], hover_color=cores["button_hover"], text_color=cores["selected_fg"])
        btn_salvar.pack(side="right")


class AppGUI(ctk.CTk):
    def __init__(self, api):
        super().__init__()
        self.api = api
        
        self.app_state = load_state()
        self.tema_atual = self.app_state.get("theme", "dark_green")
        self.colunas_visiveis = self.app_state.get("colunas_visiveis", COLUNAS)
        
        self.controller = DataController(COLUNAS, ITENS_POR_PAGINA)
        self.exportar = Exportar(self, self.controller)

        self._debounce_id, self._status_clear_id, self.current_render_thread = None, None, None
        self.pagina_atual, self.is_fullscreen = 1, False
        self.client_status, self._monitoring_job_id = {}, None
        self.monitoring_interval_ms, self._last_monitoring_start = 10 * 60 * 1000, 0
        
        self.MAX_MONITORING_THREADS = 4 
        
        self.render_queue = Queue()

        self.title("App de Consulta Avançada")
        self.geometry(self.app_state.get("geometry", "1300x700"))
        self.minsize(1000, 550)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._criar_widgets()
        self.aplicar_tema_completo()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.controller.coluna_ordenacao = self.app_state.get("coluna_ordenacao", "DATAHORA")
        self.controller.ordem_desc = self.app_state.get("ordem_desc", True)
        self.pagina_atual = self.app_state.get("pagina_atual", 1)
        
        threading.Thread(target=self.carregar_dados_iniciais_com_cache, daemon=True).start()
        self.schedule_auto_refresh()
        self.after(5000, self.monitor_all_clients)
        
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)
        
        self.processar_fila_renderizacao()
        
        self.show_frame("Consultas")
        self.gerir_estado_widgets(False)

    def _criar_widgets(self):
        # --- Menu ComboBox ---
        self.menu_frame = ctk.CTkFrame(self, corner_radius=0)
        self.menu_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10,5))
        
        self.screen_names = ["Consultas", "Dashboard", "Configurações"]
        self.menu_combobox = ctk.CTkComboBox(self.menu_frame, values=self.screen_names, command=self.show_frame, font=ctk.CTkFont(size=14))
        self.menu_combobox.pack(side="left", padx=10, pady=10)
        
        self.btn_alternar_tema = ctk.CTkButton(self.menu_frame, text="🎨", command=self.alternar_tema, width=40)
        self.btn_alternar_tema.pack(side="right", padx=10, pady=10)
        
        # --- Conteúdo Principal ---
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 5))
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        self.screen_classes = {"Consultas": ConsultaScreen, "Dashboard": DashboardScreen, "Configurações": SettingsScreen}
        self.active_frame_name = None

        # --- Status Bar ---
        self.status_bar = ctk.CTkFrame(self, height=25, corner_radius=0)
        self.status_bar.grid(row=2, column=0, sticky="ew")
        self.status_bar.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(self.status_bar, text="Bem-vindo!", anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew", padx=10, pady=2)
        self.last_updated_label = ctk.CTkLabel(self.status_bar, text="", anchor="e")
        self.last_updated_label.grid(row=0, column=1, sticky="e", padx=10, pady=2)
    
    def on_closing(self):
        self.app_state.update({
            "theme": self.tema_atual, "geometry": self.geometry(),
            "colunas_visiveis": self.colunas_visiveis, "coluna_ordenacao": self.controller.coluna_ordenacao,
            "ordem_desc": self.controller.ordem_desc, "pagina_atual": self.pagina_atual
        })
        if self._monitoring_job_id: self.after_cancel(self._monitoring_job_id)
        save_state(self.app_state)
        self.destroy()

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
        return "break"

    def exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.attributes("-fullscreen", False)
            return "break"

    def _create_frame_if_not_exists(self, frame_name):
        if frame_name not in self.frames:
            screen_class = self.screen_classes[frame_name]
            
            if screen_class == ConsultaScreen:
                frame = screen_class(self.container, self.controller, self.api, main_app=self)
                # Define os widgets interativos da app principal aqui
                self.all_interactive_widgets = frame.widgets_interativos + [self.menu_combobox, self.btn_alternar_tema]
            elif screen_class == DashboardScreen:
                frame = screen_class(self.container, self.client_status, main_app=self)
            else: # SettingsScreen e outros
                frame = screen_class(self.container, main_app=self)

            self.frames[frame_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_remove()


    def show_frame(self, frame_name_to_show):
        if self.active_frame_name == frame_name_to_show: return
        if self.active_frame_name and self.active_frame_name in self.frames:
            old_frame = self.frames[self.active_frame_name]
            old_frame.grid_remove()
            if hasattr(old_frame, 'stop_periodic_update'): old_frame.stop_periodic_update()
        self._create_frame_if_not_exists(frame_name_to_show)
        new_frame = self.frames[frame_name_to_show]
        new_frame.grid()
        new_frame.tkraise()
        if hasattr(new_frame, 'start_periodic_update'): new_frame.start_periodic_update()
        self.active_frame_name = frame_name_to_show
        self.menu_combobox.set(frame_name_to_show)
        self.aplicar_tema_completo()

    def abrir_configuracao_colunas(self, tabela_ref):
        ColumnSettingsWindow(self, COLUNAS, self.colunas_visiveis)

    def aplicar_novas_colunas(self, novas_colunas_visiveis, tabela_ref):
        self.colunas_visiveis = novas_colunas_visiveis
        tabela_ref.reconstruir_colunas(self.colunas_visiveis, on_sort_command=self.ordenar_por_coluna)
        self.update_status(f"Colunas atualizadas: {len(novas_colunas_visiveis)}/{len(COLUNAS)}.")

    def aplicar_filtro_debounce(self, event=None):
        if self._debounce_id: self.after_cancel(self._debounce_id)
        if not self._handle_date_validation(): return
        self._debounce_id = self.after(300, self.aplicar_filtro)

    def aplicar_filtro(self):
        screen = self.frames["Consultas"]
        try:
            self.controller.set_filtro_texto(screen.entry_filtro.get(), screen.combo_coluna.get())
            self.controller.set_filtro_data(screen.entry_data_inicio.get(), screen.entry_data_fim.get())
            self.controller.aplicar_filtro()
        except ValueError: return
        self.pagina_atual = 1
        self.renderizar_dados()

    def limpar_filtro(self):
        screen = self.frames["Consultas"]
        screen.entry_filtro.delete(0, 'end')
        screen.entry_data_inicio.delete(0, 'end')
        screen.entry_data_fim.delete(0, 'end')
        self._reset_date_border(screen.entry_data_inicio)
        self._reset_date_border(screen.entry_data_fim)
        self.aplicar_filtro()

    def ordenar_por_coluna(self, coluna):
        self.controller.ordenar(coluna)
        self.controller.aplicar_filtro(re_sort_only=True)
        self.pagina_atual = 1
        self.renderizar_dados()

    def ir_para_pagina(self, numero_pagina):
        self.pagina_atual = numero_pagina
        self.renderizar_dados()

    def primeira_pagina(self): self.ir_para_pagina(1)
    def ultima_pagina(self): self.ir_para_pagina(self.controller.total_paginas)
    def pagina_anterior(self): self.ir_para_pagina(self.pagina_atual - 1)
    def proxima_pagina(self): self.ir_para_pagina(self.pagina_atual + 1)

    def atualizar_label_pagina(self, label_pagina):
        total_registos = self.controller.total_registos
        total_paginas = self.controller.total_paginas if total_registos > 0 else 1
        self.pagina_atual = max(1, min(self.pagina_atual, total_paginas))
        label_pagina.configure(text=f"Página {self.pagina_atual}/{total_paginas} ({total_registos})")

    def exportar_excel(self): self.exportar.salvar_excel_async()
    def exportar_csv(self): self.exportar.salvar_csv_async()

    def renderizar_dados(self):
        if "Consultas" not in self.frames: return
        self.configure(cursor="watch")
        self.current_render_thread = threading.get_ident()
        threading.Thread(target=self.renderizar_dados_thread, args=(self.current_render_thread, self.pagina_atual), daemon=True).start()

    def renderizar_dados_thread(self, thread_id, numero_pagina):
        if self.current_render_thread != thread_id: return
        page_num, dados = self.controller.get_dados_pagina(numero_pagina)
        if self.current_render_thread == thread_id:
            self.render_queue.put((page_num, dados))

    def processar_fila_renderizacao(self):
        try:
            page_num, dados = self.render_queue.get_nowait()
            if "Consultas" in self.frames and self.frames["Consultas"].winfo_exists():
                screen = self.frames["Consultas"]
                self.pagina_atual = page_num
                screen.tabela.atualizar_tabela(dados)
                screen.atualizar_elementos()
                self.update_status(f"{self.controller.total_registos} registos.")
                self.configure(cursor="")
        except Exception: pass
        finally: self.after(100, self.processar_fila_renderizacao)

    def carregar_dados_iniciais_com_cache(self, is_auto_refresh=False):
        def update_status(message, clear_after_ms=0):
            self.after(0, lambda: self.update_status(message, clear_after_ms))
        def show_msg(message):
            if "Consultas" in self.frames:
                self.after(0, lambda: self.frames["Consultas"].tabela.mostrar_mensagem(message))
        try:
            if not is_auto_refresh:
                update_status("A carregar do cache...")
                show_msg("A carregar...")
                dados = self.api.buscar_todos()
                if dados:
                    self.controller.dados_completos = dados
                    self.after(0, self.renderizar_dados)
                    update_status(f"{len(dados)} registos do cache.")
            dados_frescos = self.api.buscar_todos(force_refresh=True)
            if dados_frescos and dados_frescos != self.controller.dados_completos:
                self.controller.dados_completos = dados_frescos
                self.after(0, self.renderizar_dados)
                update_status(f"Dados atualizados: {len(dados_frescos)} registos.")
            elif is_auto_refresh: update_status("Nenhum dado novo.")
            self.last_updated_label.configure(text=f"Última verificação: {datetime.now():%H:%M:%S}")
        except ConsultaAPIException as e: update_status(f"ERRO API: {e}", 5000)
        finally:
            if not is_auto_refresh: self.after(0, lambda: self.gerir_estado_widgets(True))

    def consultar_api_async(self):
        threading.Thread(target=self.consultar_api, daemon=True).start()

    def refresh_data_async(self):
        self.gerir_estado_widgets(False)
        self.update_status("A atualizar dados...")
        threading.Thread(target=self.carregar_dados_iniciais_com_cache, args=(True,), daemon=True).start()

    def consultar_api(self):
        id_msg = self.frames["Consultas"].entry_id.get().strip()
        if not (id_msg and id_msg.isdigit()):
            return self.after(0, lambda: messagebox.showwarning("Atenção", "IDMENSAGEM deve ser um número."))
        self.after(0, lambda: self.frames["Consultas"].btn_consultar.configure(state="disabled", text="..."))
        try:
            dados = self.api.consultar(id_msg)
            self.controller.dados_completos = dados
            self.after(0, self.renderizar_dados)
            self.after(0, lambda: self.update_status(f"ID {id_msg}: {len(dados) if dados else 'Nenhum'} registo(s).", 5000))
        except ConsultaAPIException as e:
            self.after(0, lambda err=e: messagebox.showerror("Erro de API", str(err)))
        finally:
            self.after(0, lambda: self.frames["Consultas"].btn_consultar.configure(state="normal", text="Consultar"))

    # CORREÇÃO: Lambdas ajustadas para capturar a exceção corretamente
    def monitor_client_task(self, track_id):
        try:
            self.after(0, lambda: self._update_client_status(track_id, 'PROCESSANDO'))
            registo = self.api.consultar_by_trackid(track_id)
            if registo and 'DATAHORA' in registo:
                self.after(0, lambda last_time=registo['DATAHORA']: self._update_client_status(track_id, 'OK', last_message_time=last_time))
            else:
                self.after(0, lambda: self._update_client_status(track_id, 'OK', message="Sem registos recentes"))
        except ConsultaAPIException as e:
            self.after(0, lambda err=e: self._update_client_status(track_id, 'ERRO', message=str(err)))
        except Exception as e:
             self.after(0, lambda err=e: self._update_client_status(track_id, 'ERRO', message=f"Erro Inesperado: {err}"))

    def _update_client_status(self, track_id, status, message="", last_message_time=None):
        self.client_status[track_id] = {
            'status': status,
            'timestamp': datetime.now(),
            'message': message,
            'last_message_time': last_message_time
        }
        if status == 'ERRO':
            logging.warning(f"TrackID {track_id} ERRO: {message}")
            self.update_status(f"ERRO MONITORAMENTO: TrackID {track_id}.", 10000)

    def monitor_all_clients(self):
        if not self.controller.dados_completos:
            return self.schedule_client_monitoring()
        ids = {item.get("TrackID") for item in self.controller.dados_completos if item.get("TrackID")}
        for i in ids:
            if i not in self.client_status: self.client_status[i] = {}
        for i in list(self.client_status.keys()):
            if i not in ids: del self.client_status[i]
        if ids:
            self.update_status(f"Monitorando {len(ids)} clientes...", 3000)
            self._last_monitoring_start = datetime.now().timestamp() * 1000
            threading.Thread(target=lambda: self._run_monitoring_tasks(ids), daemon=True).start()
        else: self.schedule_client_monitoring()

    def _run_monitoring_tasks(self, track_ids):
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_MONITORING_THREADS) as executor:
            executor.map(self.monitor_client_task, track_ids)
        self.schedule_client_monitoring()

    def schedule_client_monitoring(self):
        if self._monitoring_job_id: self.after_cancel(self._monitoring_job_id)
        self._monitoring_job_id = self.after(self.monitoring_interval_ms, self.monitor_all_clients)

    def _handle_date_validation(self):
        is_valid = True
        for entry in [self.frames["Consultas"].entry_data_inicio, self.frames["Consultas"].entry_data_fim]:
            if entry.get() and not is_valid_ui_date(entry.get()):
                entry.configure(border_color=TEMAS[self.tema_atual]["error_color"], border_width=2)
                is_valid = False
            else: self._reset_date_border(entry)
        if not is_valid: self.update_status("ERRO: Data inválida (Use AAAA-MM-DD).", 5000)
        return is_valid

    def _reset_date_border(self, entry):
        entry.configure(border_color=TEMAS[self.tema_atual]["placeholder"], border_width=1)

    def gerir_estado_widgets(self, habilitar):
        estado = "normal" if habilitar else "disabled"
        all_widgets = getattr(self, 'all_interactive_widgets', [])
        for widget in all_widgets:
            if widget and widget.winfo_exists():
                widget.configure(state=estado)

    def update_status(self, message, clear_after_ms=0):
        if self.status_label.winfo_exists():
            self.status_label.configure(text=message)
            if self._status_clear_id: self.after_cancel(self._status_clear_id)
            if clear_after_ms > 0:
                self._status_clear_id = self.after(clear_after_ms, lambda: self.status_label.configure(text=""))

    def schedule_auto_refresh(self):
        if AUTO_REFRESH_MINUTES > 0:
            self.after(AUTO_REFRESH_MINUTES * 60 * 1000, self.auto_refresh_data)

    def auto_refresh_data(self):
        self.update_status("Atualizando em segundo plano...")
        threading.Thread(target=self.carregar_dados_iniciais_com_cache, args=(True,), daemon=True).start()
        self.schedule_auto_refresh()

    def alternar_tema(self):
        self.tema_atual = "light_green" if self.tema_atual == "dark_green" else "dark_green"
        self.aplicar_tema_completo()

    def aplicar_tema_completo(self):
        cores = TEMAS[self.tema_atual]
        self.configure(fg_color=cores["bg"])
        self.menu_frame.configure(fg_color=cores["alt_bg"])
        self.status_bar.configure(fg_color=cores["alt_bg"])
        self.status_label.configure(text_color=cores["fg"])
        self.last_updated_label.configure(text_color=cores["fg"])
        
        self.menu_combobox.configure(fg_color=cores["button_bg"], text_color=cores["selected_fg"],
                                     border_color=cores["placeholder"], button_color=cores["button_bg"],
                                     button_hover_color=cores["button_hover"],
                                     dropdown_fg_color=cores["alt_bg"],
                                     dropdown_hover_color=cores["button_hover"],
                                     dropdown_text_color=cores["fg"])

        self.btn_alternar_tema.configure(fg_color=cores["button_bg"], hover_color=cores["button_hover"], text_color=cores["selected_fg"])
        
        for frame in self.frames.values():
            if frame.winfo_exists() and hasattr(frame, 'aplicar_tema'):
                frame.aplicar_tema(cores)