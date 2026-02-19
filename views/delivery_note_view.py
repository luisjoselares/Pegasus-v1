from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTableWidget, QTableWidgetItem, 
                             QPushButton, QFrame, QHeaderView, QMessageBox, 
                             QCompleter, QInputDialog, QAbstractItemView, QApplication,
                             QGridLayout)
from PyQt6.QtCore import Qt
from controllers.inventory_controller import InventoryController
from controllers.sales_controller import SalesController
from controllers.master_data_controller import MasterDataController
from controllers.config_controller import ConfigController
from controllers.printer_controller import PrinterController
from controllers.customer_controller import CustomerController
from controllers.cash_controller import CashController
from views.customer_dialog import CustomerDialog
from views.invoice_viewer_dialog import InvoiceViewerDialog
from views.payment_dialog import PaymentDialog

class DeliveryNoteView(QWidget):
    def __init__(self):
        super().__init__()
        self.carrito = []
        self.id_cliente_actual = None
        self.prods_cache = []
        
        self.tasa_bcv = 1.0
        self.tasa_cop = 1.0
        
        self.init_ui()
        self.configurar_buscador()
        self.actualizar_tasas()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QHBoxLayout()
        lbl_titulo = QLabel("EMISIÓN DE NOTAS DE ENTREGA")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #6200EE;") 
        header.addWidget(lbl_titulo)
        header.addStretch()
        layout.addLayout(header)

        frame_top = QFrame()
        frame_top.setStyleSheet("background: #1E1E1E; border-radius: 8px;")
        h_layout = QHBoxLayout(frame_top)
        h_layout.setContentsMargins(15, 15, 15, 15)
        
        self.txt_cliente = QLineEdit()
        self.txt_cliente.setPlaceholderText("🔍 Cédula/RIF Cliente")
        self.txt_cliente.setFixedWidth(180)
        self.txt_cliente.setStyleSheet("background: #2D2D2D; color: white; padding: 8px; border: 1px solid #444; border-radius: 5px;")
        self.txt_cliente.returnPressed.connect(self.buscar_cliente) 
        
        self.lbl_nombre_cliente = QLabel("CONSUMIDOR FINAL")
        self.lbl_nombre_cliente.setStyleSheet("color: #03DAC6; font-weight: bold; font-size: 14px; margin-left: 10px;")
        
        self.txt_buscar_prod = QLineEdit()
        self.txt_buscar_prod.setPlaceholderText("🔍 Buscar producto por nombre o código...")
        self.txt_buscar_prod.setStyleSheet("background: #2D2D2D; color: white; padding: 8px; border: 1px solid #444; border-radius: 5px;")
        
        h_layout.addWidget(self.txt_cliente)
        h_layout.addWidget(self.lbl_nombre_cliente)
        h_layout.addSpacing(40) 
        h_layout.addWidget(self.txt_buscar_prod, 1) 
        layout.addWidget(frame_top)

        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels(["CÓDIGO", "DESCRIPCIÓN", "CANT", "PRECIO ($)", "Bs", "COP", "SUBTOTAL ($)", "ACCIÓN"])
        
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
        self.tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)   
        self.tabla.setColumnWidth(7, 80)
        
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.tabla.setStyleSheet("""
            QTableWidget { background-color: #121212; color: white; gridline-color: #222; border: none; outline: none; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #1E1E1E; color: #6200EE; border-bottom: 2px solid #6200EE; }
            QHeaderView::section { background-color: #1E1E1E; color: #B3B3B3; padding: 10px; border: none; font-weight: bold; }
        """)
        layout.addWidget(self.tabla)

        layout_footer = QHBoxLayout()
        
        self.frame_totales = QFrame()
        self.frame_totales.setStyleSheet("background: transparent;")
        l_totales = QVBoxLayout(self.frame_totales)
        l_totales.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_total_usd = QLabel("TOTAL COBRAR: $ 0.00")
        self.lbl_total_usd.setStyleSheet("color: #03DAC6; font-size: 22px; font-weight: bold;")
        self.lbl_total_bs = QLabel(f"Bs: 0.00 (Tasa: {self.tasa_bcv})")
        self.lbl_total_bs.setStyleSheet("color: #AAA; font-size: 14px;")
        self.lbl_total_cop = QLabel(f"COP: 0 (Tasa: {self.tasa_cop})")
        self.lbl_total_cop.setStyleSheet("color: #AAA; font-size: 14px;")
        
        l_totales.addWidget(self.lbl_total_usd)
        l_totales.addWidget(self.lbl_total_bs)
        l_totales.addWidget(self.lbl_total_cop)
        
        layout_footer.addWidget(self.frame_totales)
        layout_footer.addStretch()
        
        btn_generar = QPushButton("🖨️  COBRAR NOTA DE ENTREGA")
        btn_generar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_generar.setFixedSize(280, 60)
        btn_generar.setStyleSheet("""
            QPushButton { background-color: #6200EE; color: white; font-weight: bold; font-size: 15px; border-radius: 8px; }
            QPushButton:hover { background-color: #7722FF; }
        """)
        btn_generar.clicked.connect(self.emitir_nota)
        
        layout_footer.addWidget(btn_generar)
        layout.addLayout(layout_footer)

    def actualizar_tasas(self):
        config = ConfigController.obtener_configuracion()
        if config:
            self.tasa_bcv = config['tasa_bcv']
            self.tasa_cop = config['tasa_cop']
            self.lbl_total_bs.setText(f"Bs: 0.00 (Tasa: {self.tasa_bcv})")
            self.lbl_total_cop.setText(f"COP: 0 (Tasa: {self.tasa_cop:,.0f})")

    def configurar_buscador(self):
        self.prods_cache = InventoryController.obtener_todos()
        nombres = [f"{p['codigo']} | {p['descripcion']}" for p in self.prods_cache]
        completer = QCompleter(nombres, self)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        popup = completer.popup()
        popup.setStyleSheet("QAbstractItemView { background-color: #2D2D2D; color: white; selection-background-color: #6200EE; selection-color: white; border: 1px solid #444; } QScrollBar:vertical { background: #2D2D2D; width: 10px; }")
        self.txt_buscar_prod.setCompleter(completer)
        completer.activated.connect(self.agregar_producto)

    def buscar_cliente(self):
        cedula_cruda = self.txt_cliente.text().strip()
        
        # Si vació la caja, regresamos a Consumidor Final
        if not cedula_cruda: 
            self.txt_cliente.clear()
            self.id_cliente_actual = 1
            self.lbl_nombre_cliente.setText("CONSUMIDOR FINAL")
            return
            
        cedula_limpia = CustomerController.normalizar_cedula(cedula_cruda)
        
        # Consultar la Base de Datos
        cliente = MasterDataController.buscar_cliente_por_cedula(cedula_limpia)
        
        if cliente:
            # MAGIA VISUAL: Actualiza la caja de texto con el formato EXACTO de la base de datos
            self.txt_cliente.setText(str(cliente[1])) # cliente[1] es la columna 'cedula_rif'
            
            self.id_cliente_actual = cliente[0]
            self.lbl_nombre_cliente.setText(cliente[2])
            self.txt_buscar_prod.setFocus()
        else:
            self.txt_cliente.setText(cedula_limpia) # Mantenemos lo que limpió por si lo crea
            
            # MENSAJE ESTANDARIZADO
            respuesta = QMessageBox.question(
                self, 
                "Cliente no encontrado", 
                f"El documento '{cedula_limpia}' no está registrado en el sistema.\\n\\n¿Desea registrar a este nuevo cliente?", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if respuesta == QMessageBox.StandardButton.Yes:
                d = CustomerDialog(self, {'cedula_rif': cedula_limpia, 'nombre': '', 'telefono': '', 'direccion': ''})
                if d.exec(): 
                    self.buscar_cliente()
            else:
                # Si cancela, devolvemos amablemente a consumidor final
                self.txt_cliente.clear()
                self.id_cliente_actual = 1
                self.lbl_nombre_cliente.setText("CONSUMIDOR FINAL")

    def agregar_producto(self, texto):
        codigo = texto.split(" | ")[0]
        prod = next((p for p in self.prods_cache if p['codigo'] == codigo), None)
        if prod:
            cant, ok = QInputDialog.getDouble(self, "Cantidad", f"Stock actual: {prod['stock_actual']}\nCantidad a despachar:", 1.0, 0.01, float(prod['stock_actual']), 2)
            if ok:
                self.carrito.append({
                    'id': prod['id'], 'codigo': prod['codigo'], 'descripcion': prod['descripcion'], 
                    'cantidad': cant, 'precio_usd': prod['precio_usd'], 'es_exento': prod['es_exento']
                })
                self.actualizar_tabla()
                self.txt_buscar_prod.clear()

    def crear_boton_eliminar(self, fila):
        btn = QPushButton("ELIMINAR")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #FF5252; font-weight: bold; font-size: 11px; border: 1px solid #FF5252; border-radius: 4px; padding: 4px 8px; }
            QPushButton:hover { background-color: #FF5252; color: white; }
        """)
        btn.clicked.connect(lambda: self.eliminar(fila))
        return btn

    def actualizar_tabla(self):
        self.tabla.setRowCount(0)
        total_a_cobrar_usd = 0.0
        
        for i, item in enumerate(self.carrito):
            r = self.tabla.rowCount()
            self.tabla.insertRow(r)
            
            tasa_iva = 0.16 if not item.get('es_exento', 0) else 0.0
            precio_real_usd = item['precio_usd'] * (1 + tasa_iva)
            
            subt_usd = precio_real_usd * item['cantidad']
            precio_bs = precio_real_usd * self.tasa_bcv
            precio_cop = precio_real_usd * self.tasa_cop
            
            total_a_cobrar_usd += subt_usd
            
            self.tabla.setItem(r, 0, QTableWidgetItem(item['codigo']))
            self.tabla.setItem(r, 1, QTableWidgetItem(item['descripcion']))
            
            item_cant = QTableWidgetItem(f"{item['cantidad']:.2f}")
            item_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(r, 2, item_cant)
            
            self.tabla.setItem(r, 3, QTableWidgetItem(f"${precio_real_usd:.2f}"))
            self.tabla.setItem(r, 4, QTableWidgetItem(f"Bs {precio_bs:,.2f}"))
            self.tabla.setItem(r, 5, QTableWidgetItem(f"COP {precio_cop:,.0f}"))
            self.tabla.setItem(r, 6, QTableWidgetItem(f"${subt_usd:.2f}"))
            
            w_btn = QWidget()
            l_btn = QGridLayout(w_btn)
            l_btn.setContentsMargins(0, 0, 0, 0)
            l_btn.addWidget(self.crear_boton_eliminar(i), 0, 0, Qt.AlignmentFlag.AlignCenter)
            self.tabla.setCellWidget(r, 7, w_btn)

        self.lbl_total_usd.setText(f"TOTAL COBRAR: $ {total_a_cobrar_usd:,.2f}")
        self.lbl_total_bs.setText(f"Bs: {total_a_cobrar_usd * self.tasa_bcv:,.2f} (Tasa: {self.tasa_bcv:,.2f})")
        self.lbl_total_cop.setText(f"COP: {total_a_cobrar_usd * self.tasa_cop:,.0f} (Tasa: {self.tasa_cop:,.0f})")

    def eliminar(self, idx):
        del self.carrito[idx]
        self.actualizar_tabla()

    def emitir_nota(self):
        sesion_activa = CashController.obtener_sesion_activa()
        if not sesion_activa:
            QMessageBox.critical(self, "Caja Cerrada", "Debe realizar la apertura de caja antes de emitir cobros.")
            return

        if not self.carrito:
            QMessageBox.warning(self, "Vacío", "Agregue productos a la lista antes de cobrar.")
            return
        
        total_a_cobrar_usd = 0.0
        carrito_modificado = []
        
        for i in self.carrito:
            tasa_iva = 0.16 if not i.get('es_exento', 0) else 0.0
            precio_real = i['precio_usd'] * (1 + tasa_iva)
            total_a_cobrar_usd += precio_real * i['cantidad']
            
            item_clon = i.copy()
            item_clon['precio_usd'] = precio_real
            carrito_modificado.append(item_clon)
        
        totales = {'subtotal': total_a_cobrar_usd, 'iva': 0, 'total': total_a_cobrar_usd, 'igtf': 0} 
        
        dialogo_pago = PaymentDialog(total_a_cobrar_usd, 0, self.tasa_bcv, self.tasa_cop, self)
        
        if dialogo_pago.exec():
            datos_pago = dialogo_pago.get_data()
            datos_pago['cliente_id'] = self.id_cliente_actual or 1
            
            exito, nro_doc = SalesController.registrar_venta(
                carrito_modificado, datos_pago, totales, self.tasa_bcv, tipo_doc="NOTA_ENTREGA"
            )
            
            if exito:
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                try:
                    ruta_pdf = PrinterController.ver_factura(nro_doc)
                    if ruta_pdf:
                        visor = InvoiceViewerDialog(ruta_pdf, parent=self.window())
                        visor.setWindowTitle(f"Nota de Entrega: {nro_doc}")
                        visor.setWindowModality(Qt.WindowModality.ApplicationModal)
                        QApplication.restoreOverrideCursor()
                        visor.exec()
                    else:
                        QApplication.restoreOverrideCursor()
                except Exception as e:
                    QApplication.restoreOverrideCursor()
                    print(f"Error abriendo PDF de Nota: {e}")

                self.carrito = []
                self.actualizar_tabla()
                self.txt_cliente.clear()
                self.lbl_nombre_cliente.setText("CONSUMIDOR FINAL")
                self.id_cliente_actual = None
            else:
                QMessageBox.critical(self, "Error", nro_doc)