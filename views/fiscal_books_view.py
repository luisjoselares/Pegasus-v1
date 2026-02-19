import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QComboBox, QSpinBox, 
                             QFileDialog, QMessageBox, QGridLayout, QApplication)
from PyQt6.QtCore import Qt
from datetime import datetime
from controllers.fiscal_books_controller import FiscalBooksController
from views.invoice_viewer_dialog import InvoiceViewerDialog

class FiscalBooksView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # --- ENCABEZADO ---
        lbl_titulo = QLabel("📚 EXPORTACIÓN DE LIBROS FISCALES (SENIAT)")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: 900; color: #03DAC6;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)
        
        lbl_sub = QLabel("Genere los reportes contables obligatorios expresados en Bolívares (Bs.)")
        lbl_sub.setStyleSheet("font-size: 14px; color: #AAAAAA;")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_sub)
        
        layout.addSpacing(20)

        # --- PANEL CENTRAL ---
        frame_central = QFrame()
        frame_central.setStyleSheet("""
            QFrame { background-color: #1E1E1E; border-radius: 12px; border: 1px solid #333; }
            QLabel { border: none; font-size: 15px; font-weight: bold; }
        """)
        l_central = QVBoxLayout(frame_central)
        l_central.setContentsMargins(40, 40, 40, 40)
        l_central.setSpacing(30)
        
        # 1. Selector de Período
        frame_periodo = QWidget()
        frame_periodo.setStyleSheet("border: none;")
        l_periodo = QHBoxLayout(frame_periodo)
        
        self.cmb_mes = QComboBox()
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.cmb_mes.addItems(meses)
        self.cmb_mes.setCurrentIndex(datetime.now().month - 1)
        self.cmb_mes.setFixedSize(150, 40)
        self.cmb_mes.setStyleSheet("QComboBox { background-color: #2D2D2D; color: white; border: 1px solid #555; border-radius: 5px; padding-left: 10px; }")
        
        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(2020, 2100)
        self.spin_anio.setValue(datetime.now().year)
        self.spin_anio.setFixedSize(100, 40)
        self.spin_anio.setStyleSheet("QSpinBox { background-color: #2D2D2D; color: white; border: 1px solid #555; border-radius: 5px; padding-left: 10px; }")
        
        l_periodo.addStretch()
        l_periodo.addWidget(QLabel("📅 Mes:"))
        l_periodo.addWidget(self.cmb_mes)
        l_periodo.addSpacing(20)
        l_periodo.addWidget(QLabel("🏢 Año:"))
        l_periodo.addWidget(self.spin_anio)
        l_periodo.addStretch()
        
        l_central.addWidget(frame_periodo)
        
        # 2. Botones de Exportación
        l_botones = QGridLayout()
        l_botones.setSpacing(20)
        
        self.btn_excel_ventas = QPushButton("📊 Descargar Libro de Ventas (EXCEL)")
        self.btn_excel_ventas.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_excel_ventas.setFixedHeight(60)
        self.btn_excel_ventas.setStyleSheet("""
            QPushButton { background-color: #1E88E5; color: white; font-weight: bold; font-size: 14px; border-radius: 8px; }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.btn_excel_ventas.clicked.connect(self.exportar_ventas_excel)
        
        self.btn_pdf_ventas = QPushButton("🖨️ Imprimir Libro de Ventas (PDF Oficio)")
        self.btn_pdf_ventas.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pdf_ventas.setFixedHeight(60)
        self.btn_pdf_ventas.setStyleSheet("""
            QPushButton { background-color: #E53935; color: white; font-weight: bold; font-size: 14px; border-radius: 8px; }
            QPushButton:hover { background-color: #D32F2F; }
        """)
        self.btn_pdf_ventas.clicked.connect(self.exportar_ventas_pdf)
        
        l_botones.addWidget(QLabel("► LIBRO DE VENTAS:"), 0, 0, 1, 2)
        l_botones.addWidget(self.btn_excel_ventas, 1, 0)
        l_botones.addWidget(self.btn_pdf_ventas, 1, 1)
        
        l_botones.addWidget(QLabel("► LIBRO DE COMPRAS (Próximamente):"), 2, 0, 1, 2)
        btn_compras_dummy = QPushButton("🔒 Bloqueado")
        btn_compras_dummy.setFixedHeight(50)
        btn_compras_dummy.setStyleSheet("background-color: #333; color: #777; border-radius: 8px; font-weight: bold;")
        l_botones.addWidget(btn_compras_dummy, 3, 0, 1, 2)
        
        l_central.addLayout(l_botones)
        
        layout.addWidget(frame_central)
        layout.addStretch()

    def exportar_ventas_excel(self):
        mes = self.cmb_mes.currentIndex() + 1
        anio = self.spin_anio.value()
        
        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self, 
            "Guardar Libro de Ventas Excel", 
            f"Libro_Ventas_{mes:02d}_{anio}.xlsx", 
            "Excel Files (*.xlsx)"
        )
        
        if ruta_archivo:
            exito, msg = FiscalBooksController.generar_excel_libro_ventas(mes, anio, ruta_archivo)
            if exito:
                QMessageBox.information(self, "Éxito", msg)
            else:
                QMessageBox.critical(self, "Error", msg)

    def exportar_ventas_pdf(self):
        mes = self.cmb_mes.currentIndex() + 1
        anio = self.spin_anio.value()
        
        os.makedirs('temp', exist_ok=True)
        ruta_pdf = os.path.abspath(f"temp/libro_ventas_{mes:02d}_{anio}.pdf")
        
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        exito, msg = FiscalBooksController.generar_pdf_libro_ventas(mes, anio, ruta_pdf)
        QApplication.restoreOverrideCursor()
        
        if exito:
            # Reutilizamos tu visor oscuro para mantener la inmersión del usuario
            visor = InvoiceViewerDialog(ruta_pdf, parent=self.window())
            visor.setWindowTitle(f"Libro de Ventas Fiscal - {self.cmb_mes.currentText()} {anio}")
            visor.setWindowModality(Qt.WindowModality.ApplicationModal)
            visor.exec()
        else:
            QMessageBox.critical(self, "Error", msg)