# src/gui/app_gui_pyqt.py

import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QStackedWidget, QMessageBox,
    QScrollArea, QDialog, QCheckBox, QDialogButtonBox, QGridLayout, QGroupBox,
    QProgressBar, QMenu, QCalendarWidget, QDateEdit, QGraphicsDropShadowEffect,
    QTabWidget # Adicionado QTabWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QDate
from PyQt6.QtGui import QPalette, QColor, QFont, QKeySequence, QShortcut, QCursor, QAction
import threading
from datetime import datetime, timedelta

# Imports para o gráfico
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from src.core.api import ConsultaAPI
from src.core.data_controller import DataController
from src.core.exceptions import ConsultaAPIException
from src.utils.exportar import Exportar
from src.utils.config import COLUNAS
from src.utils.settings_manager import ITENS_POR_PAGINA
from src.utils.state_manager import load_state, save_state
from src.utils.datetime_utils import is_valid_ui_date, parse_api_datetime_to_date

# --- PALETAS DE CORES (sem alterações) ---
PALETTES = {
    "dark_green": {
        "bg": "#111111",
        "alt_bg": "#1C1C1C",
        "fg": "#D0F0C0",
        "primary": "#33CC33",
        "primary_dark": "#22AA22",
        "primary_light": "#66FF66",
        "selected_bg": "#33CC33",
        "selected_fg": "#111111",
        "entry_bg": "#222222",
        "border": "#333333",
        "text_main": "#E0E0E0",
        "text_dark": "#000000",
        "text_light": "#FFFFFF",
    },
    "light_green": {
        "bg": "#F0F0F0",
        "alt_bg": "#FFFFFF",
        "fg": "#111111",
        "primary": "#4CAF50",
        "primary_dark": "#388E3C",
        "primary_light": "#C8E6C9",
        "selected_bg": "#4CAF50",
        "selected_fg": "#FFFFFF",
        "entry_bg": "#FFFFFF",
        "border": "#B0BEC5",
        "text_main": "#1A1A1A",
        "text_dark": "#000000",
        "text_light": "#FFFFFF",
    }
}

# --- FUNÇÃO GERADORA DE TEMAS (sem alterações) ---
def generate_theme_qss(p):
    """Gera uma string QSS a partir de uma paleta de cores."""
    return f"""
        QWidget {{
            background-color: {p["bg"]};
            color: {p["text_main"]};
            font-size: 15px;
            border: none;
        }}
        QMainWindow, QDialog {{
            background-color: {p["bg"]};
        }}
        QGroupBox {{
            background-color: {p["alt_bg"]};
            border-radius: 8px;
            margin-top: 10px;
            padding: 10px;
            border: 1px solid {p["border"]};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 10px;
            font-weight: bold;
            color: {p["primary"]};
        }}
        QTabWidget::pane {{
            border: 1px solid {p["border"]};
            border-top: none;
            border-radius: 0 0 8px 8px;
        }}
        QTabBar::tab {{
            background: {p["bg"]};
            border: 1px solid {p["border"]};
            border-bottom: none;
            padding: 8px 16px;
            font-weight: bold;
            border-radius: 8px 8px 0 0;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background: {p["alt_bg"]};
            border: 1px solid {p["border"]};
            border-bottom: 2px solid {p["alt_bg"]};
            color: {p["primary"]};
        }}
        QTabBar::tab:!selected:hover {{
            background: {p["border"]};
        }}
        QTableWidget {{
            background-color: {p["alt_bg"]};
            alternate-background-color: {p["bg"]};
            gridline-color: {p["border"]};
            color: {p["text_main"]};
        }}
        QTableWidget::item {{
            border-bottom: 1px solid {p["border"]};
            padding: 5px;
        }}
        QTableWidget::item:selected {{
            background-color: {p["selected_bg"]};
            color: {p["selected_fg"]};
        }}
        QHeaderView::section {{
            background-color: {p["primary"]};
            color: {p["text_dark"]};
            padding: 5px;
            border: none;
            font-weight: bold;
        }}
        QPushButton {{
            background-color: {p["entry_bg"]};
            color: {p["text_main"]};
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid {p["border"]};
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {p["border"]};
        }}
        QPushButton:pressed {{
            background-color: {p["bg"]};
        }}
        QPushButton#PrimaryAction {{
            background-color: {p["primary"]};
            color: {p["text_dark"]};
            border-radius: 6px;
            border: 2px solid {p["primary_dark"]};
            font-weight: bold;
            padding: 8px 14px;
        }}
        QPushButton#PrimaryAction:hover {{
            background-color: {p["primary_light"]};
        }}
        QPushButton#PrimaryAction:pressed {{
            background-color: {p["primary_dark"]};
        }}
        QLineEdit, QComboBox, QDateEdit {{
            background-color: {p["entry_bg"]};
            border: 1px solid {p["border"]};
            padding: 6px;
            border-radius: 4px;
            color: {p["text_main"]};
        }}
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
            border: 1px solid {p["primary"]};
        }}
        QMenuBar {{
            background-color: {p["alt_bg"]};
            color: {p["text_main"]};
        }}
        QMenuBar::item:selected {{
            background: {p["primary"]};
            color: {p["selected_fg"]};
        }}
        QMenu {{
            background-color: {p["alt_bg"]};
            border: 1px solid {p["border"]};
        }}
        QMenu::item:selected {{
            background-color: {p["primary"]};
            color: {p["selected_fg"]};
        }}
        QScrollBar:vertical {{
            background: {p["bg"]};
            width: 12px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {p["primary"]};
            border-radius: 6px;
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            background: none;
        }}
    """

