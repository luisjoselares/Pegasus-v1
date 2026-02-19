import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout
# ASEGÚRATE DE QUE QWebEngineView ESTÉ IMPORTADO
from PyQt6.QtWebEngineWidgets import QWebEngineView 
from PyQt6.QtCore import QUrl

class InvoiceViewerDialog(QDialog):
    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visor de Documento")
        self.resize(900, 950) 
        self.setStyleSheet("background-color: #121212;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0) 
        self.visor = QWebEngineView()
        
        # Habilitar plugins para el visor PDF nativo de Chromium
        settings = self.visor.settings()
        settings.setAttribute(settings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(settings.WebAttribute.PdfViewerEnabled, True)
  
        full_path = os.path.abspath(pdf_path)
        base_url = QUrl.fromLocalFile(full_path).toString()
    
        final_url = base_url + "#view=FitH"
        self.visor.load(QUrl(final_url))
       
        
        layout.addWidget(self.visor)