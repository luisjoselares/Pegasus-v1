from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QLabel, QMessageBox, QComboBox, QPlainTextEdit)
from PyQt6.QtCore import Qt
from controllers.cash_controller import CashController

class CashMovementsDialog(QDialog):
    def __init__(self, sesion_id, parent=None):
        super().__init__(parent)
        self.sesion_id = sesion_id
        self.setWindowTitle("Movimientos de Caja")
        self.setFixedWidth(400)
        self.setStyleSheet("background-color: #1E1E1E; color: white;")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl = QLabel("REGISTRO MANUAL E/S")
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")
        layout.addWidget(lbl)

        form = QFormLayout()
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["EGRESO (Salida de Dinero)", "INGRESO (Entrada Extra)"])
        self.combo_tipo.setStyleSheet("background: #333; padding: 5px; border: 1px solid #555; color: white;")
        
        self.txt_monto_usd = QLineEdit("0.00")
        self.txt_monto_bs = QLineEdit("0.00")
        self.txt_monto_cop = QLineEdit("0.00") # Nuevo campo
        self.txt_motivo = QPlainTextEdit()
        self.txt_motivo.setFixedHeight(60)
        
        for w in [self.txt_monto_usd, self.txt_monto_bs, self.txt_monto_cop, self.txt_motivo]:
            w.setStyleSheet("background: #2D2D2D; border: 1px solid #444; padding: 5px; color: white;")
            if isinstance(w, QLineEdit): w.setAlignment(Qt.AlignmentFlag.AlignRight)

        form.addRow("Tipo:", self.combo_tipo)
        form.addRow("Monto ($):", self.txt_monto_usd)
        form.addRow("Monto (Bs):", self.txt_monto_bs)
        form.addRow("Monto (COP):", self.txt_monto_cop) # Añadido
        form.addRow("Motivo:", self.txt_motivo)
        
        layout.addLayout(form)
        
        btn = QPushButton("REGISTRAR")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("background-color: #03DAC6; color: black; font-weight: bold; padding: 10px; border-radius: 5px;")
        btn.clicked.connect(self.guardar)
        layout.addWidget(btn)

    def guardar(self):
        try:
            tipo = "EGRESO" if "EGRESO" in self.combo_tipo.currentText() else "INGRESO"
            usd = float(self.txt_monto_usd.text() or 0)
            bs = float(self.txt_monto_bs.text() or 0)
            cop = float(self.txt_monto_cop.text() or 0) # Leemos COP
            motivo = self.txt_motivo.toPlainText().strip()
            
            if not motivo:
                QMessageBox.warning(self, "Falta dato", "El motivo es obligatorio.")
                return
            
            if usd == 0 and bs == 0 and cop == 0:
                QMessageBox.warning(self, "Falta dato", "Ingrese al menos un monto.")
                return

            exito, msg = CashController.registrar_movimiento(self.sesion_id, tipo, usd, bs, cop, motivo)
            if exito:
                QMessageBox.information(self, "Registrado", msg)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", msg)
        except ValueError:
            QMessageBox.warning(self, "Error", "Montos inválidos.")