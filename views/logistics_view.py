from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QFormLayout, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QHBoxLayout, QLabel, QComboBox, QMessageBox, 
                             QFrame, QAbstractItemView)
from PyQt6.QtCore import Qt, QSize
import qtawesome as qta

from controllers.logistics_controller import LogisticsController
from controllers.master_data_controller import MasterDataController
from views.purchases_view import PurchasesView # <--- Módulo de Compras

class LogisticsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent 
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        
        # --- TÍTULO ---
        lbl_titulo = QLabel("GESTIÓN LOGÍSTICA")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #03DAC6; margin-bottom: 10px;")
        layout_principal.addWidget(lbl_titulo)

        # --- TABS ---
        self.tabs = QTabWidget()
        # Matamos el outline (recuadro gris) en las pestañas por si acaso
        self.tabs.setStyleSheet("""
            QTabWidget:focus { outline: none; }
            QTabWidget::pane { 
                border: 1px solid #333; 
                background: #1E1E1E; 
                border-radius: 8px; 
            }
            QTabBar::tab { 
                outline: none;
                background: #252525; 
                color: #888; 
                padding: 10px 20px; 
                margin-right: 4px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: bold;
            }
            QTabBar::tab:selected { 
                background: #1E1E1E; 
                color: #03DAC6;      
                border-bottom: 2px solid #03DAC6;
            }
            QTabBar::tab:hover { 
                background: #333; 
                color: white;
            }
        """)

        # Inicializamos Pestañas
        self.tab_compras = PurchasesView() # 1. Compras
        self.tab_ajustes = QWidget()       # 2. Ajustes
        self.tab_categorias = QWidget()    # 3. Categorías
        self.tab_proveedores = QWidget()   # 4. Proveedores

        self.init_tab_ajustes()
        self.init_tab_categorias()
        self.init_tab_proveedores()

        # Añadimos al QTabWidget con Iconos Pro
        self.tabs.addTab(self.tab_compras, qta.icon('fa5s.file-invoice-dollar', color='#888'), " Registro de Compras")
        self.tabs.addTab(self.tab_ajustes, qta.icon('fa5s.exchange-alt', color='#888'), " Ajustes de Stock")
        self.tabs.addTab(self.tab_categorias, qta.icon('fa5s.tags', color='#888'), " Categorías")
        self.tabs.addTab(self.tab_proveedores, qta.icon('fa5s.truck', color='#888'), " Proveedores")

        layout_principal.addWidget(self.tabs)
        
        # --- ESTILOS GLOBALES ORIGINALES ---
        self.setStyleSheet("""
            QLineEdit, QComboBox {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 6px;
                selection-background-color: #6200EE;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #03DAC6;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QTableWidget {
                background-color: #121212;
                color: white;
                gridline-color: #222;
                border: none;
                outline: none;
            }
            QTableWidget:focus { outline: none; }
            QTableWidget::item:selected {
                background-color: #1E1E1E;
                color: #03DAC6;
                border-bottom: 1px solid #03DAC6;
            }
            QHeaderView::section {
                background-color: #252525;
                color: #B3B3B3;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)

    def init_tab_ajustes(self):
        layout = QVBoxLayout(self.tab_ajustes)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Filtros
        filtros_frame = QFrame()
        filtros_frame.setStyleSheet("background: #252525; border-radius: 6px;")
        filtros_layout = QHBoxLayout(filtros_frame)
        filtros_layout.setContentsMargins(10, 10, 10, 10)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Filtrar por código o nombre...")
        self.txt_buscar.textChanged.connect(self.actualizar_tabla)

        self.cmb_filtro_cat = QComboBox()
        self.cmb_filtro_prov = QComboBox()
        self.cmb_filtro_cat.currentIndexChanged.connect(self.actualizar_tabla)
        self.cmb_filtro_prov.currentIndexChanged.connect(self.actualizar_tabla)

        filtros_layout.addWidget(self.txt_buscar, 2)
        filtros_layout.addWidget(self.cmb_filtro_cat, 1)
        filtros_layout.addWidget(self.cmb_filtro_prov, 1)
        layout.addWidget(filtros_frame)

        # Tabla
        self.tabla_prod = QTableWidget(0, 5)
        self.tabla_prod.setHorizontalHeaderLabels(["CÓDIGO", "DESCRIPCIÓN", "STOCK", "CATEGORÍA", "PROVEEDOR"])
        self.tabla_prod.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_prod.verticalHeader().setVisible(False)
        self.tabla_prod.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_prod.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla_prod)

        # Panel Acción
        accion_frame = QFrame()
        accion_frame.setStyleSheet("""
            QFrame { background-color: #252525; border-radius: 8px; border: 1px solid #333; }
            QLabel { color: #DDD; font-weight: bold; }
        """)
        accion_layout = QHBoxLayout(accion_frame)
        accion_layout.setContentsMargins(15, 15, 15, 15)
        
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["ENTRADA", "SALIDA"])
        self.cmb_tipo.setFixedWidth(120)
        self.cmb_tipo.setStyleSheet("font-weight: bold;")
        
        self.txt_cant = QLineEdit()
        self.txt_cant.setPlaceholderText("Cant.")
        self.txt_cant.setFixedWidth(80)
        self.txt_cant.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Motivo (ej: Dañado, Conteo anual...)")
        
        btn_apply = QPushButton("APLICAR CAMBIO")
        btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #6200EE; color: white; font-weight: bold; 
                padding: 10px 20px; border-radius: 5px; border: none; outline: none;
            }
            QPushButton:hover { background-color: #7722FF; }
        """)
        btn_apply.clicked.connect(self.aplicar_ajuste)

        accion_layout.addWidget(QLabel("TIPO MOVIMIENTO:"))
        accion_layout.addWidget(self.cmb_tipo)
        accion_layout.addWidget(self.txt_cant)
        accion_layout.addWidget(self.txt_obs)
        accion_layout.addWidget(btn_apply)
        layout.addWidget(accion_frame)

        self.refrescar_combos()
        self.actualizar_tabla()

    def init_tab_categorias(self):
        layout = QVBoxLayout(self.tab_categorias)
        layout.setContentsMargins(20, 20, 20, 20)
        
        h_layout = QHBoxLayout()
        self.txt_new_cat = QLineEdit()
        self.txt_new_cat.setPlaceholderText("Nombre de la nueva categoría...")
        
        btn = QPushButton(" + CREAR")
        btn.setIcon(qta.icon('fa5s.plus', color='black'))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedWidth(110)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #03DAC6; color: black; font-weight: bold; 
                padding: 6px; border-radius: 5px; outline: none;
            }
            QPushButton:hover { background-color: #00F0DA; }
        """)
        btn.clicked.connect(self.guardar_categoria)
        
        h_layout.addWidget(self.txt_new_cat)
        h_layout.addWidget(btn)
        
        self.table_cat = QTableWidget(0, 2)
        self.table_cat.setHorizontalHeaderLabels(["ID", "NOMBRE CATEGORÍA"])
        self.table_cat.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_cat.verticalHeader().setVisible(False)
        self.table_cat.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_cat.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        layout.addLayout(h_layout)
        layout.addWidget(self.table_cat)
        self.cargar_datos_cat()

    def init_tab_proveedores(self):
        layout = QHBoxLayout(self.tab_proveedores)
        layout.setContentsMargins(20, 20, 20, 20)
        
        frame_form = QFrame()
        frame_form.setFixedWidth(320)
        frame_form.setStyleSheet("background: #252525; border-radius: 8px;")
        layout_form = QVBoxLayout(frame_form)
        layout_form.setSpacing(10)
        
        lbl_sub = QLabel("NUEVO PROVEEDOR")
        lbl_sub.setStyleSheet("color: #03DAC6; font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        layout_form.addWidget(lbl_sub)
        
        self.txt_p_rif = QLineEdit()
        self.txt_p_rif.setPlaceholderText("RIF / Documento")
        
        self.txt_p_nombre = QLineEdit()
        self.txt_p_nombre.setPlaceholderText("Razón Social")
        
        self.txt_p_cont = QLineEdit()
        self.txt_p_cont.setPlaceholderText("Teléfono / Contacto")
        
        btn_p = QPushButton(" REGISTRAR")
        btn_p.setIcon(qta.icon('fa5s.save', color='white'))
        btn_p.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_p.setFixedHeight(45)
        btn_p.setStyleSheet("""
            QPushButton {
                background-color: #6200EE; color: white; font-weight: bold; 
                border-radius: 5px; margin-top: 15px; outline: none;
            }
            QPushButton:hover { background-color: #7722FF; }
        """)
        btn_p.clicked.connect(self.guardar_proveedor)
        
        layout_form.addWidget(QLabel("RIF:"))
        layout_form.addWidget(self.txt_p_rif)
        layout_form.addWidget(QLabel("Nombre:"))
        layout_form.addWidget(self.txt_p_nombre)
        layout_form.addWidget(QLabel("Contacto:"))
        layout_form.addWidget(self.txt_p_cont)
        layout_form.addWidget(btn_p)
        layout_form.addStretch()
        
        layout.addWidget(frame_form)
        
        self.table_prov = QTableWidget(0, 3)
        self.table_prov.setHorizontalHeaderLabels(["RIF", "RAZÓN SOCIAL", "CONTACTO"])
        self.table_prov.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table_prov.verticalHeader().setVisible(False)
        self.table_prov.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_prov.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        layout.addWidget(self.table_prov)
        self.cargar_datos_prov()

    def actualizar_tabla(self):
        """Refresca todas las sub-vistas para mantener consistencia de datos"""
        # Refrescar la pestaña de compras
        self.tab_compras.cargar_datos_iniciales()
        
        # Filtros para Ajustes
        texto = self.txt_buscar.text()
        cat_id = self.cmb_filtro_cat.currentData()
        prov_id = self.cmb_filtro_prov.currentData()
        
        productos = LogisticsController.filtrar_productos(texto, cat_id, prov_id)
        self.tabla_prod.setRowCount(0)
        
        for p in productos:
            row = self.tabla_prod.rowCount()
            self.tabla_prod.insertRow(row)
            
            item_cod = QTableWidgetItem(str(p[1]))
            item_cod.setData(Qt.ItemDataRole.UserRole, p[0])
            
            self.tabla_prod.setItem(row, 0, item_cod)
            self.tabla_prod.setItem(row, 1, QTableWidgetItem(str(p[2])))
            
            item_stock = QTableWidgetItem(str(p[3]))
            item_stock.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_prod.setItem(row, 2, item_stock)
            
            self.tabla_prod.setItem(row, 3, QTableWidgetItem(str(p[4] or "S/C")))
            self.tabla_prod.setItem(row, 4, QTableWidgetItem(str(p[5] or "S/P")))

    def aplicar_ajuste(self):
        row = self.tabla_prod.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Error", "Seleccione un producto de la tabla")
        
        try:
            cant = float(self.txt_cant.text())
            if cant <= 0: raise ValueError
        except:
            return QMessageBox.warning(self, "Error", "Ingrese una cantidad válida")

        if not self.txt_obs.text():
            return QMessageBox.warning(self, "Error", "Debe indicar el motivo del ajuste")

        prod_id = self.tabla_prod.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        datos = {
            'producto_id': prod_id,
            'tipo': self.cmb_tipo.currentText(),
            'cantidad': cant,
            'motivo': "AJUSTE MANUAL",
            'proveedor_id': None,
            'referencia': "LOG-INT",
            'observaciones': self.txt_obs.text()
        }

        exito, msg = LogisticsController.registrar_movimiento(datos)
        if exito:
            self.actualizar_tabla()
            self.txt_cant.clear()
            self.txt_obs.clear()
            if self.main_window and hasattr(self.main_window, 'vista_inventario'):
                self.main_window.vista_inventario.cargar_datos()
            QMessageBox.information(self, "Éxito", "Movimiento procesado y stock sincronizado")
        else:
            QMessageBox.critical(self, "Error", msg)

    def refrescar_combos(self):
        self.cmb_filtro_cat.clear()
        self.cmb_filtro_cat.addItem("Todas las Categorías", None)
        for c in MasterDataController.obtener_categorias():
            self.cmb_filtro_cat.addItem(c[1], c[0])

        self.cmb_filtro_prov.clear()
        self.cmb_filtro_prov.addItem("Todos los Proveedores", None)
        for p in MasterDataController.obtener_proveedores():
            self.cmb_filtro_prov.addItem(p[2], p[0])

    def guardar_categoria(self):
        if self.txt_new_cat.text():
            MasterDataController.añadir_categoria(self.txt_new_cat.text())
            self.txt_new_cat.clear()
            self.cargar_datos_cat()
            self.refrescar_combos()

    def guardar_proveedor(self):
        if self.txt_p_rif.text() and self.txt_p_nombre.text():
            MasterDataController.añadir_proveedor(self.txt_p_rif.text(), self.txt_p_nombre.text(), self.txt_p_cont.text())
            self.txt_p_rif.clear(); self.txt_p_nombre.clear(); self.txt_p_cont.clear()
            self.cargar_datos_prov()
            self.refrescar_combos()

    def cargar_datos_cat(self):
        self.table_cat.setRowCount(0)
        for c in MasterDataController.obtener_categorias():
            r = self.table_cat.rowCount()
            self.table_cat.insertRow(r)
            self.table_cat.setItem(r, 0, QTableWidgetItem(str(c[0])))
            self.table_cat.setItem(r, 1, QTableWidgetItem(c[1]))

    def cargar_datos_prov(self):
        self.table_prov.setRowCount(0)
        for p in MasterDataController.obtener_proveedores():
            r = self.table_prov.rowCount()
            self.table_prov.insertRow(r)
            self.table_prov.setItem(r, 0, QTableWidgetItem(p[1]))
            self.table_prov.setItem(r, 1, QTableWidgetItem(p[2]))
            self.table_prov.setItem(r, 2, QTableWidgetItem(p[3]))