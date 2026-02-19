from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from controllers.config_controller import ConfigController

class ScreensaverView(QWidget):
    # Señal para avisar a la ventana principal que debe "despertar"
    desbloquear_sistema = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #0d0d0d;") # Fondo casi negro profundo
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        # --- CONTENEDOR CENTRAL ---
        card = QFrame()
        card.setFixedWidth(700)
        card.setStyleSheet("""
            QFrame {
                background-color: #151515;
                border: 2px solid #333;
                border-radius: 20px;
                padding: 40px;
            }
        """)
        l_card = QVBoxLayout(card)
        l_card.setSpacing(15)
        l_card.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # LOGO
        lbl_logo = QLabel("PEGASUS FISCO")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_logo.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-size: 60px; 
            font-weight: 900; 
            color: #6200EE;
            letter-spacing: 8px;
            margin-bottom: 20px;
        """)
        
        # DATOS DE LA EMPRESA (Placeholders que se llenarán dinámicamente)
        self.lbl_empresa = QLabel("CARGANDO EMPRESA...")
        self.lbl_empresa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_empresa.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        self.lbl_empresa.setWordWrap(True)

        self.lbl_rif = QLabel("J-00000000-0")
        self.lbl_rif.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_rif.setStyleSheet("color: #03DAC6; font-size: 22px; font-weight: bold; letter-spacing: 2px;")

        self.lbl_dir = QLabel("Dirección Fiscal...")
        self.lbl_dir.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_dir.setStyleSheet("color: #888; font-size: 16px; margin-top: 10px;")
        self.lbl_dir.setWordWrap(True)

        # PIE DE PÁGINA
        lbl_footer = QLabel("Haga clic en cualquier lugar para volver")
        lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_footer.setStyleSheet("color: #444; font-size: 14px; margin-top: 40px; font-style: italic;")

        # Animación de "respiración" para el footer
        self.opacity_effect = QGraphicsOpacityEffect(lbl_footer)
        lbl_footer.setGraphicsEffect(self.opacity_effect)
        
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(1500)
        self.anim.setStartValue(0.3)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.anim.setLoopCount(-1) # Infinito
        self.anim.start()

        l_card.addWidget(lbl_logo)
        l_card.addWidget(self.lbl_empresa)
        l_card.addWidget(self.lbl_rif)
        l_card.addWidget(self.lbl_dir)
        l_card.addWidget(lbl_footer)

        layout.addWidget(card)

    def showEvent(self, event):
        """Cada vez que se muestra esta pantalla, recargamos los datos actualizados."""
        config = ConfigController.obtener_configuracion()
        if config:
            self.lbl_empresa.setText(config.get('razon_social', 'SIN NOMBRE').upper())
            self.lbl_rif.setText(f"RIF: {config.get('rif', 'N/A')}")
            direc = config.get('direccion_fiscal', 'Sin dirección')
            self.lbl_dir.setText(direc if direc else "Sin dirección fiscal registrada")
        super().showEvent(event)

    def mousePressEvent(self, event):
        """Cualquier clic emite la señal para desbloquear."""
        self.desbloquear_sistema.emit()