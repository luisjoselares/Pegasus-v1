from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QLabel, QMessageBox, QFrame, QHBoxLayout)
from PyQt6.QtCore import Qt
from controllers.cash_controller import CashController

class CashCloseDialog(QDialog):
    def __init__(self, sesion_id, parent=None):
        super().__init__(parent)
        self.sesion_id = sesion_id
        self.resumen = CashController.obtener_resumen_caja(sesion_id)
        
        self.setWindowTitle("Arqueo y Cierre de Caja")
        self.setFixedWidth(420)
        
        # Aplicamos la paleta de modern_style.qss
        self.setStyleSheet("""
            QDialog { background-color: #121212; color: white; }
            QLabel { color: #B3B3B3; font-size: 13px; font-weight: bold; }
            QLineEdit { 
                background-color: #1E1E1E; color: white; 
                border: 2px solid #333333; border-radius: 8px; 
                padding: 10px; font-size: 16px; font-weight: bold;
            }
            QLineEdit:focus { border: 2px solid #6200EE; }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # --- 1. RESUMEN DEL SISTEMA (Lo que debería haber) ---
        frame_info = QFrame()
        frame_info.setStyleSheet("QFrame { background-color: #1E1E1E; border: 1px solid #333333; border-radius: 10px; }")
        l_info = QVBoxLayout(frame_info)
        
        sys_usd = self.resumen['sistema_usd']
        sys_bs = self.resumen['sistema_bs']
        sys_cop = self.resumen['sistema_cop']
        
        lbl_titulo = QLabel("📊 SEGÚN SISTEMA DEBERÍA HABER EN CAJA:")
        lbl_titulo.setStyleSheet("color: #FFFFFF; font-size: 14px; border: none;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_vals = QLabel(f"<span style='color:#03DAC6;'>$ {sys_usd:,.2f}</span>  |  Bs {sys_bs:,.2f}  |  COP {sys_cop:,.0f}")
        lbl_vals.setStyleSheet("font-size: 18px; border: none;")
        lbl_vals.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        l_info.addWidget(lbl_titulo)
        l_info.addWidget(lbl_vals)
        layout.addWidget(frame_info)

        # --- 2. INPUT DE CONTEO FÍSICO REAL ---
        lbl_input = QLabel("📝 INGRESE SU CONTEO FÍSICO REAL:")
        lbl_input.setStyleSheet("color: #6200EE; font-size: 14px;")
        layout.addWidget(lbl_input)

        form = QFormLayout()
        form.setVerticalSpacing(10)
        
        self.txt_final_usd = QLineEdit()
        self.txt_final_usd.setPlaceholderText("0.00")
        self.txt_final_bs = QLineEdit()
        self.txt_final_bs.setPlaceholderText("0.00")
        self.txt_final_cop = QLineEdit()
        self.txt_final_cop.setPlaceholderText("0")
        
        for t in [self.txt_final_usd, self.txt_final_bs, self.txt_final_cop]:
            t.setAlignment(Qt.AlignmentFlag.AlignRight)
            t.textChanged.connect(self.calcular_diferencia)

        form.addRow("Total Billetes ($):", self.txt_final_usd)
        form.addRow("Total Efectivo (Bs):", self.txt_final_bs)
        form.addRow("Total Efectivo (COP):", self.txt_final_cop)
        layout.addLayout(form)

        # --- 3. DIFERENCIA EN TIEMPO REAL ---
        self.frame_diff = QFrame()
        self.frame_diff.setStyleSheet("QFrame { background-color: #2D2D2D; border-radius: 8px; }")
        l_diff = QVBoxLayout(self.frame_diff)
        
        self.lbl_diff = QLabel("Diferencia: $ 0.00 | Bs 0.00 | COP 0")
        self.lbl_diff.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_diff.setStyleSheet("font-size: 13px; color: #B3B3B3; border: none;")
        l_diff.addWidget(self.lbl_diff)
        layout.addWidget(self.frame_diff)

        # --- 4. BOTÓN CERRAR ---
        self.btn_cerrar = QPushButton("🔒 CERRAR TURNO Y ARQUEAR")
        self.btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cerrar.setFixedHeight(50)
        # Usamos el color de "peligro" corporativo para el cierre
        self.btn_cerrar.setStyleSheet("""
            QPushButton { background-color: #CF6679; color: white; font-weight: bold; font-size: 15px; border-radius: 8px; border: none; }
            QPushButton:hover { background-color: #B00020; }
        """)
        self.btn_cerrar.clicked.connect(self.ejecutar_cierre)
        layout.addWidget(self.btn_cerrar)

        self.calcular_diferencia()

    def calcular_diferencia(self):
        try:
            usu_usd = float(self.txt_final_usd.text() or 0)
            usu_bs = float(self.txt_final_bs.text() or 0)
            usu_cop = float(self.txt_final_cop.text() or 0)
            
            dif_usd = usu_usd - self.resumen['sistema_usd']
            dif_bs = usu_bs - self.resumen['sistema_bs']
            dif_cop = usu_cop - self.resumen['sistema_cop']
            
            es_perfecto = (abs(dif_usd) < 0.1 and abs(dif_bs) < 1 and abs(dif_cop) < 100)
            color = "#03DAC6" if es_perfecto else "#CF6679"
            texto = "✅ CUADRE PERFECTO" if es_perfecto else "⚠️ DESCUADRE DETECTADO"
            
            self.lbl_diff.setText(f"{texto}\nDif: $ {dif_usd:.2f} | Bs {dif_bs:.2f} | COP {dif_cop:.0f}")
            self.lbl_diff.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color}; border: none; text-align: center;")
            
        except ValueError:
            self.lbl_diff.setText("Ingrese montos numéricos válidos...")
            self.lbl_diff.setStyleSheet("font-size: 13px; color: #B3B3B3; border: none;")

    def ejecutar_cierre(self):
        try:
            final_usd = float(self.txt_final_usd.text() or 0)
            final_bs = float(self.txt_final_bs.text() or 0)
            final_cop = float(self.txt_final_cop.text() or 0)
            
            dif_usd = final_usd - self.resumen['sistema_usd']
            if abs(dif_usd) > 5: 
                resp = QMessageBox.warning(self, "Diferencia Detectada", 
                                        f"Hay un descuadre de ${dif_usd:.2f}.\n¿Está seguro de cerrar la caja con esta diferencia?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if resp == QMessageBox.StandardButton.No:
                    return

            exito, msg = CashController.cerrar_caja(self.sesion_id, final_usd, final_bs, final_cop, "Cierre Normal")
            if exito:
                QMessageBox.information(self, "Caja Cerrada", "El turno ha sido cerrado.\nPuede imprimir el Reporte Z en el módulo de Reportes.")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", msg)
        except ValueError:
            QMessageBox.warning(self, "Error", "Verifique los montos ingresados.")