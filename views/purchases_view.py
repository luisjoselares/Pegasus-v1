from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTableWidget, QTableWidgetItem, 
                             QPushButton, QFrame, QHeaderView, QAbstractItemView, 
                             QMessageBox, QCompleter, QInputDialog, QComboBox,
                             QDateEdit, QCalendarWidget)
from PyQt6.QtCore import Qt, QDate
import sqlite3

from controllers.purchases_controller import PurchasesController
from controllers.master_data_controller import MasterDataController
from controllers.inventory_controller import InventoryController
from controllers.config_controller import ConfigController

class PurchasesView(QWidget):
    def __init__(self):
        super().__init__()
        self.carrito = [] 
        self.prods_cache = []
        self.tasa_bcv = 1.0
        
        self.init_ui()
        self.cargar_datos_iniciales()

    def init_ui(self):
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        
        # ==========================================
        # COLUMNA IZQUIERDA: DATOS DE LA FACTURA
        # ==========================================
        col_izquierda = QVBoxLayout()
        
        # 1. Panel del Proveedor y Factura
        frame_datos = QFrame()
        frame_datos.setStyleSheet("""
            QFrame { background-color: #1E1E1E; border-radius: 8px; border: 1px solid #333333; }
            QLabel { border: none; font-weight: bold; color: #B3B3B3; font-size: 11px; }
            QLineEdit, QComboBox, QDateEdit { background-color: #2D2D2D; color: white; border: 1px solid #444; padding: 6px; border-radius: 4px; }
        """)
        l_datos = QVBoxLayout(frame_datos)
        
        lbl_tit = QLabel("📄 DATOS DE LA FACTURA FÍSICA")
        lbl_tit.setStyleSheet("color: #03DAC6; font-size: 14px; margin-bottom: 5px;")
        l_datos.addWidget(lbl_tit)
        
        h_prov = QHBoxLayout()
        self.cmb_proveedor = QComboBox()
        h_prov.addWidget(QLabel("PROVEEDOR:"))
        h_prov.addWidget(self.cmb_proveedor, 1)
        l_datos.addLayout(h_prov)
        
        h_fac = QHBoxLayout()
        self.txt_factura = QLineEdit()
        self.txt_factura.setPlaceholderText("Ej: 000123")
        self.txt_control = QLineEdit()
        self.txt_control.setPlaceholderText("Ej: 00-123456")
        h_fac.addWidget(QLabel("NRO FACTURA:"))
        h_fac.addWidget(self.txt_factura)
        h_fac.addWidget(QLabel("NRO CONTROL:"))
        h_fac.addWidget(self.txt_control)
        l_datos.addLayout(h_fac)
        
        h_fec = QHBoxLayout()
        self.date_emision = QDateEdit()
        self.date_emision.setCalendarPopup(True)
        self.date_emision.setDate(QDate.currentDate())
        
        # --- SOLUCIÓN: CALENDARIO ESTILO PEGASUS FISCO ---
        calendario = QCalendarWidget()
        calendario.setStyleSheet("""
            /* Elimina la cabecera azul de Windows */
            QCalendarWidget QWidget#qt_calendar_navigationbar { 
                background-color: #1E1E1E; 
                border-bottom: 1px solid #333333;
            }
            /* Botones de Mes y Año */
            QCalendarWidget QToolButton { 
                color: white; 
                background-color: transparent; 
                font-weight: bold; 
                padding: 4px;
            }
            QCalendarWidget QToolButton:hover { 
                background-color: #333333; 
                border-radius: 4px; 
            }
            /* Desplegable del mes */
            QCalendarWidget QMenu { background-color: #1E1E1E; color: white; }
            QCalendarWidget QSpinBox { background-color: #2D2D2D; color: white; selection-background-color: #6200EE; }
            /* Tabla de días (El cuerpo del calendario) */
            QCalendarWidget QAbstractItemView:enabled { 
                background-color: #121212; 
                color: white; 
                selection-background-color: #6200EE; 
                selection-color: white; 
            }
            QCalendarWidget QAbstractItemView:disabled { color: #555555; }
        """)
        self.date_emision.setCalendarWidget(calendario)
        # -------------------------------------------------

        h_fec.addWidget(QLabel("FECHA EMISIÓN:"))
        h_fec.addWidget(self.date_emision)
        h_fec.addStretch()
        l_datos.addLayout(h_fec)
        
        col_izquierda.addWidget(frame_datos)
        
        # 2. Buscador de Productos
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar producto para ingresar al inventario...")
        self.txt_buscar.setFixedHeight(45)
        self.txt_buscar.setStyleSheet("""
            QLineEdit { font-size: 14px; padding-left: 15px; background: #1E1E1E; border: 1px solid #333333; border-radius: 8px; color: white; }
            QLineEdit:focus { border: 2px solid #6200EE; }
        """)
        col_izquierda.addWidget(self.txt_buscar)
        
        # 3. Tabla de Productos a Ingresar
        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(["CÓDIGO", "DESCRIPCIÓN", "CANTIDAD", "COSTO UNIT (Bs)", "TOTAL (Bs)", "EXENTO", "✖"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.setColumnWidth(6, 60)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setStyleSheet("""
            QTableWidget { background-color: #121212; color: white; border: none; gridline-color: #222; outline: none; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:selected { background-color: #1E1E1E; color: #03DAC6; }
            QHeaderView::section { background-color: #1E1E1E; color: #B3B3B3; padding: 10px; border: none; font-weight: bold; }
        """)
        col_izquierda.addWidget(self.tabla)
        
        layout_principal.addLayout(col_izquierda, 7)
        
        # ==========================================
        # COLUMNA DERECHA: AUDITORÍA Y TOTALES
        # ==========================================
        col_derecha = QVBoxLayout()
        
        frame_totales = QFrame()
        frame_totales.setStyleSheet("""
            QFrame { background-color: #1E1E1E; border-radius: 8px; border: 1px solid #333333; padding: 10px; }
            QLabel { border: none; font-size: 14px; color: #B3B3B3; }
        """)
        l_totales = QVBoxLayout(frame_totales)
        
        lbl_tot_tit = QLabel("AUDITORÍA FISCAL (En Bolívares)")
        lbl_tot_tit.setStyleSheet("color: #6200EE; font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        l_totales.addWidget(lbl_tot_tit)
        
        self.lbl_tasa = QLabel("Tasa BCV Referencial: 0.00")
        self.lbl_tasa.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 10px;")
        l_totales.addWidget(self.lbl_tasa)
        
        self.lbl_exento = QLabel("Monto Exento: Bs 0.00")
        self.lbl_base = QLabel("Base Imponible: Bs 0.00")
        self.lbl_iva = QLabel("IVA (16%): Bs 0.00")
        self.lbl_total = QLabel("TOTAL FACTURA: Bs 0.00")
        
        self.lbl_total.setStyleSheet("color: #03DAC6; font-size: 22px; font-weight: bold; margin-top: 15px;")
        
        l_totales.addWidget(self.lbl_exento)
        l_totales.addWidget(self.lbl_base)
        l_totales.addWidget(self.lbl_iva)
        l_totales.addWidget(self.lbl_total)
        l_totales.addStretch()
        
        self.btn_guardar = QPushButton("💾 PROCESAR COMPRA")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setFixedHeight(60)
        self.btn_guardar.setStyleSheet("""
            QPushButton { background-color: #6200EE; color: white; font-weight: bold; font-size: 16px; border-radius: 8px; outline: none; }
            QPushButton:hover { background-color: #7722FF; }
        """)
        self.btn_guardar.clicked.connect(self.procesar_compra)
        l_totales.addWidget(self.btn_guardar)
        
        col_derecha.addWidget(frame_totales)
        layout_principal.addLayout(col_derecha, 3)

    # --- CLON EXACTO DEL BOTÓN DE LA VENTANA DE VENTAS ---
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
                outline: none;
            }
            QPushButton:hover { background-color: #FF5252; color: white; }
        """)
        btn.clicked.connect(lambda: self.eliminar_item(fila))
        return btn
    # ------------------------------------------------------

    def cargar_datos_iniciales(self):
        self.cmb_proveedor.clear()
        for p in MasterDataController.obtener_proveedores():
            self.cmb_proveedor.addItem(f"{p['rif']} - {p['razon_social']}", p['id'])
            
        config = ConfigController.obtener_configuracion()
        if config:
            self.tasa_bcv = config['tasa_bcv']
            self.lbl_tasa.setText(f"Tasa BCV del día: {self.tasa_bcv:,.2f} Bs/$")
            
        self.prods_cache = InventoryController.obtener_todos()
        nombres = [f"{p['codigo']} | {p['descripcion']}" for p in self.prods_cache]
        completer = QCompleter(nombres, self)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        popup = completer.popup()
        popup.setStyleSheet("QAbstractItemView { background-color: #2D2D2D; color: white; selection-background-color: #6200EE; border: 1px solid #444; outline: none; }")
        self.txt_buscar.setCompleter(completer)
        completer.activated.connect(self.agregar_producto)

    def agregar_producto(self, texto):
        codigo = texto.split(" | ")[0]
        prod = next((p for p in self.prods_cache if p['codigo'] == codigo), None)
        
        if prod:
            cant, ok_cant = QInputDialog.getDouble(self, "Cantidad", f"¿Cuántas unidades de '{prod['descripcion']}' entraron?", 1.0, 0.01, 99999, 2)
            if not ok_cant or cant <= 0: return
            
            costo_ref_bs = float(prod['precio_usd']) * self.tasa_bcv * 0.7 
            costo, ok_costo = QInputDialog.getDouble(self, "Costo Unitario", f"Costo Unitario en BOLÍVARES (Según Factura):", costo_ref_bs, 0.01, 99999999, 2)
            if not ok_costo: return
            
            self.carrito.append({
                'id': prod['id'], 'codigo': prod['codigo'], 'descripcion': prod['descripcion'],
                'cantidad': cant, 'costo_bs': costo, 'es_exento': prod['es_exento']
            })
            self.actualizar_tabla()
            self.txt_buscar.clear()

    def actualizar_tabla(self):
        self.tabla.setRowCount(0)
        exento_total = 0.0
        base_total = 0.0
        
        for i, item in enumerate(self.carrito):
            r = self.tabla.rowCount()
            self.tabla.insertRow(r)
            
            subt_bs = item['cantidad'] * item['costo_bs']
            
            if item['es_exento']: exento_total += subt_bs
            else: base_total += subt_bs
            
            self.tabla.setItem(r, 0, QTableWidgetItem(item['codigo']))
            self.tabla.setItem(r, 1, QTableWidgetItem(item['descripcion']))
            
            item_cant = QTableWidgetItem(f"{item['cantidad']:.2f}")
            item_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(r, 2, item_cant)
            
            self.tabla.setItem(r, 3, QTableWidgetItem(f"Bs {item['costo_bs']:,.2f}"))
            self.tabla.setItem(r, 4, QTableWidgetItem(f"Bs {subt_bs:,.2f}"))
            
            item_ex = QTableWidgetItem("SÍ" if item['es_exento'] else "NO")
            item_ex.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(r, 5, item_ex)
            
            # --- USO EXACTO DEL MÉTODO DE VENTAS ---
            widget_btn = QWidget()
            layout_btn = QHBoxLayout(widget_btn)
            layout_btn.setContentsMargins(0, 0, 0, 0)
            layout_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_btn.addWidget(self.crear_boton_eliminar(i))
            
            self.tabla.setCellWidget(r, 6, widget_btn)

        iva_total = base_total * 0.16
        gran_total = exento_total + base_total + iva_total
        
        self.lbl_exento.setText(f"Monto Exento: Bs {exento_total:,.2f}")
        self.lbl_base.setText(f"Base Imponible: Bs {base_total:,.2f}")
        self.lbl_iva.setText(f"IVA (16%): Bs {iva_total:,.2f}")
        self.lbl_total.setText(f"TOTAL: Bs {gran_total:,.2f}")

    def eliminar_item(self, idx):
        if 0 <= idx < len(self.carrito):
            del self.carrito[idx]
            self.actualizar_tabla()

    def procesar_compra(self):
        if not self.carrito:
            return QMessageBox.warning(self, "Error", "Debe agregar productos a la factura.")
            
        id_prov = self.cmb_proveedor.currentData()
        factura = self.txt_factura.text().strip().upper()
        control = self.txt_control.text().strip().upper()
        
        if not id_prov or not factura or not control:
            return QMessageBox.warning(self, "Error", "Faltan datos de la factura (Proveedor, Nro Factura o Nro Control).")

        exento_bs = sum((i['cantidad'] * i['costo_bs']) for i in self.carrito if i['es_exento'])
        base_bs = sum((i['cantidad'] * i['costo_bs']) for i in self.carrito if not i['es_exento'])
        iva_bs = base_bs * 0.16
        total_bs = exento_bs + base_bs + iva_bs

        datos_compra = {
            'proveedor_id': id_prov,
            'nro_factura': factura,
            'nro_control': control,
            'fecha_emision': self.date_emision.date().toString("yyyy-MM-dd"),
            'tasa_cambio': self.tasa_bcv,
            'monto_exento_bs': exento_bs,
            'base_imponible_bs': base_bs,
            'impuesto_iva_bs': iva_bs,
            'total_compra_bs': total_bs
        }

        resp = QMessageBox.question(self, "Confirmar", 
                                    f"Se ingresarán {len(self.carrito)} productos al inventario y se registrará la compra por Bs {total_bs:,.2f}.\n\n¿Desea continuar?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                    
        if resp == QMessageBox.StandardButton.Yes:
            exito, msj = PurchasesController.registrar_compra(datos_compra, self.carrito)
            
            if exito:
                QMessageBox.information(self, "Éxito", msj)
                self.carrito.clear()
                self.actualizar_tabla()
                self.txt_factura.clear()
                self.txt_control.clear()
                self.cargar_datos_iniciales() 
            else:
                QMessageBox.critical(self, "Error", msj)