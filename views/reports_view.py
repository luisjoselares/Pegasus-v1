from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QMessageBox, QTabWidget, QApplication)
from PyQt6.QtCore import Qt
import os

from controllers.reports_controller import ReportsController
from views.invoice_viewer_dialog import InvoiceViewerDialog

# --- NUEVA IMPORTACIÓN DEL MÓDULO FISCAL ---
from views.fiscal_books_view import FiscalBooksView

class ReportsView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        
        # TÍTULO (Alineado con el estilo general)
        lbl_titulo = QLabel("📊 MÓDULO DE REPORTES Y AUDITORÍA")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #03DAC6; margin-bottom: 10px;")
        layout_principal.addWidget(lbl_titulo)

        # TABS PRINCIPALES (Integrados al modern_style.qss)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { 
                border: 1px solid #333333; 
                background: #1E1E1E; 
                border-radius: 8px; 
            }
            QTabBar::tab { 
                background: #121212; 
                color: #B3B3B3; 
                padding: 10px 20px; 
                font-weight: bold; 
                border-top-left-radius: 8px; 
                border-top-right-radius: 8px;
                border: 1px solid transparent;
            }
            QTabBar::tab:selected { 
                background: #1E1E1E; 
                color: #6200EE; 
                border: 1px solid #333333;
                border-bottom: none;
            }
            QTabBar::tab:hover:!selected {
                color: white;
            }
        """)

        # PESTAÑA 1: REPORTES DE CAJA
        self.tab_caja = QWidget()
        self.init_tab_caja()
        
        # PESTAÑA 2: LIBROS FISCALES
        self.tab_libros = FiscalBooksView()

        # Añadimos las pestañas al contenedor
        self.tabs.addTab(self.tab_caja, "🧾 Reportes Z / X (Caja)")
        self.tabs.addTab(self.tab_libros, "📚 Libros Fiscales")

        layout_principal.addWidget(self.tabs)

    def init_tab_caja(self):
        layout = QVBoxLayout(self.tab_caja)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_info = QLabel("Emisión Rápida de Reportes de Caja")
        lbl_info.setStyleSheet("font-size: 16px; font-weight: bold;") # El color lo hereda del QSS
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # BOTÓN REPORTE X (Color secundario, pero respetando la forma del QSS)
        self.btn_reporte_x = QPushButton("Reporte X (Lectura de Caja)")
        self.btn_reporte_x.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reporte_x.setFixedSize(300, 60)
        self.btn_reporte_x.setStyleSheet("""
            QPushButton { 
                background-color: #03DAC6; 
                color: black; 
                font-size: 16px; 
                font-weight: bold; 
                border-radius: 8px; 
                border: none;
            }
            QPushButton:hover { background-color: #00F0DA; }
        """)
        self.btn_reporte_x.clicked.connect(self.generar_reporte_x)

        # BOTÓN REPORTE Z (Hereda casi todo del QSS corporativo)
        self.btn_reporte_z = QPushButton("Reporte Z (Cierre Fiscal)")
        self.btn_reporte_z.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reporte_z.setFixedSize(300, 60)
        # Solo forzamos el tamaño de fuente y quitamos el borde extra, el color morado ya viene del QSS
        self.btn_reporte_z.setStyleSheet("""
            QPushButton { 
                font-size: 16px; 
                border: none;
            }
        """)
        self.btn_reporte_z.clicked.connect(self.generar_reporte_z)

        layout.addWidget(lbl_info)
        layout.addWidget(self.btn_reporte_x, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.btn_reporte_z, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def generar_reporte_x(self):
        """Busca la caja abierta actualmente y muestra su estado (Lectura Parcial)"""
        sesion_id = ReportsController.obtener_sesion_activa_id()
        if not sesion_id:
            QMessageBox.warning(self, "Aviso", "No hay ninguna caja abierta actualmente para generar el Reporte X.")
            return
        self.abrir_visor_emergente(sesion_id)

    def generar_reporte_z(self):
        """Busca la ÚLTIMA caja que fue cerrada y muestra su reporte definitivo"""
        sesion_id = ReportsController.obtener_ultima_sesion_cerrada_id()
        if not sesion_id:
            QMessageBox.warning(self, "Aviso", "No hay cortes de caja (Reportes Z) previos registrados en el sistema.")
            return
        self.abrir_visor_emergente(sesion_id)

    def abrir_visor_emergente(self, sesion_id):
        datos = ReportsController.obtener_datos_reporte_caja(sesion_id)
        if datos:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            
            try:
                os.makedirs('temp', exist_ok=True)
                ruta_pdf = os.path.abspath(f"temp/reporte_caja_{sesion_id}.pdf")
                
                exito = ReportsController.generar_pdf_ticket(datos, ruta_pdf)
                
                if exito:
                    tipo_reporte = "Z" if datos['sesion']['estado'] == 'CERRADA' else "X"
                    
                    visor = InvoiceViewerDialog(ruta_pdf, parent=self)
                    visor.setWindowTitle(f"Visor de Reporte {tipo_reporte} - Sesión {sesion_id}")
                    visor.setWindowModality(Qt.WindowModality.ApplicationModal)
                    
                    QApplication.restoreOverrideCursor()
                    visor.exec()
                else:
                    QApplication.restoreOverrideCursor()
                    QMessageBox.critical(self, "Error", "No se pudo generar el PDF del reporte.")
                    
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, "Error", f"Ocurrió un error inesperado:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Error", "No se pudieron cargar los datos de este reporte.")
            
    def cargar_lista_sesiones(self):
        pass