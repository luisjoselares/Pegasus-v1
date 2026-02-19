from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from PyQt6.QtCore import Qt
from views.delivery_note_view import DeliveryNoteView
from views.returns_view import ReturnsView

class DocumentManagementView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # TÍTULO PRINCIPAL
        lbl_titulo = QLabel("📄 GESTIÓN DE DOCUMENTOS COMERCIALES")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #03DAC6; margin: 10px;")
        layout.addWidget(lbl_titulo)

        # CONTENEDOR DE PESTAÑAS
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333; background: #121212; border-radius: 8px; }
            QTabBar::tab { 
                background: #1E1E1E; color: #888; padding: 12px 25px; 
                margin-right: 4px; border-top-left-radius: 6px; border-top-right-radius: 6px; 
                font-weight: bold;
            }
            QTabBar::tab:selected { background: #121212; color: #6200EE; border-bottom: 2px solid #6200EE; }
            QTabBar::tab:hover { background: #252525; color: white; }
        """)

        # INSTANCIAS DE LAS VISTAS
        self.vista_notas = DeliveryNoteView()
        self.vista_devoluciones = ReturnsView()

        # AGREGAR PESTAÑAS
        self.tabs.addTab(self.vista_notas, "🚚 Emisión de Notas de Entrega")
        self.tabs.addTab(self.vista_devoluciones, "⏪ Devoluciones / Notas de Crédito")

        layout.addWidget(self.tabs)