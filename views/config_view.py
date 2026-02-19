from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QMessageBox)
from PyQt6.QtCore import Qt
from controllers.config_controller import ConfigController

class ConfigView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.cargar_datos_actuales()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # --- TÍTULO ---
        lbl_titulo = QLabel("AJUSTES DE TASAS DE CAMBIO")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #6200EE;")
        layout.addWidget(lbl_titulo)

        # --- CONTENEDOR DE ENTRADAS ---
        frame = QFrame()
        frame.setStyleSheet("background-color: #1E1E1E; border-radius: 12px; padding: 25px;")
        f_layout = QVBoxLayout(frame)

        # Campo BCV
        f_layout.addWidget(QLabel("Tasa BCV (Bolívares por Dólar):"))
        self.txt_bcv = QLineEdit()
        self.txt_bcv.setPlaceholderText("Ej: 36.50")
        self.txt_bcv.setStyleSheet(self._input_style())
        f_layout.addWidget(self.txt_bcv)

        f_layout.addSpacing(15)

        # Campo COP
        f_layout.addWidget(QLabel("Tasa Pesos (COP por Dólar):"))
        self.txt_cop = QLineEdit()
        self.txt_cop.setPlaceholderText("Ej: 3950")
        self.txt_cop.setStyleSheet(self._input_style())
        f_layout.addWidget(self.txt_cop)

        layout.addWidget(frame)

        # --- BOTÓN DE ACCIÓN ---
        self.btn_guardar = QPushButton("GUARDAR Y ACTUALIZAR SISTEMA")
        self.btn_guardar.setFixedHeight(45)
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #6200EE; color: white; font-weight: bold; 
                border-radius: 6px; font-size: 14px;
            }
            QPushButton:hover { background-color: #7722FF; }
        """)
        self.btn_guardar.clicked.connect(self.procesar_guardado)
        layout.addWidget(self.btn_guardar)

        layout.addStretch()

    def _input_style(self):
        return """
            QLineEdit {
                background-color: #121212; color: white; border: 1px solid #333;
                padding: 12px; border-radius: 6px; font-size: 15px;
            }
            QLineEdit:focus { border: 1px solid #6200EE; }
        """

    def cargar_datos_actuales(self):
        """Carga las tasas desde la BD al iniciar la vista"""
        config = ConfigController.obtener_configuracion()
        if config:
            self.txt_bcv.setText(str(config['tasa_bcv']))
            self.txt_cop.setText(str(config['tasa_cop']))

    def procesar_guardado(self):
        """Valida y guarda las nuevas tasas"""
        try:
            nueva_bcv = float(self.txt_bcv.text().replace(',', '.'))
            nueva_cop = float(self.txt_cop.text().replace(',', '.'))

            if ConfigController.actualizar_tasas(nueva_bcv, nueva_cop):
                QMessageBox.information(self, "Éxito", "Tasas actualizadas correctamente.\nLos precios en Inventario y POS se han sincronizado.")
            else:
                QMessageBox.critical(self, "Error", "No se pudo actualizar la base de datos.")
        except ValueError:
            QMessageBox.warning(self, "Error", "Por favor, introduce valores numéricos válidos (Ej: 36.50).")