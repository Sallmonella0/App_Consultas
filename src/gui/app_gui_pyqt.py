# src/gui/app_gui_pyqt.py

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QStackedWidget, QMessageBox,
    QScrollArea, QDialog, QCheckBox, QDialogButtonBox, QGridLayout, QGroupBox,
    QProgressBar, QMenu, QCalendarWidget, QDateEdit, QGraphicsDropShadowEffect
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

from src.core.data_controller import DataController
from src.core.exceptions import ConsultaAPIException
from src.utils.exportar import Exportar
from src.utils.config import COLUNAS
from src.utils.settings_manager import ITENS_POR_PAGINA
from src.utils.state_manager import load_state, save_state
from src.utils.datetime_utils import is_valid_ui_date, parse_api_datetime_to_date

# --- NOVOS TEMAS "TECH DARK / LIGHT" ---
THEMES = {
    "tech_dark": """
        QWidget {
            background-color: #121212;
            color: #E0E0E0;
            font-size: 15px;
            border: none;
        }

        QMainWindow, QDialog {
            background-color: #121212;
        }

        QGroupBox {
            background-color: #1E1E1E;
            border-radius: 8px;
            margin-top: 10px;
            padding: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 10px;
            font-weight: bold;
            color: #00E676;
        }

        QTableWidget {
            background-color: #1E1E1E;
            alternate-background-color: #2A2A2A;
            gridline-color: #333;
            color: #E0E0E0;
        }

        QTableWidget::item {
            border-bottom: 1px solid #333;
            padding: 5px;
        }

        QTableWidget::item:selected {
            background-color: #00C853;
            color: #000000;
        }

        QHeaderView::section {
            background-color: #00E676;
            color: #000000;
            padding: 5px;
            border: none;
            font-weight: bold;
        }

        QPushButton {
            background-color: #2C2C2C;
            color: #FFFFFF;
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid #3A3A3A;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #3A3A3A;
        }

        QPushButton:pressed {
            background-color: #1A1A1A;
        }

        /* Botões principais — como 'Ver na Tabela' */
        QPushButton#PrimaryAction {
            background-color: #00E676;
            color: #0B0B0B;
            border-radius: 6px;
            border: 2px solid #00C853;
            font-weight: bold;
            padding: 8px 14px;
        }

        QPushButton#PrimaryAction:hover {
            background-color: #00FF88;
            border-color: #00E676;
        }

        QPushButton#PrimaryAction:pressed {
            background-color: #00C853;
            border-color: #009E47;
        }

        QLineEdit, QComboBox, QDateEdit {
            background-color: #1A1A1A;
            border: 1px solid #444;
            padding: 6px;
            border-radius: 4px;
            color: #FFFFFF;
        }

        QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
            border: 1px solid #00E676;
        }

        QMenuBar {
            background-color: #1E1E1E;
            color: #E0E0E0;
        }

        QMenuBar::item:selected {
            background: #00E676;
            color: #000000;
        }

        QMenu {
            background-color: #1E1E1E;
            border: 1px solid #333;
        }

        QMenu::item:selected {
            background-color: #00E676;
            color: #000000;
        }

        QScrollBar:vertical {
            background: #1A1A1A;
            width: 12px;
            margin: 0;
        }

        QScrollBar::handle:vertical {
            background: #00E676;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background: none;
        }
    """,

    "tech_light": """
        QWidget {
            background-color: #ECEFF1;
            color: #1C1C1C;
            font-size: 15px;
            border: none;
        }

        QMainWindow, QDialog {
            background-color: #ECEFF1;
        }

        QGroupBox {
            background-color: #F7F9FA;
            border-radius: 8px;
            margin-top: 10px;
            padding: 10px;
        }

        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 10px;
            font-weight: bold;
            color: #43A047;
        }

        QTableWidget {
            background-color: #F7F9FA;
            alternate-background-color: #E0E4E7;
            gridline-color: #B0BEC5;
            color: #1A1A1A;
        }

        QTableWidget::item {
            border-bottom: 1px solid #C0C9CC;
            padding: 5px;
        }

        QTableWidget::item:selected {
            background-color: #43A047;
            color: #FFFFFF;
        }

        QHeaderView::section {
            background-color: #4CAF50;
            color: #FFFFFF;
            padding: 5px;
            border: none;
            font-weight: bold;
        }

        QPushButton {
            background-color: #CFD8DC;
            color: #1A1A1A;
            padding: 8px 16px;
            border-radius: 6px;
            border: 1px solid #B0BEC5;
            font-weight: bold;
        }

        QPushButton:hover {
            background-color: #BFC9CA;
        }

        QPushButton:pressed {
            background-color: #AEB6BF;
        }

        /* Botões principais — como 'Ver na Tabela' */
        QPushButton#PrimaryAction {
            background-color: #43A047;
            color: #FFFFFF;
            border-radius: 6px;
            border: 2px solid #388E3C;
            font-weight: bold;
            padding: 8px 14px;
        }

        QPushButton#PrimaryAction:hover {
            background-color: #4CAF50;
            border-color: #43A047;
        }

        QPushButton#PrimaryAction:pressed {
            background-color: #388E3C;
            border-color: #2E7D32;
        }

        QLineEdit, QComboBox, QDateEdit {
            background-color: #FFFFFF;
            border: 1px solid #B0BEC5;
            padding: 6px;
            border-radius: 4px;
        }

        QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
            border: 1px solid #43A047;
        }

        QMenuBar {
            background-color: #F7F9FA;
            color: #1A1A1A;
        }

        QMenuBar::item:selected {
            background: #43A047;
            color: #FFFFFF;
        }

        QMenu {
            background-color: #F7F9FA;
            border: 1px solid #B0BEC5;
        }

        QMenu::item:selected {
            background-color: #43A047;
            color: #FFFFFF;
        }

        QScrollBar:vertical {
            background: #E0E4E7;
            width: 12px;
            margin: 0;
        }

        QScrollBar::handle:vertical {
            background: #43A047;
            border-radius: 6px;
            min-height: 20px;
        }

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background: none;
        }
    """
}




