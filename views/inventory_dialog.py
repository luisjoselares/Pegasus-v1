from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QCheckBox, QHBoxLayout, QLabel, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt
from controllers.inventory_controller import InventoryController
from controllers.master_data_controller import MasterDataController

class InventoryDialog(QDialog):
    def __init__(self, parent=None, producto=None):
        super().__init__(parent)
        self.producto = producto 
        self.setWindowTitle("Nuevo Producto" if not producto else "Editar Producto")
        self.setFixedWidth(500) # Un poco más ancho para los precios
        self.iva_tasa = 0.16
        
        # Obtenemos tasas actuales para referencia visual
        tasas = InventoryController.obtener_tasas()
        self.tasa_bcv = tasas['bcv']
        self.tasa_cop = tasas['cop']
        
        # Estilos oscuros
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; color: white; }
            QLabel { font-weight: bold; color: #BBB; }
            QLineEdit, QComboBox { 
                background-color: #2D2D2D; color: white; padding: 6px; 
                border: 1px solid #444; border-radius: 4px;
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #6200EE; }
            QLineEdit:disabled, QLineEdit:read-only { 
                background-color: #1A1A1A; color: #AAA; border: 1px solid #333; 
            }
        """)
        
        self.init_ui()

        if self.producto:
            self.cargar_datos()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.txt_codigo = QLineEdit()
        self.txt_codigo.setPlaceholderText("Código de Barras o Interno")
        
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Descripción del Producto")
        
        # --- PRECIOS MULTIMONEDA ---
        
        # 1. Base y Final USD
        h_usd = QHBoxLayout()
        self.txt_precio = QLineEdit("0.00")
        self.txt_precio.setPlaceholderText("Base $")
        self.txt_precio.textEdited.connect(self.calcular_precios_desde_base) 
        
        self.txt_final = QLineEdit("0.00")
        self.txt_final.setPlaceholderText("Final $ (Con IVA)")
        self.txt_final.setStyleSheet("color: #03DAC6; font-weight: bold;")
        self.txt_final.textEdited.connect(self.calcular_base_desde_final)
        
        h_usd.addWidget(QLabel("Base $:"))
        h_usd.addWidget(self.txt_precio)
        h_usd.addWidget(QLabel("➡ PVP $:"))
        h_usd.addWidget(self.txt_final)

        # 2. Referencia Bs y COP (Solo lectura)
        h_otras = QHBoxLayout()
        self.txt_final_bs = QLineEdit("0.00")
        self.txt_final_bs.setReadOnly(True)
        self.txt_final_bs.setPlaceholderText("Bs (PVP)")
        
        self.txt_final_cop = QLineEdit("0")
        self.txt_final_cop.setReadOnly(True)
        self.txt_final_cop.setPlaceholderText("COP (PVP)")
        
        h_otras.addWidget(QLabel(f"Bs ({self.tasa_bcv}):"))
        h_otras.addWidget(self.txt_final_bs)
        h_otras.addWidget(QLabel(f"COP ({self.tasa_cop}):"))
        h_otras.addWidget(self.txt_final_cop)
        
        self.cmb_categoria = QComboBox()
        self.cmb_proveedor = QComboBox()
        self.llenar_combos() 
        
        self.txt_minimo = QLineEdit("5")
        
        self.chk_exento = QCheckBox("Producto Exento de IVA")
        self.chk_exento.setStyleSheet("color: white;")
        self.chk_exento.toggled.connect(self.recalcular_al_cambiar_impuesto)

        form.addRow("Código:", self.txt_codigo)
        form.addRow("Descripción:", self.txt_desc)
        form.addRow("Precios USD:", h_usd)
        form.addRow("Ref. Moneda:", h_otras)
        form.addRow("Categoría:", self.cmb_categoria)
        form.addRow("Proveedor:", self.cmb_proveedor)
        form.addRow("Stock Mínimo:", self.txt_minimo)
        form.addRow("", self.chk_exento)

        layout.addLayout(form)

        h_btns = QHBoxLayout()
        btn_cancel = QPushButton("CANCELAR")
        btn_cancel.clicked.connect(self.reject)
        btn_cancel.setStyleSheet("background: transparent; color: #CF6679; border: 1px solid #CF6679; padding: 8px; font-weight: bold;")
        
        btn_save = QPushButton("GUARDAR")
        btn_save.clicked.connect(self.validar_y_guardar)
        btn_save.setStyleSheet("background-color: #6200EE; color: white; border: none; padding: 10px; font-weight: bold;")
        btn_save.setDefault(True)
        btn_save.setAutoDefault(True)
        
        h_btns.addWidget(btn_cancel)
        h_btns.addWidget(btn_save)
        layout.addLayout(h_btns)

    # --- LÓGICA DE CÁLCULOS ---
    def obtener_tasa_iva(self):
        return 0 if self.chk_exento.isChecked() else self.iva_tasa

    def calcular_precios_desde_base(self):
        """ Escribo Base $ -> Calcula Final $, Bs y COP """
        try:
            base_usd = float(self.txt_precio.text().replace(',', '.') or 0)
            final_usd = base_usd * (1 + self.obtener_tasa_iva())
            
            # Bloqueamos señales para evitar bucles
            self.txt_final.blockSignals(True)
            self.txt_final.setText(f"{final_usd:.2f}")
            self.txt_final.blockSignals(False)
            
            self.actualizar_otras_monedas(final_usd)
        except ValueError: pass

    def calcular_base_desde_final(self):
        """ Escribo Final $ -> Calcula Base $, Bs y COP """
        try:
            final_usd = float(self.txt_final.text().replace(',', '.') or 0)
            base_usd = final_usd / (1 + self.obtener_tasa_iva())
            
            self.txt_precio.blockSignals(True)
            self.txt_precio.setText(f"{base_usd:.2f}")
            self.txt_precio.blockSignals(False)
            
            self.actualizar_otras_monedas(final_usd)
        except ValueError: pass
        
    def actualizar_otras_monedas(self, precio_final_usd):
        # Bs
        precio_bs = precio_final_usd * self.tasa_bcv
        self.txt_final_bs.setText(f"{precio_bs:.2f}")
        
        # COP
        precio_cop = precio_final_usd * self.tasa_cop
        self.txt_final_cop.setText(f"{precio_cop:,.0f}".replace(',', '.'))

    def recalcular_al_cambiar_impuesto(self):
        self.calcular_precios_desde_base()

    def llenar_combos(self):
        cats = MasterDataController.obtener_categorias()
        self.cmb_categoria.addItem("Sin Categoría", None)
        for c in cats:
            id_cat = c['id'] if isinstance(c, dict) else c[0]
            nom_cat = c['nombre'] if isinstance(c, dict) else c[1]
            self.cmb_categoria.addItem(nom_cat, id_cat)
            
        provs = MasterDataController.obtener_proveedores()
        self.cmb_proveedor.addItem("Sin Proveedor", None)
        for p in provs:
            id_prov = p['id'] if isinstance(p, dict) else p[0]
            try:
                nom_prov = p['razon_social'] if isinstance(p, dict) else p[2]
            except: nom_prov = "Proveedor"
            self.cmb_proveedor.addItem(nom_prov, id_prov)

    def cargar_datos(self):
        self.txt_codigo.setText(str(self.producto.get('codigo', '')))
        self.txt_desc.setText(str(self.producto.get('descripcion', '')))
        self.txt_precio.setText(str(self.producto.get('precio_usd', '0.00')))
        self.txt_minimo.setText(str(self.producto.get('stock_minimo', '5')))
        self.chk_exento.setChecked(bool(self.producto.get('es_exento', 0)))
        
        # Disparar cálculo visual
        self.calcular_precios_desde_base()
        
        idx_cat = self.cmb_categoria.findData(self.producto.get('categoria_id'))
        if idx_cat >= 0: self.cmb_categoria.setCurrentIndex(idx_cat)
        
        idx_prov = self.cmb_proveedor.findData(self.producto.get('proveedor_id'))
        if idx_prov >= 0: self.cmb_proveedor.setCurrentIndex(idx_prov)

        self.txt_codigo.setReadOnly(True)
        self.txt_codigo.setStyleSheet("background-color: #151515; color: #555;")

    def validar_y_guardar(self):
        cod = self.txt_codigo.text().strip().upper()
        desc = self.txt_desc.text().strip().upper()
        
        try:
            precio = float(self.txt_precio.text().replace(',', '.'))
            minimo = float(self.txt_minimo.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Precio y Mínimo deben ser números válidos.")
            return

        if not cod or not desc:
            QMessageBox.warning(self, "Error", "Código y Descripción son obligatorios.")
            return
            
        datos = {
            'codigo': cod,
            'descripcion': desc,
            'precio_usd': precio,
            'stock_actual': 0, 
            'stock_minimo': minimo,
            'es_exento': 1 if self.chk_exento.isChecked() else 0,
            'categoria_id': self.cmb_categoria.currentData(),
            'proveedor_id': self.cmb_proveedor.currentData()
        }

        if self.producto:
            exito = InventoryController.actualizar_producto(self.producto['id'], datos)
            msg_exito = "Producto actualizado."
        else:
            exito = InventoryController.añadir_producto(datos)
            msg_exito = "Producto registrado."
            
        if exito:
            QMessageBox.information(self, "Éxito", msg_exito)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudo guardar (Verifique código duplicado).")