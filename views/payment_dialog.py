from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, 
                             QDoubleSpinBox, QTabWidget, QWidget, QComboBox,
                             QCheckBox, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt, QTimer

# ====================================================================
# COMPONENTE PERSONALIZADO PARA ENTRADA ÁGIL DE DINERO
# ====================================================================
class POSInput(QDoubleSpinBox):
    def __init__(self, es_cop=False, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.setSpecialValueText("") 
        self.setGroupSeparatorShown(True) 
        self.setRange(0, 999999999 if es_cop else 999999)
        self.setDecimals(0 if es_cop else 2)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # Se eliminó la conexión agresiva textChanged para permitir escritura fluida

    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.selectAll)
        
    def stepBy(self, steps):
        pass 

# ====================================================================
# DIÁLOGO DE PAGOS COMPACTO
# ====================================================================
class PaymentDialog(QDialog):
    def __init__(self, total_usd, iva_usd, tasa_bcv, tasa_cop, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Procesar Pago")
        self.setFixedWidth(550)
        
        self.setStyleSheet("""
            QDialog { background-color: #121212; color: white; }
            QLabel { color: #B3B3B3; font-size: 12px; }
            QDoubleSpinBox {
                background-color: #1E1E1E; color: #FFFFFF; border: 2px solid #333333;
                border-radius: 4px; padding: 2px; font-size: 13px; font-weight: bold;
                selection-background-color: #6200EE;
            }
            QDoubleSpinBox:focus { border: 2px solid #6200EE; }
            QDoubleSpinBox:disabled { background-color: #1A1A1A; color: #555; border: 1px solid #222; }
            QTabWidget::pane { border: 1px solid #333333; background: #1E1E1E; border-radius: 6px; }
            QTabBar::tab { background: #121212; color: #B3B3B3; padding: 5px 12px; border-top-left-radius: 6px; border-top-right-radius: 6px; font-weight: bold; font-size: 11px; }
            QTabBar::tab:selected { background: #1E1E1E; color: #6200EE; border-bottom: 2px solid #6200EE; }
            QTabBar::tab:hover { background: #1E1E1E; color: white; }
            QComboBox { background-color: #1E1E1E; color: white; padding: 4px; border: 2px solid #333333; border-radius: 4px; font-weight: bold;}
            QLineEdit { background-color: #1E1E1E; color: white; padding: 4px; border: 2px solid #333333; border-radius: 4px; font-size: 12px;}
            QLineEdit:focus { border: 2px solid #6200EE; }
        """)
        
        self.total_a_pagar_usd = round(total_usd, 2)
        self.iva_usd = round(iva_usd, 2)
        self.tasa_bcv = tasa_bcv
        self.tasa_cop = tasa_cop
        self.datos_pago = {} 
        
        self.init_ui()
        self.actualizar_restante()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5) 
        layout.setContentsMargins(10, 10, 10, 10) 

        # --- 1. RESUMEN FIJO ---
        frame_totales = QFrame()
        frame_totales.setStyleSheet("QFrame { background-color: #1E1E1E; border: 1px solid #333333; border-radius: 6px; }")
        l_tot = QGridLayout(frame_totales)
        l_tot.setContentsMargins(8, 6, 8, 6) 
        
        lbl_tit_total = QLabel("TOTAL DE LA FACTURA:")
        lbl_tit_total.setStyleSheet("font-weight: bold; color: white; font-size: 13px; border: none;")
        l_tot.addWidget(lbl_tit_total, 0, 0)
        
        self.lbl_total_usd = QLabel(f"$ {self.total_a_pagar_usd:,.2f}")
        self.lbl_total_usd.setStyleSheet("font-size: 20px; color: #03DAC6; font-weight: 900; border: none;")
        self.lbl_total_usd.setAlignment(Qt.AlignmentFlag.AlignRight)
        l_tot.addWidget(self.lbl_total_usd, 0, 1)
        
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setStyleSheet("color: #333; margin: 0px;")
        l_tot.addWidget(line, 1, 0, 1, 2)
        
        total_bs = round(self.total_a_pagar_usd * self.tasa_bcv, 2)
        total_cop = round(self.total_a_pagar_usd * self.tasa_cop, 0)
        
        lbl_fijo_bs_cop = QLabel(f"Equivalente fijo:   Bs {total_bs:,.2f}   |   COP {total_cop:,.0f}")
        lbl_fijo_bs_cop.setStyleSheet("color: #B3B3B3; font-size: 12px; font-weight: bold; border: none;")
        lbl_fijo_bs_cop.setAlignment(Qt.AlignmentFlag.AlignRight)
        l_tot.addWidget(lbl_fijo_bs_cop, 2, 0, 1, 2)

        layout.addWidget(frame_totales)
        
        # --- 2. PANEL DE RETENCIÓN ---
        self.frame_retencion = QFrame()
        self.frame_retencion.setStyleSheet("QFrame { background-color: #1E1E1E; border: 1px solid #6200EE; border-radius: 6px; }")
        l_ret = QVBoxLayout(self.frame_retencion)
        l_ret.setContentsMargins(8, 6, 8, 6) 
        l_ret.setSpacing(4)
        
        self.chk_retencion = QCheckBox("🖩 Cliente Contribuyente Especial (Aplica Retención IVA)")
        self.chk_retencion.setStyleSheet("font-weight: bold; color: #6200EE; border: none; font-size: 12px;")
        self.chk_retencion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_retencion.stateChanged.connect(self.toggle_retencion)
        l_ret.addWidget(self.chk_retencion)
        
        self.panel_ret_detalles = QWidget()
        self.panel_ret_detalles.setStyleSheet("border: none;")
        l_ret_det = QHBoxLayout(self.panel_ret_detalles)
        l_ret_det.setContentsMargins(0, 0, 0, 0)
        
        self.cmb_porcentaje_ret = QComboBox()
        self.cmb_porcentaje_ret.addItems(["75%", "100%"])
        self.cmb_porcentaje_ret.currentIndexChanged.connect(self.actualizar_restante)
        
        self.txt_comprobante_ret = QLineEdit()
        self.txt_comprobante_ret.setPlaceholderText("Nro. Comprobante")
        self.txt_comprobante_ret.textChanged.connect(self.actualizar_restante)
        
        l_ret_det.addWidget(QLabel("Porcentaje:"))
        l_ret_det.addWidget(self.cmb_porcentaje_ret)
        l_ret_det.addSpacing(10)
        l_ret_det.addWidget(QLabel("Comprobante:"))
        l_ret_det.addWidget(self.txt_comprobante_ret, 1)
        
        self.panel_ret_detalles.setVisible(False)
        l_ret.addWidget(self.panel_ret_detalles)
        
        if self.iva_usd <= 0:
            self.chk_retencion.setEnabled(False)
            self.chk_retencion.setText("🖩 Retención de IVA (No aplica - Factura Exenta)")
            self.frame_retencion.setStyleSheet("QFrame { background-color: #1A1A1A; border: 1px solid #333; border-radius: 6px; }")
            self.chk_retencion.setStyleSheet("color: #777; border: none; font-size: 12px;")
            
        layout.addWidget(self.frame_retencion)
        
        # NETO A COBRAR
        self.lbl_neto_cobrar = QLabel()
        self.lbl_neto_cobrar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_neto_cobrar.setVisible(False)
        layout.addWidget(self.lbl_neto_cobrar)
        
        # --- 3. PESTAÑAS DE PAGOS ---
        self.tabs = QTabWidget()
        
        # USD
        self.tab_usd = QWidget()
        l_usd = QGridLayout(self.tab_usd)
        l_usd.setContentsMargins(8, 8, 8, 8); l_usd.setSpacing(6)
        self.spin_usd_efectivo = self.crear_spinbox()
        self.spin_usd_zelle = self.crear_spinbox()
        l_usd.addWidget(QLabel("💵 Efectivo ($):"), 0, 0); l_usd.addWidget(self.spin_usd_efectivo, 0, 1)
        l_usd.addWidget(QLabel("📱 Zelle / Transf ($):"), 1, 0); l_usd.addWidget(self.spin_usd_zelle, 1, 1)
        l_usd.setRowStretch(2, 1) 
        
        # BS
        self.tab_bs = QWidget()
        l_bs = QGridLayout(self.tab_bs)
        l_bs.setContentsMargins(8, 8, 8, 8); l_bs.setSpacing(6)
        self.spin_bs_efectivo = self.crear_spinbox()
        self.spin_bs_punto = self.crear_spinbox()
        self.spin_bs_transf = self.crear_spinbox()
        l_bs.addWidget(QLabel("💵 Efectivo (Bs):"), 0, 0); l_bs.addWidget(self.spin_bs_efectivo, 0, 1)
        l_bs.addWidget(QLabel("💳 Punto de Venta:"), 1, 0); l_bs.addWidget(self.spin_bs_punto, 1, 1)
        l_bs.addWidget(QLabel("📲 Pago Móvil/Transf:"), 2, 0); l_bs.addWidget(self.spin_bs_transf, 2, 1)
        
        # COP
        self.tab_cop = QWidget()
        l_cop = QGridLayout(self.tab_cop)
        l_cop.setContentsMargins(8, 8, 8, 8); l_cop.setSpacing(6)
        self.spin_cop_efectivo = self.crear_spinbox(es_cop=True)
        self.spin_cop_transf = self.crear_spinbox(es_cop=True)
        l_cop.addWidget(QLabel("💵 Efectivo (COP):"), 0, 0); l_cop.addWidget(self.spin_cop_efectivo, 0, 1)
        l_cop.addWidget(QLabel("📲 Transferencia (COP):"), 1, 0); l_cop.addWidget(self.spin_cop_transf, 1, 1)
        l_cop.setRowStretch(2, 1)

        self.tabs.addTab(self.tab_usd, " 🇺🇸 USD ")
        self.tabs.addTab(self.tab_bs, " 🇻🇪 BS ")
        self.tabs.addTab(self.tab_cop, " 🇨🇴 COP ")
        layout.addWidget(self.tabs)

        # --- 4. PANEL DE FALTAN O VUELTO ---
        self.lbl_restante = QLabel("FALTAN: $ 0.00")
        self.lbl_restante.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_restante.setMinimumHeight(30) 
        layout.addWidget(self.lbl_restante)

        self.frame_vuelto = QFrame()
        self.frame_vuelto.setStyleSheet("QFrame { background-color: #121212; border: 1px dashed #03DAC6; border-radius: 6px; } QLabel { border: none; }")
        l_vuelto_main = QVBoxLayout(self.frame_vuelto)
        l_vuelto_main.setContentsMargins(5, 5, 5, 5) 
        
        self.lbl_titulo_vuelto = QLabel("💵 DESGLOSE DE VUELTO A ENTREGAR")
        self.lbl_titulo_vuelto.setStyleSheet("color: #03DAC6; font-weight: bold; font-size: 11px;")
        self.lbl_titulo_vuelto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_vuelto_main.addWidget(self.lbl_titulo_vuelto)
        
        l_vuelto_grid = QGridLayout()
        self.spin_vuelto_usd = self.crear_spinbox_vuelto()
        self.spin_vuelto_bs = self.crear_spinbox_vuelto()
        self.spin_vuelto_cop = self.crear_spinbox_vuelto(es_cop=True)
        
        l_vuelto_grid.addWidget(QLabel("En USD ($):"), 0, 0); l_vuelto_grid.addWidget(self.spin_vuelto_usd, 0, 1)
        l_vuelto_grid.addWidget(QLabel("En Bolívares:"), 1, 0); l_vuelto_grid.addWidget(self.spin_vuelto_bs, 1, 1)
        l_vuelto_grid.addWidget(QLabel("En Pesos (COP):"), 2, 0); l_vuelto_grid.addWidget(self.spin_vuelto_cop, 2, 1)
        l_vuelto_grid.setVerticalSpacing(4)
        
        l_vuelto_main.addLayout(l_vuelto_grid)
        
        self.lbl_vuelto_pendiente = QLabel("Por asignar: $ 0.00")
        self.lbl_vuelto_pendiente.setStyleSheet("color: #FF9800; font-weight: bold; font-size: 11px;")
        self.lbl_vuelto_pendiente.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l_vuelto_main.addWidget(self.lbl_vuelto_pendiente)
        
        self.frame_vuelto.setVisible(False)
        layout.addWidget(self.frame_vuelto)

        # --- BOTÓN PAGAR ---
        self.btn_confirmar = QPushButton("CONFIRMAR PAGO (F10)")
        self.btn_confirmar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirmar.setFixedHeight(40) 
        self.btn_confirmar.setStyleSheet("""
            QPushButton { background-color: #6200EE; color: white; font-weight: bold; font-size: 14px; border-radius: 6px; }
            QPushButton:hover { background-color: #3700B3; }
            QPushButton:disabled { background-color: #1E1E1E; color: #555555; border: 1px solid #333333; }
        """)
        self.btn_confirmar.clicked.connect(self.confirmar_pago)
        layout.addWidget(self.btn_confirmar)

    def crear_spinbox(self, es_cop=False):
        spin = POSInput(es_cop=es_cop, parent=self)
        spin.valueChanged.connect(self.actualizar_restante)
        return spin

    def crear_spinbox_vuelto(self, es_cop=False):
        spin = POSInput(es_cop=es_cop, parent=self)
        spin.valueChanged.connect(self.actualizar_vuelto)
        return spin

    def toggle_retencion(self, state):
        self.panel_ret_detalles.setVisible(state == 2) 
        self.lbl_neto_cobrar.setVisible(state == 2)
        if state != 2:
            self.txt_comprobante_ret.clear()
        self.actualizar_restante()

    def obtener_monto_retencion(self):
        if self.chk_retencion.isChecked() and self.iva_usd > 0:
            porc = 0.75 if self.cmb_porcentaje_ret.currentText() == "75%" else 1.0
            return round(self.iva_usd * porc, 2)
        return 0.0

    def actualizar_restante(self):
        pagado_usd = self.spin_usd_efectivo.value() + self.spin_usd_zelle.value()
        pagado_bs = self.spin_bs_efectivo.value() + self.spin_bs_punto.value() + self.spin_bs_transf.value()
        usd_de_bs = pagado_bs / self.tasa_bcv if self.tasa_bcv > 0 else 0
        pagado_cop = self.spin_cop_efectivo.value() + self.spin_cop_transf.value()
        usd_de_cop = pagado_cop / self.tasa_cop if self.tasa_cop > 0 else 0
        
        total_pagado = round(pagado_usd + usd_de_bs + usd_de_cop, 2)
        monto_retenido = self.obtener_monto_retencion()
        total_a_cobrar_real = round(self.total_a_pagar_usd - monto_retenido, 2)
        
        if monto_retenido > 0:
            self.lbl_neto_cobrar.setText(f"👇 <b>NETO A COBRAR</b>: <span style='color:#03DAC6; font-size: 14px;'>$ {total_a_cobrar_real:,.2f}</span> 👇")
            self.lbl_neto_cobrar.setStyleSheet("background: #1E1E1E; padding: 4px; border-radius: 4px; border: 1px dashed #6200EE;")
        
        diferencia = round(total_a_cobrar_real - total_pagado, 2)
        if abs(diferencia) < 0.01: diferencia = 0

        falta_comprobante = self.chk_retencion.isChecked() and not self.txt_comprobante_ret.text().strip()

        if diferencia > 0:
            self.frame_vuelto.setVisible(False)
            dif_bs = round(diferencia * self.tasa_bcv, 2)
            dif_cop = round(diferencia * self.tasa_cop, 0)
            
            # LIMPIEZA FORZADA DE FANTASMAS: Si falta dinero, el vuelto debe ser cero absoluto.
            self.spin_vuelto_usd.blockSignals(True)
            self.spin_vuelto_bs.blockSignals(True)
            self.spin_vuelto_cop.blockSignals(True)
            self.spin_vuelto_usd.setValue(0.0)
            self.spin_vuelto_bs.setValue(0.0)
            self.spin_vuelto_cop.setValue(0.0)
            self.spin_vuelto_usd.blockSignals(False)
            self.spin_vuelto_bs.blockSignals(False)
            self.spin_vuelto_cop.blockSignals(False)
            
            self.lbl_restante.setText(
                f"⚠️ RESTA POR PAGAR: <b>$ {diferencia:,.2f}</b> &nbsp;|&nbsp; "
                f"Bs {dif_bs:,.2f} &nbsp;|&nbsp; COP {dif_cop:,.0f}"
            )
            self.lbl_restante.setStyleSheet("color: white; font-size: 12px; background: #c62828; border-radius: 4px; padding: 4px;")
            
            self.btn_confirmar.setEnabled(False)
            self.btn_confirmar.setText(f"COMPLETE EL PAGO (Faltan ${diferencia:,.2f})")
            
        elif falta_comprobante:
            self.frame_vuelto.setVisible(False)
            
            self.spin_vuelto_usd.blockSignals(True); self.spin_vuelto_bs.blockSignals(True); self.spin_vuelto_cop.blockSignals(True)
            self.spin_vuelto_usd.setValue(0.0); self.spin_vuelto_bs.setValue(0.0); self.spin_vuelto_cop.setValue(0.0)
            self.spin_vuelto_usd.blockSignals(False); self.spin_vuelto_bs.blockSignals(False); self.spin_vuelto_cop.blockSignals(False)
            
            self.lbl_restante.setText("⚠️ INGRESE COMPROBANTE DE RETENCIÓN")
            self.lbl_restante.setStyleSheet("color: white; font-size: 12px; font-weight: bold; background: #e65100; border-radius: 4px; padding: 4px;")
            self.btn_confirmar.setEnabled(False)
            self.btn_confirmar.setText("ESPERANDO COMPROBANTE...")
            
        else:
            if diferencia < 0:
                self.frame_vuelto.setVisible(True)
                vuelto_base = abs(diferencia)
                v_bs = round(vuelto_base * self.tasa_bcv, 2)
                v_cop = round(vuelto_base * self.tasa_cop, 0)
                
                self.lbl_restante.setText(
                    f"✅ SOBRANTE (VUELTO): <b>$ {vuelto_base:,.2f}</b> &nbsp;|&nbsp; "
                    f"Bs {v_bs:,.2f} &nbsp;|&nbsp; COP {v_cop:,.0f}"
                )
                self.lbl_restante.setStyleSheet("color: white; font-size: 12px; background: #2e7d32; border-radius: 4px; padding: 4px;")
                
                # REASIGNACIÓN TOTAL DINÁMICA: Siempre que el pago cambie, el vuelto se auto-asigna a USD limpio.
                self.spin_vuelto_usd.blockSignals(True)
                self.spin_vuelto_bs.blockSignals(True)
                self.spin_vuelto_cop.blockSignals(True)
                
                self.spin_vuelto_usd.setValue(vuelto_base)
                self.spin_vuelto_bs.setValue(0.0)
                self.spin_vuelto_cop.setValue(0.0)
                
                self.spin_vuelto_usd.blockSignals(False)
                self.spin_vuelto_bs.blockSignals(False)
                self.spin_vuelto_cop.blockSignals(False)
                
                self.actualizar_vuelto() 
            else:
                self.frame_vuelto.setVisible(False)
                
                # Pago exacto: limpiar basuras de vuelto previas
                self.spin_vuelto_usd.blockSignals(True); self.spin_vuelto_bs.blockSignals(True); self.spin_vuelto_cop.blockSignals(True)
                self.spin_vuelto_usd.setValue(0.0); self.spin_vuelto_bs.setValue(0.0); self.spin_vuelto_cop.setValue(0.0)
                self.spin_vuelto_usd.blockSignals(False); self.spin_vuelto_bs.blockSignals(False); self.spin_vuelto_cop.blockSignals(False)

                self.lbl_restante.setText(f"✅ PAGO EXACTO")
                self.lbl_restante.setStyleSheet("color: #03DAC6; font-size: 13px; font-weight: bold; background: #1E1E1E; border: 1px solid #03DAC6; border-radius: 4px; padding: 4px;")
                self.btn_confirmar.setEnabled(True)
                self.btn_confirmar.setText("CONFIRMAR PAGO (F10)")
                self.btn_confirmar.setStyleSheet("""
                    QPushButton { background-color: #03DAC6; color: black; font-weight: bold; font-size: 14px; border-radius: 6px; }
                    QPushButton:hover { background-color: #00F0DA; }
                """)

    def actualizar_vuelto(self):
        monto_retenido = self.obtener_monto_retencion()
        total_a_cobrar_real = round(self.total_a_pagar_usd - monto_retenido, 2)
        
        pagado_usd = self.spin_usd_efectivo.value() + self.spin_usd_zelle.value()
        pagado_bs = self.spin_bs_efectivo.value() + self.spin_bs_punto.value() + self.spin_bs_transf.value()
        usd_de_bs = pagado_bs / self.tasa_bcv if self.tasa_bcv > 0 else 0
        pagado_cop = self.spin_cop_efectivo.value() + self.spin_cop_transf.value()
        usd_de_cop = pagado_cop / self.tasa_cop if self.tasa_cop > 0 else 0
        
        total_pagado = round(pagado_usd + usd_de_bs + usd_de_cop, 2)
        diferencia = round(total_a_cobrar_real - total_pagado, 2)
        
        if diferencia >= 0: return 
        
        vuelto_total = abs(diferencia)
        
        vuelto_asignado_usd = self.spin_vuelto_usd.value()
        vuelto_asignado_bs_en_usd = self.spin_vuelto_bs.value() / self.tasa_bcv if self.tasa_bcv > 0 else 0
        vuelto_asignado_cop_en_usd = self.spin_vuelto_cop.value() / self.tasa_cop if self.tasa_cop > 0 else 0
        
        asignado_total = round(vuelto_asignado_usd + vuelto_asignado_bs_en_usd + vuelto_asignado_cop_en_usd, 2)
        pendiente = round(vuelto_total - asignado_total, 2)
        
        pend_bs = round(pendiente * self.tasa_bcv, 2)
        pend_cop = round(pendiente * self.tasa_cop, 0)
        
        if abs(pendiente) < 0.05: 
            self.lbl_vuelto_pendiente.setText("✅ Vuelto distribuido correctamente")
            self.lbl_vuelto_pendiente.setStyleSheet("color: #03DAC6; font-weight: bold; font-size: 12px;")
            self.btn_confirmar.setEnabled(True)
            self.btn_confirmar.setText("CONFIRMAR PAGO (F10)")
            self.btn_confirmar.setStyleSheet("""
                QPushButton { background-color: #03DAC6; color: black; font-weight: bold; font-size: 14px; border-radius: 6px; }
                QPushButton:hover { background-color: #00F0DA; }
            """)
        else:
            if pendiente > 0:
                self.lbl_vuelto_pendiente.setText(
                    f"⚠️ Falta asignar: <b>$ {pendiente:,.2f}</b> &nbsp;|&nbsp; Bs {pend_bs:,.2f} &nbsp;|&nbsp; COP {pend_cop:,.0f}"
                )
                self.lbl_vuelto_pendiente.setStyleSheet("color: #FF9800; font-size: 12px;")
            else:
                self.lbl_vuelto_pendiente.setText(
                    f"❌ Exceso asignado: <b>$ {abs(pendiente):,.2f}</b> &nbsp;|&nbsp; Bs {abs(pend_bs):,.2f} &nbsp;|&nbsp; COP {abs(pend_cop):,.0f}"
                )
                self.lbl_vuelto_pendiente.setStyleSheet("color: #F44336; font-size: 12px;")
                
            self.btn_confirmar.setEnabled(False)
            self.btn_confirmar.setText("DISTRIBUYA EL VUELTO EXACTO")
            self.btn_confirmar.setStyleSheet("QPushButton { background-color: #1E1E1E; color: #555555; border: 1px solid #333; }")

    def confirmar_pago(self):
        pagado_usd = self.spin_usd_efectivo.value() + self.spin_usd_zelle.value()
        pagado_bs = self.spin_bs_efectivo.value() + self.spin_bs_punto.value() + self.spin_bs_transf.value()
        pagado_cop = self.spin_cop_efectivo.value() + self.spin_cop_transf.value()
        
        monto_retenido = self.obtener_monto_retencion()
        
        self.datos_pago = {
            'metodo_pago': 'MIXTO',
            'pago_usd_efectivo': self.spin_usd_efectivo.value(),
            'pago_usd_zelle': self.spin_usd_zelle.value(),
            'pago_bs_efectivo': self.spin_bs_efectivo.value(),
            'pago_bs_punto': self.spin_bs_punto.value(),
            'pago_bs_transf': self.spin_bs_transf.value(),
            'pago_cop_efectivo': self.spin_cop_efectivo.value(),
            'pago_cop_transf': self.spin_cop_transf.value(),
            
            'recibido_usd': pagado_usd,
            'recibido_bs': pagado_bs,
            'recibido_cop': pagado_cop,
            
            'vuelto_usd': self.spin_vuelto_usd.value(),
            'vuelto_bs': self.spin_vuelto_bs.value(),
            'vuelto_cop': self.spin_vuelto_cop.value(),
            
            'aplica_retencion': self.chk_retencion.isChecked() and self.iva_usd > 0,
            'porcentaje_retencion': 75.0 if self.cmb_porcentaje_ret.currentText() == "75%" else 100.0 if self.chk_retencion.isChecked() else 0.0,
            'monto_retenido_usd': monto_retenido,
            'comprobante_retencion': self.txt_comprobante_ret.text().strip() if self.chk_retencion.isChecked() else None
        }
        
        metodos = []
        if pagado_usd > 0: metodos.append("USD")
        if pagado_bs > 0: metodos.append("BS")
        if pagado_cop > 0: metodos.append("COP")
        if self.chk_retencion.isChecked() and self.iva_usd > 0: metodos.append("RET_IVA")
        
        if len(metodos) == 1: self.datos_pago['metodo_pago'] = metodos[0]
        
        self.accept()

    def get_data(self):
        return self.datos_pago