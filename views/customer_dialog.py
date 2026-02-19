from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QHBoxLayout, QMessageBox, QLabel, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator
from controllers.customer_controller import CustomerController
import re # Importamos expresiones regulares para separar letras de números

class CustomerDialog(QDialog):
    def __init__(self, parent=None, cliente=None):
        super().__init__(parent)
        self.cliente = cliente
        
        # Detectamos si es edición (si tiene ID)
        self.modo_edicion = bool(self.cliente and self.cliente.get('id'))

        self.setWindowTitle("Gestión de Cliente")
        self.setFixedWidth(420) # Un poquito más ancho para que quepa bien el combo
        
        # Estilos oscuros (Manteniendo tu diseño original)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; color: white; }
            QLabel { font-weight: bold; color: #BBB; font-size: 13px; }
            QLineEdit, QComboBox { 
                background-color: #2D2D2D; color: white; padding: 8px; 
                border: 1px solid #444; border-radius: 4px;
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #6200EE; }
            QLineEdit:read-only { background-color: #151515; color: #555; }
            
            /* Estilo específico para el Combo */
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; border-left: 2px solid #555; width: 0; height: 0; }
        """)
        self.init_ui()
        
        # Siempre intentamos cargar datos, sea edición o nuevo desde POS
        if self.cliente:
            self.cargar_datos()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(15)

        # --- CAMPO CÉDULA COMPUESTO (COMBO + TEXTO) ---
        self.layout_rif = QHBoxLayout()
        self.layout_rif.setSpacing(5)
        
        self.cmb_tipo_doc = QComboBox()
        self.cmb_tipo_doc.addItems(["V", "J", "E", "G", "P"])
        self.cmb_tipo_doc.setFixedWidth(50)
        self.cmb_tipo_doc.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.txt_rif_numero = QLineEdit()
        self.txt_rif_numero.setPlaceholderText("12345678")
        # Validar que solo se escriban números
        self.txt_rif_numero.setValidator(QIntValidator(1, 999999999))
        
        self.layout_rif.addWidget(self.cmb_tipo_doc)
        self.layout_rif.addWidget(self.txt_rif_numero)
        # -----------------------------------------------
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre Fiscal o Razón Social")
        
        self.txt_telefono = QLineEdit()
        self.txt_direccion = QLineEdit()

        # Agregamos filas al formulario
        # Nota: Usamos el layout_rif en lugar de un solo widget
        form.addRow("Identificación:", self.layout_rif)
        form.addRow("Nombre / Razón:", self.txt_nombre)
        form.addRow("Teléfono:", self.txt_telefono)
        form.addRow("Dirección:", self.txt_direccion)

        layout.addLayout(form)

        # Botones
        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("CANCELAR")
        btn_cancel.setStyleSheet("background: transparent; color: #CF6679; border: 1px solid #CF6679; padding: 8px; font-weight: bold; border-radius: 4px;")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("GUARDAR")
        btn_save.setStyleSheet("background-color: #6200EE; color: white; border: none; padding: 10px; font-weight: bold; border-radius: 4px;")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setDefault(True)
        btn_save.setAutoDefault(True)
        btn_save.clicked.connect(self.validar_y_guardar)
        
        h_btns.addWidget(btn_cancel)
        h_btns.addWidget(btn_save)
        layout.addLayout(h_btns)

    def cargar_datos(self):
        """
        Esta función ahora es inteligente. 
        Si viene 'V-12345' lo separa.
        Si viene '12345' (desde POS), asume 'V' y pone el número.
        """
        rif_completo = str(self.cliente.get('cedula_rif', '')).strip().upper()
        
        # Lógica de Separación (Parsing)
        if rif_completo:
            # Intentamos detectar si ya tiene guión o letra (Ej: J-123456)
            match = re.match(r"^([VJEGP])[-]?(\d+)$", rif_completo)
            
            if match:
                # Caso ideal: Encontramos Letra y Número
                letra = match.group(1)
                numero = match.group(2)
                self.cmb_tipo_doc.setCurrentText(letra)
                self.txt_rif_numero.setText(numero)
            else:
                # Caso "Solo números" o formato sucio: Asumimos V y limpiamos lo que no sea número
                solo_numeros = re.sub(r"[^0-9]", "", rif_completo)
                if solo_numeros:
                    self.cmb_tipo_doc.setCurrentText("V") # Por defecto Venezuela
                    self.txt_rif_numero.setText(solo_numeros)
        
        self.txt_nombre.setText(str(self.cliente.get('nombre', '')))
        self.txt_telefono.setText(str(self.cliente.get('telefono', '')))
        self.txt_direccion.setText(str(self.cliente.get('direccion', '')))
        
        if self.modo_edicion:
            # Bloqueamos ambos controles
            self.cmb_tipo_doc.setEnabled(False)
            self.txt_rif_numero.setReadOnly(True)
            self.txt_rif_numero.setToolTip("El RIF no se puede editar.")

    def validar_y_guardar(self):
        tipo = self.cmb_tipo_doc.currentText()
        numero = self.txt_rif_numero.text().strip()
        nombre = self.txt_nombre.text().strip().upper()
        
        if not numero or not nombre:
            QMessageBox.warning(self, "Error", "El Número de Identificación y el Nombre son obligatorios.")
            return
        
        # ESTANDARIZACIÓN: Unimos todo aquí
        rif_final = f"{tipo}-{numero}"
        
        tel = self.txt_telefono.text().strip()
        direc = self.txt_direccion.text().strip()

        datos = {
            'cedula_rif': rif_final, 
            'nombre': nombre,
            'direccion': direc, 
            'telefono': tel
        }

        # Llamada al controlador
        if self.modo_edicion:
            exito, msg = CustomerController.actualizar_cliente(self.cliente['id'], datos)
        else:
            exito, msg = CustomerController.guardar_cliente(datos)
            
        if exito:
            QMessageBox.information(self, "Éxito", "Datos guardados correctamente.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", msg)

    def get_datos(self):
        """
        Devuelve los datos procesados para que la vista de Ventas reciba el RIF ya formateado.
        """
        tipo = self.cmb_tipo_doc.currentText()
        numero = self.txt_rif_numero.text().strip()
        rif_final = f"{tipo}-{numero}" if numero else ""
        
        return {
            'cedula_rif': rif_final,
            'nombre': self.txt_nombre.text().strip().upper(),
            'telefono': self.txt_telefono.text().strip(),
            'direccion': self.txt_direccion.text().strip()
        }