from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from controllers.customer_controller import CustomerController
from views.customer_dialog import CustomerDialog

class CustomerView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- ENCABEZADO ---
        header = QHBoxLayout()
        lbl_titulo = QLabel("GESTIÓN DE CLIENTES")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #6200EE;")
        
        self.btn_nuevo = QPushButton("+ AGREGAR CLIENTE")
        self.btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_nuevo.setStyleSheet("""
            QPushButton {
                background-color: #6200EE; color: white; border-radius: 5px; 
                padding: 10px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #7722FF; }
        """)
        self.btn_nuevo.clicked.connect(self.abrir_dialogo_nuevo)
        
        header.addWidget(lbl_titulo)
        header.addStretch()
        header.addWidget(self.btn_nuevo)
        layout.addLayout(header)

        # --- BARRA DE BÚSQUEDA ---
        search_frame = QFrame()
        search_frame.setStyleSheet("background: #1E1E1E; border-radius: 8px;")
        search_layout = QHBoxLayout(search_frame)
        
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por nombre, cédula o RIF...")
        self.txt_buscar.setStyleSheet("border: none; background: transparent; color: white; padding: 8px;")
        self.txt_buscar.textChanged.connect(self.filtrar_tabla)
        
        search_layout.addWidget(self.txt_buscar)
        layout.addWidget(search_frame)

        # --- TABLA ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["CÉDULA / RIF", "NOMBRE", "TELÉFONO", "DIRECCIÓN", "GESTIÓN"])
        
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header_view = self.tabla.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(4, 150)

        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: #121212; color: white; gridline-color: #222;
                border: none; outline: none;
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

    def _crear_acciones(self, cliente):
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
        btn_edit.clicked.connect(lambda: self.abrir_dialogo_editar(cliente))
        
        layout.addWidget(btn_edit)
        return container

    def cargar_datos(self):
        clientes = CustomerController.obtener_todos()
        self.tabla.setRowCount(0)
        for c in clientes:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            
            # Convertimos a string para evitar errores con None
            rif = str(c['cedula_rif']) if c['cedula_rif'] else ""
            nombre = str(c['nombre']) if c['nombre'] else ""
            telf = str(c['telefono']) if c['telefono'] else ""
            direc = str(c['direccion']) if c['direccion'] else ""

            item_rif = QTableWidgetItem(rif)
            item_rif.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.tabla.setItem(row, 0, item_rif)
            self.tabla.setItem(row, 1, QTableWidgetItem(nombre))
            self.tabla.setItem(row, 2, QTableWidgetItem(telf))
            self.tabla.setItem(row, 3, QTableWidgetItem(direc))
            
            self.tabla.setCellWidget(row, 4, self._crear_acciones(c))

    def filtrar_tabla(self):
        filtro = self.txt_buscar.text().lower()
        for fila in range(self.tabla.rowCount()):
            rif = self.tabla.item(fila, 0).text().lower()
            nombre = self.tabla.item(fila, 1).text().lower()
            self.tabla.setRowHidden(fila, not (filtro in rif or filtro in nombre))

    def abrir_dialogo_nuevo(self):
        # --- AQUÍ ESTABA EL ERROR ---
        # Antes intentabas guardar aquí. Ahora NO.
        # El diálogo se encarga de guardar.
        dialogo = CustomerDialog(self)
        if dialogo.exec():
            # Si el diálogo retorna True (Accepted), significa que guardó con éxito.
            # Solo recargamos la tabla visualmente.
            self.cargar_datos()

    def abrir_dialogo_editar(self, cliente):
        dialogo = CustomerDialog(self, cliente=cliente)
        if dialogo.exec():
            self.cargar_datos()