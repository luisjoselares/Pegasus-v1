from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from views.inventory_dialog import InventoryDialog
from controllers.inventory_controller import InventoryController

class InventoryView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- ENCABEZADO ---
        header = QHBoxLayout()
        self.lbl_titulo = QLabel("GESTIÓN DE PRODUCTOS")
        self.lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #6200EE;")
        
        self.btn_nuevo = QPushButton("+ REGISTRAR NUEVO")
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.setStyleSheet("""
            QPushButton {
                background-color: #6200EE; color: white; border-radius: 5px; 
                padding: 10px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #7722FF; }
        """)
        self.btn_nuevo.clicked.connect(self.abrir_dialogo_nuevo)
        
        header.addWidget(self.lbl_titulo)
        header.addStretch()
        header.addWidget(self.btn_nuevo)
        layout.addLayout(header)

        # --- BARRA DE BÚSQUEDA ---
        search_frame = QFrame()
        search_frame.setStyleSheet("background: #1E1E1E; border-radius: 8px;")
        search_layout = QHBoxLayout(search_frame)
        
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por código o descripción...")
        self.txt_buscar.setStyleSheet("border: none; background: transparent; color: white; padding: 8px;")
        self.txt_buscar.textChanged.connect(self.filtrar_tabla)
        
        search_layout.addWidget(self.txt_buscar)
        layout.addWidget(search_frame)

        # --- TABLA DE INVENTARIO ---
        self.tabla = QTableWidget()
        # Aumentamos columnas para incluir Bs y COP
        self.tabla.setColumnCount(10) 
        self.tabla.setHorizontalHeaderLabels([
            "CÓDIGO", "DESCRIPCIÓN", "USD ($)", "BS (VES)", "COP ($)", "STOCK", 
            "MIN", "CATEGORÍA", "PROVEEDOR", "ACCIONES"
        ])
        
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header_view = self.tabla.horizontalHeader()
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Descripción
        header_view.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed) # Acciones
        self.tabla.setColumnWidth(9, 100)

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
        self.cargar_datos()

    def _crear_acciones(self, producto):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_edit = QPushButton("EDITAR")
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setMinimumWidth(80) 
        btn_edit.setStyleSheet("""
            QPushButton {
                color: #2196F3; background: transparent;
                border: 1px solid #2196F3; border-radius: 4px;
                font-size: 11px; font-weight: bold; padding: 5px;
            }
            QPushButton:hover { background: #2196F3; color: white; }
        """)
        btn_edit.clicked.connect(lambda: self.abrir_dialogo_editar(producto))
        
        layout.addWidget(btn_edit)
        return container

    def cargar_datos(self):
        productos = InventoryController.obtener_todos()
        self.tabla.setRowCount(0)
        for p in productos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            
            self.tabla.setItem(row, 0, QTableWidgetItem(str(p['codigo'])))
            self.tabla.setItem(row, 1, QTableWidgetItem(p['descripcion']))
            
            # Precios Multimoneda
            self.tabla.setItem(row, 2, QTableWidgetItem(f"{p['precio_usd']:.2f}"))
            self.tabla.setItem(row, 3, QTableWidgetItem(f"{p['precio_bs']:.2f}"))
            self.tabla.setItem(row, 4, QTableWidgetItem(f"{p['precio_cop']:,.0f}".replace(',', '.'))) # Formato COP con miles
            
            # Stock con alerta visual
            item_stock = QTableWidgetItem(str(p['stock_actual']))
            if p['stock_actual'] <= p['stock_minimo']:
                item_stock.setForeground(Qt.GlobalColor.red)
                item_stock.setToolTip("Stock Bajo!")
            self.tabla.setItem(row, 5, item_stock)
            
            self.tabla.setItem(row, 6, QTableWidgetItem(str(p['stock_minimo'])))
            
            cat = p.get('categoria') or "Sin Categoría"
            prov = p.get('proveedor') or "Sin Proveedor"
            
            self.tabla.setItem(row, 7, QTableWidgetItem(str(cat)))
            self.tabla.setItem(row, 8, QTableWidgetItem(str(prov)))
            
            self.tabla.setCellWidget(row, 9, self._crear_acciones(p))

    def filtrar_tabla(self):
        filtro = self.txt_buscar.text().lower()
        for fila in range(self.tabla.rowCount()):
            codigo = self.tabla.item(fila, 0).text().lower()
            desc = self.tabla.item(fila, 1).text().lower()
            self.tabla.setRowHidden(fila, not (filtro in codigo or filtro in desc))

    def abrir_dialogo_nuevo(self):
        dialogo = InventoryDialog(self)
        if dialogo.exec():
            self.cargar_datos()

    def abrir_dialogo_editar(self, producto):
        dialogo = InventoryDialog(self, producto=producto)
        if dialogo.exec():
            self.cargar_datos()