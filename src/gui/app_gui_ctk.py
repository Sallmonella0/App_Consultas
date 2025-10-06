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
from src.core.exceptions import ConsultaAPIException, APIAuthError
# -------------------------

from src.gui.tabela import Tabela 

from src.utils.exportar import Exportar
from src.utils.config import COLUNAS
from src.utils.settings_manager import AUTO_REFRESH_MINUTES, ITENS_POR_PAGINA 
from src.utils.state_manager import load_state, save_state
from src.utils.datetime_utils import is_valid_ui_date, parse_api_datetime_to_date 

# --- PALETA DE CORES CONFORME ESPECIFICAÇÃO DO TEMA ESCURO ---
TEMAS = {
    "dark_green": { 
        "bg": "#1E1E1E",        # Fundo principal
        "alt_bg": "#2B2B2B",    # Containers/Cards/Tabela
        "fg": "#EAEAEA",        # Textos primários (branco suave)
        "selected_bg": "#4CAF50", # Cor de seleção/Status OK (Verde)
        "selected_fg": "#EAEAEA", # Texto em cor de seleção (Branco)
        "button_bg": "#4CAF50",   # Botões principais (Verde)
        "button_hover": "#6FD36F",# Hover de botão (Verde claro)
        "entry_bg": "#1E1E1E",    # Fundo dos inputs
        "placeholder": "#B0B0B0", # Textos secundários/placeholder (Cinza-claro)
        "error_color": "#E74C3C"  # Erro Status/Borda (Vermelho)
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
    # Mantida como Toplevel para configuração de colunas
    def __init__(self, master, all_columns, current_visible_columns, apply_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.title("Configurar Colunas Visíveis")
        self.transient(master)
        self.master = master
        self.all_columns = all_columns
        self.apply_callback = apply_callback
        self.checkbox_vars = {}
        
        self.grab_set() 
        self.grid_columnconfigure(0, weight=1)
        
        frame = ctk.CTkScrollableFrame(self)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        for i, col in enumerate(self.all_columns):
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

        self.apply_callback(selected_columns)
        self.destroy()
        
    def destroy(self):
        self.grab_release()
        super().destroy()

# --- CLASSES DE ECRÃ (SCREENS) ---

class ConsultaScreen(ctk.CTkFrame):
    """Implementa a Tela de Consultas e Tabela (funcionalidade original)."""
    def __init__(self, master, controller, api, main_app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.master_app = main_app 
        self.controller = controller
        self.api = api
        
        # Configuração de Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Tabela é row 2
        
        self._criar_widgets()
        
    def _criar_widgets(self):
        # --- 1. Cabeçalho Superior (Consulta ID) ---
        self.frame_top = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        self.label_id = ctk.CTkLabel(self.frame_top, text="IDMENSAGEM:")
        self.label_id.pack(side="left", padx=(0, 5))
        self.entry_id = ctk.CTkEntry(self.frame_top, width=150)
        self.entry_id.pack(side="left")
        self.entry_id.bind("<Return>", lambda e: self.master_app.consultar_api_async())
        
        self.btn_consultar = ctk.CTkButton(self.frame_top, text="Consultar", width=100, command=lambda: self.master_app.consultar_api_async())
        self.btn_consultar.pack(side="left", padx=5)

        self.btn_refresh = ctk.CTkButton(self.frame_top, text="Refresh", width=100, command=self.master_app.refresh_data_async)
        self.btn_refresh.pack(side="left", padx=5)

        self.btn_config_colunas = ctk.CTkButton(self.frame_top, text="Colunas", width=100, command=self._abrir_configuracao_colunas)
        self.btn_config_colunas.pack(side="left", padx=15)
        
        # --- Seção Filtros (Termo, Coluna, Data) ---
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

        # --- 2. Área Central (Tabela de Dados) ---
        self.frame_table = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_table.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.frame_table.grid_rowconfigure(0, weight=1)
        self.frame_table.grid_columnconfigure(0, weight=1)
        
        # A Tabela é criada na AppGUI e a referência é salva aqui para acesso fácil
        # Passando o argumento on_rebuild_command
        self.tabela = Tabela(self.frame_table, COLUNAS, self.master_app.colunas_visiveis, 
                             on_sort_command=self.master_app.ordenar_por_coluna,
                             on_rebuild_command=self.master_app.renderizar_dados)
        self.tabela.grid(row=0, column=0, sticky="nsew")

        # --- 3. Rodapé (Paginação e Exportação) ---
        self.frame_bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_bottom.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 0))
        
        self.frame_paginacao = ctk.CTkFrame(self.frame_bottom, fg_color="transparent")
        self.frame_paginacao.pack(side="left", expand=True, fill="x")

        self.btn_primeira = ctk.CTkButton(self.frame_paginacao, text="<< Primeira", width=100, command=self.master_app.primeira_pagina)
        self.btn_primeira.pack(side="left", padx=(0, 5))

        self.btn_anterior = ctk.CTkButton(self.frame_paginacao, text="< Anterior", width=100, command=self.master_app.pagina_anterior)
        self.btn_anterior.pack(side="left", padx=5)
        self.label_pagina = ctk.CTkLabel(self.frame_paginacao, text="Página 1 / 1")
        self.label_pagina.pack(side="left", padx=10)
        self.btn_proximo = ctk.CTkButton(self.frame_paginacao, text="Próximo >", width=100, command=self.master_app.proxima_pagina)
        self.btn_proximo.pack(side="left", padx=5)

        self.btn_ultima = ctk.CTkButton(self.frame_paginacao, text="Última >>", width=100, command=self.master_app.ultima_pagina)
        self.btn_ultima.pack(side="left", padx=5)

        # Envolver o método de exportação em lambda para evitar o AttributeError
        self.btn_excel = ctk.CTkButton(self.frame_bottom, text="Salvar Excel", command=lambda: self.master_app.exportar_excel())
        self.btn_excel.pack(side="right", padx=5)
        self.btn_csv = ctk.CTkButton(self.frame_bottom, text="Salvar CSV", command=lambda: self.master_app.exportar_csv())
        self.btn_csv.pack(side="right")
        
        # Lista de widgets interativos para gerir estado (habilitar/desabilitar)
        self.widgets_interativos = [
            self.entry_id, self.btn_consultar, self.btn_refresh, self.btn_config_colunas,
            self.entry_filtro, self.combo_coluna, self.btn_limpar_filtro,
            self.entry_data_inicio, self.entry_data_fim,
            self.btn_primeira, self.btn_anterior, self.btn_proximo, self.btn_ultima, 
            self.btn_excel, self.btn_csv
        ]

    def _abrir_configuracao_colunas(self):
        """Chama o método na AppGUI para abrir a janela Toplevel."""
        self.master_app.abrir_configuracao_colunas(self.tabela)

    def atualizar_elementos(self):
        """Usado pela AppGUI para atualizar labels de paginação e estado da tabela."""
        self.master_app.atualizar_label_pagina(self.label_pagina)
        self.tabela.atualizar_indicador_ordenacao(self.controller.coluna_ordenacao, self.controller.ordem_desc)
    
    def aplicar_tema(self, cores):
        """Aplica as cores específicas do tema a esta tela."""
        for entry in [self.entry_id, self.entry_filtro, self.entry_data_inicio, self.entry_data_fim]:
            entry.configure(fg_color=cores["entry_bg"], text_color=cores["fg"], border_color=cores["placeholder"], border_width=1, placeholder_text_color=cores["placeholder"])
        for lbl in [self.label_id, self.label_filtro, self.label_data_inicio, self.label_data_fim]:
            lbl.configure(text_color=cores["fg"])
        self.combo_coluna.configure(fg_color=cores["entry_bg"], text_color=cores["fg"], border_color=cores["placeholder"],
                                    button_color=cores["button_bg"], button_hover_color=cores["button_hover"],
                                    dropdown_fg_color=cores["alt_bg"], dropdown_hover_color=cores["button_hover"])
        # Aplica o tema aos botões, que foram criados na ConsultaScreen
        botoes = [self.btn_consultar, self.btn_refresh, self.btn_config_colunas, self.btn_limpar_filtro, 
                  self.btn_primeira, self.btn_anterior, self.btn_proximo, self.btn_ultima, 
                  self.btn_excel, self.btn_csv]
        for btn in botoes:
            btn.configure(fg_color=cores["button_bg"], hover_color=cores["button_hover"], text_color=cores["fg"])

        self.tabela.atualizar_cores(cores)


class DashboardScreen(ctk.CTkFrame):
    """Implementa o Dashboard de Status (Incorporado no Main Window)."""
    def __init__(self, master, client_status_ref, main_app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.master_app = main_app 
        self.client_status_ref = client_status_ref
        self.status_labels = {}
        self.current_ids = set() 
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self._criar_widgets()
        
        # Inicia a atualização periódica dos labels, essencialmente substituindo periodic_update do Toplevel
        self._after_id = self.after(100, self.periodic_update)

    def _criar_widgets(self):
        cores = TEMAS[self.master_app.tema_atual]
        
        # 1. Cabeçalho do Dashboard
        self.header_frame = ctk.CTkFrame(self, fg_color=cores["alt_bg"], height=80)
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 5))
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.title_label = ctk.CTkLabel(self.header_frame, text="Dashboard de Status do Cliente", font=ctk.CTkFont(size=22, weight="bold"), text_color=cores["fg"])
        self.title_label.grid(row=0, column=0, sticky="w", padx=15, pady=15)

        self.status_summary_label = ctk.CTkLabel(self.header_frame, text="Monitorando 0 clientes | Última atualização: N/A", text_color=cores["placeholder"])
        self.status_summary_label.grid(row=0, column=1, sticky="e", padx=15, pady=15)

        # 2. Área Central (Painel de Status Scrollable)
        # NOTA: Alterado o label de "IDMENSAGEM" para "TrackID"
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Status por TrackID", fg_color=cores["alt_bg"])
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        # 3. Rodapé de Configuração (Tempo Restante)
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 10))

        self.interval_label = ctk.CTkLabel(self.footer_frame, text="Próxima Verificação em: N/A", anchor="w", text_color=cores["fg"])
        self.interval_label.pack(side="left", padx=10)

        # Inicia a primeira construção de labels
        self.update_display()
        
    # --- Lógica de Atualização (Mantida a otimização de atualização leve) ---
    def update_display(self):
        """Verifica se a lista de IDs mudou e decide entre reconstrução total ou atualização leve."""
        new_ids = set(self.client_status_ref.keys())
        
        if new_ids != self.current_ids:
            self.current_ids = new_ids
            # Reconstrução completa
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.status_labels = {}
            self._build_labels(sorted(list(new_ids)))
        else:
            # Atualização leve
            self._update_labels_only(sorted(list(new_ids)))

        # Atualiza o cabeçalho
        total_clientes = len(self.current_ids)
        ok_count = sum(1 for status in self.client_status_ref.values() if status.get('status') == 'OK')
        now = datetime.now().strftime("%H:%M:%S")
        self.status_summary_label.configure(text=f"Monitorando {total_clientes} clientes ({ok_count} OK) | Última atualização: {now}")

        # Atualiza o rodapé (Timer)
        app = self.master_app
        if hasattr(app, '_last_monitoring_start') and app._last_monitoring_start > 0:
             time_elapsed = datetime.now().timestamp() * 1000 - app._last_monitoring_start
             time_remaining_ms = max(0, app.monitoring_interval_ms - time_elapsed)
             seconds_remaining = math.ceil(time_remaining_ms / 1000)
             self.interval_label.configure(text=f"Próxima Verificação em: {seconds_remaining}s")

    def _build_labels(self, sorted_ids):
        """Cria todos os widgets de status de cliente."""
        cores = TEMAS[self.master_app.tema_atual]
        
        for i, track_id in enumerate(sorted_ids): # Variável alterada para track_id
            # Card Status
            frame = ctk.CTkFrame(self.scrollable_frame, fg_color=cores["alt_bg"], border_color=cores["placeholder"], border_width=1)
            frame.grid(row=i, column=0, sticky="ew", pady=5, padx=5)
            frame.grid_columnconfigure(1, weight=1)

            # Label alterado para exibir TrackID
            id_label = ctk.CTkLabel(frame, text=f"TrackID: {track_id}", width=100, anchor="w", text_color=cores["fg"], font=ctk.CTkFont(weight="bold"))
            id_label.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")
            
            status_label = ctk.CTkLabel(frame, text="AGUARDANDO", anchor="w")
            status_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
            
            self.status_labels[track_id] = status_label
            
        self._update_labels_only(sorted_ids)

    def _update_labels_only(self, sorted_ids):
        """Atualiza o texto, a cor e o binding dos labels existentes (processo leve)."""
        cores = TEMAS[self.master_app.tema_atual]
        
        for track_id in sorted_ids: # Variável alterada para track_id
            status = self.client_status_ref.get(track_id, {})
            label = self.status_labels.get(track_id)
            if not label: continue 
            
            status_text = status.get('status', 'AGUARDANDO')
            status_time = status.get('timestamp', 'N/A')
            status_message = status.get('message', '')
            
            display_text = f"{status_text} ({status_time.strftime('%H:%M:%S') if status_time != 'N/A' else 'N/A'})"
            
            color = cores["fg"]
            if status_text == "OK": color = "#4CAF50" # Verde
            elif status_text == "ERRO": 
                color = cores["error_color"] # Vermelho (#E74C3C)
                label.unbind("<Button-1>") 
                # Mensagem de erro alterada para TrackID
                label.bind("<Button-1>", lambda e, id=track_id, msg=status_message: messagebox.showerror(f"Erro de Monitoramento - TrackID {id}", msg))
            elif status_text == "PROCESSANDO": 
                color = "#F1C40F" # Amarelo (Timeout/Indisponível)
                label.unbind("<Button-1>") 
            
            label.configure(text=display_text, text_color=color)

    def periodic_update(self):
        """Agenda a atualização do dashboard a cada 1 segundo."""
        if self.winfo_exists():
            self.update_display() 
            self._after_id = self.after(1000, self.periodic_update)

    def destroy(self):
        """Certifica-se de que a atualização periódica para quando o ecrã é fechado/trocado."""
        if hasattr(self, '_after_id') and self._after_id:
            self.after_cancel(self._after_id)
        super().destroy()


