import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QFrame, QPushButton, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt, QSize

# --- GESTOR DE ICONOS PROFESIONALES ---
try:
    import qtawesome as qta
    HAS_QTA = True
except ImportError:
    HAS_QTA = False
    print("Aviso: QtAwesome no está instalado. Usando emojis de respaldo. (pip install qtawesome)")

# --- IMPORTACIÓN DE VISTAS ---
from views.inventory_view import InventoryView
from views.logistics_view import LogisticsView
from views.customer_view import CustomerView
from views.config_view import ConfigView
from views.sales_view import SalesView
from views.dashboard_view import DashboardView 
from views.document_management_view import DocumentManagementView 
from views.reports_view import ReportsView

class MainWindow(QMainWindow):
    def __init__(self, usuario_actual="Admin"):
        super().__init__()
        self.setWindowTitle(f"Pegasus Fisco - {usuario_actual}")
        self.setMinimumSize(1100, 700)
        self.showMaximized()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout_principal = QHBoxLayout(self.central_widget)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        self.init_sidebar()
        self.init_content_area()
        self.ir_a_dashboard()

    def crear_boton(self, texto, icono_qta):
        btn = QPushButton(f"  {texto}")
        if HAS_QTA:
            btn.setIcon(qta.icon(icono_qta, color='#B3B3B3'))
            btn.setIconSize(QSize(20, 20))
        else:
            btn.setText(f"  >  {texto}") # Respaldo por si no está la librería
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def init_sidebar(self):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setStyleSheet("#sidebar { background-color: #121212; border-right: 1px solid #222222; }")
        
        layout_sidebar = QVBoxLayout(self.sidebar)
        layout_sidebar.setContentsMargins(0, 20, 0, 20)
        layout_sidebar.setSpacing(5)
        
        lbl_logo = QLabel("PEGASUS FISCO")
        lbl_logo.setStyleSheet("color: #6200EE; font-size: 20px; font-weight: 900; margin-bottom: 20px;")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_sidebar.addWidget(lbl_logo)

        # CONFIGURACIÓN DE NAVEGACIÓN (Orden Original)
        config = [
            ("btn_inicio", "Dashboard", "fa5s.chart-pie"),
            ("btn_ventas", "Facturación (POS)", "fa5s.cash-register"),
            ("btn_gestion", "Gestión de Docs", "fa5s.folder-open"), 
            ("btn_inventario", "Inventario", "fa5s.boxes"),
            ("btn_clientes", "Clientes", "fa5s.users"),
            ("btn_logistica", "Logística", "fa5s.truck-loading"),
            ("btn_reportes", "Auditoría y Libros", "fa5s.file-invoice-dollar"),
            ("btn_config", "Configuración", "fa5s.cogs")
        ]

        self.lista_botones = []
        self.iconos_ref = []

        for attr, texto, icono in config:
            btn = self.crear_boton(texto, icono)
            setattr(self, attr, btn)
            self.lista_botones.append(btn)
            self.iconos_ref.append(icono)
            layout_sidebar.addWidget(btn)

        self.btn_inicio.clicked.connect(self.ir_a_dashboard)
        self.btn_ventas.clicked.connect(self.ir_a_ventas)
        self.btn_gestion.clicked.connect(self.ir_a_gestion)
        self.btn_inventario.clicked.connect(self.ir_a_inventario)
        self.btn_clientes.clicked.connect(self.ir_a_clientes)
        self.btn_logistica.clicked.connect(self.ir_a_logistica)
        self.btn_reportes.clicked.connect(self.ir_a_reportes)
        self.btn_config.clicked.connect(self.ir_a_configuracion)

        layout_sidebar.addStretch()
        
        btn_salir = QPushButton("  Cerrar Sesión")
        if HAS_QTA:
            btn_salir.setIcon(qta.icon('fa5s.power-off', color='#CF6679'))
            btn_salir.setIconSize(QSize(20, 20))
        btn_salir.setStyleSheet("QPushButton { outline: none; color: #CF6679; border: none; text-align: left; padding: 15px 20px; font-size: 14px; font-weight: bold; background: transparent; }")
        btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salir.clicked.connect(self.close)
        layout_sidebar.addWidget(btn_salir)

        self.layout_principal.addWidget(self.sidebar)

    def init_content_area(self):
        self.stack = QStackedWidget()
        
        self.vista_dashboard = DashboardView() 
        self.vista_pos = SalesView()
        self.vista_gestion = DocumentManagementView()
        self.vista_inventario = InventoryView()
        self.vista_clientes = CustomerView()
        self.vista_logistica = LogisticsView(self)
        self.vista_reportes = ReportsView()
        self.vista_config = ConfigView() 

        self.stack.addWidget(self.vista_dashboard)  # 0
        self.stack.addWidget(self.vista_pos)        # 1
        self.stack.addWidget(self.vista_gestion)    # 2 
        self.stack.addWidget(self.vista_inventario) # 3
        self.stack.addWidget(self.vista_clientes)   # 4
        self.stack.addWidget(self.vista_logistica)  # 5
        self.stack.addWidget(self.vista_reportes)   # 6
        self.stack.addWidget(self.vista_config)     # 7

        self.layout_principal.addWidget(self.stack)

    def ir_a_dashboard(self): self.cambiar_pantalla(0, self.btn_inicio)
    def ir_a_ventas(self): 
        self.vista_pos.txt_buscar.setFocus()
        self.cambiar_pantalla(1, self.btn_ventas)
    def ir_a_gestion(self): self.cambiar_pantalla(2, self.btn_gestion)
    def ir_a_inventario(self): 
        self.vista_inventario.cargar_datos()
        self.cambiar_pantalla(3, self.btn_inventario)
    def ir_a_clientes(self): 
        self.vista_clientes.cargar_datos()
        self.cambiar_pantalla(4, self.btn_clientes)
    def ir_a_logistica(self): 
        self.vista_logistica.actualizar_tabla()
        self.cambiar_pantalla(5, self.btn_logistica)
    def ir_a_reportes(self): 
        self.vista_reportes.cargar_lista_sesiones()
        self.cambiar_pantalla(6, self.btn_reportes)
    def ir_a_configuracion(self): 
        self.vista_config.cargar_datos_actuales()
        self.cambiar_pantalla(7, self.btn_config)

    def cambiar_pantalla(self, indice, boton_activo):
        self.stack.setCurrentIndex(indice)
        
        # Estilo base INACTIVO (Con outline: none; para matar el recuadro gris)
        for i, btn in enumerate(self.lista_botones):
            btn.setStyleSheet("""
                QPushButton { 
                    outline: none; 
                    background-color: transparent; 
                    color: #B3B3B3; 
                    text-align: left; 
                    padding: 15px 20px; 
                    border: none; 
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #1E1E1E; color: #6200EE; }
            """)
            if HAS_QTA: btn.setIcon(qta.icon(self.iconos_ref[i], color='#B3B3B3'))

        # Estilo ACTIVO
        boton_activo.setStyleSheet("""
            QPushButton {
                outline: none;
                color: #6200EE; 
                font-weight: bold; 
                background-color: #1E1E1E; 
                border-left: 5px solid #6200EE; 
                text-align: left; 
                padding: 15px 20px; 
                font-size: 14px;
            }
        """)
        if HAS_QTA:
            idx = self.lista_botones.index(boton_activo)
            boton_activo.setIcon(qta.icon(self.iconos_ref[idx], color='#6200EE'))