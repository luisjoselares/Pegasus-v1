import sqlite3
import os
from datetime import datetime
from data.conexion import crear_conexion
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm

class ReportsController:
    
    @staticmethod
    def obtener_sesiones_caja():
        conn = crear_conexion()
        if not conn: return []
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cs.*, u.username as cajero 
                FROM caja_sesiones cs
                LEFT JOIN usuarios u ON cs.usuario_id = u.id
                ORDER BY cs.id DESC LIMIT 50
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def obtener_datos_reporte_caja(sesion_id):
        conn = crear_conexion()
        if not conn: return None
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT cs.*, u.username as cajero FROM caja_sesiones cs LEFT JOIN usuarios u ON cs.usuario_id = u.id WHERE cs.id = ?", (sesion_id,))
            sesion = dict(cursor.fetchone())
            
            cursor.execute("SELECT * FROM configuracion LIMIT 1")
            config = dict(cursor.fetchone() or {})
            
            fecha_inicio = sesion['fecha_apertura']
            fecha_fin = sesion['fecha_cierre'] if sesion['fecha_cierre'] else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # EXTRACCIÓN ESTRICTAMENTE FISCAL
            # Se convierte todo a Bolívares usando la tasa del momento de cada factura
            cursor.execute("""
                SELECT 
                    COUNT(id) as cantidad_facturas, 
                    MIN(nro_documento) as doc_inicial, 
                    MAX(nro_documento) as doc_final,
                    SUM(subtotal_usd * tasa_cambio_momento) as subtotal_bs, 
                    SUM(impuesto_iva_usd * tasa_cambio_momento) as iva_bs, 
                    SUM(total_usd * tasa_cambio_momento) as total_bs
                FROM documentos 
                WHERE tipo_doc = 'FACTURA' AND fecha BETWEEN ? AND ? AND estado = 'PROCESADO'
            """, (fecha_inicio, fecha_fin))
            
            fiscal = dict(cursor.fetchone())
            
            return {'empresa': config, 'sesion': sesion, 'fiscal': fiscal}
        finally:
            conn.close()

    @staticmethod
    def generar_texto_ticket(datos):
        if not datos: return "Error cargando datos del reporte."
        
        s = datos['sesion']
        e = datos['empresa']
        f = datos['fiscal']
        
        es_cierre = s['estado'] == 'CERRADA'
        tipo = "REPORTE Z - CIERRE DIARIO" if es_cierre else "REPORTE X - LECTURA EN CURSO"
        fecha_imp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        linea = "-" * 40 + "\n"
        linea_igual = "=" * 40 + "\n"
        
        txt = f"{e.get('razon_social', 'MI EMPRESA C.A.').center(40)}\n"
        txt += f"RIF: {e.get('rif', 'J-00000000-0').center(40)}\n"
        txt += linea
        txt += f"{tipo.center(40)}\n"
        
        if es_cierre:
            # El Reporte Z lleva una numeración correlativa obligatoria. 
            # Usamos el ID de la sesión como simulador del número Z de la máquina.
            txt += f"NRO REPORTE: Z-{s['id']:06d}\n".center(40) + "\n"
            
        txt += linea
        txt += f"FECHA IMPRESION: {fecha_imp}\n"
        txt += f"CAJERO: {s.get('cajero', 'Admin')}\n"
        txt += linea
        
        txt += f"FACTURA INICIAL: {f.get('doc_inicial') or 'N/A':>23}\n"
        txt += f"FACTURA FINAL:   {f.get('doc_final') or 'N/A':>23}\n"
        txt += f"FACTURAS EMITIDAS: {f.get('cantidad_facturas') or 0:>21}\n"
        txt += linea
        
        # --- CÁLCULO DE DESGLOSE FISCAL ---
        subtotal = f.get('subtotal_bs') or 0.0
        iva = f.get('iva_bs') or 0.0
        total = f.get('total_bs') or 0.0
        
        # Matemáticas de retroceso para hallar Base Imponible y Exento exactos
        if iva > 0:
            base = iva / 0.16
            exento = subtotal - base
        else:
            base = 0.0
            exento = subtotal
            
        # Limpieza de decimales flotantes
        exento = max(0, exento)
        base = max(0, base)
        
        txt += f"VENTAS EXENTAS (E):    Bs{exento:>15,.2f}\n"
        txt += f"BASE IMPONIBLE (G):    Bs{base:>15,.2f}\n"
        txt += f"IMPUESTO IVA (16%):    Bs{iva:>15,.2f}\n"
        txt += linea_igual
        txt += f"TOTAL VENTAS FISCALES: Bs{total:>15,.2f}\n"
        txt += linea_igual
        txt += "\n"
        
        # SIMULACIÓN DE HARDWARE FISCAL
        txt += "MÁQUINA: Z1C2345678".center(40) + "\n"
        txt += "*** FIN DE REPORTE ***".center(40) + "\n"
        return txt

    @staticmethod
    def generar_pdf_ticket(datos, filepath):
        if not datos: return False
        
        texto = ReportsController.generar_texto_ticket(datos)
        lineas = texto.split('\n')
        
        ancho = 80 * mm
        largo = (len(lineas) * 4 * mm) + (20 * mm) 
        
        c = canvas.Canvas(filepath, pagesize=(ancho, largo))
        
        # Utilizamos la fuente de recibo para mantener la consistencia con el ticket de venta
        c.setFont("Courier-Bold", 8.5) 
        
        y = largo - (10 * mm)
        for linea in lineas:
            c.drawString(4 * mm, y, linea)
            y -= 4 * mm 
            
        c.save()
        return True

    @staticmethod
    def obtener_sesion_activa_id():
        conn = crear_conexion()
        if not conn: return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM caja_sesiones WHERE estado = 'ABIERTA' ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    @staticmethod
    def obtener_ultima_sesion_cerrada_id():
        conn = crear_conexion()
        if not conn: return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM caja_sesiones WHERE estado = 'CERRADA' ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()