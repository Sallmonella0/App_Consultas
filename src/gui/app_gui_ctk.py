# src/gui/app_gui_ctk.py
import customtkinter as ctk
from tkinter import messagebox
from tkinter import ttk # Necessário para a Tabela
import threading
import logging
from datetime import datetime, timedelta 
import math
from queue import Queue

# --- NOVAS IMPORTAÇÕES ---
from src.core.data_controller import DataController # Importa o Controller
from src.core.exceptions import ConsultaAPIException, APIAuthError # Importa exceções
# -------------------------

from src.gui.tabela import Tabela 

from src.utils.exportar import Exportar
from src.utils.config import COLUNAS
from src.utils.settings_manager import AUTO_REFRESH_MINUTES, ITENS_POR_PAGINA 
from src.utils.state_manager import load_state, save_state
from src.utils.datetime_utils import is_valid_ui_date, parse_api_datetime_to_date 

TEMAS = {
    "dark_green": { "bg": "#111111", "alt_bg": "#1C1C1C", "fg": "#D0F0C0", "selected_bg": "#66FF66", "selected_fg": "#111111", "button_bg": "#33CC33", "button_hover": "#22AA22", "entry_bg": "#222222", "placeholder": "#88CC88", "error_color": "#FF6666" },
    "light_green": { "bg": "#D3D3D3", "alt_bg": "#FFFAFA", "fg": "#111111", "selected_bg": "#80EF80", "selected_fg": "#000000", "button_bg": "#80EF80", "button_hover": "#80EF80", "entry_bg": "#FFFAFA", "placeholder": "#80EF80", "error_color": "#CC3333" }
}

# NOVO: Janela de Configuração de Colunas
class ColumnSettingsWindow(ctk.CTkToplevel):
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

        # Cria Checkboxes para cada coluna
        for i, col in enumerate(self.all_columns):
            var = ctk.BooleanVar(value=(col in current_visible_columns))
            chk = ctk.CTkCheckBox(frame, text=col, variable=var)
            chk.pack(anchor="w", pady=2)
            self.checkbox_vars[col] = var
        
        # Frame para os botões
        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=10, pady=(0, 10))
        
        btn_aplicar = ctk.CTkButton(frame_botoes, text="Aplicar", command=self._aplicar_configuracao)
        btn_aplicar.pack(side="right", padx=5)
        
        btn_cancelar = ctk.CTkButton(frame_botoes, text="Cancelar", command=self.destroy)
        btn_cancelar.pack(side="right", padx=5)

    def _aplicar_configuracao(self):
        """Coleta as colunas selecionadas e chama o callback."""
        selected_columns = [col for col, var in self.checkbox_vars.items() if var.get()]
        
        if not selected_columns:
            messagebox.showerror("Erro", "Pelo menos uma coluna deve ser selecionada.")
            return

        self.apply_callback(selected_columns)
        self.destroy()
        
    def destroy(self):
        self.grab_release()
        super().destroy()
# FIM: ColumnSettingsWindow

