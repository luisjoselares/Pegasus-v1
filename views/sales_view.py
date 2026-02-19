from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTableWidget, QTableWidgetItem, 
                             QPushButton, QFrame, QHeaderView, QAbstractItemView, 
                             QMessageBox, QCompleter, QInputDialog, QMenu, QStyle, QSizePolicy,
                             QApplication)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QShortcut, QKeySequence, QAction, QIcon
from datetime import datetime
import sqlite3

# Importamos los controladores
from controllers.inventory_controller import InventoryController
from controllers.config_controller import ConfigController
from controllers.master_data_controller import MasterDataController
from controllers.sales_controller import SalesController
from controllers.cash_controller import CashController
from controllers.stats_controller import StatsController
from controllers.printer_controller import PrinterController
from controllers.customer_controller import CustomerController # <--- IMPORTACIÓN AÑADIDA

# Importamos los diálogos
from views.customer_dialog import CustomerDialog
from views.payment_dialog import PaymentDialog
from views.on_hold_dialog import OnHoldDialog 
from views.cash_open_dialog import CashOpenDialog
from views.cash_movements_dialog import CashMovementsDialog
from views.cash_close_dialog import CashCloseDialog
from views.invoice_viewer_dialog import InvoiceViewerDialog

from core.app_signals import comunicacion 

