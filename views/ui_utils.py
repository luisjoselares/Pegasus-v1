import os
import sys
from PyQt6.QtWidgets import QApplication

def aplicar_estilo_global(app: QApplication):
    """
    Lee el archivo QSS y lo aplica a toda la aplicación Pegasus.
    """
    ruta_estilo = "views/styles/modern_style.qss"
    if hasattr(sys, '_MEIPASS'): # Para cuando lo conviertas en .exe
        ruta_estilo = os.path.join(sys._MEIPASS, ruta_estilo)

    try:
        with open(ruta_estilo, "r") as f:
            estilo = f.read()
            app.setStyleSheet(estilo)
    except FileNotFoundError:
        print("⚠️ Advertencia: No se encontró el archivo de estilos.")