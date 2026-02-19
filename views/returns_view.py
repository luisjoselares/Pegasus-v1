from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTableWidget, QTableWidgetItem, 
                             QPushButton, QFrame, QHeaderView, QMessageBox, 
                             QComboBox, QDoubleSpinBox, QApplication)
from PyQt6.QtCore import Qt
from controllers.returns_controller import ReturnsController
from views.invoice_viewer_dialog import InvoiceViewerDialog
import os

class ReturnsView(QWidget):
    def __init__(self):
        super().__init__()
        self.factura_data = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- ENCABEZADO ---
        header = QHBoxLayout()
        self.lbl_titulo = QLabel("DEVOLUCIONES Y NOTAS DE CRÉDITO")
        self.lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #6200EE;") 
        
        self.btn_procesar = QPushButton("📝 PROCESAR DEVOLUCIÓN")
        self.btn_procesar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_procesar.setEnabled(False)
        self.btn_procesar.setStyleSheet("""
            QPushButton {
                background-color: #6200EE; color: white; border-radius: 5px; 
                padding: 10px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #7722FF; }
            QPushButton:disabled { background-color: #333; color: #777; }
        """)
        self.btn_procesar.clicked.connect(self.procesar_devolucion)
        
        header.addWidget(self.lbl_titulo)
        header.addStretch()
        header.addWidget(self.btn_procesar)
        layout.addLayout(header)

        # --- BARRA DE BÚSQUEDA ---
        search_frame = QFrame()
        search_frame.setStyleSheet("background: #1E1E1E; border-radius: 8px;")
        search_layout = QHBoxLayout(search_frame)
        
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Ingrese número de factura (Ej: FAC-00000001 o 1)...")
        self.txt_buscar.setStyleSheet("border: none; background: transparent; color: white; padding: 8px; font-size: 14px;")
        self.txt_buscar.returnPressed.connect(self.buscar_factura)
        
        search_layout.addWidget(self.txt_buscar)
        layout.addWidget(search_frame)

        # --- INFO DEL CLIENTE ---
        self.lbl_info_factura = QLabel("Esperando factura...")
        self.lbl_info_factura.setStyleSheet("color: #B3B3B3; font-size: 13px; margin-left: 5px;")
        layout.addWidget(self.lbl_info_factura)

        # --- TABLA DE ITEMS ---
        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels([
            "CÓDIGO", "DESCRIPCIÓN", "CANT. DISPONIBLE", "A DEVOLVER", "P. UNIT BASE ($)", "REEMBOLSO INC. IVA ($)"
        ])
        
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header_view = self.tabla.horizontalHeader()
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 

        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: #121212; color: white;
                gridline-color: #222; border: none; outline: none;
            }
            QTableWidget::item:selected {
                background-color: #1E1E1E; color: #6200EE;
                border-bottom: 2px solid #6200EE;
            }
            QHeaderView::section {
                background-color: #1E1E1E; color: #B3B3B3;
                padding: 10px; border: none; font-weight: bold;
            }
        """)
        layout.addWidget(self.tabla)

        # --- PANEL DE TOTALES ---
        footer_frame = QFrame()
        footer_frame.setStyleSheet("background: #1E1E1E; border-radius: 8px;")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(15, 10, 15, 10)
        
        self.cmb_metodo = QComboBox()
        self.cmb_metodo.addItems([
            "Saldo a Favor", 
            "Efectivo USD", 
            "Efectivo Bs", 
            "Efectivo Pesos (COP)",
            "Transferencia"
        ])
        self.cmb_metodo.setStyleSheet("""
            QComboBox { background-color: #2D2D2D; color: white; border-radius: 4px; padding: 5px; border: 1px solid #444; font-weight: bold; }
        """)
        
        self.lbl_total_reembolso = QLabel("TOTAL REEMBOLSO: $ 0.00")
        self.lbl_total_reembolso.setStyleSheet("color: #03DAC6; font-size: 18px; font-weight: bold;")
        
        footer_layout.addWidget(QLabel("<b>MÉTODO DE PAGO:</b>"))
        footer_layout.addWidget(self.cmb_metodo)
        footer_layout.addStretch()
        footer_layout.addWidget(self.lbl_total_reembolso)
        
        layout.addWidget(footer_frame)

    def buscar_factura(self):
        nro = self.txt_buscar.text().strip()
        if not nro: return
        
        res, msg = ReturnsController.buscar_factura(nro)
        if not res:
            QMessageBox.warning(self, "Aviso", msg)
            return
            
        self.factura_data = res
        f = res['factura']
        self.lbl_info_factura.setText(f"✅ CLIENTE: {f['nombre']} | CI/RIF: {f['cedula_rif']} | FECHA: {f['fecha']} | TOTAL FAC: ${f['total_usd']:.2f}")
        
        self.cargar_tabla(res['detalles'])
        self.btn_procesar.setEnabled(True)

    def cargar_tabla(self, detalles):
        self.tabla.setRowCount(0)
        for i, d in enumerate(detalles):
            self.tabla.insertRow(i)
            
            # CALCULAMOS LA CANTIDAD QUE REALMENTE ESTÁ DISPONIBLE PARA DEVOLVER
            cant_disponible = d['cantidad'] - d['cantidad_devuelta']
            
            marcador = " (E)" if d['es_exento'] else " (+16%)"
            
            self.tabla.setItem(i, 0, QTableWidgetItem(d['codigo_interno']))
            self.tabla.setItem(i, 1, QTableWidgetItem(d['descripcion'] + marcador))
            
            # Mostramos visualmente el disponible versus lo que compró originalmente
            item_cant = QTableWidgetItem(f"{cant_disponible:.2f} (de {d['cantidad']:.0f})")
            item_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Si ya no queda saldo de ese producto, lo pintamos de gris para advertir al usuario
            if cant_disponible <= 0:
                item_cant.setForeground(Qt.GlobalColor.darkGray)
            
            self.tabla.setItem(i, 2, item_cant)
            
            # Configuramos el SpinBox con el límite del disponible actual
            spin = QDoubleSpinBox()
            spin.setRange(0, cant_disponible)
            spin.setValue(0)
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if cant_disponible <= 0:
                spin.setEnabled(False)
                spin.setStyleSheet("background: #1A1A1A; color: #555; border: 1px solid #333; border-radius: 4px;")
            else:
                spin.setStyleSheet("background: #2D2D2D; color: white; border: 1px solid #444; border-radius: 4px; font-weight:bold;")
                
            spin.valueChanged.connect(self.recalcular_totales)
            self.tabla.setCellWidget(i, 3, spin)
            
            self.tabla.setItem(i, 4, QTableWidgetItem(f"{d['precio_unitario_usd']:.2f}"))
            self.tabla.setItem(i, 5, QTableWidgetItem("0.00"))

    def recalcular_totales(self):
        total = 0.0
        for i in range(self.tabla.rowCount()):
            cant = self.tabla.cellWidget(i, 3).value()
            det = self.factura_data['detalles'][i]
            
            precio_base = det['precio_unitario_usd']
            iva = 0.0 if det['es_exento'] else (precio_base * 0.16)
            precio_con_iva = precio_base + iva
            
            subt = cant * precio_con_iva
            
            self.tabla.setItem(i, 5, QTableWidgetItem(f"{subt:.2f}"))
            total += subt
            
        self.lbl_total_reembolso.setText(f"TOTAL REEMBOLSO: $ {total:.2f}")

    def procesar_devolucion(self):
        items_devolver = []
        total_reembolso = 0.0
        
        for i in range(self.tabla.rowCount()):
            cant = self.tabla.cellWidget(i, 3).value()
            if cant > 0:
                det = self.factura_data['detalles'][i]
                precio_base = det['precio_unitario_usd']
                iva = 0.0 if det['es_exento'] else (precio_base * 0.16)
                
                items_devolver.append({
                    'detalle_id': det['detalle_id'], # <--- PASAMOS EL ID PARA ACTUALIZAR EL HISTORIAL
                    'producto_id': det['producto_id'],
                    'cantidad': cant,
                    'precio_usd': precio_base,
                    'es_exento': det['es_exento']
                })
                total_reembolso += (cant * (precio_base + iva))
        
        if not items_devolver:
            QMessageBox.warning(self, "Aviso", "No ha seleccionado cantidades para devolver.")
            return

        if QMessageBox.question(self, "Confirmar", f"¿Emitir Nota de Crédito por $ {total_reembolso:.2f}?") == QMessageBox.StandardButton.Yes:
            exito, nro_nc = ReturnsController.procesar_devolucion(
                self.factura_data['factura']['nro_documento'],
                items_devolver,
                self.cmb_metodo.currentText(),
                total_reembolso
            )
            
            if exito:
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                os.makedirs('temp', exist_ok=True)
                ruta_pdf = os.path.abspath(f"temp/nota_credito_{nro_nc}.pdf")
                if ReturnsController.generar_pdf_nota_credito(nro_nc, ruta_pdf):
                    QApplication.restoreOverrideCursor()
                    visor = InvoiceViewerDialog(ruta_pdf, parent=self.window())
                    visor.exec()
                else:
                    QApplication.restoreOverrideCursor()
                
                QMessageBox.information(self, "Éxito", "Operación procesada correctamente.")
                self.limpiar()
            else:
                QMessageBox.critical(self, "Error", nro_nc)

    def limpiar(self):
        self.factura_data = None
        self.tabla.setRowCount(0)
        self.txt_buscar.clear()
        self.lbl_info_factura.setText("Esperando factura...")
        self.lbl_total_reembolso.setText("TOTAL REEMBOLSO: $ 0.00")
        self.btn_procesar.setEnabled(False)