# --- GERAÇÃO DOS TEMAS ---
THEMES = {
    "dark_green": generate_theme_qss(PALETTES["dark_green"]),
    "light_green": generate_theme_qss(PALETTES["light_green"]),
}

# --- WIDGETS E DIÁLOGOS (sem alterações) ---
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class RecordDetailDialog(QDialog):
    def __init__(self, record_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Registo")
        layout = QGridLayout(self)
        for i, (key, value) in enumerate(record_data.items()):
            layout.addWidget(QLabel(f"<b>{key}:</b>"), i, 0)
            layout.addWidget(QLabel(str(value)), i, 1)
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, i + 1, 0, 1, 2)

class ExportOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opções de Exportação")
        self.layout = QVBoxLayout(self)
        self.result = None
        self.btn_pagina_atual = QPushButton("Apenas a Página Atual")
        self.btn_pagina_atual.clicked.connect(lambda: self.set_result("pagina_atual"))
        self.btn_filtrados = QPushButton("Apenas Resultados Filtrados")
        self.btn_filtrados.clicked.connect(lambda: self.set_result("filtrados"))
        self.btn_todos = QPushButton("Todos os Dados")
        self.btn_todos.clicked.connect(lambda: self.set_result("todos"))
        self.layout.addWidget(self.btn_pagina_atual)
        self.layout.addWidget(self.btn_filtrados)
        self.layout.addWidget(self.btn_todos)
    def set_result(self, result):
        self.result = result
        self.accept()


# --- WORKER E COLUMN SETTINGS (sem alterações) ---
class Worker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(object) # Alterado para emitir um objeto (ex: (nome_cliente, erro_msg))
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e) # Emitir a exceção