class AppGUI(ctk.CTk):
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
        
        # NOVO: Carrega as colunas visíveis do estado
        self.colunas_visiveis = self.app_state.get("colunas_visiveis", COLUNAS)
        
        # Instancia o DataController
        self.controller = DataController(COLUNAS, ITENS_POR_PAGINA) 
        
        # --- Controlo de Threads de Filtragem ---
        self.render_queue = Queue()
        self.current_render_thread = None

        # --- Configuração da Janela Principal ---
        self.title("App de Consulta Avançada")
        self.geometry(self.app_state.get("geometry", "1300x700"))
        self.minsize(1000, 550)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- Widgets e Inicialização ---
        self._criar_widgets()
        self.aplicar_tema_completo()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.gerir_estado_widgets(False)
        
        # Configura o estado inicial do controller (com base no estado persistente)
        self.controller.coluna_ordenacao = self.app_state.get("coluna_ordenacao", "DATAHORA")
        self.controller.ordem_desc = self.app_state.get("ordem_desc", True)
        self.pagina_atual = self.app_state.get("pagina_atual", 1)
        
        threading.Thread(target=self.carregar_dados_iniciais_com_cache, daemon=True).start()
        self.schedule_auto_refresh()
        
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)
        
        self.processar_fila_renderizacao()

    def _criar_widgets(self):
        # --- Frame Superior (Consulta ID) ---
        self.frame_top = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_top.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        self.label_id = ctk.CTkLabel(self.frame_top, text="IDMENSAGEM:")
        self.label_id.pack(side="left", padx=(0, 5))
        self.entry_id = ctk.CTkEntry(self.frame_top, width=150)
        self.entry_id.pack(side="left")
        self.entry_id.bind("<Return>", lambda e: self.consultar_api_async())
        
        self.btn_consultar = ctk.CTkButton(self.frame_top, text="Consultar", width=100, command=lambda: self.consultar_api_async())
        self.btn_consultar.pack(side="left", padx=5)

        # ADICIONADO: Botão de Refresh
        self.btn_refresh = ctk.CTkButton(self.frame_top, text="Refresh", width=100, command=self.refresh_data_async)
        self.btn_refresh.pack(side="left", padx=5)

        # ADICIONADO: Botão de Configuração de Colunas
        self.btn_config_colunas = ctk.CTkButton(self.frame_top, text="Colunas", width=100, command=self.abrir_configuracao_colunas)
        self.btn_config_colunas.pack(side="left", padx=15)
        # FIM ADIÇÕES
        
        self.btn_alternar_tema = ctk.CTkButton(self.frame_top, text="Alternar Tema", command=self.alternar_tema)
        self.btn_alternar_tema.pack(side="right", padx=5)
        
        # --- Frame de Filtros (Meio) ---
        self.frame_filtros = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_filtros.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        self.label_filtro = ctk.CTkLabel(self.frame_filtros, text="Filtrar:")
        self.label_filtro.pack(side="left", padx=(0, 5))
        self.entry_filtro = ctk.CTkEntry(self.frame_filtros, placeholder_text="Digite para filtrar...")
        self.entry_filtro.pack(side="left", padx=5, expand=True, fill="x")
        self.entry_filtro.bind("<KeyRelease>", self.aplicar_filtro_debounce)
        
        self.combo_coluna = ctk.CTkComboBox(self.frame_filtros, values=["TODAS"] + COLUNAS, width=150)
        self.combo_coluna.set("PLACA")
        self.combo_coluna.pack(side="left")
        
        self.btn_limpar_filtro = ctk.CTkButton(self.frame_filtros, text="Limpar", width=80, command=self.limpar_filtro)
        self.btn_limpar_filtro.pack(side="left", padx=5)
        
        self.label_data_inicio = ctk.CTkLabel(self.frame_filtros, text="De:")
        self.label_data_inicio.pack(side="left", padx=(10, 5))
        
        self.entry_data_inicio = ctk.CTkEntry(self.frame_filtros, placeholder_text="AAAA-MM-DD", width=120)
        self.entry_data_inicio.pack(side="left")
        self.entry_data_inicio.bind("<KeyRelease>", self.aplicar_filtro_debounce)
        self.entry_data_inicio.bind("<FocusIn>", lambda e: self._reset_date_border(self.entry_data_inicio))

        self.label_data_fim = ctk.CTkLabel(self.frame_filtros, text="Até:")
        self.label_data_fim.pack(side="left", padx=(10, 5))
        
        self.entry_data_fim = ctk.CTkEntry(self.frame_filtros, placeholder_text="AAAA-MM-DD", width=120)
        self.entry_data_fim.pack(side="left")
        self.entry_data_fim.bind("<KeyRelease>", self.aplicar_filtro_debounce)
        self.entry_data_fim.bind("<FocusIn>", lambda e: self._reset_date_border(self.entry_data_fim))

        # --- Frame da Tabela (Principal) ---
        self.frame_table = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_table.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        self.frame_table.grid_rowconfigure(0, weight=1)
        self.frame_table.grid_columnconfigure(0, weight=1)
        
        # ALTERAÇÃO: Tabela recebe COLUNAS (completas) e self.colunas_visiveis (estado inicial)
        self.tabela = Tabela(self, COLUNAS, self.colunas_visiveis, on_sort_command=self.ordenar_por_coluna)
        self.tabela.grid(in_=self.frame_table, row=0, column=0, sticky="nsew")

        # --- Frame Inferior (Paginação e Exportação) ---
        self.frame_bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_bottom.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 0))
        
        self.frame_paginacao = ctk.CTkFrame(self.frame_bottom, fg_color="transparent")
        self.frame_paginacao.pack(side="left", expand=True, fill="x")

        self.btn_primeira = ctk.CTkButton(self.frame_paginacao, text="<< Primeira", width=100, command=self.primeira_pagina)
        self.btn_primeira.pack(side="left", padx=(0, 5))

        self.btn_anterior = ctk.CTkButton(self.frame_paginacao, text="< Anterior", width=100, command=self.pagina_anterior)
        self.btn_anterior.pack(side="left", padx=5)
        self.label_pagina = ctk.CTkLabel(self.frame_paginacao, text="Página 1 / 1")
        self.label_pagina.pack(side="left", padx=10)
        self.btn_proximo = ctk.CTkButton(self.frame_paginacao, text="Próximo >", width=100, command=self.proxima_pagina)
        self.btn_proximo.pack(side="left", padx=5)

        self.btn_ultima = ctk.CTkButton(self.frame_paginacao, text="Última >>", width=100, command=self.ultima_pagina)
        self.btn_ultima.pack(side="left", padx=5)

        self.exportar = Exportar(self, COLUNAS)
        self.btn_excel = ctk.CTkButton(self.frame_bottom, text="Salvar Excel", command=self.exportar_excel)
        self.btn_excel.pack(side="right", padx=5)
        self.btn_csv = ctk.CTkButton(self.frame_bottom, text="Salvar CSV", command=self.exportar_csv)
        self.btn_csv.pack(side="right")
        
        self.status_bar = ctk.CTkFrame(self, height=25)
        self.status_bar.grid(row=4, column=0, sticky="ew", padx=10, pady=(5, 10))
        self.status_label = ctk.CTkLabel(self.status_bar, text="Bem-vindo!", anchor="w")
        self.status_label.pack(side="left", padx=10)
        self.last_updated_label = ctk.CTkLabel(self.status_bar, text="", anchor="e")
        self.last_updated_label.pack(side="right", padx=10)
        
        self.widgets_interativos = [
            self.entry_filtro, self.combo_coluna, self.btn_limpar_filtro,
            self.entry_data_inicio, self.entry_data_fim,
            self.btn_primeira, self.btn_anterior, self.btn_proximo, self.btn_ultima, 
            self.btn_excel, self.btn_csv,
            self.btn_refresh,
            self.btn_config_colunas # ADICIONADO
        ]
    
    # --- Funções de Configuração de Colunas ---

    def abrir_configuracao_colunas(self):
        """Abre a janela modal para o utilizador configurar as colunas visíveis."""
        ColumnSettingsWindow(self, COLUNAS, self.colunas_visiveis, self.aplicar_novas_colunas)

    def aplicar_novas_colunas(self, novas_colunas_visiveis):
        """Callback para atualizar as colunas visíveis após a janela de configuração."""
        self.colunas_visiveis = novas_colunas_visiveis
        
        # 1. Reconstroi a Treeview com as novas colunas
        self.tabela.reconstruir_colunas(self.colunas_visiveis, self.ordenar_por_coluna)
        
        # 2. Re-renderiza os dados para garantir que a ordenação e paginação se adaptam
        self.renderizar_dados()
        
        self.update_status(f"Colunas atualizadas. Visíveis: {len(novas_colunas_visiveis)}/{len(COLUNAS)}.")
    
    # --- Funções de Tela Cheia, _handle_date_validation, _reset_date_border (mantidas) ---
    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
        return "break"

    def exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.attributes("-fullscreen", False)
            return "break"

    def _handle_date_validation(self):
        """Valida o formato das datas inseridas e fornece feedback visual."""
        data_inicio_str = self.entry_data_inicio.get()
        data_fim_str = self.entry_data_fim.get()
        cores = TEMAS[self.tema_atual]
        is_valid = True
        
        # 1. Validação de Data Início
        if data_inicio_str and not is_valid_ui_date(data_inicio_str):
            self.entry_data_inicio.configure(border_color=cores["error_color"], border_width=2)
            self.update_status("ERRO: Formato de data inválido (Use AAAA-MM-DD).", clear_after_ms=5000)
            is_valid = False
        else:
            self._reset_date_border(self.entry_data_inicio)
        
        # 2. Validação de Data Fim
        if data_fim_str and not is_valid_ui_date(data_fim_str):
            self.entry_data_fim.configure(border_color=cores["error_color"], border_width=2)
            if is_valid: 
                self.update_status("ERRO: Formato de data inválido (Use AAAA-MM-DD).", clear_after_ms=5000)
            is_valid = False
        else:
            self._reset_date_border(self.entry_data_fim)
            
        return is_valid
        
    def _reset_date_border(self, entry_widget):
        """Reseta a cor da borda de um widget de entrada de data."""
        cores = TEMAS[self.tema_atual]
        entry_widget.configure(border_color=cores["button_hover"], border_width=1)

    # --- Funções de Renderização e Filtro/Paginação (Delegadas ao Controller) ---
    def processar_fila_renderizacao(self):
        try:
            # Obtém os dados processados e a página atual do Controller
            data_page_num, dados_da_pagina = self.render_queue.get_nowait()
            
            self.pagina_atual = data_page_num
            total_registos = self.controller.total_registos 
            
            self.tabela.atualizar_tabela(dados_da_pagina)
            self.atualizar_label_pagina()
            self.update_status(f"{total_registos} registos encontrados.")
            # Atualiza o indicador de ordenação com base no estado do Controller
            self.tabela.atualizar_indicador_ordenacao(self.controller.coluna_ordenacao, self.controller.ordem_desc)
            self.configure(cursor="")
        except Exception:
            pass
        finally:
            self.after(100, self.processar_fila_renderizacao)

    def renderizar_dados_thread(self, thread_id):
        if thread_id != self.current_render_thread:
            return

        try:
            # 1. Aplica o filtro e ordenação no Controller
            self.controller.aplicar_filtro()
            
            # 2. Obtém os dados da página atual (já ordenados e filtrados)
            page_num, dados_da_pagina = self.controller.get_dados_pagina(self.pagina_atual)
            
            if thread_id == self.current_render_thread:
                self.render_queue.put((page_num, dados_da_pagina))
                
        except Exception as e:
            logging.error(f"Erro na thread de renderização: {e}")
            self.after(0, lambda: self.update_status("ERRO: Falha ao processar os dados.", clear_after_ms=5000))
            self.after(0, lambda: self.configure(cursor=""))

    def renderizar_dados(self):
        self.configure(cursor="watch")
        
        thread_id = threading.get_ident()
        self.current_render_thread = thread_id

        args = (thread_id,)
        
        threading.Thread(target=self.renderizar_dados_thread, args=args, daemon=True).start()

    def aplicar_filtro_debounce(self, event=None):
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
            
        if not self._handle_date_validation():
            return

        self._debounce_id = self.after(300, self.aplicar_filtro)

    def aplicar_filtro(self):
        
        # 1. Define os novos parâmetros de filtro no Controller
        try:
            self.controller.set_filtro_texto(self.entry_filtro.get(), self.combo_coluna.get())
            self.controller.set_filtro_data(self.entry_data_inicio.get(), self.entry_data_fim.get())
        except ValueError:
            return 

        # 2. Reseta a página e aciona a renderização
        self.pagina_atual = 1
        self.renderizar_dados()

    def limpar_filtro(self):
        self.entry_filtro.delete(0, 'end')
        self.entry_data_inicio.delete(0, 'end')
        self.entry_data_fim.delete(0, 'end')
        self._reset_date_border(self.entry_data_inicio)
        self._reset_date_border(self.entry_data_fim)
        self.aplicar_filtro()
        
    def ordenar_por_coluna(self, coluna):
        # Delega a lógica de ordenação ao Controller
        self.controller.ordenar(coluna)
        # Reseta para a primeira página após a ordenação
        self.pagina_atual = 1 
        self.renderizar_dados()

    def ir_para_pagina(self, numero_pagina):
        
        page_num, dados_da_pagina = self.controller.get_dados_pagina(numero_pagina)
        
        self.pagina_atual = page_num
        
        self.tabela.atualizar_tabela(dados_da_pagina)
        self.atualizar_label_pagina()
    
    def primeira_pagina(self):
        self.ir_para_pagina(1)

    def ultima_pagina(self):
        self.ir_para_pagina(self.controller.total_paginas)

    def pagina_anterior(self):
        self.ir_para_pagina(self.pagina_atual - 1)

    def proxima_pagina(self):
        self.ir_para_pagina(self.pagina_atual + 1)
        
    def atualizar_label_pagina(self):
        total_registos = self.controller.total_registos
        total_paginas = self.controller.total_paginas
        self.label_pagina.configure(text=f"Página {self.pagina_atual} / {total_paginas} (Total: {total_registos})")

    # --- Funções de Carga de Dados e API ---
    def carregar_dados_iniciais_com_cache(self, is_auto_refresh=False):
        try:
            if not is_auto_refresh:
                self.after(0, lambda: self.update_status("A carregar dados do cache..."))
                self.after(0, lambda: self.tabela.mostrar_mensagem("A carregar..."))
                
                # Carrega no controller
                dados_iniciais = self.api.buscar_todos(force_refresh=False)
                if dados_iniciais:
                    self.controller.dados_completos = dados_iniciais
                    self.after(0, self.renderizar_dados)
                    self.after(0, lambda: self.update_status(f"{len(dados_iniciais)} registos carregados do cache."))
                else:
                    self.after(0, lambda: self.update_status("Cache vazio. A buscar dados da API..."))
            
            dados_frescos = self.api.buscar_todos(force_refresh=True)
            
            if dados_frescos and dados_frescos != self.controller.dados_completos:
                logging.info("Dados atualizados encontrados. A atualizar a interface.")
                self.controller.dados_completos = dados_frescos
                self.after(0, self.renderizar_dados)
                self.after(0, lambda: self.update_status(f"Dados atualizados. Total de {len(dados_frescos)} registos."))
            elif is_auto_refresh:
                 self.after(0, lambda: self.update_status("Nenhum dado novo encontrado."))
                 
            now = datetime.now().strftime("%H:%M:%S")
            self.last_updated_label.configure(text=f"Última verificação: {now}")

        except ConsultaAPIException as e: # Captura exceções customizadas
            logging.error(f"Falha ao carregar dados: {e}")
            self.after(0, lambda err=e: self.update_status(f"ERRO API: {e}", clear_after_ms=5000))
        except Exception as e:
            logging.error(f"Falha inesperada ao carregar dados: {e}")
            self.after(0, lambda err=e: self.update_status(f"ERRO INESPERADO: {e}", clear_after_ms=5000))
        finally:
            if not is_auto_refresh:
                self.after(0, lambda: self.gerir_estado_widgets(True))

    def consultar_api_async(self):
        threading.Thread(target=self.consultar_api, daemon=True).start()

    # ADICIONADO: Função assíncrona para o botão Refresh
    def refresh_data_async(self):
        """Inicia o carregamento e atualização de dados forçada da API."""
        self.gerir_estado_widgets(False) 
        self.update_status("A forçar atualização de dados da API...")
        threading.Thread(target=self.carregar_dados_iniciais_com_cache, daemon=True).start()
    # FIM ADIÇÃO

    def consultar_api(self):
        id_msg = self.entry_id.get().strip()
        
        if not id_msg or not id_msg.isdigit():
            self.after(0, lambda: messagebox.showwarning("Atenção", "IDMENSAGEM deve ser um número inteiro e não pode estar vazio!"))
            return
            
        self.after(0, lambda: self.btn_consultar.configure(state="disabled", text="Buscando..."))
        self.update_status(f"A buscar IDMENSAGEM {id_msg}...")
        try:
            # Garante que a entrada é tratada como número antes de enviar à API
            dados = self.api.consultar(id_msg)
            
            self.controller.dados_completos = dados 
            
            self.after(0, self.renderizar_dados)
            
            if not dados:
                 self.after(0, lambda: self.update_status(f"ID {id_msg} consultado. Nenhum registo encontrado.", clear_after_ms=5000))
            else:
                 self.after(0, lambda: self.update_status(f"{len(dados)} registos encontrados para o ID {id_msg}.", clear_after_ms=5000))
                 
        except ConsultaAPIException as e: # Captura exceções customizadas
            self.after(0, lambda err=e: messagebox.showerror("Erro de API", f"Falha na consulta:\n{err}"))
            self.after(0, lambda: self.update_status(f"Erro na consulta do ID {id_msg}.", clear_after_ms=5000))
        except Exception as e:
            logging.error(f"Falha inesperada na consulta: {e}")
            self.after(0, lambda err=e: messagebox.showerror("Erro Inesperado", f"Falha na consulta:\n{e}"))
            self.after(0, lambda: self.update_status(f"Erro inesperado na consulta do ID {id_msg}.", clear_after_ms=5000))
        finally:
            self.after(0, lambda: self.btn_consultar.configure(state="normal", text="Consultar"))
    
    def gerir_estado_widgets(self, habilitar):
        estado = "normal" if habilitar else "disabled"
        for widget in self.widgets_interativos:
            widget.configure(state=estado)
            
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
        dados_para_exportar = self._get_dados_para_exportar()
        self.exportar.salvar_excel_async(dados_para_exportar, callback=lambda: self.gerir_estado_exportacao(exportando=False))

    def exportar_csv(self):
        self.gerir_estado_exportacao(exportando=True)
        dados_para_exportar = self._get_dados_para_exportar()
        self.exportar.salvar_csv_async(dados_para_exportar, callback=lambda: self.gerir_estado_exportacao(exportando=False))
        
    def _get_dados_para_exportar(self):
        dados_selecionados = self.tabela.get_itens_selecionados()
        # Delega ao Controller quais dados exportar (filtrados ou selecionados)
        dados = self.controller.get_dados_para_exportar(dados_selecionados) 
        
        if dados_selecionados:
            self.update_status(f"A exportar {len(dados)} linhas selecionadas...")
        else:
            self.update_status(f"A exportar {len(dados)} linhas (dados filtrados)...")
        return dados

    def on_closing(self):
        self.app_state["theme"] = self.tema_atual
        self.app_state["geometry"] = self.geometry()
        # NOVO: Salva a lista de colunas visíveis
        self.app_state["colunas_visiveis"] = self.colunas_visiveis 
        # Salva o estado de ordenação e paginação do Controller
        self.app_state["coluna_ordenacao"] = self.controller.coluna_ordenacao
        self.app_state["ordem_desc"] = self.controller.ordem_desc
        self.app_state["pagina_atual"] = self.pagina_atual
        save_state(self.app_state)
        logging.info("Aplicação a encerrar.")
        self.destroy()

    # CORREÇÃO: Implementação de gerenciamento de status concorrente
    def update_status(self, message, clear_after_ms=0):
        self.status_label.configure(text=message)
        
        # 1. Cancela a limpeza agendada anteriormente
        if self._status_clear_id:
            self.after_cancel(self._status_clear_id)
            self._status_clear_id = None
        
        if clear_after_ms > 0:
            # Função interna para limpar o status
            def clear():
                self.status_label.configure(text="")
                self._status_clear_id = None

            # 2. Agenda a nova limpeza e salva o ID
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
        self.status_bar.configure(fg_color=cores["button_bg"])
        self.status_label.configure(text_color=cores["selected_fg"])
        self.last_updated_label.configure(text_color=cores["selected_fg"])
        
        botoes = [
            self.btn_consultar, self.btn_csv, self.btn_excel, self.btn_alternar_tema, 
            self.btn_primeira, self.btn_anterior, self.btn_proximo, self.btn_ultima, 
            self.btn_limpar_filtro,
            self.btn_refresh,
            self.btn_config_colunas # ADICIONADO
        ]
        entries = [self.entry_id, self.entry_filtro, self.entry_data_inicio, self.entry_data_fim]
        labels = [self.label_id, self.label_filtro, self.label_pagina, self.label_data_inicio, self.label_data_fim]
        combos = [self.combo_coluna]
        
        for btn in botoes:
            btn.configure(fg_color=cores["button_bg"], hover_color=cores["button_hover"], text_color=cores["selected_fg"])
        for entry in entries:
            entry.configure(fg_color=cores["entry_bg"], text_color=cores["fg"], border_color=cores["button_hover"], border_width=1, placeholder_text_color=cores["placeholder"])
        for lbl in labels:
            lbl.configure(text_color=cores["fg"])
        for combo in combos:
             combo.configure(fg_color=cores["entry_bg"], text_color=cores["fg"], border_color=cores["button_hover"],
                             button_color=cores["button_bg"], button_hover_color=cores["button_hover"],
                             dropdown_fg_color=cores["alt_bg"], dropdown_hover_color=cores["button_hover"])
        self.tabela.atualizar_cores(cores)