class SettingsScreen(ctk.CTkFrame):
    """Implementa a Tela de Configurações (Esquelética)."""
    def __init__(self, master, main_app, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.master_app = main_app 
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Configurações do Sistema", label_font=ctk.CTkFont(size=20))
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self._criar_cards()

    def _criar_cards(self):
        cores = TEMAS[self.master_app.tema_atual]
        
        # --- 1. Seção Monitoramento ---
        elements_monitoramento = [
            ("Intervalo de Verificação (min):", ctk.CTkEntry(self.scrollable_frame, placeholder_text="10")),
            ("Timeout de Requisição (ms):", ctk.CTkEntry(self.scrollable_frame, placeholder_text="15000")),
            ("Tentativas de Reconexão:", ctk.CTkEntry(self.scrollable_frame, placeholder_text="3")),
            ctk.CTkCheckBox(self.scrollable_frame, text="Ativar monitoramento em tempo real")
        ]
        self._create_setting_card("Monitoramento e Performance", 0, cores, elements_monitoramento)

        # --- 2. Seção Notificações ---
        elements_notificacoes = [
            ctk.CTkLabel(self.scrollable_frame, text="Canais de Notificação:", text_color=cores["fg"]),
            ctk.CTkCheckBox(self.scrollable_frame, text="Email"),
            ctk.CTkCheckBox(self.scrollable_frame, text="Navegador"),
            ctk.CTkCheckBox(self.scrollable_frame, text="Slack"),
            ctk.CTkCheckBox(self.scrollable_frame, text="Webhook")
        ]
        self._create_setting_card("Notificações", 1, cores, elements_notificacoes)

        # --- 3. Seção Interface ---
        elements_interface = [
            ("Itens por Página:", ctk.CTkComboBox(self.scrollable_frame, values=["50", "100", "200"])),
            ("Intervalo Atualização Tabela (min):", ctk.CTkEntry(self.scrollable_frame, placeholder_text="10")),
            ctk.CTkCheckBox(self.scrollable_frame, text="Modo Compacto"),
        ]
        self._create_setting_card("Interface e Aparência", 2, cores, elements_interface)

        # --- 4. Seção Dados e Cache ---
        elements_dados = [
            ("Retenção de Dados (dias):", ctk.CTkEntry(self.scrollable_frame, placeholder_text="30")),
            ("Máx. Registros Armazenados:", ctk.CTkEntry(self.scrollable_frame, placeholder_text="10000")),
            ("Formato Exportação Padrão:", ctk.CTkComboBox(self.scrollable_frame, values=["CSV", "Excel", "JSON"])),
            ctk.CTkButton(self.scrollable_frame, text="Limpar Cache Local Agora", fg_color=cores["alt_bg"], hover_color=cores["button_hover"], text_color=cores["fg"])
        ]
        self._create_setting_card("Gestão de Dados", 3, cores, elements_dados)

        # --- 5. Seção Chaves de API ---
        elements_chaves = [
            ("Slack API Key:", ctk.CTkEntry(self.scrollable_frame)),
            ("Webhook URL:", ctk.CTkEntry(self.scrollable_frame)),
            ("Email API Key:", ctk.CTkEntry(self.scrollable_frame)),
        ]
        self._create_setting_card("Chaves de Integração (API)", 4, cores, elements_chaves)

        # --- 6. Rodapé de Ações ---
        footer = ctk.CTkFrame(self.scrollable_frame, fg_color="transparent")
        footer.grid(row=5, column=0, sticky="ew", pady=(15, 0))
        footer.grid_columnconfigure(0, weight=1)

        btn_salvar = ctk.CTkButton(footer, text="Salvar Configurações", fg_color=cores["button_bg"], hover_color=cores["button_hover"], text_color=cores["fg"])
        btn_salvar.pack(side="right", padx=5)

        btn_restaurar = ctk.CTkButton(footer, text="Restaurar Padrões", fg_color=cores["alt_bg"], hover_color=cores["placeholder"], text_color=cores["fg"])
        btn_restaurar.pack(side="right", padx=5)


    def _create_setting_card(self, title, row, cores, elements):
        """Cria um card genérico para agrupar elementos de configuração."""
        card = ctk.CTkFrame(self.scrollable_frame, fg_color=cores["alt_bg"], border_color=cores["placeholder"], border_width=1)
        card.grid(row=row, column=0, sticky="ew", pady=10, padx=5)
        card.grid_columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=16, weight="bold"), text_color=cores["fg"])
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(15, 10))

        for i, element in enumerate(elements):
            if isinstance(element, tuple):
                label_text, widget = element
                lbl = ctk.CTkLabel(card, text=label_text, anchor="w", text_color=cores["fg"])
                lbl.grid(row=i+1, column=0, sticky="w", padx=15, pady=5)
                
                # A re-parentação é tratada pelo widget.grid() com in_=card.
                widget.configure(text_color=cores["fg"], fg_color=cores["entry_bg"], border_color=cores["placeholder"]) 
                widget.grid(row=i+1, column=1, sticky="ew", padx=15, pady=5, in_=card) 
            elif isinstance(element, (ctk.CTkCheckBox, ctk.CTkButton, ctk.CTkLabel)):
                # A re-parentação é tratada pelo widget.grid() com in_=card.
                element.configure(text_color=cores["fg"]) # Aplica tema
                element.grid(row=i+1, column=0, columnspan=2, sticky="w", padx=15, pady=5, in_=card) 
        
    def destroy(self):
        # Destrói o ecrã
        super().destroy()


