import os
import textwrap
from data.conexion import crear_conexion
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import letter

class PrinterController:
    
    @staticmethod
    def ver_factura(nro_documento):
        """Enruta la impresión: Ticket 80mm para Facturas, Carta para Notas de Entrega"""
        conn = crear_conexion()
        if not conn: return None
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT rif, razon_social, direccion_fiscal FROM configuracion LIMIT 1")
            empresa = cursor.fetchone()
            if not empresa: 
                empresa = {'rif': 'J-00000000-0', 'razon_social': 'EMPRESA NO CONFIGURADA', 'direccion_fiscal': 'DIRECCION NO CONFIGURADA'}

            cursor.execute("""
                SELECT d.*, c.nombre, c.cedula_rif, c.direccion, c.telefono 
                FROM documentos d
                JOIN clientes c ON d.cliente_id = c.id
                WHERE d.nro_documento = ?
            """, (nro_documento,))
            doc = cursor.fetchone()
            if not doc: return None

            cursor.execute("""
                SELECT dd.cantidad, p.codigo_interno, p.descripcion, dd.precio_unitario_usd, 
                       (dd.cantidad * dd.precio_unitario_usd) as subtotal_linea, p.es_exento
                FROM documento_detalles dd
                JOIN productos p ON dd.producto_id = p.id
                WHERE dd.documento_id = ?
            """, (doc['id'],))
            detalles = cursor.fetchall()

            if doc['tipo_doc'] == 'NOTA_ENTREGA':
                return PrinterController._generar_pdf_carta(doc, empresa, detalles)
            else:
                return PrinterController._generar_pdf_ticket(doc, empresa, detalles)
                
        except Exception as e:
            print(f"Error principal de impresión: {e}")
            return None
        finally:
            if conn: conn.close()

    @staticmethod
    def _generar_pdf_carta(doc, empresa, detalles):
        """Genera un PDF en formato Tamaño Carta (Letter) para uso Administrativo"""
        os.makedirs('temp', exist_ok=True)
        ruta_pdf = os.path.abspath(f"temp/ne_{doc['nro_documento']}.pdf")
        
        c = canvas.Canvas(ruta_pdf, pagesize=letter)
        ancho, alto = letter
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, alto - 50, empresa['razon_social'])
        c.setFont("Helvetica", 10)
        c.drawString(50, alto - 65, f"RIF: {empresa['rif']}")
        
        dir_lines = textwrap.wrap(empresa['direccion_fiscal'], width=50)
        y_dir = alto - 80
        for linea in dir_lines:
            c.drawString(50, y_dir, linea)
            y_dir -= 12
            
        c.setFont("Helvetica-Bold", 18)
        c.drawRightString(ancho - 50, alto - 50, "NOTA DE ENTREGA")
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(ancho - 50, alto - 70, f"Nro: {doc['nro_documento']}")
        c.setFont("Helvetica", 10)
        c.drawRightString(ancho - 50, alto - 85, f"Fecha: {doc['fecha']}")
        
        y_cliente = y_dir - 20
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y_cliente, "DATOS DEL CLIENTE:")
        c.setFont("Helvetica", 10)
        c.drawString(50, y_cliente - 15, f"Nombre / Razón: {doc['nombre']}")
        c.drawString(50, y_cliente - 30, f"CI/RIF: {doc['cedula_rif']}")
        c.drawString(50, y_cliente - 45, f"Teléfono: {doc['telefono']}")
        c.drawString(50, y_cliente - 60, f"Dirección: {doc['direccion']}")
        
        y_tabla = y_cliente - 90
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0.9, 0.9, 0.9) 
        c.rect(50, y_tabla - 5, ancho - 100, 20, fill=True, stroke=True)
        c.setFillColorRGB(0, 0, 0)
        
        c.drawString(55, y_tabla, "CÓDIGO")
        c.drawString(130, y_tabla, "DESCRIPCIÓN")
        c.drawRightString(380, y_tabla, "CANT")
        c.drawRightString(460, y_tabla, "PRECIO ($)")
        c.drawRightString(550, y_tabla, "SUBTOTAL ($)")
        
        y_items = y_tabla - 20
        c.setFont("Helvetica", 10)
        
        for item in detalles:
            if y_items < 150: 
                c.showPage()
                y_items = alto - 50
                c.setFont("Helvetica", 10)
                
            c.drawString(55, y_items, str(item['codigo_interno']))
            c.drawString(130, y_items, str(item['descripcion'])[:40])
            c.drawRightString(380, y_items, f"{item['cantidad']:.2f}")
            c.drawRightString(460, y_items, f"{item['precio_unitario_usd']:,.2f}")
            c.drawRightString(550, y_items, f"{item['subtotal_linea']:,.2f}")
            y_items -= 15
            
        c.line(50, y_items + 5, ancho - 50, y_items + 5)
        
        y_totales = y_items - 15
        tasa = doc['tasa_cambio_momento']
        total_usd = doc['total_usd']
        total_bs = total_usd * tasa
        
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(460, y_totales, "TOTAL USD:")
        c.drawRightString(550, y_totales, f"$ {total_usd:,.2f}")
        
        c.setFont("Helvetica", 10)
        c.drawRightString(460, y_totales - 15, f"Tasa BCV:")
        c.drawRightString(550, y_totales - 15, f"{tasa:,.2f} Bs/$")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawRightString(460, y_totales - 30, "TOTAL Bs:")
        c.drawRightString(550, y_totales - 30, f"Bs {total_bs:,.2f}")
        
        y_firmas = 80
        c.line(100, y_firmas, 250, y_firmas)
        c.drawCentredString(175, y_firmas - 15, "Despachado por")
        
        c.line(ancho - 250, y_firmas, ancho - 100, y_firmas)
        c.drawCentredString(ancho - 175, y_firmas - 15, "Recibido conforme")
        
        c.setFont("Helvetica-Oblique", 9)
        c.drawCentredString(ancho / 2, 30, "Documento interno de control - No válido como Factura Fiscal - Pegasus Fisco POS")
        
        c.save()
        return ruta_pdf

    @staticmethod
    def _generar_pdf_ticket(doc, empresa, detalles):
        """Versión Definitiva SENIAT para Facturas (80mm)"""
        os.makedirs('temp', exist_ok=True)
        ruta_pdf = os.path.abspath(f"temp/ticket_{doc['nro_documento']}.pdf")

        monto_exento = sum(item['subtotal_linea'] for item in detalles if item['es_exento'])
        base_imponible = sum(item['subtotal_linea'] for item in detalles if not item['es_exento'])
        
        if doc['descuento_porcentaje'] > 0:
            factor = 1 - (doc['descuento_porcentaje'] / 100)
            monto_exento *= factor
            base_imponible *= factor

        linea_guiones = "-" * 40
        linea_iguales = "=" * 40
        lineas = []

        lineas.append(empresa['razon_social'].center(40))
        lineas.append(f"RIF: {empresa['rif']}".center(40))
        
        dir_lines = textwrap.wrap(empresa['direccion_fiscal'], width=40)
        lineas.extend([l.center(40) for l in dir_lines])
        lineas.append(linea_guiones)

        lineas.append("FACTURA".center(40))
        lineas.append(f"FACTURA NRO: {doc['nro_documento']}")
        lineas.append(f"NRO CONTROL: {doc['nro_control']}")
        lineas.append(f"FECHA: {doc['fecha']}")
        lineas.append(linea_guiones)

        # Datos de Cliente (Alineado y limpio)
        lineas.append("DATOS DEL CLIENTE:")
        lineas.append(f"NOMBRE: {doc['nombre'][:32]}")
        lineas.append(f"CI/RIF: {doc['cedula_rif']}")
        lineas.append(linea_guiones)

        # Cabecera de Ítems SENIAT
        lineas.append(f"{'CANT':<5} {'DESCRIPCION':<20} {'TOTAL(Bs)':>13}")
        lineas.append(linea_guiones)

        tasa = doc['tasa_cambio_momento']

        for item in detalles:
            # MARCADOR FISCAL: (E) Exento, (G) Gravable
            marc = "(E)" if item['es_exento'] else "(G)"
            desc_lines = textwrap.wrap(item['descripcion'], width=20)

            cant = f"{item['cantidad']:.2f}"
            precio_bs = item['precio_unitario_usd'] * tasa
            subt_bs = item['subtotal_linea'] * tasa

            # Primera línea: Cantidad, Parte del Nombre, Total Bs + Marcador
            lineas.append(f"{cant:<5} {desc_lines[0]:<16} {subt_bs:>10,.2f} {marc}")
            
            # Resto de la descripción
            for dl in desc_lines[1:]:
                lineas.append(f"{'':<5} {dl:<20}")
                
            # Precio unitario base
            lineas.append(f"{'':<5} 1 x {precio_bs:,.2f}")

        lineas.append(linea_guiones)

        # TOTALES ESTRICTAMENTE FISCALES
        subt_bs = doc['subtotal_usd'] * tasa
        desc_bs = doc['descuento_monto'] * tasa
        exento_bs = monto_exento * tasa
        base_bs = base_imponible * tasa
        iva_bs = doc['impuesto_iva_usd'] * tasa
        total_bs = doc['total_usd'] * tasa

        lineas.append(f"{'SUBTOTAL:':<20} {subt_bs:>19,.2f}")
        if desc_bs > 0:
            lineas.append(f"{f'DESC ({doc['descuento_porcentaje']}%):':<20} -{desc_bs:>18,.2f}")

        lineas.append(f"{'EXENTO (E):':<20} {exento_bs:>19,.2f}")
        lineas.append(f"{'BASE IMPONIBLE (G):':<20} {base_bs:>19,.2f}")
        lineas.append(f"{'IVA (16%):':<20} {iva_bs:>19,.2f}")

        lineas.append(linea_iguales)
        lineas.append(f"{'TOTAL FACTURA Bs:':<20} {total_bs:>19,.2f}")
        lineas.append(linea_iguales)

        # RETENCIONES
        if doc['iva_retenido_bs'] > 0:
            lineas.append(f"{'RETENCION IVA:':<20} -{doc['iva_retenido_bs']:>18,.2f}")
            lineas.append(f"{'COMPROBANTE:':<15} {doc['documento_referencia'][:24]:>24}")
            neto_bs = total_bs - doc['iva_retenido_bs']
            lineas.append(linea_guiones)
            lineas.append(f"{'NETO A PAGAR Bs:':<20} {neto_bs:>19,.2f}")

        # TASA CAMBIARIA INFORMATIVA
        lineas.append("")
        lineas.append(f"TASA BCV: {tasa:,.2f} Bs/USD".center(40))
        lineas.append(f"EQUIVALENTE: $ {doc['total_usd']:,.2f}".center(40))
        lineas.append(linea_guiones)

        # PIE DE PÁGINA OBLIGATORIO
        lineas.append("MÁQUINA: Z1C2345678".center(40)) # Simulación de serial fiscal
        lineas.append("ESTE DOCUMENTO ES UNA REPRESENTACION".center(40))
        lineas.append("IMPRESA DE UNA FACTURA".center(40))
        lineas.append("")

        # CÁLCULO DE PANTALLA
        alto_linea = 4 * mm
        alto_pdf = (len(lineas) * alto_linea) + (20 * mm) 
        if alto_pdf < 120 * mm: alto_pdf = 120 * mm

        c = canvas.Canvas(ruta_pdf, pagesize=(80 * mm, alto_pdf))
        
        # Fuente obligatoria en este tipo de impresoras: Courier
        c.setFont("Courier-Bold", 8.5) 
        
        y = alto_pdf - (10 * mm)
        for linea in lineas:
            c.drawString(4 * mm, y, linea) 
            y -= alto_linea

        c.save()
        return ruta_pdf