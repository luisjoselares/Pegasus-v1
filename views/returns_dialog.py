from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, 
                             QFrame, QSpinBox, QCheckBox, QComboBox, QWidget)
from PyQt6.QtCore import Qt
from controllers.returns_controller import ReturnsController

class ReturnsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Procesar Devolución / Nota de Crédito")
        self.setFixedSize(700, 500)
        self.setStyleSheet("background-color: #1E1E1E; color: white;")
        
        self.factura_actual = None
        self.items_factura = []
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # --- BUSCADOR ---
        frame_search = QFrame()
        frame_search.setStyleSheet("background: #2D2D2D; border-radius: 5px; padding: 5px;")
        l_search = QHBoxLayout(frame_search)
        
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Nro. Factura (Ej: 00000001)")
        self.txt_buscar.setStyleSheet("background: #121212; border: 1px solid #444; padding: 5px; color: white;")
        self.txt_buscar.returnPressed.connect(self.buscar_factura)
        
        btn_buscar = QPushButton("🔍 BUSCAR")
        btn_buscar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_buscar.setStyleSheet("background-color: #6200EE; color: white; padding: 5px 15px; border-radius: 3px; font-weight: bold;")
        btn_buscar.clicked.connect(self.buscar_factura)
        
        l_search.addWidget(QLabel("Documento:"))
        l_search.addWidget(self.txt_buscar)
        l_search.addWidget(btn_buscar)
        layout.addWidget(frame_search)

        # Info Cliente
        self.lbl_info = QLabel("Ingrese número de factura para comenzar...")
        self.lbl_info.setStyleSheet("color: #AAA; font-size: 13px; margin: 5px 0;")
        layout.addWidget(self.lbl_info)

        # --- TABLA ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["", "CÓDIGO", "DESCRIPCIÓN", "COMPRADO", "PRECIO", "DEVOLVER"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla.setStyleSheet("""
            QTableWidget { background-color: #121212; border: none; gridline-color: #333; outline: 0; }
            QHeaderView::section { background-color: #2D2D2D; padding: 4px; border: 1px solid #333; }
        """)
        layout.addWidget(self.tabla)

        # --- PIE DE PÁGINA ---
        frame_footer = QFrame()
        l_footer = QHBoxLayout(frame_footer)
        
        self.combo_metodo = QComboBox()
        self.combo_metodo.addItems(["EFECTIVO", "WALLET"])
        self.combo_metodo.setStyleSheet("background: #333; padding: 5px;")
        
        self.txt_motivo = QLineEdit()
        self.txt_motivo.setPlaceholderText("Motivo de la devolución...")
        self.txt_motivo.setStyleSheet("background: #333; border: 1px solid #555; padding: 5px;")
        
        btn_procesar = QPushButton("CONFIRMAR DEVOLUCIÓN")
        btn_procesar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_procesar.setStyleSheet("background-color: #CF6679; color: black; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn_procesar.clicked.connect(self.procesar)
        
        l_footer.addWidget(QLabel("Reembolso:"))
        l_footer.addWidget(self.combo_metodo)
        l_footer.addWidget(QLabel("Motivo:"))
        l_footer.addWidget(self.txt_motivo)
        l_footer.addWidget(btn_procesar)
        
        layout.addWidget(frame_footer)

    def buscar_factura(self):
        nro = self.txt_buscar.text().strip()
        if not nro: return
        
        factura = ReturnsController.buscar_factura(nro)
        if factura:
            self.factura_actual = factura
            self.lbl_info.setText(f"📄 FACTURA: {factura['nro_documento']} | 👤 {factura['cliente']} | 📅 {factura['fecha']}")
            self.lbl_info.setStyleSheet("color: #03DAC6; font-weight: bold;")
            
            items = ReturnsController.obtener_items_factura(factura['id'])
            self.items_factura = items
            self.cargar_tabla(items)
        else:
            QMessageBox.warning(self, "Error", "Factura no encontrada.")
            self.lbl_info.setText("Factura no encontrada.")

    def cargar_tabla(self, items):
        self.tabla.setRowCount(0)
        for i, item in enumerate(items):
            self.tabla.insertRow(i)
            
            # Checkbox
            chk_w = QWidget(); chk_l = QHBoxLayout(chk_w); chk_l.setContentsMargins(0,0,0,0); chk_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chk = QCheckBox(); chk_l.addWidget(chk)
            self.tabla.setCellWidget(i, 0, chk_w)
            
            self.tabla.setItem(i, 1, QTableWidgetItem(item['codigo_interno']))
            self.tabla.setItem(i, 2, QTableWidgetItem(item['descripcion']))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(item['cantidad'])))
            self.tabla.setItem(i, 4, QTableWidgetItem(f"${item['precio_unitario_usd']:.2f}"))
            
            spin = QSpinBox(); spin.setRange(1, int(item['cantidad'])); spin.setValue(int(item['cantidad']))
            spin.setStyleSheet("background: #333; color: white;")
            self.tabla.setCellWidget(i, 5, spin)

    def procesar(self):
        if not self.factura_actual: return
        motivo = self.txt_motivo.text().strip()
        if not motivo:
            QMessageBox.warning(self, "Falta dato", "Ingrese el motivo.")
            return

        items_dev = []
        for r in range(self.tabla.rowCount()):
            # Obtener checkbox desde el widget contenedor
            widget = self.tabla.cellWidget(r, 0)
            chk = widget.findChild(QCheckBox)
            
            if chk.isChecked():
                cant = self.tabla.cellWidget(r, 5).value()
                orig = self.items_factura[r]
                items_dev.append({'id_prod': orig['producto_id'], 'cantidad': cant, 'precio': orig['precio_unitario_usd']})

        if not items_dev:
            QMessageBox.warning(self, "Error", "Seleccione productos.")
            return

        resp = QMessageBox.question(self, "Confirmar", "¿Generar Nota de Crédito?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            ok, msg = ReturnsController.procesar_devolucion(self.factura_actual, items_dev, motivo, self.combo_metodo.currentText())
            if ok:
                QMessageBox.information(self, "Éxito", msg)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", msg)