# --- CLASSE PRINCIPAL ---

class AppGUI(ctk.CTk):
    """Gerencia a janela principal, o menu lateral e a troca de telas."""
    
    def __init__(self, api):
        super().__init__()
        self.api = api
        
        # --- Gestão de Estado e Controller ---
        self.app_state = load_state()
        self.tema_atual = self.app_state.get("theme", "dark_green")
        self._debounce_id = None
        self._status_clear_id = None 
        self.pagina_atual = 1
        self.is_fullscreen = False
        self.colunas_visiveis = self.app_state.get("colunas_visiveis", COLUNAS)
        
        # Instancia o DataController e Exportar (serão usados em todas as telas)
        self.controller = DataController(COLUNAS, ITENS_POR_PAGINA) 
        self.exportar = Exportar(self, COLUNAS)

        # Monitoramento
        self.client_status = {}
        self._monitoring_job_id = None
        self.monitoring_interval_ms = 10 * 60 * 1000 
        self._last_monitoring_start = datetime.now().timestamp() * 1000 # Para o timer do dashboard
        self.MAX_MONITORING_THREADS = 10 
        
        # --- Controlo de Threads ---
        self.render_queue = Queue()
        self.current_render_thread = None

        # Inicialização da lista de widgets interativos
        self.all_interactive_widgets = []
        
        # --- Configuração da Janela Principal ---
        self.title("App de Consulta Avançada")
        self.geometry(self.app_state.get("geometry", "1300x700"))
        self.minsize(1000, 550)
        
        # Layout principal: 1 coluna para menu, 1 coluna para conteúdo. 1 linha.
        self.grid_columnconfigure(0, weight=0) # Menu Fixo
        self.grid_columnconfigure(1, weight=1) # Conteúdo Dinâmico
        self.grid_rowconfigure(0, weight=1)    # Área de Conteúdo
        
        self._criar_widgets()
        self.aplicar_tema_completo()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configura o estado inicial do controller e carrega dados
        self.controller.coluna_ordenacao = self.app_state.get("coluna_ordenacao", "DATAHORA")
        self.controller.ordem_desc = self.app_state.get("ordem_desc", True)
        self.pagina_atual = self.app_state.get("pagina_atual", 1)
        
        # Carrega dados iniciais e agenda refreshes
        threading.Thread(target=self.carregar_dados_iniciais_com_cache, daemon=True).start()
        self.schedule_auto_refresh()
        self.after(5000, self.monitor_all_clients)
        
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)
        
        self.processar_fila_renderizacao()
        
        # Exibe a tela inicial (Consultas)
        self.show_frame("Consultas")
        self.gerir_estado_widgets(False) # Desabilita UI até os dados carregarem

    def toggle_fullscreen(self, event=None):
        """Alterna o estado de tela cheia."""
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
        return "break"

    def exit_fullscreen(self, event=None):
        """Sai do modo tela cheia."""
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.attributes("-fullscreen", False)
            return "break"

    def _criar_widgets(self):
        # --- Frame do Menu Lateral (Hamburger Menu) ---
        self.menu_frame = ctk.CTkFrame(self, width=200)
        self.menu_frame.grid(row=0, column=0, sticky="ns", padx=(10, 5), pady=10)
        self.menu_frame.grid_rowconfigure(4, weight=1) # Espaçador

        self.btn_toggle_menu = ctk.CTkButton(self.menu_frame, text="☰ Menu", command=self.toggle_menu, font=ctk.CTkFont(weight="bold"))
        self.btn_toggle_menu.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        self.navigation_buttons = {}
        self.screen_names = ["Consultas", "Dashboard", "Configurações"]
        for i, name in enumerate(self.screen_names):
            btn = ctk.CTkButton(self.menu_frame, text=name, command=lambda n=name: self.show_frame(n))
            btn.grid(row=i+1, column=0, sticky="ew", padx=10, pady=5)
            self.navigation_buttons[name] = btn
        
        # Botão Tema (Rodapé do menu)
        self.btn_alternar_tema = ctk.CTkButton(self.menu_frame, text="Alternar Tema", command=self.alternar_tema)
        self.btn_alternar_tema.grid(row=99, column=0, sticky="ew", padx=10, pady=(5, 10))


        # --- Frame de Conteúdo Central ---
        # Este Frame ocupa a maior parte do espaço e troca os ecrãs
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=(10, 5))
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # Criação das telas (Screens)
        self.frames = {}
        for F in (ConsultaScreen, DashboardScreen, SettingsScreen):
            # Passa 'self' (AppGUI) explicitamente como 'main_app'
            if F == ConsultaScreen:
                frame = F(self.container, self.controller, self.api, main_app=self)
            elif F == DashboardScreen:
                frame = F(self.container, self.client_status, main_app=self)
            else: # SettingsScreen
                frame = F(self.container, main_app=self)
                
            self.frames[F.__name__.replace('Screen', '')] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # --- Frame do Status Bar ---
        self.status_bar = ctk.CTkFrame(self, height=25)
        self.status_bar.grid(row=1, column=1, sticky="ew", padx=(5, 10), pady=(5, 10))
        self.status_bar.grid_columnconfigure(0, weight=1)
        self.status_bar.grid_columnconfigure(1, weight=1)
        
        self.status_label = ctk.CTkLabel(self.status_bar, text="Bem-vindo!", anchor="w")
        self.status_label.grid(row=0, column=0, sticky="w", padx=10, pady=2)
        self.last_updated_label = ctk.CTkLabel(self.status_bar, text="", anchor="e")
        self.last_updated_label.grid(row=0, column=1, sticky="e", padx=10, pady=2)
        
        # Lista de todos os widgets interativos de TODAS as telas (para gerir estado)
        # Garante que a lista só é preenchida se a chave existir
        if "Consultas" in self.frames:
            self.all_interactive_widgets = self.frames["Consultas"].widgets_interativos + [
                self.btn_toggle_menu, self.btn_alternar_tema
            ]
        else:
            self.all_interactive_widgets = [self.btn_toggle_menu, self.btn_alternar_tema]
        
    def show_frame(self, cont_name):
        """Troca o frame exibido na área de conteúdo central."""
        frame_to_show = self.frames.get(cont_name + "Screen")
        if frame_to_show:
            # 1. Destrói/cancela timers do frame anterior
            for frame in self.frames.values():
                if frame != frame_to_show and hasattr(frame, 'destroy'):
                    frame.destroy() 
            
            # 2. Exibe o novo frame
            frame_to_show.tkraise()
            
            # 3. Atualiza o estado visual dos botões do menu
            cores = TEMAS[self.tema_atual]
            for name, btn in self.navigation_buttons.items():
                if name == cont_name:
                    btn.configure(fg_color=cores["button_hover"]) # Botão selecionado
                else:
                    btn.configure(fg_color=cores["button_bg"]) # Botão normal
            
    def toggle_menu(self):
        # A implementação de toggle do menu lateral é complexa no CTk.
        # Mantendo o placeholder de função.
        pass
            
    # --- DELEGAÇÃO DE CHAMADAS DA CONSULTASCREEN ---

    def abrir_configuracao_colunas(self, tabela_ref):
        """Abre a janela Toplevel e passa a referência da Tabela para reconstrução."""
        ColumnSettingsWindow(self, COLUNAS, self.colunas_visiveis, 
                             lambda cols: self.aplicar_novas_colunas(cols, tabela_ref))

    def aplicar_novas_colunas(self, novas_colunas_visiveis, tabela_ref):
        """Callback para atualizar as colunas visíveis."""
        self.colunas_visiveis = novas_colunas_visiveis
        tabela_ref.reconstruir_colunas(self.colunas_visiveis, self.controller.ordenar_por_coluna)
        self.renderizar_dados()
        self.update_status(f"Colunas atualizadas. Visíveis: {len(novas_colunas_visiveis)}/{len(COLUNAS)}.")
    
    # Restante da lógica de filtro, ordenação e paginação é a mesma, mas chama a Tabela correta.

    def aplicar_filtro_debounce(self, event=None):
        if self._debounce_id: self.after_cancel(self._debounce_id)
        if not self.frames["Consultas"].master_app._handle_date_validation(): return
        self._debounce_id = self.after(300, self.aplicar_filtro)

    def aplicar_filtro(self):
        screen = self.frames["Consultas"]
        try:
            self.controller.set_filtro_texto(screen.entry_filtro.get(), screen.combo_coluna.get())
            self.controller.set_filtro_data(screen.entry_data_inicio.get(), screen.entry_data_fim.get())
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
        self.pagina_atual = 1 
        self.renderizar_dados()

    def ir_para_pagina(self, numero_pagina):
        screen = self.frames["Consultas"]
        page_num, dados_da_pagina = self.controller.get_dados_pagina(numero_pagina)
        self.pagina_atual = page_num
        screen.tabela.atualizar_tabela(dados_da_pagina)
        screen.atualizar_elementos()
    
    def primeira_pagina(self): self.ir_para_pagina(1)
    def ultima_pagina(self): self.ir_para_pagina(self.controller.total_paginas)
    def pagina_anterior(self): self.ir_para_pagina(self.pagina_atual - 1)
    def proxima_pagina(self): self.ir_para_pagina(self.pagina_atual + 1)
        
    def atualizar_label_pagina(self, label_pagina):
        total_registos = self.controller.total_registos
        total_paginas = self.controller.total_paginas
        label_pagina.configure(text=f"Página {self.pagina_atual} / {total_paginas} (Total: {total_registos})")

    # --- Lógica de API e Monitoramento ---

    def renderizar_dados(self):
        # FIX CRÍTICO: Checagem de segurança para evitar KeyError
        if "Consultas" not in self.frames:
            logging.warning("renderizar_dados chamado antes do frame 'Consultas' estar pronto. Ignorando a chamada inicial.")
            return

        screen = self.frames["Consultas"]
        self.configure(cursor="watch")
        thread_id = threading.get_ident()
        self.current_render_thread = thread_id
        args = (thread_id,)
        threading.Thread(target=self.renderizar_dados_thread, args=args, daemon=True).start()

    def processar_fila_renderizacao(self):
        # Sobreescrito para chamar o .tabela correto e atualizar os labels na screen
        try:
            data_page_num, dados_da_pagina = self.render_queue.get_nowait()
            screen = self.frames["Consultas"]
            self.pagina_atual = data_page_num
            total_registos = self.controller.total_registos 
            screen.tabela.atualizar_tabela(dados_da_pagina)
            screen.atualizar_elementos()
            self.update_status(f"{total_registos} registos encontrados.")
            self.configure(cursor="")
        except Exception:
            pass
        finally:
            self.after(100, self.processar_fila_renderizacao)

    def carregar_dados_iniciais_com_cache(self, is_auto_refresh=False):
        # FIX CRÍTICO: Encapsulamento das chamadas da UI para evitar KeyError no lambda
        
        def safe_update_status(message):
            self.after(0, lambda: self.update_status(message))

        def safe_mostrar_mensagem(message):
            screen = self.frames.get("Consultas")
            if screen:
                self.after(0, lambda: screen.tabela.mostrar_mensagem(message))
                
        try:
            if not is_auto_refresh:
                safe_update_status("A carregar dados do cache...")
                safe_mostrar_mensagem("A carregar...")
                
                dados_iniciais = self.api.buscar_todos(force_refresh=False)
                if dados_iniciais:
                    self.controller.dados_completos = dados_iniciais
                    self.after(0, self.renderizar_dados)
                    safe_update_status(f"{len(dados_iniciais)} registos carregados do cache.")
                    
                else:
                    safe_update_status("Cache vazio. A buscar dados da API...")
                    safe_mostrar_mensagem("Cache vazio. A buscar dados da API...")
            
            dados_frescos = self.api.buscar_todos(force_refresh=True)
            
            if dados_frescos and dados_frescos != self.controller.dados_completos:
                logging.info("Dados atualizados encontrados. A atualizar a interface.")
                self.controller.dados_completos = dados_frescos
                self.after(0, self.renderizar_dados)
                safe_update_status(f"Dados atualizados. Total de {len(dados_frescos)} registos.")
            elif is_auto_refresh:
                 safe_update_status("Nenhum dado novo encontrado.")
                 
            now = datetime.now().strftime("%H:%M:%S")
            self.last_updated_label.configure(text=f"Última verificação: {now}")

        except ConsultaAPIException as e: 
            self.after(0, lambda err=e: self.update_status(f"ERRO API: {err}", clear_after_ms=5000))
        except Exception as e:
            self.after(0, lambda err=e: self.update_status(f"ERRO INESPERADO: {err}", clear_after_ms=5000))
        finally:
            if not is_auto_refresh:
                self.after(0, lambda: self.gerir_estado_widgets(True))

    def consultar_api_async(self):
        threading.Thread(target=self.consultar_api, daemon=True).start()

    def refresh_data_async(self):
        self.gerir_estado_widgets(False) 
        self.update_status("A forçar atualização de dados da API...")
        threading.Thread(target=self.carregar_dados_iniciais_com_cache, daemon=True).start()

    def consultar_api(self):
        id_msg = self.frames["Consultas"].entry_id.get().strip()
        
        if not id_msg or not id_msg.isdigit():
            self.after(0, lambda: messagebox.showwarning("Atenção", "IDMENSAGEM deve ser um número inteiro e não pode estar vazio!"))
            return
            
        self.after(0, lambda: self.frames["Consultas"].btn_consultar.configure(state="disabled", text="Buscando..."))
        self.update_status(f"A buscar IDMENSAGEM {id_msg}...")
        try:
            dados = self.api.consultar(id_msg)
            self.controller.dados_completos = dados 
            self.after(0, self.renderizar_dados)
            
            if not dados:
                 self.after(0, lambda: self.update_status(f"ID {id_msg} consultado. Nenhum registo encontrado.", clear_after_ms=5000))
            else:
                 self.after(0, lambda: self.update_status(f"{len(dados)} registos encontrados para o ID {id_msg}.", clear_after_ms=5000))
                 
        except ConsultaAPIException as e:
            self.after(0, lambda err=e: messagebox.showerror("Erro de API", f"Falha na consulta:\n{err}"))
            self.after(0, lambda: self.update_status(f"Erro na consulta do ID {id_msg}.", clear_after_ms=5000))
        except Exception as e:
            self.after(0, lambda err=e: messagebox.showerror("Erro Inesperado", f"Falha na consulta:\n{err}"))
            self.after(0, lambda: self.update_status(f"Erro inesperado na consulta do ID {id_msg}.", clear_after_ms=5000))
        finally:
            self.after(0, lambda: self.frames["Consultas"].btn_consultar.configure(state="normal", text="Consultar"))

    # --- Lógica de Monitoramento (Corrigido para usar TrackID) ---

    def monitor_client_task(self, track_id):
        """Executa a consulta de monitoramento (síncrona) pelo TrackID dentro de uma thread do Executor."""
        
        try:
            # 1. Sinaliza que o processamento começou
            self.after(0, lambda: self._update_client_status(track_id, 'PROCESSANDO', message='Em andamento...'))
            
            # 2. Executa a chamada de API síncrona: ASSUME self.api.consultar_by_trackid EXISTE E ACEITA STRING
            self.api.consultar_by_trackid(track_id) 
            
            # 3. Sucesso
            self.after(0, lambda: self._update_client_status(track_id, 'OK'))

        except ConsultaAPIException as e:
            # 4. Erros da API
            self.after(0, lambda err=str(e): self._update_client_status(track_id, 'ERRO', message=f"Falha API: {err}"))
        except Exception as e:
            # 5. Erros inesperados
            self.after(0, lambda err=str(e): self._update_client_status(track_id, 'ERRO', message=f"Erro Inesperado: {err}"))

    def _update_client_status(self, track_id, status, message=""):
        """Atualiza o estado de monitoramento na thread principal da GUI."""
        # A chave do dicionário é agora o TrackID
        self.client_status[track_id] = {
            'status': status,
            'timestamp': datetime.now(),
            'message': message
        }
        if status == 'ERRO':
             logging.warning(f"TrackID {track_id} ERRO DE MONITORAMENTO: {message}")
             self.update_status(f"ERRO DE MONITORAMENTO: TrackID {track_id}. Detalhes no Dashboard.", clear_after_ms=10000)

    def monitor_all_clients(self):
        """Identifica todos os TrackIDs de cliente e inicia o monitoramento, limitando a concorrência."""
        
        if not self.controller.dados_completos:
            logging.info("Dados completos vazios. Não é possível monitorar clientes, reagendando.")
            self.schedule_client_monitoring()
            return
            
        # 1. Identificar TrackIDs Únicos
        unique_track_ids = {item.get("TrackID") for item in self.controller.dados_completos if item.get("TrackID") is not None}

        # 2. Inicializar status dos novos TrackIDs e Limpar obsoletos
        for track_id in unique_track_ids:
            if track_id not in self.client_status:
                 self.client_status[track_id] = {'status': 'AGUARDANDO', 'timestamp': 'N/A', 'message': ''}
        
        obsolete_ids = list(set(self.client_status.keys()) - unique_track_ids)
        for track_id in obsolete_ids:
             if track_id in self.client_status:
                 del self.client_status[track_id]
        
        logging.info(f"Iniciando monitoramento assíncrono para {len(unique_track_ids)} clientes (TrackIDs) com limite de {self.MAX_MONITORING_THREADS} threads.")
        self.after(0, lambda: self.update_status(f"Ciclo de monitoramento de {len(unique_track_ids)} clientes (TrackIDs) iniciado.", clear_after_ms=3000))

        self._last_monitoring_start = datetime.now().timestamp() * 1000 # Salva o início para o timer

        # 3. Executar o monitoramento usando ThreadPoolExecutor para limitar concorrência
        def run_tasks():
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.MAX_MONITORING_THREADS) as executor:
                executor.map(self.monitor_client_task, unique_track_ids)
            self.schedule_client_monitoring()
            
        threading.Thread(target=run_tasks, daemon=True).start()

    def schedule_client_monitoring(self):
        if self._monitoring_job_id: self.after_cancel(self._monitoring_job_id)
        logging.info(f"A agendar próximo monitoramento de clientes em {self.monitoring_interval_ms // 60000} minutos.")
        self._monitoring_job_id = self.after(self.monitoring_interval_ms, self.monitor_all_clients)
        
    # --- Fim Funções de Monitoramento ---

    def _handle_date_validation(self):
        # Método auxiliar para a ConsultaScreen
        screen = self.frames["Consultas"]
        # Implementação de validação...
        data_inicio_str = screen.entry_data_inicio.get()
        data_fim_str = screen.entry_data_fim.get()
        cores = TEMAS[self.tema_atual]
        is_valid = True
        
        if data_inicio_str and not is_valid_ui_date(data_inicio_str):
            screen.entry_data_inicio.configure(border_color=cores["error_color"], border_width=2)
            self.update_status("ERRO: Formato de data inválido (Use AAAA-MM-DD).", clear_after_ms=5000)
            is_valid = False
        else:
            self._reset_date_border(screen.entry_data_inicio)
        
        if data_fim_str and not is_valid_ui_date(data_fim_str):
            screen.entry_data_fim.configure(border_color=cores["error_color"], border_width=2)
            if is_valid: self.update_status("ERRO: Formato de data inválido (Use AAAA-MM-DD).", clear_after_ms=5000)
            is_valid = False
        else:
            self._reset_date_border(screen.entry_data_fim)
            
        return is_valid

    def _reset_date_border(self, entry_widget):
        cores = TEMAS[self.tema_atual]
        entry_widget.configure(border_color=cores["placeholder"], border_width=1)

    # ... (Resto dos métodos auxiliares mantidos)
    def gerir_estado_widgets(self, habilitar):
        estado = "normal" if habilitar else "disabled"
        # Garante que todos os widgets interativos sejam gerenciados
        for widget in self.all_interactive_widgets:
            widget.configure(state=estado)
            
    def on_closing(self):
        self.app_state["theme"] = self.tema_atual
        self.app_state["geometry"] = self.geometry()
        self.app_state["colunas_visiveis"] = self.colunas_visiveis 
        self.app_state["coluna_ordenacao"] = self.controller.coluna_ordenacao
        self.app_state["ordem_desc"] = self.controller.ordem_desc
        self.app_state["pagina_atual"] = self.pagina_atual
        
        # Cancela o agendamento de monitoramento ao fechar
        if self._monitoring_job_id:
             self.after_cancel(self._monitoring_job_id)
             
        save_state(self.app_state)
        logging.info("Aplicação a encerrar.")
        self.destroy()

    def update_status(self, message, clear_after_ms=0):
        self.status_label.configure(text=message)
        
        if self._status_clear_id:
            self.after_cancel(self._status_clear_id)
            self._status_clear_id = None
        
        if clear_after_ms > 0:
            def clear():
                self.status_label.configure(text="")
                self._status_clear_id = None

            self._status_clear_id = self.after(clear_after_ms, clear)

    def schedule_auto_refresh(self):
        if AUTO_REFRESH_MINUTES > 0:
            logging.info(f"A agendar próxima atualização automática em {AUTO_REFRESH_MINUTES} minutos.")
            self.after(AUTO_REFRESH_MINUTES * 60 * 1000, self.auto_refresh_data)

    def auto_refresh_data(self):
        logging.info("A iniciar atualização automática de dados...")
        self.update_status("A atualizar dados em segundo plano...")
        threading.Thread(target=self.carregar_dados_iniciais_com_cache, args=(True,), daemon=True).start()
        self.schedule_auto_refresh()
        
    def alternar_tema(self):
        self.tema_atual = "light_green" if self.tema_atual == "dark_green" else "dark_green"
        self.aplicar_tema_completo()

    def aplicar_tema_completo(self):
        cores = TEMAS[self.tema_atual]
        self.configure(fg_color=cores["bg"])
        self.status_bar.configure(fg_color=cores["alt_bg"])
        self.status_label.configure(text_color=cores["fg"])
        self.last_updated_label.configure(text_color=cores["fg"])
        self.menu_frame.configure(fg_color=cores["alt_bg"]) 
        
        # Aplica tema aos botões de navegação
        for name, btn in self.navigation_buttons.items():
             btn.configure(fg_color=cores["button_bg"], hover_color=cores["button_hover"], text_color=cores["fg"])
        
        self.btn_alternar_tema.configure(fg_color=cores["button_bg"], hover_color=cores["button_hover"], text_color=cores["fg"])
        
        # Aplica tema às telas (que possuem o método .aplicar_tema ou usam o mestre)
        if "Consultas" in self.frames and hasattr(self.frames["Consultas"], 'aplicar_tema'):
            self.frames["Consultas"].aplicar_tema(cores)