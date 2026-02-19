import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from controllers.auth_controller import AuthController
from views.main_window import MainWindow # Importamos la meta

class LoginView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pegasus Fisco - Acceso")
        self.setFixedSize(400, 550)
        
        # Centrar la ventana en pantalla
        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.main_layout)

        # Tarjeta Central
        self.card = QFrame()
        self.card.setObjectName("login_card")
        self.card.setFixedWidth(340)
        self.card_layout = QVBoxLayout()
        self.card.setLayout(self.card_layout)
        
        # Logo simbólico
        self.icon_label = QLabel("🚀") 
        self.icon_label.setStyleSheet("font-size: 60px; margin-bottom: 10px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_layout.addWidget(self.icon_label)

        # Título
        self.title = QLabel("PEGASUS FISCO")
        self.title.setStyleSheet("font-size: 24px; font-weight: bold; color: #6200EE; margin-bottom: 5px;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_layout.addWidget(self.title)

        self.subtitle = QLabel("Ingrese sus credenciales")
        self.subtitle.setStyleSheet("color: #B3B3B3; margin-bottom: 20px;")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_layout.addWidget(self.subtitle)

        # Campos de entrada
        self.card_layout.addWidget(QLabel("Usuario:"))
        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("Nombre de usuario")
        self.card_layout.addWidget(self.input_user)

        self.card_layout.addSpacing(10)

        self.card_layout.addWidget(QLabel("Contraseña:"))
        self.input_pass = QLineEdit()
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.setPlaceholderText("••••••••")
        self.input_pass.returnPressed.connect(self.intentar_login) # Enter para entrar
        self.card_layout.addWidget(self.input_pass)

        self.card_layout.addSpacing(30)

        # Botón Ingresar
        self.btn_login = QPushButton("INICIAR SESIÓN")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.clicked.connect(self.intentar_login)
        self.card_layout.addWidget(self.btn_login)

        self.main_layout.addWidget(self.card)

        # Variable para mantener la referencia de la MainWindow
        self.dashboard = None

    def intentar_login(self):
        username = self.input_user.text().strip()
        password = self.input_pass.text()

        if not username or not password:
            QMessageBox.warning(self, "Campos Vacíos", "Por favor, rellene todos los campos.")
            return

        # Validación con el controlador
        exito, mensaje = AuthController.login(username, password)

        if exito:
            # --- MOMENTO DE TRANSICIÓN ---
            # 1. Crear la instancia del Dashboard
            self.dashboard = MainWindow(usuario_actual=username)
            
            # 2. Mostrar el Dashboard
            self.dashboard.show()
            
            # 3. Cerrar la ventana de Login
            self.close()
        else:
            QMessageBox.critical(self, "Error de Acceso", mensaje)
            self.input_pass.clear() # Limpiar clave por seguridad
            self.input_pass.setFocus()