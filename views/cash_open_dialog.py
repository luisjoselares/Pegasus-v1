from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QLabel, QMessageBox, QHBoxLayout)
from PyQt6.QtCore import Qt
from controllers.cash_controller import CashController

class CashOpenDialog(QDialog):
    def __init__(self, parent=None, usuario_id=1):
        super().__init__(parent)
        self.usuario_id = usuario_id
        self.setWindowTitle("Apertura de Caja")
        self.setFixedWidth(350)
        self.setStyleSheet("background-color: #1E1E1E; color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # --- CAMBIO: Texto sin icono ---
        lbl_info = QLabel("INICIO DE TURNO")
        lbl_info.setStyleSheet("font-size: 16px; font-weight: bold; color: #03DAC6; margin-bottom: 10px;")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_info)

        form = QFormLayout()
        
        self.txt_usd = QLineEdit("0.00")
        self.txt_bs = QLineEdit("0.00")
        # --- CAMBIO: Campo COP ---
        self.txt_cop = QLineEdit("0.00")
        
        for txt in [self.txt_usd, self.txt_bs, self.txt_cop]:
            txt.setStyleSheet("background: #333; border: 1px solid #555; padding: 5px; font-size: 14px; color: white;")
            txt.setAlignment(Qt.AlignmentFlag.AlignRight)

        form.addRow("Fondo en Dólares ($):", self.txt_usd)
        form.addRow("Fondo en Bolívares (Bs):", self.txt_bs)
        form.addRow("Fondo en Pesos (COL):", self.txt_cop) # Etiqueta nueva
        
        layout.addLayout(form)
        
        btn_abrir = QPushButton("ABRIR CAJA")
        btn_abrir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_abrir.setStyleSheet("""
            QPushButton { background-color: #6200EE; padding: 10px; font-weight: bold; border-radius: 5px; font-size: 14px; }
            QPushButton:hover { background-color: #7722FF; }
        """)
        btn_abrir.clicked.connect(self.procesar_apertura)
        layout.addWidget(btn_abrir)

    def procesar_apertura(self):
        try:
            usd = float(self.txt_usd.text() or 0)
            bs = float(self.txt_bs.text() or 0)
            cop = float(self.txt_cop.text() or 0) # Leemos COP
            
            exito, msg = CashController.abrir_caja(self.usuario_id, usd, bs, cop)
            if exito:
                QMessageBox.information(self, "Éxito", msg)
                self.accept()
            else:
                QMessageBox.warning(self, "Error", msg)
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingrese montos válidos.")