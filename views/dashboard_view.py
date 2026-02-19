from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

# Intentamos importar matplotlib, si falla mostramos aviso elegante
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from controllers.stats_controller import StatsController
from core.app_signals import comunicacion

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.cargar_datos()
        
        # Conectamos señal para actualización en tiempo real
        comunicacion.venta_realizada.connect(self.cargar_datos)

    def init_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(20, 20, 20, 20)
        self.layout_principal.setSpacing(20)
        
        # --- 1. HEADER ---
        lbl_titulo = QLabel("📊 VISIÓN GENERAL DEL NEGOCIO")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: 900; color: #03DAC6; letter-spacing: 1px;")
        self.layout_principal.addWidget(lbl_titulo)

        # --- 2. TARJETAS KPI (Indicadores) ---
        self.layout_kpi = QHBoxLayout()
        self.layout_kpi.setSpacing(15)

        # Creamos 4 tarjetas con colores distintivos
        self.card_ventas = self.crear_card("VENTAS HOY", "$0.00", "💰", "#BB86FC") # Morado
        self.card_ganancia = self.crear_card("GANANCIA EST.", "$0.00", "📈", "#03DAC6") # Teal
        self.card_trans = self.crear_card("TRANSACCIONES", "0", "🧾", "#018786") # Teal Oscuro
        self.card_stock = self.crear_card("STOCK BAJO", "0", "⚠️", "#CF6679") # Rojo

        self.layout_kpi.addWidget(self.card_ventas)
        self.layout_kpi.addWidget(self.card_ganancia)
        self.layout_kpi.addWidget(self.card_trans)
        self.layout_kpi.addWidget(self.card_stock)
        
        self.layout_principal.addLayout(self.layout_kpi)

        # --- 3. ÁREA DE GRÁFICOS ---
        self.layout_graficos = QHBoxLayout()
        self.layout_graficos.setSpacing(15)
        
        if MATPLOTLIB_AVAILABLE:
            # Contenedor Gráfico Barras (Izquierda)
            frame_barras = QFrame()
            frame_barras.setStyleSheet("background-color: #1E1E1E; border-radius: 10px; border: 1px solid #333;")
            lay_barras = QVBoxLayout(frame_barras)
            
            self.fig_barras, self.ax_barras = plt.subplots(figsize=(5, 3))
            self.aplicar_estilo_oscuro(self.fig_barras, self.ax_barras)
            
            self.canvas_barras = FigureCanvas(self.fig_barras)
            lay_barras.addWidget(QLabel("📅 Ventas Últimos 7 Días"))
            lay_barras.addWidget(self.canvas_barras)
            
            # Contenedor Gráfico Torta (Derecha)
            frame_pie = QFrame()
            frame_pie.setStyleSheet("background-color: #1E1E1E; border-radius: 10px; border: 1px solid #333;")
            lay_pie = QVBoxLayout(frame_pie)
            
            self.fig_pie, self.ax_pie = plt.subplots(figsize=(4, 3))
            self.fig_pie.patch.set_facecolor('#1E1E1E') # Fondo figura
            
            self.canvas_pie = FigureCanvas(self.fig_pie)
            lay_pie.addWidget(QLabel("💳 Métodos de Pago"))
            lay_pie.addWidget(self.canvas_pie)
            
            # Añadir al layout (60% barras, 40% torta)
            self.layout_graficos.addWidget(frame_barras, 6)
            self.layout_graficos.addWidget(frame_pie, 4)
        else:
            lbl_error = QLabel("⚠️ Librería 'matplotlib' no instalada. Los gráficos no están disponibles.")
            lbl_error.setStyleSheet("color: #CF6679; padding: 20px; background: #222; border-radius: 8px;")
            lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout_graficos.addWidget(lbl_error)

        self.layout_principal.addLayout(self.layout_graficos)

        # --- 4. TABLA TOP PRODUCTOS ---
        lbl_top = QLabel("🔥 PRODUCTOS MÁS VENDIDOS")
        lbl_top.setStyleSheet("font-size: 14px; font-weight: bold; color: #AAA; margin-top: 10px;")
        self.layout_principal.addWidget(lbl_top)

        self.tabla_top = QTableWidget()
        self.tabla_top.setColumnCount(3)
        self.tabla_top.setHorizontalHeaderLabels(["CÓDIGO", "PRODUCTO", "CANTIDAD"])
        
        # Configuración de la tabla
        self.tabla_top.verticalHeader().setVisible(False)
        self.tabla_top.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla_top.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_top.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_top.setFocusPolicy(Qt.FocusPolicy.NoFocus) # Quita el marco punteado
        self.tabla_top.setFixedHeight(200)
        
        # --- ESTILOS CSS (CORREGIDO) ---
        self.tabla_top.setStyleSheet("""
            QTableWidget {
                background-color: #121212; 
                color: white; 
                gridline-color: #333;
                border: 1px solid #333; 
                border-radius: 8px;
                outline: none; /* Quita el foco por defecto */
            }
            QTableWidget::item { padding: 8px; }
            
            /* --- ESTILO DE SELECCIÓN (El que faltaba) --- */
            QTableWidget::item:selected {
                background-color: #252525;  /* Fondo gris oscuro al seleccionar */
                color: #03DAC6;            /* Texto Teal */
                border-bottom: 1px solid #03DAC6; /* Borde sutil inferior */
            }

            QHeaderView::section { 
                background-color: #1E1E1E; 
                color: #B0B0B0; 
                border: none;
                border-bottom: 2px solid #333; 
                padding: 6px; 
                font-weight: bold;
            }
        """)
        self.layout_principal.addWidget(self.tabla_top)

    def crear_card(self, titulo, valor, icono, color_borde):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #1E1E1E;
                border: 1px solid #333;
                border-left: 4px solid {color_borde};
                border-radius: 8px;
            }}
        """)
        # Layout interno de la tarjeta
        layout = QGridLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_icon = QLabel(icono)
        lbl_icon.setStyleSheet("font-size: 24px; border: none;")
        
        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("color: #888; font-size: 11px; font-weight: bold; text-transform: uppercase; border: none;")
        
        lbl_val = QLabel(valor)
        lbl_val.setStyleSheet(f"color: {color_borde}; font-size: 20px; font-weight: 900; border: none;")
        lbl_val.setObjectName("valor") # ID para actualizar luego
        
        layout.addWidget(lbl_tit, 0, 0)
        layout.addWidget(lbl_icon, 0, 1, 2, 1, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(lbl_val, 1, 0)
        
        return frame

    def aplicar_estilo_oscuro(self, fig, ax):
        """Aplica colores oscuros a los gráficos de Matplotlib"""
        color_bg = '#1E1E1E'
        color_text = '#AAAAAA'
        
        fig.patch.set_facecolor(color_bg)
        ax.set_facecolor(color_bg)
        
        # Colores de ejes y textos
        ax.tick_params(axis='x', colors=color_text)
        ax.tick_params(axis='y', colors=color_text)
        ax.spines['bottom'].set_color('#444')
        ax.spines['left'].set_color('#444')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    def cargar_datos(self):
        # 1. Cargar KPIs
        kpis = StatsController.obtener_kpis_hoy()
        if kpis:
            self.card_ventas.findChild(QLabel, "valor").setText(f"${kpis['ventas']:,.2f}")
            self.card_ganancia.findChild(QLabel, "valor").setText(f"${kpis['ganancia']:,.2f}")
            self.card_trans.findChild(QLabel, "valor").setText(str(kpis['transacciones']))
            self.card_stock.findChild(QLabel, "valor").setText(f"{kpis['stock_bajo']}")

        if MATPLOTLIB_AVAILABLE:
            self.actualizar_grafico_barras()
            self.actualizar_grafico_pie()

        # 4. Cargar Tabla Top
        top_prods = StatsController.obtener_top_productos()
        self.tabla_top.setRowCount(0)
        
        for prod in top_prods:
            # prod = (codigo, descripcion, cantidad)
            row = self.tabla_top.rowCount()
            self.tabla_top.insertRow(row)
            
            # Código
            item_cod = QTableWidgetItem(str(prod[0]))
            item_cod.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_top.setItem(row, 0, item_cod)
            
            # Descripción
            self.tabla_top.setItem(row, 1, QTableWidgetItem(str(prod[1])))
            
            # Cantidad
            item_cant = QTableWidgetItem(f"{prod[2]:.0f}")
            item_cant.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_cant.setForeground(QColor("#03DAC6")) # Color Teal para resaltar
            item_cant.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.tabla_top.setItem(row, 2, item_cant)

    def actualizar_grafico_barras(self):
        fechas, montos = StatsController.obtener_ventas_semana()
        self.ax_barras.clear()
        
        if fechas:
            barras = self.ax_barras.bar(fechas, montos, color='#6200EE', width=0.6)
            
            # Etiquetas encima de las barras
            for bar in barras:
                height = bar.get_height()
                if height > 0:
                    self.ax_barras.text(bar.get_x() + bar.get_width()/2., height,
                            f'${int(height)}', ha='center', va='bottom', color='white', fontsize=9)
        else:
            self.ax_barras.text(0.5, 0.5, "Sin datos recientes", ha='center', va='center', color='#555')

        self.canvas_barras.draw()

    def actualizar_grafico_pie(self):
        labels, values = StatsController.obtener_metodos_pago()
        self.ax_pie.clear()
        
        if values:
            colors = ['#03DAC6', '#BB86FC', '#CF6679', '#018786', '#3700B3']
            wedges, texts, autotexts = self.ax_pie.pie(
                values, labels=None, autopct='%1.1f%%',
                startangle=90, colors=colors, pctdistance=0.85,
                textprops=dict(color="white", fontsize=9, weight="bold")
            )
            
            # Dona (Agujero en el centro)
            centre_circle = plt.Circle((0,0),0.70,fc='#1E1E1E')
            self.fig_pie.gca().add_artist(centre_circle)
            
            self.ax_pie.legend(wedges, labels, loc="center", frameon=False, labelcolor="#CCC", fontsize=8)
        else:
            self.ax_pie.text(0, 0, "Sin ventas", ha='center', va='center', color='#555')

        self.canvas_pie.draw()