# --- NOVOS WIDGETS E DIÁLOGOS ---
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


# --- WORKER THREAD, COLUMN SETTINGS, CONSULTA SCREEN, CONTROLE SCREEN ---
class Worker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
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
            self.error.emit(str(e))

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

class ConsultaScreen(QWidget):
    def __init__(self, controller, api, main_app):
        super().__init__()
        self.controller = controller
        self.api = api
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
        self.entry_filtro.setPlaceholderText("Filtrar por termo...")
        self.combo_coluna = QComboBox()
        self.combo_coluna.addItems(["TODAS"] + COLUNAS)
        self.combo_coluna.setCurrentText("PLACA")
        self.btn_aplicar_filtros = QPushButton("Aplicar Filtros")
        self.btn_aplicar_filtros.setObjectName("PrimaryAction")
        self.btn_aplicar_filtros.clicked.connect(self.main_app.aplicar_filtro)
        self.btn_limpar_filtros = QPushButton("Limpar Filtros")
        self.btn_limpar_filtros.clicked.connect(self.main_app.limpar_filtros)
        controls_layout.addWidget(QLabel("Busca por ID:"), 0, 0)
        controls_layout.addWidget(self.entry_id, 0, 1)
        controls_layout.addWidget(self.btn_consultar, 0, 2)
        controls_layout.addWidget(self.btn_refresh, 0, 3)
        controls_layout.addWidget(self.btn_config_colunas, 0, 4)
        controls_layout.addWidget(QLabel("Filtro Rápido:"), 1, 0)
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

