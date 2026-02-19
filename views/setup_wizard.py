import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QStackedWidget, 
                             QCheckBox, QMessageBox)
from PyQt6.QtCore import Qt
from controllers.auth_controller import AuthController

class SetupWizard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pegasus Fisco - Asistente de Configuración")
        self.setFixedSize(500, 650)
        
        # 1. Configuración del Layout Principal
        self.layout_principal = QVBoxLayout()
        self.layout_principal.setContentsMargins(30, 30, 30, 30)
        self.layout_principal.setSpacing(15)
        self.setLayout(self.layout_principal)

        # 2. Contenedor de pasos (Stack)
        self.stack = QStackedWidget()
        
        # 3. Inicializar las páginas de los pasos
        self.init_paso_empresa()
        self.init_paso_admin()
        
        # Añadir el stack al layout principal
        self.layout_principal.addWidget(self.stack)

        # 4. Botón de navegación (Se crea antes de conectarlo)
        self.btn_siguiente = QPushButton("Siguiente Paso")
        self.btn_siguiente.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_siguiente.clicked.connect(self.controlar_navegacion)
        
        self.layout_principal.addWidget(self.btn_siguiente)

    def init_paso_empresa(self):
        """Paso 1: Datos Fiscales del Negocio"""
        self.pagina_empresa = QWidget()
        layout = QVBoxLayout()
        self.pagina_empresa.setLayout(layout)

        titulo = QLabel("Configuración de la Entidad")
        titulo.setObjectName("titulo_setup") # Para CSS específico
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #6200EE; margin-bottom: 5px;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Datos para la emisión de facturas y reportes.")
        subtitulo.setStyleSheet("color: #B3B3B3; margin-bottom: 15px;")
        layout.addWidget(subtitulo)

        # Campos
        layout.addWidget(QLabel("Razón Social:"))
        self.input_razon_social = QLineEdit()
        self.input_razon_social.setPlaceholderText("Nombre legal del negocio")
        layout.addWidget(self.input_razon_social)

        layout.addWidget(QLabel("RIF Fiscal:"))
        self.input_rif = QLineEdit()
        self.input_rif.setPlaceholderText("J-12345678-9")
        layout.addWidget(self.input_rif)

        layout.addWidget(QLabel("Dirección Fiscal:"))
        self.input_direccion = QLineEdit()
        self.input_direccion.setPlaceholderText("Ubicación legal completa")
        layout.addWidget(self.input_direccion)

        layout.addWidget(QLabel("Tasa BCV Inicial (Bs/$):"))
        self.input_tasa_bcv = QLineEdit()
        self.input_tasa_bcv.setPlaceholderText("Ej: 36.50")
        layout.addWidget(self.input_tasa_bcv)

        layout.addSpacing(10)
        self.check_especial = QCheckBox("Es Sujeto Pasivo Especial (IGTF 3%)")
        layout.addWidget(self.check_especial)

        layout.addStretch()
        self.stack.addWidget(self.pagina_empresa)

    def init_paso_admin(self):
        """Paso 2: Datos del Usuario Maestro"""
        self.pagina_admin = QWidget()
        layout = QVBoxLayout()
        self.pagina_admin.setLayout(layout)

        titulo = QLabel("Usuario Administrador")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #6200EE; margin-bottom: 5px;")
        layout.addWidget(titulo)

        subtitulo = QLabel("Cree la cuenta con acceso total al sistema.")
        subtitulo.setStyleSheet("color: #B3B3B3; margin-bottom: 15px;")
        layout.addWidget(subtitulo)

        layout.addWidget(QLabel("Nombre del Propietario:"))
        self.input_nombre_real = QLineEdit()
        layout.addWidget(self.input_nombre_real)

        layout.addWidget(QLabel("Cédula / ID:"))
        self.input_cedula = QLineEdit()
        layout.addWidget(self.input_cedula)

        layout.addWidget(QLabel("Nombre de Usuario:"))
        self.input_username = QLineEdit()
        layout.addWidget(self.input_username)

        layout.addWidget(QLabel("Contraseña:"))
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.input_password)

        layout.addWidget(QLabel("Confirmar Contraseña:"))
        self.input_confirm_password = QLineEdit()
        self.input_confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.input_confirm_password)

        layout.addStretch()
        self.stack.addWidget(self.pagina_admin)

    def controlar_navegacion(self):
        """Maneja el cambio entre pasos y la finalización."""
        indice = self.stack.currentIndex()
        
        if indice == 0:
            # Validar que el paso 1 no esté vacío
            if not self.input_razon_social.text() or not self.input_rif.text():
                QMessageBox.warning(self, "Campos Requeridos", "Por favor complete los datos fiscales.")
                return
            self.stack.setCurrentIndex(1)
            self.btn_siguiente.setText("Finalizar Configuración")
        else:
            self.finalizar_setup()

    def finalizar_setup(self):
        """Procesa y guarda la información inicial."""
        # Recolección
        datos_empresa = {
            'razon_social': self.input_razon_social.text().strip(),
            'rif': self.input_rif.text().strip(),
            'direccion': self.input_direccion.text().strip(),
            'tasa_bcv': self.input_tasa_bcv.text().strip() or "0.0",
            'es_especial': 1 if self.check_especial.isChecked() else 0
        }

        datos_admin = {
            'nombre_real': self.input_nombre_real.text().strip(),
            'cedula': self.input_cedula.text().strip(),
            'username': self.input_username.text().strip(),
            'password': self.input_password.text()
        }

        # Validaciones
        if not datos_admin['username'] or not datos_admin['password']:
            QMessageBox.warning(self, "Error", "Debe crear un usuario y contraseña.")
            return

        if datos_admin['password'] != self.input_confirm_password.text():
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden.")
            return

        # Guardado
        exito, mensaje = AuthController.configurar_sistema_inicial(datos_empresa, datos_admin)

        if exito:
            QMessageBox.information(self, "Éxito", "Sistema configurado. Inicie sesión para continuar.")
            self.close()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {mensaje}")