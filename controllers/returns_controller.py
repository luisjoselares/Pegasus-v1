import os
import sqlite3
import textwrap
from datetime import datetime
from data.conexion import crear_conexion
from core.app_signals import comunicacion
from controllers.cash_controller import CashController

from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

class ReturnsController:
    
    @staticmethod
    def buscar_factura(nro_factura):
        conn = crear_conexion()
        if not conn: return None, "Error de conexión."
        try:
            cursor = conn.cursor()
            nro_formateado = nro_documento_formateado(nro_factura)
            
            cursor.execute("""
                SELECT d.*, c.nombre, c.cedula_rif 
                FROM documentos d
                JOIN clientes c ON d.cliente_id = c.id
                WHERE d.nro_documento = ? AND d.tipo_doc = 'FACTURA' AND d.estado = 'PROCESADO'
            """, (nro_formateado,))
            
            factura = cursor.fetchone()
            if not factura:
                return None, f"La factura {nro_formateado} no existe, está anulada o es una Nota de Entrega."
                
            # AHORA EXTRAEMOS TAMBIÉN EL ID DEL DETALLE Y LA CANTIDAD DEVUELTA
            cursor.execute("""
                SELECT dd.id as detalle_id, dd.producto_id, p.codigo_interno, p.descripcion, 
                       dd.cantidad, dd.cantidad_devuelta, dd.precio_unitario_usd, p.es_exento
                FROM documento_detalles dd
                JOIN productos p ON dd.producto_id = p.id
                WHERE dd.documento_id = ?
            """, (factura['id'],))
            
            detalles = cursor.fetchall()
            
            # Verificamos si aún queda algo por devolver en esta factura
            total_disponible = sum((d['cantidad'] - d['cantidad_devuelta']) for d in detalles)
            if total_disponible <= 0:
                return None, f"La factura {nro_formateado} ya ha sido devuelta en su totalidad en operaciones previas."
                
            return {'factura': dict(factura), 'detalles': [dict(d) for d in detalles]}, "OK"
            
        except Exception as e:
            return None, f"Error en búsqueda: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def procesar_devolucion(nro_factura, items_a_devolver, metodo_reembolso, total_reembolso_usd):
        conn = crear_conexion()
        if not conn: return False, "Error de conexión."
        conn.execute("PRAGMA busy_timeout = 5000")
        
        try:
            cursor = conn.cursor()
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("SELECT * FROM documentos WHERE nro_documento = ?", (nro_factura,))
            factura_orig = cursor.fetchone()
            
            cursor.execute("SELECT tasa_bcv, tasa_cop, proximo_nro_nc, proximo_nro_control FROM configuracion LIMIT 1")
            conf = cursor.fetchone()
            
            tasa_historica = factura_orig['tasa_cambio_momento']
            tasa_cop_actual = conf['tasa_cop']
            cliente_id = factura_orig['cliente_id']
            
            # --- CANDADO DE CAJA ---
            m_usd = 0; m_bs = 0; m_cop = 0
            if "Saldo a Favor" not in metodo_reembolso:
                sesion = CashController.obtener_sesion_activa()
                if not sesion: return False, "No hay una caja abierta para entregar el efectivo."
                
                saldo_u, saldo_b, saldo_c = CashController.obtener_saldos_actuales()
                
                if "USD" in metodo_reembolso: m_usd = total_reembolso_usd
                elif "Bs" in metodo_reembolso: m_bs = total_reembolso_usd * tasa_historica
                elif "Pesos" in metodo_reembolso: m_cop = total_reembolso_usd * tasa_cop_actual
                
                if (m_usd > saldo_u) or (m_bs > saldo_b) or (m_cop > saldo_c):
                    return False, (f"FONDOS INSUFICIENTES EN CAJA.\n\n"
                                   f"Saldo Disponible: $ {saldo_u:.2f} | Bs {saldo_b:.2f} | COP {saldo_c:,.0f}\n"
                                   f"Requerido: $ {m_usd:.2f} | Bs {m_bs:.2f} | COP {m_cop:,.0f}\n\n"
                                   f"Vaya al módulo 'Facturación' y registre un INGRESO manual de fondos.")

            # --- GENERAR CORRELATIVOS ---
            nro_nc = f"NC-{str(conf['proximo_nro_nc']).zfill(8)}"
            nro_ctrl_nc = f"00-{str(conf['proximo_nro_control']).zfill(8)}"
            
            # --- CÁLCULO FISCAL ---
            base_usd = 0; iva_usd = 0; exento_usd = 0
            for item in items_a_devolver:
                subt = item['cantidad'] * item['precio_usd']
                if item['es_exento']: exento_usd += subt
                else: 
                    base_usd += subt
                    iva_usd += subt * 0.16 
            
            # --- INSERTAR DOCUMENTO NC ---
            cursor.execute("""
                INSERT INTO documentos (
                    tipo_doc, nro_documento, nro_control, cliente_id, fecha, tasa_cambio_momento,
                    subtotal_usd, impuesto_iva_usd, total_usd, 
                    documento_referencia, metodo_pago, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PROCESADO')
            """, ('NOTA_CREDITO', nro_nc, nro_ctrl_nc, cliente_id, fecha_actual, tasa_historica,
                  (base_usd + exento_usd), iva_usd, total_reembolso_usd, nro_factura, metodo_reembolso))
            nc_id = cursor.lastrowid
            
            # --- ACTUALIZAR FACTURA ORIGINAL, DEVOLVER INVENTARIO Y KARDEX ---
            for item in items_a_devolver:
                # 1. Registrar detalle de la Nota de Crédito
                cursor.execute("INSERT INTO documento_detalles (documento_id, producto_id, cantidad, precio_unitario_usd) VALUES (?, ?, ?, ?)", 
                               (nc_id, item['producto_id'], item['cantidad'], item['precio_usd']))
                
                # 2. RESTAR DISPONIBILIDAD EN LA FACTURA ORIGINAL
                cursor.execute("UPDATE documento_detalles SET cantidad_devuelta = cantidad_devuelta + ? WHERE id = ?", 
                               (item['cantidad'], item['detalle_id']))

                # 3. Devolver producto al inventario
                cursor.execute("UPDATE productos SET stock_actual = stock_actual + ? WHERE id = ?", (item['cantidad'], item['producto_id']))
                cursor.execute("SELECT stock_actual FROM productos WHERE id=?", (item['producto_id'],))
                nuevo_stock = cursor.fetchone()[0]
                
                # 4. Registrar movimiento en Kardex de inventario
                cursor.execute("""
                    INSERT INTO inventario_kardex (producto_id, tipo_movimiento, cantidad, stock_resultante, motivo, referencia, fecha, usuario_id) 
                    VALUES (?, 'ENTRADA', ?, ?, 'DEVOLUCION', ?, ?, 1)
                """, (item['producto_id'], item['cantidad'], nuevo_stock, nro_nc, fecha_actual))

            # --- MOVIMIENTOS DE DINERO ---
            if "Saldo a Favor" in metodo_reembolso:
                cursor.execute("UPDATE clientes SET saldo_favor = saldo_favor + ? WHERE id = ?", (total_reembolso_usd, cliente_id))
            else:
                desc = f"Devolución {nro_nc} (Fact: {nro_factura})"
                
                cursor.execute("""
                    INSERT INTO caja_movimientos (sesion_id, tipo, monto_usd, monto_bs, monto_cop, motivo, fecha, usuario_id) 
                    VALUES (?, 'EGRESO', ?, ?, ?, ?, ?, 1)
                """, (sesion['id'], m_usd, m_bs, m_cop, desc, fecha_actual))
                
                CashController._registrar_kardex(
                    cursor, sesion['id'], 'EGRESO',
                    0, m_usd, 0, m_bs, 0, m_cop, 
                    desc, nro_nc
                )

            # --- FINALIZAR Y EVALUAR ANULACIÓN DE FACTURA ---
            cursor.execute("UPDATE configuracion SET proximo_nro_nc = proximo_nro_nc + 1, proximo_nro_control = proximo_nro_control + 1")
            
            # Comprobamos si la factura ya se devolvió al 100%
            cursor.execute("SELECT sum(cantidad) as tot, sum(cantidad_devuelta) as dev FROM documento_detalles WHERE documento_id = ?", (factura_orig['id'],))
            estado_factura = cursor.fetchone()
            
            # Solo si la suma de las devoluciones iguala o supera lo comprado, se anula la factura madre.
            if estado_factura and (estado_factura['tot'] <= estado_factura['dev']):
                cursor.execute("UPDATE documentos SET estado = 'ANULADO', motivo_anulacion = ? WHERE nro_documento = ?", 
                               (f"Devolución Total completada con {nro_nc}", nro_factura))

            conn.commit()
            return True, nro_nc
            
        except Exception as e:
            conn.rollback()
            return False, f"Error en BD: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def generar_pdf_nota_credito(nro_nc, ruta_pdf):
        """Genera el PDF de la Nota de Crédito en formato Ticket de 80mm"""
        conn = crear_conexion()
        if not conn: return False
        
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT rif, razon_social, direccion_fiscal FROM configuracion LIMIT 1")
            empresa = cursor.fetchone()
            
            cursor.execute("""
                SELECT d.*, c.nombre, c.cedula_rif, c.direccion 
                FROM documentos d JOIN clientes c ON d.cliente_id = c.id WHERE d.nro_documento = ?
            """, (nro_nc,))
            doc = cursor.fetchone()
            
            cursor.execute("""
                SELECT dd.cantidad, p.codigo_interno, p.descripcion, dd.precio_unitario_usd, p.es_exento
                FROM documento_detalles dd JOIN productos p ON dd.producto_id = p.id WHERE dd.documento_id = ?
            """, (doc['id'],))
            detalles = cursor.fetchall()
            
            monto_exento_usd = 0
            base_imponible_usd = 0
            for item in detalles:
                subt = item['cantidad'] * item['precio_unitario_usd']
                if item['es_exento']:
                    monto_exento_usd += subt
                else:
                    base_imponible_usd += subt
            
            tasa = doc['tasa_cambio_momento']

            linea_guiones = "-" * 40
            linea_iguales = "=" * 40
            lineas = []

            lineas.append(empresa['razon_social'].center(40))
            lineas.append(f"RIF: {empresa['rif']}".center(40))
            dir_lines = textwrap.wrap(empresa['direccion_fiscal'], width=40)
            lineas.extend([l.center(40) for l in dir_lines])
            lineas.append(linea_guiones)

            lineas.append("NOTA DE CREDITO".center(40))
            lineas.append(f"NRO: {doc['nro_documento']}")
            lineas.append(f"CONTROL: {doc['nro_control']}")
            lineas.append(f"FECHA: {doc['fecha']}")
            lineas.append(f"AFECTA FACTURA: {doc['documento_referencia']}")
            lineas.append(linea_guiones)

            lineas.append(f"NOMBRE: {doc['nombre'][:32]}")
            lineas.append(f"CI/RIF: {doc['cedula_rif']}")
            lineas.append(linea_guiones)

            lineas.append(f"{'CANT':<5} {'DESCRIPCION':<20} {'TOTAL(Bs)':>13}")
            lineas.append(linea_guiones)

            for item in detalles:
                marc = " (E)" if item['es_exento'] else ""
                desc = item['descripcion'] + marc
                desc_lines = textwrap.wrap(desc, width=20)

                cant = f"{item['cantidad']:.2f}"
                precio_bs = item['precio_unitario_usd'] * tasa
                subt_bs = (item['cantidad'] * item['precio_unitario_usd']) * tasa

                lineas.append(f"{cant:<5} {desc_lines[0]:<20} {subt_bs:>13,.2f}")
                for dl in desc_lines[1:]:
                    lineas.append(f"{'':<5} {dl:<20}")
                lineas.append(f"{'':<5} 1 x {precio_bs:,.2f}")

            lineas.append(linea_guiones)

            exento_bs = monto_exento_usd * tasa
            base_bs = base_imponible_usd * tasa
            iva_bs = doc['impuesto_iva_usd'] * tasa
            total_bs = doc['total_usd'] * tasa

            lineas.append(f"{'EXENTO (E):':<20} {exento_bs:>19,.2f}")
            lineas.append(f"{'BASE IMPONIBLE:':<20} {base_bs:>19,.2f}")
            lineas.append(f"{'IVA (16%):':<20} {iva_bs:>19,.2f}")

            lineas.append(linea_iguales)
            lineas.append(f"{'TOTAL REEMBOLSO Bs:':<20} {total_bs:>19,.2f}")
            lineas.append(linea_iguales)

            lineas.append(f"{'METODO:':<15} {doc['metodo_pago'][:24]:>24}")

            lineas.append("")
            lineas.append(f"TASA BCV: {tasa:,.2f} Bs/USD".center(40))
            lineas.append(f"EQUIVALENTE: $ {doc['total_usd']:,.2f}".center(40))
            lineas.append(linea_guiones)

            lineas.append("ESTE DOCUMENTO ES UNA REPRESENTACION".center(40))
            lineas.append("IMPRESA DE UNA NOTA DE CREDITO".center(40))
            lineas.append("Pegasus Fisco POS".center(40))
            lineas.append("")

            os.makedirs('temp', exist_ok=True)
            
            alto_linea = 4 * mm
            alto_pdf = (len(lineas) * alto_linea) + (20 * mm) 
            if alto_pdf < 120 * mm: alto_pdf = 120 * mm

            c = canvas.Canvas(ruta_pdf, pagesize=(80 * mm, alto_pdf))
            c.setFont("Courier-Bold", 8.5) 

            y = alto_pdf - (10 * mm)
            for linea in lineas:
                c.drawString(4 * mm, y, linea)
                y -= alto_linea

            c.save()
            return True
            
        except Exception as e:
            print(f"Error generando PDF Nota de Crédito: {e}")
            return False
        finally:
            conn.close()

def nro_documento_formateado(texto):
    texto = texto.upper().strip().replace("F-", "").replace("FAC-", "")
    try:
        return f"FAC-{str(int(texto)).zfill(8)}"
    except:
        return texto