class ControleScreen(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.status_widgets = {}
        self.current_ids = set()

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
        list_group = QGroupBox("Status por Cliente")
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

        # --- Timer de atualização ---
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)

    def start_periodic_update(self):
        if not self.update_timer.isActive():
            self.update_display()
            self.update_timer.start(5000)

    def stop_periodic_update(self):
        self.update_timer.stop()

    def update_display(self):
        client_status_ref = self.main_app.client_status
        new_ids = set(client_status_ref.keys())

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
                btn.setFixedWidth(140)
                btn.clicked.connect(lambda _, tid=track_id: self.main_app.show_in_table(tid))

                card_layout.addWidget(icon)
                card_layout.addWidget(label, 1)
                card_layout.addWidget(btn)

                card.setFrameShape(QFrame.Shape.StyledPanel)
                card.setStyleSheet("border-radius: 10px; padding: 8px;")
                self.scroll_layout.addWidget(card)
                self.status_widgets[track_id] = {"card": card, "icon": icon, "label": label}

        # --- Atualização de status ---
        ok_count, error_count, no_signal_count = 0, 0, 0
        is_dark = self.main_app.tema_atual == "tech_dark"

        # Paleta por tema
        palette_dark = {
            "ok": "#00FF88",
            "error": "#FF5252",
            "no_signal": "#8E9BAA",
            "pending": "#FFC107",
            "card_bg": "#1E2226",
            "border": "#2D3338",
            "text": "#FFFFFF",
        }
        palette_light = {
            "ok": "#43A047",
            "error": "#E53935",
            "no_signal": "#90A4AE",
            "pending": "#FFB300",
            "card_bg": "#FFFFFF",
            "border": "#D9DEE2",
            "text": "#1A1A1A",
        }
        colors = palette_dark if is_dark else palette_light

        for track_id, status_info in client_status_ref.items():
            if track_id in self.status_widgets:
                w = self.status_widgets[track_id]
                status = status_info.get("status", "N/A")
                message = status_info.get("message", "")
                card_style = f"background-color: {colors['card_bg']}; border: 1px solid {colors['border']}; border-radius: 10px;"

                if status == "OK":
                    color = colors["ok"]
                    msg = f"<b>Latitude:</b> {status_info.get('latitude', 'N/A')}<br>" \
                          f"<b>Longitude:</b> {status_info.get('longitude', 'N/A')}<br>" \
                          f"<b>Data/Hora:</b> {status_info.get('datahora', 'N/A')}"
                    ok_count += 1
                elif status == "ERRO":
                    color = colors["error"]
                    msg = f"<b>ERRO:</b> {message}"
                    error_count += 1
                elif status == "SEM REGISTRO RECENTE":
                    color = colors["no_signal"]
                    msg = f"<i>{message}</i>"
                    no_signal_count += 1
                else:
                    color = colors["pending"]
                    msg = "<i>Aguardando atualização...</i>"
                    no_signal_count += 1

                w["icon"].setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
                w["label"].setText(f"<b>TrackID:</b> {track_id}<br>{msg}")
                w["card"].setStyleSheet(card_style)

        now = datetime.now().strftime("%H:%M:%S")
        self.status_summary_label.setText(
            f"<b>Total: {len(self.current_ids)}</b> | Última atualização: {now}"
        )
        self.update_chart(ok_count, error_count, no_signal_count)

    def update_chart(self, ok, error, no_signal):
        self.chart_canvas.axes.clear()
        is_dark = self.main_app.tema_atual == "tech_dark"
        theme_colors = {
            "ok": "#00FF88" if is_dark else "#43A047",
            "error": "#FF5252" if is_dark else "#E53935",
            "no_signal": "#8E9BAA" if is_dark else "#90A4AE",
        }
        labels, sizes, colors = [], [], []
        if ok > 0:
            labels.append(f"OK ({ok})"); sizes.append(ok); colors.append(theme_colors["ok"])
        if error > 0:
            labels.append(f"Erro ({error})"); sizes.append(error); colors.append(theme_colors["error"])
        if no_signal > 0:
            labels.append(f"Sem Sinal ({no_signal})"); sizes.append(no_signal); colors.append(theme_colors["no_signal"])
        if not sizes:
            sizes, labels, colors = [1], ["Nenhum cliente"], ["#444444" if is_dark else "#CCCCCC"]

        text_color = "#FFFFFF" if is_dark else "#1A1A1A"
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


