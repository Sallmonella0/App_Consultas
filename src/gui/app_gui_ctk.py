# src/gui/app_gui_ctk.py
import customtkinter as ctk
from tkinter import messagebox
import threading
import logging
from datetime import datetime
import math
from queue import Queue

from src.gui.tabela import Tabela, chave_de_ordenacao_segura
from src.utils.exportar import Exportar
from src.utils.config import COLUNAS
from src.utils.settings_manager import AUTO_REFRESH_MINUTES, ITENS_POR_PAGINA
from src.utils.state_manager import load_state, save_state
from src.utils.datetime_utils import is_valid_ui_date, parse_api_datetime_to_date 

TEMAS = {
    "dark_green": { "bg": "#111111", "alt_bg": "#1C1C1C", "fg": "#D0F0C0", "selected_bg": "#66FF66", "selected_fg": "#111111", "button_bg": "#33CC33", "button_hover": "#22AA22", "entry_bg": "#222222", "placeholder": "#88CC88", "error_color": "#FF6666" },
    "light_green": { "bg": "#D3D3D3", "alt_bg": "#FFFAFA", "fg": "#111111", "selected_bg": "#80EF80", "selected_fg": "#000000", "button_bg": "#80EF80", "button_hover": "#80EF80", "entry_bg": "#FFFAFA", "placeholder": "#80EF80", "error_color": "#CC3333" }
}