class ColumnSettingsDialog(QDialog):
    def __init__(self, all_columns, visible_columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Colunas Visíveis")
        self.setMinimumWidth(300)
        layout = QVBoxLayout(self)
        self.checkboxes = {}
        for col in all_columns:
            checkbox = QCheckBox(col)
            checkbox.setChecked(col in visible_columns)
            layout.addWidget(checkbox)
            self.checkboxes[col] = checkbox
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    def get_selected_columns(self):
        return [col for col, checkbox in self.checkboxes.items() if checkbox.isChecked()]

# --- TELA DE CONSULTAS (sem alterações) ---
class ConsultaScreen(QWidget):
    def __init__(self, controller, api, main_app):
        super().__init__()
        self.controller = controller
        self.api = api # Esta referência será atualizada pela AppGUI
        self.main_app = main_app
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        controls_group = QGroupBox()
        self.set_shadow(controls_group)
        controls_layout = QGridLayout(controls_group)
        self.entry_id = QLineEdit()
        self.entry_id.setPlaceholderText("IDMENSAGEM")
        self.entry_id.returnPressed.connect(self.main_app.consultar_api_async)
        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.setObjectName("PrimaryAction")
        self.btn_consultar.clicked.connect(self.main_app.consultar_api_async)
        self.btn_refresh = QPushButton("Atualizar")
        self.btn_refresh.clicked.connect(self.main_app.refresh_data_async)
        self.btn_config_colunas = QPushButton("Colunas")
        self.btn_config_colunas.clicked.connect(self.main_app.open_column_settings)
        self.entry_filtro = QLineEdit()
        self.entry_filtro.setPlaceholderText("")
        self.combo_coluna = QComboBox()
        self.combo_coluna.addItems(["TODAS"] + COLUNAS)
        self.combo_coluna.setCurrentText("PLACA")
        self.btn_aplicar_filtros = QPushButton("Aplicar")
        self.btn_aplicar_filtros.setObjectName("PrimaryAction")
        self.btn_aplicar_filtros.clicked.connect(self.main_app.aplicar_filtro)
        self.btn_limpar_filtros = QPushButton("Limpar Filtros")
        self.btn_limpar_filtros.clicked.connect(self.main_app.limpar_filtros)
        controls_layout.addWidget(QLabel("Busca por ID:"), 0, 0)
        controls_layout.addWidget(self.entry_id, 0, 1)
        controls_layout.addWidget(self.btn_consultar, 0, 2)
        controls_layout.addWidget(self.btn_refresh, 0, 3)
        controls_layout.addWidget(self.btn_config_colunas, 0, 4)
        controls_layout.addWidget(QLabel("Filtro:"), 1, 0)
        controls_layout.addWidget(self.entry_filtro, 1, 1)
        controls_layout.addWidget(self.combo_coluna, 1, 2)
        controls_layout.addWidget(self.btn_aplicar_filtros, 1, 3)
        controls_layout.addWidget(self.btn_limpar_filtros, 1, 4)
        controls_layout.setColumnStretch(5, 1)
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(len(COLUNAS))
        self.tabela.setHorizontalHeaderLabels(COLUNAS)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.horizontalHeader().setHighlightSections(False)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.horizontalHeader().sectionClicked.connect(self.main_app.ordenar_por_coluna)
        self.tabela.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabela.customContextMenuRequested.connect(self.show_table_context_menu)
        self.tabela.itemDoubleClicked.connect(self.main_app.show_record_details)
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        bottom_layout = QHBoxLayout()
        paginacao_group = QGroupBox()
        self.set_shadow(paginacao_group)
        paginacao_layout = QHBoxLayout(paginacao_group)
        self.btn_primeira = QPushButton("<<")
        self.btn_primeira.clicked.connect(self.main_app.primeira_pagina)
        self.btn_anterior = QPushButton("<")
        self.btn_anterior.clicked.connect(self.main_app.pagina_anterior)
        self.label_pagina = QLabel("Página 1 / 1")
        self.btn_proximo = QPushButton(">")
        self.btn_proximo.clicked.connect(self.main_app.proxima_pagina)
        self.btn_ultima = QPushButton(">>")
        self.btn_ultima.clicked.connect(self.main_app.ultima_pagina)
        paginacao_layout.addWidget(self.btn_primeira)
        paginacao_layout.addWidget(self.btn_anterior)
        paginacao_layout.addWidget(self.label_pagina)
        paginacao_layout.addWidget(self.btn_proximo)
        paginacao_layout.addWidget(self.btn_ultima)
        export_group = QGroupBox("Exportar")
        self.set_shadow(export_group)
        export_layout = QHBoxLayout(export_group)
        self.btn_excel = QPushButton("Excel")
        self.btn_excel.clicked.connect(self.main_app.exportar_excel)
        self.btn_csv = QPushButton("CSV")
        self.btn_csv.clicked.connect(self.main_app.exportar_csv)
        export_layout.addWidget(self.btn_excel)
        export_layout.addWidget(self.btn_csv)
        bottom_layout.addWidget(paginacao_group)
        bottom_layout.addStretch()
        bottom_layout.addWidget(export_group)
        main_layout.addWidget(controls_group)
        main_layout.addWidget(self.tabela, 1)
        main_layout.addLayout(bottom_layout)
    def set_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 5)
        widget.setGraphicsEffect(shadow)
    def show_table_context_menu(self, pos):
        item = self.tabela.itemAt(pos)
        if not item: return
        menu = QMenu()
        copy_row_action = menu.addAction("Copiar Linha")
        copy_cell_action = menu.addAction("Copiar Célula")
        action = menu.exec(self.tabela.mapToGlobal(pos))
        if action == copy_row_action:
            row_index = item.row()
            row_data = [self.tabela.item(row_index, c).text() for c in range(self.tabela.columnCount())]
            QApplication.clipboard().setText(", ".join(row_data))
        elif action == copy_cell_action:
            QApplication.clipboard().setText(item.text())
    def atualizar_tabela(self, dados):
        self.tabela.setRowCount(0)
        if not dados: return
        self.tabela.setRowCount(len(dados))
        header_labels = [self.tabela.horizontalHeaderItem(i).text().replace(" ↓", "").replace(" ↑", "") for i in range(self.tabela.columnCount())]
        for row_idx, row_data in enumerate(dados):
            for col_idx, col_name in enumerate(header_labels):
                if not self.tabela.isColumnHidden(col_idx):
                    item_text = str(row_data.get(col_name, ""))
                    self.tabela.setItem(row_idx, col_idx, QTableWidgetItem(item_text))
    
    def atualizar_label_pagina(self):
        total_registos = self.controller.total_registos
        total_paginas = self.controller.total_paginas if self.controller.total_registos > 0 else 1
        self.main_app.pagina_atual = max(1, min(self.main_app.pagina_atual, total_paginas))
        self.label_pagina.setText(f"Página {self.main_app.pagina_atual}/{total_paginas} ({total_registos})")