# --- JANELA PRINCIPAL (APP GUI) ---
class AppGUI(QMainWindow):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self.app_state = load_state()
        self.tema_atual = self.app_state.get("theme", "tech_dark")
        if self.tema_atual not in THEMES:
            self.tema_atual = "tech_dark"
        self.visible_columns = self.app_state.get("visible_columns", COLUNAS[:])
        self.controller = DataController(COLUNAS, ITENS_POR_PAGINA)
        self.exportar = Exportar(self, self.controller)
        self.pagina_atual = 1
        self.workers = []
        self.client_status = {}
        self.is_first_load = True
        self.setWindowTitle("App de Consulta Avançada")
        geometry = self.app_state.get("geometry")
        if geometry and isinstance(geometry, (list, tuple)) and len(geometry) == 4:
            self.setGeometry(*geometry)
        else:
            self.setGeometry(100, 100, 1300, 700)
        self._create_menu()
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        self.container = QStackedWidget()
        self.frames = {
            "Consultas": ConsultaScreen(self.controller, self.api, self),
            "Controle": ControleScreen(self)
        }
        self.container.addWidget(self.frames["Consultas"])
        self.container.addWidget(self.frames["Controle"])
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Bem-vindo!")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        main_layout.addWidget(self.container)
        self.carregar_dados_iniciais()
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.monitor_all_clients)
        self.monitor_timer.start(15000)
        self.update_visible_columns()
        self.aplicar_tema_completo()
        self.setup_shortcuts()

    def _create_menu(self):
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
        prefs_menu = menu_bar.addMenu("Preferências")
        theme_menu = QMenu("Tema", self)
        prefs_menu.addMenu(theme_menu)
        self.dark_action = QAction("Tech Dark", self, checkable=True)
        self.dark_action.triggered.connect(lambda: self.set_theme("tech_dark"))
        self.light_action = QAction("Tech Light", self, checkable=True)
        self.light_action.triggered.connect(lambda: self.set_theme("tech_light"))
        theme_menu.addAction(self.dark_action)
        theme_menu.addAction(self.light_action)

    def closeEvent(self, event):
        header = self.frames["Consultas"].tabela.horizontalHeader()
        widths = [header.sectionSize(i) for i in range(header.count())]
        self.app_state['theme'] = self.tema_atual
        self.app_state['visible_columns'] = self.visible_columns
        self.app_state['geometry'] = self.geometry().getRect()
        self.app_state['column_widths'] = widths
        save_state(self.app_state)
        event.accept()
        
    def setup_shortcuts(self):
        shortcut_refresh = QShortcut(QKeySequence("F5"), self)
        shortcut_refresh.activated.connect(self.refresh_data_async)
        shortcut_filter = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_filter.activated.connect(lambda: self.frames["Consultas"].entry_filtro.setFocus())

    def set_theme(self, theme_name):
        self.tema_atual = theme_name
        self.aplicar_tema_completo()

    def aplicar_tema_completo(self):
        self.setStyleSheet(THEMES[self.tema_atual])
        self.dark_action.setChecked(self.tema_atual == "tech_dark")
        self.light_action.setChecked(self.tema_atual == "tech_light")
        for dialog in self.findChildren(QDialog):
            dialog.setStyleSheet(THEMES[self.tema_atual])
        self.frames["Controle"].update_display()

    def open_column_settings(self):
        dialog = ColumnSettingsDialog(COLUNAS, self.visible_columns, self)
        if dialog.exec():
            self.visible_columns = dialog.get_selected_columns()
            self.update_visible_columns()

    def update_visible_columns(self):
        tabela = self.frames["Consultas"].tabela
        for i, col_name in enumerate(COLUNAS):
            tabela.setColumnHidden(i, col_name not in self.visible_columns)

    def show_frame(self, frame_name):
        self.consultas_action.setChecked(frame_name == "Consultas")
        self.controle_action.setChecked(frame_name == "Controle")
        if frame_name == "Consultas":
            self.container.setCurrentWidget(self.frames["Consultas"])
            self.frames["Controle"].stop_periodic_update()
        elif frame_name == "Controle":
            self.container.setCurrentWidget(self.frames["Controle"])
            self.frames["Controle"].start_periodic_update()

    def show_in_table(self, track_id):
        self.show_frame("Consultas")
        screen = self.frames["Consultas"]
        screen.combo_coluna.setCurrentText("TrackID")
        screen.entry_filtro.setText(str(track_id))
        self.aplicar_filtro()
    
    def monitor_all_clients(self):
        if not self.controller.dados_completos: return
        
        limite_tempo = timedelta(hours=24)
        agora = datetime.now()

        all_data = self.controller.dados_completos
        records_by_trackid = {}
        for record in all_data:
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

            self.client_status[track_id] = status_cliente

        current_ids = set(records_by_trackid.keys())
        for old_id in list(self.client_status.keys()):
            if old_id not in current_ids:
                del self.client_status[old_id]


    def on_worker_finished(self, worker):
        if worker in self.workers:
            self.workers.remove(worker)

    def run_in_thread(self, func, on_finish, on_error, *args, **kwargs):
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
        QMessageBox.critical(self, "Erro de API", error_msg)
        self.gerir_estado_widgets(True)

    def on_task_completed(self):
        self.progress_bar.setVisible(False)
        self.gerir_estado_widgets(True)

    def carregar_dados_iniciais(self):
        self.is_first_load = True
        self.status_bar.showMessage("A carregar dados iniciais...")
        self.run_in_thread(
            self.api.buscar_todos,
            on_finish=self.on_dados_carregados,
            on_error=self.on_task_error,
            force_refresh=True
        )

    def on_dados_carregados(self, dados):
        if dados is None: dados = []
        self.controller.dados_completos = dados
        self.aplicar_filtro()
        self.status_bar.showMessage(f"Dados carregados: {len(dados)} registos.", 5000)
        self.on_task_completed()
        self.monitor_all_clients()
        tabela = self.frames["Consultas"].tabela
        header = tabela.horizontalHeader()
        widths = self.app_state.get("column_widths")
        if not self.is_first_load and widths and len(widths) == header.count():
            for i, width in enumerate(widths):
                header.resizeSection(i, width)
        else:
            tabela.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.is_first_load = False

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
        self.carregar_dados_iniciais()

    def ir_para_pagina(self, numero_pagina):
        self.pagina_atual = numero_pagina
        self.renderizar_dados()
        
    def primeira_pagina(self): self.ir_para_pagina(1)
    def ultima_pagina(self): self.ir_para_pagina(self.controller.total_paginas)
    def pagina_anterior(self): self.ir_para_pagina(self.pagina_atual - 1)
    def proxima_pagina(self): self.ir_para_pagina(self.pagina_atual + 1)
    
    def show_record_details(self, item):
        row_index = item.row()
        id_col_index = -1
        for i, col_name in enumerate(COLUNAS):
            if col_name == "IDMENSAGEM":
                id_col_index = i
                break
        
        if id_col_index != -1:
            record_id = self.frames["Consultas"].tabela.item(row_index, id_col_index).text()
            full_record = self.controller.get_record_by_id(record_id)
            if full_record:
                dialog = RecordDetailDialog(full_record, self)
                dialog.exec()
            
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