class AppGUI(ctk.CTk):
    def __init__(self, api):
        super().__init__()
        self.api = api
        
        # --- Gestão de Estado ---
        self.app_state = load_state()
        self.tema_atual = self.app_state.get("theme", "dark_green")
        self._debounce_id = None
        self.dados_completos = []
        self.dados_exibidos = []
        self.pagina_atual = 1
        self.coluna_ordenacao = "DATAHORA"
        self.ordem_desc = True
        self.is_fullscreen = False
        
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
        
        # CORREÇÃO: Envolver o comando em lambda para resolver AttributeError
        self.btn_consultar = ctk.CTkButton(self.frame_top, text="Consultar", width=100, command=lambda: self.consultar_api_async())
        self.btn_consultar.pack(side="left", padx=5)

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
        self.tabela = Tabela(self, COLUNAS)
        self.tabela.grid(in_=self.frame_table, row=0, column=0, sticky="nsew")

        # --- Frame Inferior (Paginação e Exportação) ---
        self.frame_bottom = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_bottom.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 0))
        
        self.frame_paginacao = ctk.CTkFrame(self.frame_bottom, fg_color="transparent")
        self.frame_paginacao.pack(side="left", expand=True, fill="x")

        # Botão para ir para a primeira página
        self.btn_primeira = ctk.CTkButton(self.frame_paginacao, text="<< Primeira", width=100, command=self.primeira_pagina)
        self.btn_primeira.pack(side="left", padx=(0, 5))

        self.btn_anterior = ctk.CTkButton(self.frame_paginacao, text="< Anterior", width=100, command=self.pagina_anterior)
        self.btn_anterior.pack(side="left", padx=5)
        self.label_pagina = ctk.CTkLabel(self.frame_paginacao, text="Página 1 / 1")
        self.label_pagina.pack(side="left", padx=10)
        self.btn_proximo = ctk.CTkButton(self.frame_paginacao, text="Próximo >", width=100, command=self.proxima_pagina)
        self.btn_proximo.pack(side="left", padx=5)

        # Botão para ir para a última página
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
            self.btn_excel, self.btn_csv
        ]
    
    # --- Funções de Tela Cheia ---
    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
        return "break"

    def exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.attributes("-fullscreen", False)
            return "break"

    # --- Lógica de Dados e UI (Otimizada) ---
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
            if is_valid: # Apenas atualiza o status se não houver outro erro de data
                self.update_status("ERRO: Formato de data inválido (Use AAAA-MM-DD).", clear_after_ms=5000)
            is_valid = False
        else:
            self._reset_date_border(self.entry_data_fim)
            
        return is_valid
        
    def _reset_date_border(self, entry_widget):
        """Reseta a cor da borda de um widget de entrada de data."""
        cores = TEMAS[self.tema_atual]
        # Restaura a cor de borda padrão e a largura
        entry_widget.configure(border_color=cores["button_hover"], border_width=1)

    def processar_fila_renderizacao(self):
        try:
            dados_processados = self.render_queue.get_nowait()
            self.dados_exibidos = dados_processados
            
            self.ir_para_pagina(self.pagina_atual)
            self.update_status(f"{len(self.dados_exibidos)} registos encontrados.")
            self.configure(cursor="")
        except Exception:
            pass
        finally:
            self.after(100, self.processar_fila_renderizacao)

    def renderizar_dados_thread(self, termo, coluna, data_inicio_str, data_fim_str, coluna_ord, ordem_desc, thread_id):
        if thread_id != self.current_render_thread:
            return

        dados_filtrados = self.dados_completos
        
        if termo:
            if coluna == "TODAS":
                dados_filtrados = [
                    item for item in dados_filtrados 
                    if termo in ' '.join(map(str, item.values())).lower()
                ]
            else:
                dados_filtrados = [item for item in dados_filtrados if termo in str(item.get(coluna, "")).lower()]
        
        # --- CORREÇÃO: Uso de utilitário de data e validação simplificada ---
        data_filter_error = False
        
        try:
            # Converte as strings da UI para objetos date, se existirem e forem válidas
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date() if data_inicio_str else None
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date() if data_fim_str else None
            
            if data_inicio or data_fim:
                def filter_date(item):
                    # Usa a função utilitária para obter o objeto date
                    item_date = parse_api_datetime_to_date(item.get("DATAHORA"))
                    if not item_date:
                        return False # Ignora itens sem DATAHORA válida
                    
                    if data_inicio and item_date < data_inicio:
                        return False
                    if data_fim and item_date > data_fim:
                        return False
                    return True

                dados_filtrados = [item for item in dados_filtrados if filter_date(item)]
                
        except (ValueError, TypeError):
            # Deve ser apanhado pela pré-validação, mas mantido como fallback
            data_filter_error = True
            logging.warning(f"Formato de data inválido ('{data_inicio_str}' ou '{data_fim_str}'). Ignorando filtro de data.")
        # --- FIM DA CORREÇÃO ---

        if thread_id != self.current_render_thread:
            return

        dados_ordenados = sorted(dados_filtrados, key=lambda item: chave_de_ordenacao_segura(item, coluna_ord), reverse=ordem_desc)
        
        if thread_id == self.current_render_thread:
            self.render_queue.put(dados_ordenados)
            # Envia erro para a UI se houver falha na data
            if data_filter_error:
                self.after(0, lambda: self.update_status("ERRO: Formato de data inválido (Use AAAA-MM-DD).", clear_after_ms=5000))

    def renderizar_dados(self):
        self.configure(cursor="watch")
        self.tabela.atualizar_indicador_ordenacao(self.coluna_ordenacao, self.ordem_desc)
        
        thread_id = threading.get_ident()
        self.current_render_thread = thread_id

        args = (
            self.entry_filtro.get().lower(),
            self.combo_coluna.get(),
            self.entry_data_inicio.get(),
            self.entry_data_fim.get(),
            self.coluna_ordenacao,
            self.ordem_desc,
            thread_id
        )
        
        threading.Thread(target=self.renderizar_dados_thread, args=args, daemon=True).start()

    def aplicar_filtro_debounce(self, event=None):
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
            
        # NOVO: Se a validação de data falhar, impede a aplicação do filtro
        if not self._handle_date_validation():
            return

        self._debounce_id = self.after(300, self.aplicar_filtro)

    def aplicar_filtro(self):
        self.pagina_atual = 1
        self.renderizar_dados()

    def limpar_filtro(self):
        self.entry_filtro.delete(0, 'end')
        self.entry_data_inicio.delete(0, 'end')
        self.entry_data_fim.delete(0, 'end')
        # NOVO: Reseta o feedback visual
        self._reset_date_border(self.entry_data_inicio)
        self._reset_date_border(self.entry_data_fim)
        self.aplicar_filtro()
        
    def ordenar_por_coluna(self, coluna):
        if self.coluna_ordenacao == coluna:
            self.ordem_desc = not self.ordem_desc
        else:
            self.coluna_ordenacao = coluna
            self.ordem_desc = True
        self.renderizar_dados()

    def ir_para_pagina(self, numero_pagina):
        total_paginas = math.ceil(len(self.dados_exibidos) / ITENS_POR_PAGINA) if self.dados_exibidos else 1
        
        if numero_pagina < 1: numero_pagina = 1
        if numero_pagina > total_paginas: numero_pagina = total_paginas
        self.pagina_atual = numero_pagina
        
        inicio = (self.pagina_atual - 1) * ITENS_POR_PAGINA
        fim = inicio + ITENS_POR_PAGINA
        dados_da_pagina = self.dados_exibidos[inicio:fim]
        
        self.tabela.atualizar_tabela(dados_da_pagina)
        self.atualizar_label_pagina()
    
    # Funções de navegação para primeira/última página
    def primeira_pagina(self):
        self.ir_para_pagina(1)

    def ultima_pagina(self):
        total_paginas = math.ceil(len(self.dados_exibidos) / ITENS_POR_PAGINA) if self.dados_exibidos else 1
        self.ir_para_pagina(total_paginas)

    def pagina_anterior(self):
        self.ir_para_pagina(self.pagina_atual - 1)

    def proxima_pagina(self):
        self.ir_para_pagina(self.pagina_atual + 1)
        
    def atualizar_label_pagina(self):
        total_paginas = math.ceil(len(self.dados_exibidos) / ITENS_POR_PAGINA) if self.dados_exibidos else 1
        self.label_pagina.configure(text=f"Página {self.pagina_atual} / {max(1, total_paginas)}")

    def carregar_dados_iniciais_com_cache(self, is_auto_refresh=False):
        try:
            if not is_auto_refresh:
                self.after(0, lambda: self.update_status("A carregar dados do cache..."))
                self.after(0, lambda: self.tabela.mostrar_mensagem("A carregar..."))
                dados_iniciais = self.api.buscar_todos(force_refresh=False)
                if dados_iniciais:
                    self.dados_completos = dados_iniciais
                    self.after(0, self.renderizar_dados)
                    self.after(0, lambda: self.update_status(f"{len(dados_iniciais)} registos carregados do cache."))
                else:
                    self.after(0, lambda: self.update_status("Cache vazio. A buscar dados da API..."))
            
            dados_frescos = self.api.buscar_todos(force_refresh=True)
            if dados_frescos and dados_frescos != self.dados_completos:
                logging.info("Dados atualizados encontrados. A atualizar a interface.")
                self.dados_completos = dados_frescos
                self.after(0, self.renderizar_dados)
                self.after(0, lambda: self.update_status(f"Dados atualizados. Total de {len(dados_frescos)} registos."))
            elif is_auto_refresh:
                 self.after(0, lambda: self.update_status("Nenhum dado novo encontrado."))
                 
            now = datetime.now().strftime("%H:%M:%S")
            self.last_updated_label.configure(text=f"Última verificação: {now}")

        except Exception as e:
            logging.error(f"Falha ao carregar dados: {e}")
            self.after(0, lambda err=e: self.update_status(f"Erro ao carregar dados: {err}", clear_after_ms=5000))
        finally:
            if not is_auto_refresh:
                self.after(0, lambda: self.gerir_estado_widgets(True))

    def consultar_api_async(self):
        threading.Thread(target=self.consultar_api, daemon=True).start()

    def consultar_api(self):
        id_msg = self.entry_id.get().strip()
        
        # --- CORREÇÃO: Validação de ID mais robusta (checa se está vazio OU não é dígito) ---
        if not id_msg or not id_msg.isdigit():
            self.after(0, lambda: messagebox.showwarning("Atenção", "IDMENSAGEM deve ser um número inteiro e não pode estar vazio!"))
            return
            
        self.after(0, lambda: self.btn_consultar.configure(state="disabled", text="Buscando..."))
        self.update_status(f"A buscar IDMENSAGEM {id_msg}...")
        try:
            dados = self.api.consultar(id_msg)
            self.dados_completos = dados
            self.after(0, self.renderizar_dados)
            self.after(0, lambda: self.update_status(f"{len(dados)} registos encontrados para o ID {id_msg}.", clear_after_ms=5000))
        except Exception as e:
            self.after(0, lambda err=e: messagebox.showerror("Erro de API", f"Falha na consulta:\n{err}"))
            self.after(0, lambda: self.update_status(f"Erro na consulta do ID {id_msg}.", clear_after_ms=5000))
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
        if dados_selecionados:
            self.update_status(f"A exportar {len(dados_selecionados)} linhas selecionadas...")
            return dados_selecionados
        self.update_status(f"A exportar {len(self.dados_exibidos)} linhas...")
        return self.dados_exibidos

    def on_closing(self):
        self.app_state["theme"] = self.tema_atual
        self.app_state["geometry"] = self.geometry()
        save_state(self.app_state)
        logging.info("Aplicação a encerrar.")
        self.destroy()

    def update_status(self, message, clear_after_ms=0):
        self.status_label.configure(text=message)
        if clear_after_ms > 0:
            self.after(clear_after_ms, lambda: self.status_label.configure(text=""))

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
            self.btn_limpar_filtro
        ]
        entries = [self.entry_id, self.entry_filtro, self.entry_data_inicio, self.entry_data_fim]
        labels = [self.label_id, self.label_filtro, self.label_pagina, self.label_data_inicio, self.label_data_fim]
        combos = [self.combo_coluna]
        
        for btn in botoes:
            btn.configure(fg_color=cores["button_bg"], hover_color=cores["button_hover"], text_color=cores["selected_fg"])
        for entry in entries:
            # Configura cor de borda padrão para entries. _handle_date_validation altera a cor de erro.
            entry.configure(fg_color=cores["entry_bg"], text_color=cores["fg"], border_color=cores["button_hover"], border_width=1, placeholder_text_color=cores["placeholder"])
        for lbl in labels:
            lbl.configure(text_color=cores["fg"])
        for combo in combos:
             combo.configure(fg_color=cores["entry_bg"], text_color=cores["fg"], border_color=cores["button_hover"],
                             button_color=cores["button_bg"], button_hover_color=cores["button_hover"],
                             dropdown_fg_color=cores["alt_bg"], dropdown_hover_color=cores["button_hover"])
        self.tabela.atualizar_cores(cores)