# --- [NOVA CLASSE] PÁGINA DE STATUS INDIVIDUAL ---
class ClientStatusPage(QWidget):
    """
    Este widget contém o dashboard de UM cliente (o gráfico e a lista de TrackIDs).
    É o layout que pertencia à 'ControleScreen' antiga.
    """
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.status_widgets = {}
        self.current_ids = set()
        self.tema_atual = self.main_app.tema_atual

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(20)

        # --- Painel do gráfico ---
        chart_group = QGroupBox("Visão Geral do Status")
        chart_group.setMinimumWidth(420)
        chart_layout = QVBoxLayout(chart_group)
        chart_layout.setContentsMargins(10, 10, 10, 10)

        self.chart_canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.chart_canvas.setFixedHeight(300)
        chart_layout.addWidget(self.chart_canvas, alignment=Qt.AlignmentFlag.AlignCenter)

        self.status_summary_label = QLabel("Monitorando 0 clientes | Última atualização: N/A")
        self.status_summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_summary_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 10px;")
        chart_layout.addWidget(self.status_summary_label)
        main_layout.addWidget(chart_group, 1)

        # --- Painel da lista de clientes ---
        list_group = QGroupBox("Status por TrackID")
        list_layout = QVBoxLayout(list_group)
        list_layout.setContentsMargins(10, 10, 10, 10)
        list_layout.setSpacing(10)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        list_layout.addWidget(self.scroll_area)
        main_layout.addWidget(list_group, 2)

    def update_display(self, client_status_ref):
        """
        Atualiza este dashboard específico com os dados de status fornecidos.
        'client_status_ref' é o dicionário de status para este cliente.
        """
        if client_status_ref is None:
            client_status_ref = {}
            
        new_ids = set(client_status_ref.keys())
        self.tema_atual = self.main_app.tema_atual # Garante que o tema está atualizado

        if new_ids != self.current_ids:
            while self.scroll_layout.count():
                child = self.scroll_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            self.status_widgets.clear()
            self.current_ids = new_ids

            for track_id in sorted(list(self.current_ids)):
                card = QFrame()
                card_layout = QHBoxLayout(card)
                card_layout.setContentsMargins(12, 8, 12, 8)
                card_layout.setSpacing(14)

                icon = QLabel("●")
                icon.setFixedWidth(25)
                icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

                label = QLabel(f"<b>TrackID:</b> {track_id}<br><i>Aguardando...</i>")
                label.setWordWrap(True)

                btn = QPushButton("Ver na Tabela")
                btn.setObjectName("PrimaryAction")
                # O botão deve funcionar apenas para o cliente ATUALMENTE selecionado na tela de Consultas
                btn.clicked.connect(lambda _, tid=track_id: self.main_app.show_in_table(tid))
                if self.main_app.cliente_atual['nome'] != self.parent().parent().tabText(self.parent().parent().currentIndex()):
                     btn.setEnabled(False)
                     btn.setToolTip("Mude para este cliente na tela de Consultas para ativar o botão")
                
                card_layout.addWidget(icon)
                card_layout.addWidget(label, 1)
                card_layout.addWidget(btn)

                card.setFrameShape(QFrame.Shape.StyledPanel)
                self.scroll_layout.addWidget(card)
                self.status_widgets[track_id] = {"card": card, "icon": icon, "label": label}

        # --- Atualização de status ---
        ok_count, error_count, no_signal_count = 0, 0, 0
        palette = PALETTES[self.tema_atual]

        for track_id, status_info in client_status_ref.items():
            if track_id in self.status_widgets:
                w = self.status_widgets[track_id]
                status = status_info.get("status", "N/A")
                message = status_info.get("message", "")
                card_style = f"background-color: {palette['alt_bg']}; border: 1px solid {palette['border']}; border-radius: 10px;"

                if status == "OK":
                    color = palette['primary']
                    msg = f"<b>Latitude:</b> {status_info.get('latitude', 'N/A')}<br>" \
                          f"<b>Longitude:</b> {status_info.get('longitude', 'N/A')}<br>" \
                          f"<b>Data/Hora:</b> {status_info.get('datahora', 'N/A')}"
                    ok_count += 1
                elif status == "ERRO":
                    color = "#FF5252"
                    msg = f"<b>ERRO:</b> {message}"
                    error_count += 1
                elif status == "SEM REGISTRO RECENTE":
                    color = "#8E9BAA"
                    msg = f"<i>{message}</i>"
                    no_signal_count += 1
                else:
                    color = "#FFC107"
                    msg = "<i>Aguardando atualização...</i>"
                    no_signal_count += 1

                w["icon"].setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
                w["label"].setText(f"<b>TrackID:</b> {track_id}<br>{msg}")
                w["card"].setStyleSheet(card_style)

        now = datetime.now().strftime("%H:%M:%S")
        self.status_summary_label.setText(
            f"<b>Total: {len(self.current_ids)}</b> | Última atualização (dados): {now}"
        )
        self.update_chart(ok_count, error_count, no_signal_count)

    def update_chart(self, ok, error, no_signal):
        self.chart_canvas.axes.clear()
        palette = PALETTES[self.tema_atual]
        
        theme_colors = {
            "ok": palette['primary'],
            "error": "#FF5252",
            "no_signal": "#8E9BAA",
        }
        labels, sizes, colors = [], [], []
        if ok > 0:
            labels.append(f"OK ({ok})"); sizes.append(ok); colors.append(theme_colors["ok"])
        if error > 0:
            labels.append(f"Erro ({error})"); sizes.append(error); colors.append(theme_colors["error"])
        if no_signal > 0:
            labels.append(f"Sem Sinal ({no_signal})"); sizes.append(no_signal); colors.append(theme_colors["no_signal"])
        if not sizes:
            sizes, labels, colors = [1], ["Nenhum dado"], [palette['border']]

        text_color = palette['text_main']
        self.chart_canvas.axes.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
            textprops={"color": text_color, "weight": "bold"},
        )
        self.chart_canvas.axes.axis("equal")
        self.chart_canvas.figure.set_facecolor("none")
        self.chart_canvas.draw()