class SalesView(QWidget):
    def __init__(self):
        super().__init__()
        self.carrito = [] 
        self.tasa_bcv = 1.0
        self.tasa_cop = 1.0
        self.id_cliente_actual = None 
        self.lista_productos_cache = [] 
        
        self.descuento_porcentaje = 0.0
        self.ventas_en_espera = [] 
        
        self.sesion_caja_id = None 

        self.init_ui()
        self.actualizar_tasas()
        self.configurar_atajos()
        self.configurar_buscador_inteligente()
        
        self.verificar_estado_caja()
        
        # Señales
        comunicacion.inventario_actualizado.connect(self.refrescar_datos_inventario)
        comunicacion.venta_realizada.connect(self.cargar_top_productos)

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(10, 10, 10, 10)
        
        # --- COLUMNA IZQUIERDA ---
        col_izquierda = QVBoxLayout()

        # 1. Panel de Cliente (Alineado al QSS)
        self.frame_cliente = QFrame()
        self.frame_cliente.setObjectName("clienteFrame")
        self.frame_cliente.setStyleSheet("""
            #clienteFrame {
                background-color: #1E1E1E; 
                border-radius: 8px; 
                border: 1px solid #333333;
                padding: 10px;
            }
        """)
        layout_cliente = QHBoxLayout(self.frame_cliente)
        layout_cliente.setContentsMargins(10, 10, 10, 10)

        info_busqueda = QVBoxLayout()
        lbl_id = QLabel("IDENTIFICACIÓN")
        lbl_id.setStyleSheet("color: #777; font-size: 11px; font-weight: bold;")
        
        self.txt_cliente_cedula = QLineEdit()
        self.txt_cliente_cedula.setPlaceholderText("🔍 Buscar cliente...")
        self.txt_cliente_cedula.setFixedWidth(160)
        # Reemplazamos editingFinished por returnPressed para matar el fantasma de PyQt
        self.txt_cliente_cedula.returnPressed.connect(self.buscar_cliente)
        
        info_busqueda.addWidget(lbl_id)
        info_busqueda.addWidget(self.txt_cliente_cedula)

        info_nombre = QVBoxLayout()
        lbl_nom_tag = QLabel("CLIENTE SELECCIONADO")
        lbl_nom_tag.setStyleSheet("color: #777; font-size: 11px; font-weight: bold;")
        self.lbl_cliente_nombre = QLabel("CONSUMIDOR FINAL")
        self.lbl_cliente_nombre.setStyleSheet("color: #03DAC6; font-weight: bold; font-size: 16px;")
        info_nombre.addWidget(lbl_nom_tag)
        info_nombre.addWidget(self.lbl_cliente_nombre)

        self.btn_add_cliente = QPushButton("+ NUEVO")
        self.btn_add_cliente.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_cliente.setFixedWidth(100)
        # El estilo principal del botón ya lo hereda del modern_style.qss
        self.btn_add_cliente.clicked.connect(lambda: self.abrir_registro_cliente())

        layout_cliente.addLayout(info_busqueda)
        layout_cliente.addSpacing(20)
        layout_cliente.addLayout(info_nombre)
        layout_cliente.addStretch()
        layout_cliente.addWidget(self.btn_add_cliente)
        col_izquierda.addWidget(self.frame_cliente)
        
        # --- ACCESO RÁPIDO ---
        lbl_top = QLabel("ACCESO RÁPIDO (MÁS VENDIDOS)")
        lbl_top.setStyleSheet("color: #B3B3B3; font-size: 12px; font-weight: bold; margin-top: 10px;")
        col_izquierda.addWidget(lbl_top)

        self.layout_top_products = QHBoxLayout()
        self.layout_top_products.setSpacing(10)
        col_izquierda.addLayout(self.layout_top_products)
        self.cargar_top_productos()

        # 2. Buscador de Productos
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Busque por nombre o escanee código de barras...")
        self.txt_buscar.setFixedHeight(50)
        # Ajustamos sutilmente para que destaque, pero manteniendo la identidad
        self.txt_buscar.setStyleSheet("""
            QLineEdit { font-size: 16px; padding-left: 15px; }
            QLineEdit:focus { border: 2px solid #03DAC6; }
        """)
        self.txt_buscar.returnPressed.connect(lambda: self.agregar_al_carrito()) 
        col_izquierda.addWidget(self.txt_buscar)

        # 3. Tabla Carrito
        self.tabla_carrito = QTableWidget(0, 8) 
        self.tabla_carrito.setHorizontalHeaderLabels([
            "CÓDIGO", "DESCRIPCIÓN", "CANT", "PRECIO ($)", "Bs", "COP", "SUBTOTAL ($)", ""
        ])
        
        self.tabla_carrito.verticalHeader().setVisible(False)
        
        header = self.tabla_carrito.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed) 
        self.tabla_carrito.setColumnWidth(7, 60)
        
        self.tabla_carrito.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_carrito.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_carrito.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.tabla_carrito.setStyleSheet("""
            QTableWidget { background-color: #121212; color: white; gridline-color: #222; border: none; outline: 0; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #1E1E1E; color: #03DAC6; border-bottom: 2px solid #03DAC6; }
            QHeaderView::section { background-color: #1E1E1E; color: #B3B3B3; padding: 10px; border: none; font-weight: bold; }
        """)
        self.tabla_carrito.cellDoubleClicked.connect(self.editar_cantidad_item)
        col_izquierda.addWidget(self.tabla_carrito)

        # --- COLUMNA DERECHA ---
        self.contenedor_derecha = QWidget()
        self.contenedor_derecha.setFixedWidth(340)
        col_derecha = QVBoxLayout(self.contenedor_derecha)
        col_derecha.setContentsMargins(0, 0, 0, 0)

        self.frame_totales = QFrame()
        self.frame_totales.setStyleSheet("background-color: #1E1E1E; border-radius: 8px; padding: 15px; border: 1px solid #333333;")
        layout_totales = QVBoxLayout(self.frame_totales)

        self.lbl_subtotal = QLabel("Subtotal: $0.00")
        self.lbl_descuento = QLabel("Descuento: -$0.00")
        self.lbl_descuento.setStyleSheet("font-size: 14px; color: #FF9800; margin-bottom: 2px;")
        self.lbl_descuento.setVisible(False) 
        self.lbl_iva = QLabel("IVA (16%): $0.00")
        self.lbl_total = QLabel("TOTAL: $0.00")
        
        self.lbl_total_bs = QLabel("Bs 0.00")
        self.lbl_total_bs.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_total_bs.setStyleSheet("font-size: 18px; color: #AAA; font-weight: bold; border: none;")
        
        self.lbl_total_cop = QLabel("COP 0")
        self.lbl_total_cop.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_total_cop.setStyleSheet("font-size: 18px; color: #AAA; font-weight: bold; border: none;")

        for lbl in [self.lbl_subtotal, self.lbl_iva, self.lbl_total]:
            lbl.setStyleSheet("font-size: 16px; color: #BBB; margin-bottom: 5px; border: none;")
        
        self.lbl_total.setStyleSheet("font-size: 30px; font-weight: bold; color: #03DAC6; margin-top: 10px; border: none;")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        layout_totales.addWidget(self.lbl_subtotal)
        layout_totales.addWidget(self.lbl_descuento)
        layout_totales.addWidget(self.lbl_iva)
        layout_totales.addWidget(self.lbl_total)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #333333; margin-top: 5px; margin-bottom: 5px;")
        layout_totales.addWidget(line)
        
        layout_totales.addWidget(self.lbl_total_bs)
        layout_totales.addWidget(self.lbl_total_cop)

        # Botones
        layout_acciones = QHBoxLayout()
        self.btn_descuento = QPushButton("🏷️ % Desc.")
        self.btn_descuento.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_descuento.setStyleSheet("QPushButton { background-color: #2D2D2D; border: 1px solid #444; } QPushButton:hover { border-color: #FF9800; color: #FF9800; }")
        self.btn_descuento.clicked.connect(self.pedir_descuento)
        
        self.btn_espera = QPushButton("⏸️ F5 - Espera")
        self.btn_espera.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_espera.setStyleSheet("QPushButton { background-color: #2D2D2D; border: 1px solid #444; } QPushButton:hover { border-color: #03DAC6; color: #03DAC6; }")
        self.btn_espera.clicked.connect(self.gestionar_espera)

        self.btn_caja = QPushButton("🔴 CAJA CERRADA")
        self.btn_caja.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_caja.setFixedHeight(45)
        self.btn_caja.clicked.connect(self.accion_boton_caja)

        layout_acciones.addWidget(self.btn_descuento)
        layout_acciones.addWidget(self.btn_espera)
        
        layout_caja = QHBoxLayout()
        layout_caja.addWidget(self.btn_caja)

        self.btn_pagar = QPushButton("F10 - COBRAR FACTURA")
        self.btn_pagar.setFixedHeight(80)
        self.btn_pagar.setCursor(Qt.CursorShape.PointingHandCursor)
        # Este sí lo forzamos a Cyan para llamar a la acción principal
        self.btn_pagar.setStyleSheet("QPushButton { background-color: #03DAC6; color: black; font-size: 20px; font-weight: bold; border-radius: 8px; } QPushButton:hover { background-color: #00F0DA; }")
        self.btn_pagar.clicked.connect(self.procesar_pago)

        col_derecha.addWidget(self.frame_totales)
        col_derecha.addSpacing(10)
        col_derecha.addLayout(layout_acciones)
        col_derecha.addLayout(layout_caja) 
        col_derecha.addStretch()
        col_derecha.addWidget(self.btn_pagar)

        layout_principal.addLayout(col_izquierda, 7)
        layout_principal.addWidget(self.contenedor_derecha, 3)

    # =========================================================
    # LÓGICA DE CLIENTES 
    # =========================================================
    def buscar_cliente(self):
        cedula_cruda = self.txt_cliente_cedula.text().strip()
        
        # 1er Filtro: Si vació la caja
        if not cedula_cruda: 
            self.txt_cliente_cedula.clear()
            self.id_cliente_actual = 1
            self.lbl_cliente_nombre.setText("CONSUMIDOR FINAL")
            return
            
        # Utilizamos el normalizador central
        cedula_limpia = CustomerController.normalizar_cedula(cedula_cruda)
        
        # 2do Filtro de Seguridad: Si escribió solo un guion y al limpiar quedó vacío
        if not cedula_limpia:
            self.txt_cliente_cedula.clear()
            self.id_cliente_actual = 1
            self.lbl_cliente_nombre.setText("CONSUMIDOR FINAL")
            return
        
        # Búsqueda Inteligente en Base de Datos
        cliente = MasterDataController.buscar_cliente_por_cedula(cedula_limpia)
        
        if cliente:
            self.txt_cliente_cedula.setText(str(cliente[1])) # Feedback Visual con formato oficial
            self.id_cliente_actual = cliente[0]
            self.lbl_cliente_nombre.setText(cliente[2])
            self.txt_buscar.setFocus()
        else:
            self.txt_cliente_cedula.setText(cedula_limpia) 
            
            respuesta = QMessageBox.question(
                self, 
                "Cliente no encontrado", 
                f"El documento '{cedula_limpia}' no está registrado en el sistema.\n\n¿Desea registrar a este nuevo cliente?", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if respuesta == QMessageBox.StandardButton.Yes:
                d = CustomerDialog(self, {'cedula_rif': cedula_limpia, 'nombre': '', 'telefono': '', 'direccion': ''})
                if d.exec(): 
                    self.buscar_cliente()
            else:
                self.txt_cliente_cedula.clear()
                self.id_cliente_actual = 1
                self.lbl_cliente_nombre.setText("CONSUMIDOR FINAL")

    def abrir_registro_cliente(self, cedula=""):
        datos = {'cedula_rif': cedula, 'nombre': '', 'telefono': '', 'direccion': ''}
        self.txt_cliente_cedula.blockSignals(True)
        
        dialogo = CustomerDialog(self, cliente=datos)
        
        if dialogo.exec():
            try:
                from data.conexion import crear_conexion
                conn = crear_conexion()
                if conn:
                    cur = conn.cursor()
                    cur.execute("SELECT * FROM clientes ORDER BY id DESC LIMIT 1")
                    cliente = cur.fetchone()
                    conn.close()
                    
                    if cliente:
                        self.txt_cliente_cedula.setText(cliente['cedula_rif'])
                        self.id_cliente_actual = cliente['id']
                        self.lbl_cliente_nombre.setText(cliente['nombre'].upper())
            except Exception as e:
                print(f"Error en auto-carga de cliente: {e}")
                
        self.txt_cliente_cedula.blockSignals(False)
        self.txt_buscar.setFocus()

    # =========================================================
    # LÓGICA DE INVENTARIO Y CARRITO
    # =========================================================
    def cargar_top_productos(self):
        while self.layout_top_products.count():
            item = self.layout_top_products.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()

        tops_brutos = StatsController.obtener_top_productos(3) 
        tops_reales = [prod for prod in tops_brutos if prod[2] > 0]

        colores = ["#BB86FC", "#03DAC6", "#CF6679"]

        for i, prod in enumerate(tops_reales):
            codigo = prod[0]
            desc = prod[1]
            ventas = prod[2]
            if len(desc) > 15: desc = desc[:15] + "..."

            btn = QPushButton(f"{desc}\n({ventas} vend.)")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"Código: {codigo}\nClick para agregar")
            
            color_borde = colores[i % 3]
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #252525;
                    color: white;
                    border: 1px solid {color_borde};
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                    text-align: center;
                }}
                QPushButton:hover {{ background-color: {color_borde}; color: black; }}
            """)
            btn.clicked.connect(lambda _, c=codigo: self.agregar_rapido(c))
            self.layout_top_products.addWidget(btn)

        if not tops_reales:
            lbl = QLabel("(Realiza ventas para ver aquí tus productos estrella)")
            lbl.setStyleSheet("color: #555; font-style: italic;")
            self.layout_top_products.addWidget(lbl)

    def agregar_rapido(self, codigo):
        self.txt_buscar.setText(codigo)
        self.agregar_al_carrito()

    def verificar_estado_caja(self):
        sesion = CashController.obtener_sesion_activa()
        if sesion:
            self.sesion_caja_id = sesion['id']
            self.btn_caja.setText(f"🟢 CAJA ABIERTA (ID: {sesion['id']})")
            self.btn_caja.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; border: 1px solid #1b5e20; border-radius: 8px; font-weight: bold;} QPushButton:hover { background-color: #388e3c; }")
        else:
            self.sesion_caja_id = None
            self.btn_caja.setText("🔴 CAJA CERRADA")
            self.btn_caja.setStyleSheet("QPushButton { background-color: #c62828; color: white; border: 1px solid #b71c1c; border-radius: 8px; font-weight: bold;} QPushButton:hover { background-color: #d32f2f; }")

    def accion_boton_caja(self):
        if not self.sesion_caja_id:
            if CashOpenDialog(self).exec(): self.verificar_estado_caja()
        else:
            menu = QMenu(self)
            menu.setStyleSheet("QMenu { background-color: #1E1E1E; color: white; border: 1px solid #333; } QMenu::item { padding: 10px 20px; } QMenu::item:selected { background-color: #6200EE; }")
            accion_mov = QAction("📝 Registrar Movimiento", self); accion_mov.triggered.connect(self.abrir_movimientos)
            accion_cierre = QAction("🔒 CERRAR CAJA (Arqueo)", self); accion_cierre.triggered.connect(self.abrir_cierre)
            menu.addAction(accion_mov); menu.addSeparator(); menu.addAction(accion_cierre)
            menu.exec(self.btn_caja.mapToGlobal(self.btn_caja.rect().bottomLeft()))

    def abrir_movimientos(self):
        if self.sesion_caja_id: CashMovementsDialog(self.sesion_caja_id, self).exec()

    def abrir_cierre(self):
        if self.sesion_caja_id:
            if CashCloseDialog(self.sesion_caja_id, self).exec(): self.verificar_estado_caja() 

    def gestionar_espera(self):
        if self.carrito: self.poner_en_espera()
        else: self.mostrar_lista_espera()

    def poner_en_espera(self):
        estado = {'timestamp': datetime.now(), 'carrito': self.carrito, 'cliente_id': self.id_cliente_actual, 'cliente_cedula': self.txt_cliente_cedula.text(), 'cliente_nombre': self.lbl_cliente_nombre.text(), 'descuento': self.descuento_porcentaje}
        self.ventas_en_espera.append(estado)
        self.btn_espera.setText(f"⏸️ Recuperar ({len(self.ventas_en_espera)})")
        self.limpiar_pantalla_sin_borrar_espera()
        QMessageBox.information(self, "En Espera", "Venta guardada temporalmente.")

    def mostrar_lista_espera(self):
        if not self.ventas_en_espera: return QMessageBox.information(self, "Vacío", "No hay ventas en espera.")
        dialogo = OnHoldDialog(self.ventas_en_espera, self)
        if dialogo.exec():
            idx = dialogo.seleccionado_idx
            if idx is not None: self.recuperar_venta(idx)

    def recuperar_venta(self, index):
        if self.carrito:
            if QMessageBox.question(self, "Conflicto", "¿Sobrescribir venta actual?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No: return
        venta = self.ventas_en_espera.pop(index)
        self.carrito = venta['carrito']; self.id_cliente_actual = venta['cliente_id']
        self.txt_cliente_cedula.setText(venta['cliente_cedula']); self.lbl_cliente_nombre.setText(venta['cliente_nombre'])
        self.descuento_porcentaje = venta['descuento']
        self.actualizar_tabla()
        count = len(self.ventas_en_espera)
        self.btn_espera.setText(f"⏸️ Recuperar ({count})" if count > 0 else "⏸️ F5 - Espera")

    def limpiar_pantalla_sin_borrar_espera(self):
        self.carrito = []; self.descuento_porcentaje = 0.0; self.lbl_descuento.setVisible(False)
        self.txt_cliente_cedula.blockSignals(True)
        self.id_cliente_actual = 1; self.txt_cliente_cedula.clear(); self.lbl_cliente_nombre.setText("CONSUMIDOR FINAL")
        self.txt_cliente_cedula.blockSignals(False)
        self.actualizar_tabla(); self.txt_buscar.setFocus()

    def limpiar_pantalla(self):
        self.limpiar_pantalla_sin_borrar_espera()
        count = len(self.ventas_en_espera)
        self.btn_espera.setText(f"⏸️ Recuperar ({count})" if count > 0 else "⏸️ F5 - Espera")

    def refrescar_datos_inventario(self): self.configurar_buscador_inteligente()

    def configurar_buscador_inteligente(self):
        self.lista_productos_cache = InventoryController.obtener_todos()
        nombres = [f"{p['codigo']} | {p['descripcion']} ({int(p['stock_actual'])} disp.)" for p in self.lista_productos_cache]
        completer = QCompleter(nombres, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive); completer.setFilterMode(Qt.MatchFlag.MatchContains)
        popup = completer.popup()
        popup.setStyleSheet("QAbstractItemView { background-color: #2D2D2D; color: white; selection-background-color: #6200EE; selection-color: white; border: 1px solid #444; } QScrollBar:vertical { background: #2D2D2D; width: 10px; }")
        self.txt_buscar.setCompleter(completer)
        completer.activated.connect(self.producto_seleccionado_completer)

    def producto_seleccionado_completer(self, texto):
        codigo = texto.split(" | ")[0]
        producto = next((p for p in self.lista_productos_cache if p['codigo'] == codigo), None)
        if producto: self.agregar_al_carrito(producto); self.txt_buscar.clear()

    def pedir_cantidad(self, producto):
        cantidad, ok = QInputDialog.getDouble(self, "Cantidad", f"Producto: {producto['descripcion']}\nStock: {producto['stock_actual']}\n\nCantidad:", 1.0, 0.1, float(producto['stock_actual']), 2)
        return cantidad if ok else None
    
    def pedir_descuento(self):
        if not self.carrito: return
        porcentaje, ok = QInputDialog.getDouble(self, "Descuento", "% Descuento:", self.descuento_porcentaje, 0, 100, 1)
        if ok: self.descuento_porcentaje = porcentaje; self.actualizar_tabla()

    def agregar_al_carrito(self, producto_obj=None):
        if producto_obj: producto = producto_obj
        else:
            codigo = self.txt_buscar.text().strip(); 
            if not codigo: return
            producto = next((p for p in self.lista_productos_cache if p['codigo'] == codigo), None)

        if producto:
            if producto['stock_actual'] <= 0: return QMessageBox.warning(self, "Sin Stock", "Producto agotado.")
            cant = self.pedir_cantidad(producto)
            if cant is None: return

            item = next((i for i in self.carrito if i['id'] == producto['id']), None)
            if item:
                if item['cantidad'] + cant > producto['stock_actual']: return QMessageBox.warning(self, "Límite", "Stock insuficiente.")
                item['cantidad'] += cant
            else:
                self.carrito.append({'id': producto['id'], 'codigo': producto['codigo'], 'descripcion': producto['descripcion'], 'precio_usd': producto['precio_usd'], 'es_exento': producto['es_exento'], 'cantidad': cant})
            self.txt_buscar.clear(); self.actualizar_tabla()
        else:
            QMessageBox.warning(self, "Error", "Producto no encontrado.")

    def crear_boton_eliminar(self, fila):
        btn = QPushButton("✖")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                color: #FF5252;
                font-weight: 900;
                font-size: 16px;
                border: 1px solid #FF5252;
                border-radius: 4px;
                padding: 0px;
                min-width: 25px;
                max-width: 25px;
            }
            QPushButton:hover { background-color: #FF5252; color: white; }
        """)
        btn.clicked.connect(lambda: self.eliminar_item_por_indice(fila))
        return btn

    def eliminar_item_por_indice(self, fila):
        if 0 <= fila < len(self.carrito): del self.carrito[fila]; self.actualizar_tabla(); self.txt_buscar.setFocus()

    def eliminar_seleccionado(self):
        fila = self.tabla_carrito.currentRow()
        if fila >= 0: self.eliminar_item_por_indice(fila)

    def editar_cantidad_item(self, fila, columna):
        if fila < 0: return
        producto = self.carrito[fila]
        p_cache = next((p for p in self.lista_productos_cache if p['id'] == producto['id']), None)
        stock_real = float(p_cache['stock_actual']) if p_cache else 9999
        cant, ok = QInputDialog.getDouble(self, "Editar", f"Nueva cantidad (Max {stock_real}):", float(producto['cantidad']), 0.01, stock_real, 2)
        if ok:
            if cant <= 0: self.eliminar_item_por_indice(fila)
            else: self.carrito[fila]['cantidad'] = cant; self.actualizar_tabla()
    
    def actualizar_tabla(self):
        self.tabla_carrito.setRowCount(0)
        subtotal_bruto = 0.0
        for i, item in enumerate(self.carrito):
            row = self.tabla_carrito.rowCount(); self.tabla_carrito.insertRow(row)
            monto_usd = item['precio_usd'] * item['cantidad']; subtotal_bruto += monto_usd
            
            precio_bs = item['precio_usd'] * self.tasa_bcv
            precio_cop = item['precio_usd'] * self.tasa_cop
            
            self.tabla_carrito.setItem(row, 0, QTableWidgetItem(item['codigo']))
            self.tabla_carrito.setItem(row, 1, QTableWidgetItem(item['descripcion']))
            cant_item = QTableWidgetItem(f"{item['cantidad']:.2f}"); cant_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_carrito.setItem(row, 2, cant_item)
            self.tabla_carrito.setItem(row, 3, QTableWidgetItem(f"${item['precio_usd']:.2f}"))
            
            self.tabla_carrito.setItem(row, 4, QTableWidgetItem(f"{precio_bs:,.2f}"))
            self.tabla_carrito.setItem(row, 5, QTableWidgetItem(f"{precio_cop:,.0f}"))
            self.tabla_carrito.setItem(row, 6, QTableWidgetItem(f"${monto_usd:.2f}"))
            
            widget_btn = QWidget()
            layout_btn = QHBoxLayout(widget_btn)
            layout_btn.setContentsMargins(0, 0, 0, 0)
            layout_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_btn.addWidget(self.crear_boton_eliminar(i))
            self.tabla_carrito.setCellWidget(row, 7, widget_btn)

        monto_desc = subtotal_bruto * (self.descuento_porcentaje / 100); subtotal_neto = subtotal_bruto - monto_desc
        gravable = sum((i['precio_usd'] * i['cantidad']) for i in self.carrito if not i['es_exento'])
        iva = (gravable * (1 - self.descuento_porcentaje/100)) * 0.16
        total_usd = subtotal_neto + iva
        
        total_bs = total_usd * self.tasa_bcv
        total_cop = total_usd * self.tasa_cop

        self.lbl_subtotal.setText(f"Subtotal: ${subtotal_bruto:,.2f}")
        if self.descuento_porcentaje > 0: self.lbl_descuento.setText(f"Descuento ({self.descuento_porcentaje:g}%): -${monto_desc:,.2f}"); self.lbl_descuento.setVisible(True)
        else: self.lbl_descuento.setVisible(False)
        self.lbl_iva.setText(f"IVA (16%): ${iva:,.2f}"); self.lbl_total.setText(f"TOTAL: ${total_usd:,.2f}")
        
        self.lbl_total_bs.setText(f"Bs {total_bs:,.2f}")
        self.lbl_total_cop.setText(f"COP {total_cop:,.0f}")

    def procesar_pago(self):
        if not self.sesion_caja_id: return QMessageBox.warning(self, "Caja Cerrada", "ABRIR CAJA para vender."), self.accion_boton_caja()
        if not self.carrito: return QMessageBox.warning(self, "Vacío", "No hay productos.")
        
        subtotal = sum(i['precio_usd'] * i['cantidad'] for i in self.carrito)
        desc = subtotal * (self.descuento_porcentaje / 100)
        gravable = sum((i['precio_usd'] * i['cantidad']) for i in self.carrito if not i['es_exento'])
        iva = (gravable * (1 - self.descuento_porcentaje/100)) * 0.16
        total = (subtotal - desc) + iva

        dialogo = PaymentDialog(total, iva, self.tasa_bcv, self.tasa_cop, self)
        if dialogo.exec():
            datos = dialogo.get_data(); datos['cliente_id'] = self.id_cliente_actual or 1
            totales = {'subtotal': subtotal, 'descuento_porc': self.descuento_porcentaje, 'descuento_monto': desc, 'iva': iva, 'igtf': 0.0, 'total': total}
            
            exito, nro_doc = SalesController.registrar_venta(self.carrito, datos, totales, self.tasa_bcv)
            
            if exito: 
                QMessageBox.information(self, "Éxito", f"Venta {nro_doc} procesada.")
                
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                try:
                    ruta_pdf = PrinterController.ver_factura(nro_doc)
                    if ruta_pdf:
                        visor = InvoiceViewerDialog(ruta_pdf, parent=self.window())
                        visor.setWindowTitle(f"Factura: {nro_doc}")
                        
                        QApplication.restoreOverrideCursor()
                        visor.exec()
                    else:
                        QApplication.restoreOverrideCursor()
                except Exception as e:
                    QApplication.restoreOverrideCursor()
                    print(f"Error abriendo PDF: {e}")
                
                self.configurar_buscador_inteligente()
                self.limpiar_pantalla()
                
    def actualizar_tasas(self):
        config = ConfigController.obtener_configuracion()
        if config: self.tasa_bcv = config['tasa_bcv']; self.tasa_cop = config['tasa_cop']

    def configurar_atajos(self):
        QShortcut(QKeySequence("F10"), self, self.procesar_pago)
        QShortcut(QKeySequence("F5"), self, self.gestionar_espera)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self, self.eliminar_seleccionado)