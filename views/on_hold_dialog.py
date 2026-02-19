from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QHeaderView, QAbstractItemView, QMessageBox, QLabel)
from PyQt6.QtCore import Qt

class OnHoldDialog(QDialog):
    def __init__(self, lista_espera, parent=None):
        super().__init__(parent)
        self.lista_espera = lista_espera
        self.seleccionado_idx = None # Índice de la venta que el usuario elija recuperar
        
        self.setWindowTitle("Ventas en Espera")
        self.setFixedWidth(600)
        self.setFixedHeight(400)
        self.setStyleSheet("background-color: #1E1E1E; color: white;")
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        lbl_titulo = QLabel("Seleccione una venta para recuperar:")
        lbl_titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #03DAC6; margin-bottom: 10px;")
        layout.addWidget(lbl_titulo)

        # Tabla
        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Hora", "Cliente", "Items", "Total $"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setStyleSheet("""
            QTableWidget {
                background-color: #121212; border: 1px solid #333; gridline-color: #333;
            }
            QTableWidget::item:selected { background-color: #333; }
            QHeaderView::section { background-color: #2D2D2D; padding: 4px; border: 1px solid #333; }
        """)
        layout.addWidget(self.tabla)

        # Llenar tabla
        self.cargar_datos()

        # Botón Recuperar
        self.btn_recuperar = QPushButton("RECUPERAR VENTA")
        self.btn_recuperar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_recuperar.setFixedHeight(40)
        self.btn_recuperar.setStyleSheet("""
            QPushButton { background-color: #6200EE; color: white; font-weight: bold; border-radius: 5px; font-size: 14px; }
            QPushButton:hover { background-color: #7722FF; }
        """)
        self.btn_recuperar.clicked.connect(self.procesar_recuperacion)
        layout.addWidget(self.btn_recuperar)

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        for i, venta in enumerate(self.lista_espera):
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            
            # Hora
            hora = venta['timestamp'].strftime("%H:%M")
            self.tabla.setItem(row, 0, QTableWidgetItem(hora))
            # Cliente
            self.tabla.setItem(row, 1, QTableWidgetItem(venta['cliente_nombre']))
            # Cantidad de Items
            cant_items = sum(item['cantidad'] for item in venta['carrito'])
            self.tabla.setItem(row, 2, QTableWidgetItem(f"{cant_items:.0f}"))
            # Total (Calculado al vuelo para visualización)
            subtotal = sum(item['precio_usd'] * item['cantidad'] for item in venta['carrito'])
            # Nota: Esto es estimado visual, el cálculo real se hará al recuperar
            self.tabla.setItem(row, 3, QTableWidgetItem(f"${subtotal:.2f}"))

    def procesar_recuperacion(self):
        row = self.tabla.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Seleccione una venta de la lista.")
            return
        
        self.seleccionado_idx = row
        self.accept()