# --- [CLASSE MODIFICADA] TELA DE CONTROLE (AGORA UM CONTAINER DE ABAS) ---
class ControleScreen(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.client_pages = {} # Dicionário para guardar as páginas: {'NomeCliente': ClientStatusPage}

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # O timer de atualização foi movido para AppGUI

    def update_dashboard(self, all_client_statuses):
        """
        Recebe o dicionário de status global e atualiza/cria as abas.
        all_client_statuses = {'Cliente A': {status_dict}, 'Cliente B': {status_dict}}
        """
        self.tab_widget.clear() # Limpa e recria as abas
        self.client_pages = {}

        for client_name, status_dict in sorted(all_client_statuses.items()):
            
            page = ClientStatusPage(self.main_app)
            self.client_pages[client_name] = page
            self.tab_widget.addTab(page, client_name)
            
            # Atualiza a página com os dados
            page.update_display(status_dict)

# --- JANELA PRINCIPAL (APP GUI) ---
class AppGUI(QMainWindow):
    def __init__(self, clientes):
        super().__init__()
        self.clientes = clientes
        self.cliente_atual = self.clientes[0]
        self.api = None # Será inicializado em 'inicializar_api_e_carregar_dados'
        
        self.app_state = load_state()
        self.tema_atual = self.app_state.get("theme", "dark_green")
        if self.tema_atual not in THEMES:
            self.tema_atual = "dark_green"
        self.visible_columns = self.app_state.get("visible_columns", COLUNAS[:])
        self.controller = DataController(COLUNAS, ITENS_POR_PAGINA)
        self.exportar = Exportar(self, self.controller)
        self.pagina_atual = 1
        self.workers = []
        
        # --- [NOVO] ARMAZENAMENTO DE STATUS GLOBAL ---
        self.global_client_data = {} # Armazena os dados brutos de todos os clientes
        self.global_client_status = {} # Armazena os status processados de todos os clientes
        
        self.is_first_load = True
        self.setWindowTitle(f"App de Consulta - {self.cliente_atual['nome']}")
        
        geometry = self.app_state.get("geometry")
        if geometry and isinstance(geometry, (list, tuple)) and len(geometry) == 4:
            self.setGeometry(*geometry)
        else:
            self.setGeometry(100, 100, 1300, 700)
            
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(QLabel("<b>Cliente:</b>"))
        self.combo_clientes = QComboBox()
        for cliente in self.clientes:
            self.combo_clientes.addItem(cliente['nome'])
        self.combo_clientes.currentIndexChanged.connect(self.on_cliente_mudou)
        top_bar_layout.addWidget(self.combo_clientes, 1)
        top_bar_layout.addStretch()
        main_layout.addLayout(top_bar_layout)
        
        self._create_menu()
        
        self.container = QStackedWidget()
        self.frames = {
            "Consultas": ConsultaScreen(self.controller, self.api, self),
            "Controle": ControleScreen(self) # A tela de controle agora é o container de abas
        }
        self.container.addWidget(self.frames["Consultas"])
        self.container.addWidget(self.frames["Controle"])
        main_layout.addWidget(self.container)
        
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Bem-vindo!")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.inicializar_api_e_carregar_dados()
        
        # --- [NOVO] MONITORAMENTO GLOBAL ---
        self.global_monitor_timer = QTimer()
        self.global_monitor_timer.timeout.connect(self.run_global_client_monitoring)
        # 10 minutos = 10 * 60 * 1000 = 600000 ms
        self.global_monitor_timer.start(600000)
        self.run_global_client_monitoring() # Executa uma vez no início
        # O timer antigo (monitor_timer) foi removido
        
        self.update_visible_columns()
        self.aplicar_tema_completo()
        self.setup_shortcuts()

    def on_cliente_mudou(self, index):
        """Chamado quando o utilizador seleciona um novo cliente na ComboBox."""
        self.cliente_atual = self.clientes[index]
        self.setWindowTitle(f"App de Consulta - {self.cliente_atual['nome']}")
        logging.info(f"Cliente (Consultas) alterado para: {self.cliente_atual['nome']}")
        
        self.controller.dados_completos = []
        self.controller.aplicar_filtro()
        self.renderizar_dados()
        
        # Carrega os dados do cliente selecionado para a tela de Consultas
        self.inicializar_api_e_carregar_dados()
        
        # Atualiza o dashboard (para re-habilitar botões 'Ver na Tabela')
        self.frames["Controle"].update_dashboard(self.global_client_status)


    def inicializar_api_e_carregar_dados(self):
        """Cria a instância da API para o cliente ATUAL e carrega os dados para a TELA DE CONSULTAS."""
        creds = self.cliente_atual
        try:
            self.api = ConsultaAPI(creds['url'], creds['user'], creds['password'])
        except Exception as e:
            logging.error(f"Falha ao inicializar API para {creds['nome']}: {e}")
            QMessageBox.critical(self, "Erro de Conexão", f"Não foi possível inicializar a API para o cliente {creds['nome']}.\nVerifique o 'clientes.json'.\nErro: {e}")
            self.gerir_estado_widgets(False)
            return

        self.frames["Consultas"].api = self.api
        
        # Carrega os dados locais para o cliente selecionado
        # Usamos os dados do cache global se já existirem, senão busca
        if creds['nome'] in self.global_client_data:
            logging.info(f"Carregando dados locais de {creds['nome']} a partir do cache global.")
            self.on_dados_carregados(self.global_client_data[creds['nome']])
        else:
            logging.info(f"Buscando dados locais para {creds['nome']} pela primeira vez.")
            self.carregar_dados_iniciais(force_refresh=True)

    def _create_menu(self):
        # ... (sem alterações) ...
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Ficheiro")
        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        view_menu = menu_bar.addMenu("Ver")
        self.consultas_action = QAction("Consultas", self, checkable=True)
        self.consultas_action.setChecked(True)
        self.consultas_action.triggered.connect(lambda: self.show_frame("Consultas"))
        self.controle_action = QAction("Controle", self, checkable=True)
        self.controle_action.triggered.connect(lambda: self.show_frame("Controle"))
        view_menu.addAction(self.consultas_action)
        view_menu.addAction(self.controle_action)
        view_menu.addSeparator()
        self.fullscreen_action = QAction("Tela Cheia (F11)", self, checkable=True)
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self.fullscreen_action)
        
        prefs_menu = menu_bar.addMenu("Preferências")
        theme_menu = QMenu("Tema", self)
        prefs_menu.addMenu(theme_menu)
        
        self.dark_action = QAction("Dark Green", self, checkable=True)
        self.dark_action.triggered.connect(lambda: self.set_theme("dark_green"))
        self.light_action = QAction("Light Green", self, checkable=True)
        self.light_action.triggered.connect(lambda: self.set_theme("light_green"))
        theme_menu.addAction(self.dark_action)
        theme_menu.addAction(self.light_action)

    def closeEvent(self, event):
        # ... (sem alterações) ...
        header = self.frames["Consultas"].tabela.horizontalHeader()
        widths = [header.sectionSize(i) for i in range(header.count())]
        self.app_state['theme'] = self.tema_atual
        self.app_state['visible_columns'] = self.visible_columns
        self.app_state['geometry'] = self.geometry().getRect()
        self.app_state['column_widths'] = widths
        save_state(self.app_state)
        event.accept()
        
    def setup_shortcuts(self):
        # ... (sem alterações) ...
        shortcut_refresh = QShortcut(QKeySequence("F5"), self)
        shortcut_refresh.activated.connect(self.refresh_data_async)
        shortcut_filter = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_filter.activated.connect(lambda: self.frames["Consultas"].entry_filtro.setFocus())
        shortcut_fullscreen_f11 = QShortcut(QKeySequence(Qt.Key.Key_F11), self)
        shortcut_fullscreen_f11.activated.connect(self.toggle_fullscreen)
        shortcut_exit_fullscreen_esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        shortcut_exit_fullscreen_esc.activated.connect(self.exit_fullscreen)

    # --- Funções de Fullscreen e Tema (sem alterações) ---
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_action.setChecked(False)
        else:
            self.showFullScreen()
            self.fullscreen_action.setChecked(True)

    def exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_action.setChecked(False)

    def set_theme(self, theme_name):
        self.tema_atual = theme_name
        self.aplicar_tema_completo()

    def aplicar_tema_completo(self):
        self.setStyleSheet(THEMES[self.tema_atual])
        self.dark_action.setChecked(self.tema_atual == "dark_green")
        self.light_action.setChecked(self.tema_atual == "light_green")
        for dialog in self.findChildren(QDialog):
            dialog.setStyleSheet(THEMES[self.tema_atual])
        # Atualiza o dashboard (que agora tem abas)
        self.frames["Controle"].update_dashboard(self.global_client_status)

    def open_column_settings(self):
        # ... (sem alterações) ...
        dialog = ColumnSettingsDialog(COLUNAS, self.visible_columns, self)
        if dialog.exec():
            self.visible_columns = dialog.get_selected_columns()
            self.update_visible_columns()

    def update_visible_columns(self):
        # ... (sem alterações) ...
        tabela = self.frames["Consultas"].tabela
        for i, col_name in enumerate(COLUNAS):
            tabela.setColumnHidden(i, col_name not in self.visible_columns)

    def show_frame(self, frame_name):
        self.consultas_action.setChecked(frame_name == "Consultas")
        self.controle_action.setChecked(frame_name == "Controle")
        
        # A lógica de iniciar/parar o timer foi REMOVIDA
        # O timer global agora corre independentemente
        
        if frame_name == "Consultas":
            self.container.setCurrentWidget(self.frames["Consultas"])
        elif frame_name == "Controle":
            self.container.setCurrentWidget(self.frames["Controle"])
            # Atualiza os botões 'Ver na Tabela' no painel de controle
            self.frames["Controle"].update_dashboard(self.global_client_status)

    def show_in_table(self, track_id):
        # ... (sem alterações) ...
        self.show_frame("Consultas")
        screen = self.frames["Consultas"]
        screen.combo_coluna.setCurrentText("TrackID")
        screen.entry_filtro.setText(str(track_id))
        self.aplicar_filtro()
    
    # --- [MÉTODO REFACTORADO] ---
    def process_data_into_status(self, dados_completos):
        """
        Recebe uma lista de dados e processa-a num dicionário de status por TrackID.
        Esta é a lógica do antigo 'monitor_all_clients'.
        """
        if not dados_completos:
            return {}
        
        limite_tempo = timedelta(hours=24)
        agora = datetime.now()
        
        client_status_output = {} # Dicionário de retorno
        records_by_trackid = {}
        
        for record in dados_completos:
            track_id = record.get("TrackID")
            if track_id:
                if track_id not in records_by_trackid:
                    records_by_trackid[track_id] = []
                records_by_trackid[track_id].append(record)

        for track_id, records in records_by_trackid.items():
            latest_record = max(records, key=lambda r: r.get("DATAHORA", ""))
            
            data_ultimo_registo_str = latest_record.get("DATAHORA", "")
            status_cliente = {}
            try:
                data_ultimo_registo_obj = parse_api_datetime_to_date(data_ultimo_registo_str)
                if data_ultimo_registo_obj is None:
                    raise ValueError("Data nula ou em formato inválido")

                data_ultimo_registo_dt = datetime.combine(data_ultimo_registo_obj, datetime.min.time())
                
                if agora - data_ultimo_registo_dt > limite_tempo:
                    status_cliente = {
                        'status': 'SEM REGISTRO RECENTE', 
                        'message': f"Último registro: {data_ultimo_registo_str}"
                    }
                else:
                    status_cliente = {
                        'status': 'OK', 
                        'latitude': latest_record.get('LATITUDE'),
                        'longitude': latest_record.get('LONGITUDE'), 
                        'datahora': data_ultimo_registo_str
                    }
            except (ValueError, TypeError):
                 status_cliente = {
                    'status': 'ERRO', 
                    'message': 'Formato de data inválido no último registo.'
                }

            client_status_output[track_id] = status_cliente
            
        return client_status_output

    # --- [NOVO] MÉTODOS DE MONITORAMENTO GLOBAL ---
    def run_global_client_monitoring(self):
        """Dispara workers para buscar dados de TODOS os clientes em paralelo."""
        logging.info("Iniciando monitoramento global de clientes...")
        self.status_bar.showMessage("Monitor global: Buscando status de todos os clientes...")
        
        for client_info in self.clientes:
            worker = Worker(self.fetch_client_data, client_info)
            worker.finished.connect(self.on_global_data_received)
            worker.error.connect(lambda err, c=client_info: self.on_global_data_error(c['nome'], err))
            # Não usamos self.run_in_thread porque não queremos desabilitar a GUI inteira
            self.workers.append(worker)
            worker.start()

    def fetch_client_data(self, client_info):
        """
        Função executada pelo Worker. Busca dados frescos de um cliente.
        Retorna (nome_cliente, dados)
        """
        logging.info(f"[Monitor Global] Buscando dados de: {client_info['nome']}")
        api = ConsultaAPI(client_info['url'], client_info['user'], client_info['password'])
        # Força a atualização, ignorando o cache local da API
        dados = api.buscar_todos(force_refresh=True) 
        return (client_info['nome'], dados)

    def on_global_data_received(self, result):
        """Handler para quando um worker de monitoramento termina."""
        client_name, dados = result
        
        if dados is None:
            # Ocorreu um erro dentro do fetch_client_data (já logado)
            status_dict = {"API_ERROR": {"status": "ERRO", "message": "Falha ao conectar ou buscar dados."}}
        else:
            logging.info(f"[Monitor Global] Dados recebidos de: {client_name} ({len(dados)} registos)")
            # Armazena os dados brutos
            self.global_client_data[client_name] = dados
            # Processa os dados em status
            status_dict = self.process_data_into_status(dados)
        
        # Armazena o status processado
        self.global_client_status[client_name] = status_dict
        
        # Notifica a Tela de Controle para atualizar as suas abas
        self.frames["Controle"].update_dashboard(self.global_client_status)
        self.status_bar.showMessage(f"Monitor global: Status de '{client_name}' atualizado.", 5000)

    def on_global_data_error(self, client_name, error):
        """Handler para falha de um worker de monitoramento."""
        logging.error(f"[Monitor Global] Erro ao buscar dados de {client_name}: {error}")
        status_dict = {"API_ERROR": {"status": "ERRO", "message": f"Falha na thread: {error}"}}
        self.global_client_status[client_name] = status_dict
        self.frames["Controle"].update_dashboard(self.global_client_status)
        self.status_bar.showMessage(f"Monitor global: Falha ao atualizar '{client_name}'.", 5000)

    # --- Funções de Threads (sem alterações) ---
    def on_worker_finished(self, worker):
        if worker in self.workers:
            self.workers.remove(worker)

    def run_in_thread(self, func, on_finish, on_error, *args, **kwargs):
        """Usado para tarefas da GUI (Carregar, Consultar, Exportar) que bloqueiam a UI."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        worker = Worker(func, *args, **kwargs)
        worker.finished.connect(on_finish)
        worker.error.connect(on_error)
        worker.finished.connect(lambda: self.on_worker_finished(worker))
        worker.error.connect(lambda: self.on_worker_finished(worker))
        self.workers.append(worker)
        worker.start()
        self.gerir_estado_widgets(False)
    
    def on_task_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"ERRO: {error_msg}", 5000)
        QMessageBox.critical(self, "Erro de API", str(error_msg))
        self.gerir_estado_widgets(True)

    def on_task_completed(self):
        self.progress_bar.setVisible(False)
        self.gerir_estado_widgets(True)

    # --- Métodos de Carregamento da TELA DE CONSULTAS ---
    def carregar_dados_iniciais(self, force_refresh=False):
        if not self.api:
             logging.warning("carregar_dados_iniciais chamado, mas a API (Consultas) não está inicializada.")
             return
        self.is_first_load = True
        self.status_bar.showMessage(f"Carregando dados para {self.cliente_atual['nome']}...")
        self.run_in_thread(
            self.api.buscar_todos,
            on_finish=self.on_dados_carregados,
            on_error=self.on_task_error,
            force_refresh=force_refresh
        )

    def on_dados_carregados(self, dados):
        if dados is None: dados = []
        
        # Atualiza o controlador de dados da TELA DE CONSULTAS
        self.controller.dados_completos = dados
        self.aplicar_filtro()
        self.status_bar.showMessage(f"Dados carregados para {self.cliente_atual['nome']}: {len(dados)} registos.", 5000)
        
        # Armazena os dados no cache global também (se ainda não estiver lá)
        if self.cliente_atual['nome'] not in self.global_client_data:
             self.global_client_data[self.cliente_atual['nome']] = dados
             # Processa e atualiza o dashboard de controle
             status_dict = self.process_data_into_status(dados)
             self.global_client_status[self.cliente_atual['nome']] = status_dict
             self.frames["Controle"].update_dashboard(self.global_client_status)
             
        self.on_task_completed()
        
        # Lógica de redimensionamento da tabela
        tabela = self.frames["Consultas"].tabela
        header = tabela.horizontalHeader()
        widths = self.app_state.get("column_widths")
        if not self.is_first_load and widths and len(widths) == header.count():
            for i, width in enumerate(widths):
                header.resizeSection(i, width)
        else:
            tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.is_first_load = False

    # --- Métodos de Paginação, Filtro e Ordenação (sem alterações) ---
    def renderizar_dados(self):
        page_num, dados_pagina = self.controller.get_dados_pagina(self.pagina_atual)
        self.pagina_atual = page_num
        self.frames["Consultas"].atualizar_tabela(dados_pagina)
        self.frames["Consultas"].atualizar_label_pagina()
        self.update_sort_indicator()

    def aplicar_filtro(self):
        screen = self.frames["Consultas"]
        self.controller.set_filtro_texto(screen.entry_filtro.text(), screen.combo_coluna.currentText())
        self.controller.aplicar_filtro()
        self.pagina_atual = 1
        self.renderizar_dados()

    def limpar_filtros(self):
        screen = self.frames["Consultas"]
        screen.entry_filtro.clear()
        screen.combo_coluna.setCurrentText("PLACA")
        self.aplicar_filtro()

    def ordenar_por_coluna(self, column_index):
        header_labels = [self.frames["Consultas"].tabela.horizontalHeaderItem(i).text().replace(" ↓", "").replace(" ↑", "") for i in range(len(COLUNAS))]
        coluna = header_labels[column_index]
        self.controller.ordenar(coluna)
        self.controller.aplicar_filtro(re_sort_only=True)
        self.pagina_atual = 1
        self.renderizar_dados()
    
    def update_sort_indicator(self):
        tabela = self.frames["Consultas"].tabela
        sorted_col_name = self.controller.coluna_ordenacao
        is_desc = self.controller.ordem_desc
        for i in range(tabela.columnCount()):
            header_item = tabela.horizontalHeaderItem(i)
            original_text = header_item.text().replace(" ↓", "").replace(" ↑", "")
            if original_text == sorted_col_name:
                arrow = "↓" if is_desc else "↑"
                header_item.setText(f"{original_text} {arrow}")
            else:
                header_item.setText(original_text)
        
    def consultar_api_async(self):
        if not self.api: return
        id_msg = self.frames["Consultas"].entry_id.text().strip()
        if not (id_msg and id_msg.isdigit()):
            QMessageBox.warning(self, "Atenção", "IDMENSAGEM deve ser um número.")
            return
        self.status_bar.showMessage(f"A consultar ID {id_msg}...")
        self.run_in_thread(
            self.api.consultar,
            on_finish=self.on_dados_carregados,
            on_error=self.on_task_error,
            id_mensagem=id_msg
        )

    def refresh_data_async(self):
        if not self.api: return
        self.carregar_dados_iniciais(force_refresh=True)

    def ir_para_pagina(self, numero_pagina):
        self.pagina_atual = numero_pagina
        self.renderizar_dados()
        
    def primeira_pagina(self): self.ir_para_pagina(1)
    def ultima_pagina(self): self.ir_para_pagina(self.controller.total_paginas)
    def pagina_anterior(self): self.ir_para_pagina(self.pagina_atual - 1)
    def proxima_pagina(self): self.ir_para_pagina(self.pagina_atual + 1)
    
    # --- Métodos de Detalhes e Exportação (sem alterações) ---
    def show_record_details(self, item):
        row_index = item.row()
        id_col_index = -1
        for i, col_name in enumerate(COLUNAS):
            if col_name == "IDMENSAGEM":
                id_col_index = i
                break
        
        if id_col_index != -1:
            try:
                record_id = self.frames["Consultas"].tabela.item(row_index, id_col_index).text()
                full_record = self.controller.get_record_by_id(record_id)
                if full_record:
                    dialog = RecordDetailDialog(full_record, self)
                    dialog.exec()
            except AttributeError:
                logging.warning("Falha ao obter detalhes do registo. A tabela pode ter sido atualizada.")
            
    def exportar_excel(self):
        self._show_export_options("excel")

    def exportar_csv(self):
        self._show_export_options("csv")

    def _show_export_options(self, file_type):
        dialog = ExportOptionsDialog(self)
        if dialog.exec():
            option = dialog.result
            if option:
                if file_type == "excel":
                    self.exportar.salvar_excel_async(option)
                elif file_type == "csv":
                    self.exportar.salvar_csv_async(option)
    
    def gerir_estado_widgets(self, habilitar):
        # A combobox de clientes deve estar sempre habilitada, exceto durante o carregamento
        self.combo_clientes.setEnabled(habilitar) 
        
        screen = self.frames["Consultas"]
        widgets_to_manage = [
            screen.entry_id, screen.btn_consultar, screen.btn_refresh, 
            screen.btn_config_colunas, screen.entry_filtro, screen.combo_coluna,
            screen.btn_aplicar_filtros, screen.btn_limpar_filtros,
            screen.btn_primeira, screen.btn_anterior, screen.btn_proximo, 
            screen.btn_ultima, screen.btn_excel, screen.btn_csv
        ]
        for widget in widgets_to_manage:
            if widget:
                widget.setEnabled(habilitar)