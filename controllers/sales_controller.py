import sqlite3
from data.conexion import crear_conexion
from datetime import datetime
from core.app_signals import comunicacion
from controllers.cash_controller import CashController

class SalesController:
    
    @staticmethod
    def registrar_venta(carrito, datos_pago, totales, tasa_bcv, tipo_doc="FACTURA"):
        """
        Registra la venta o nota de entrega con numeración secuencial, desglose de pagos, 
        multimoneda y retenciones de IVA para el libro fiscal.
        tipo_doc: 'FACTURA' o 'NOTA_ENTREGA'
        """
        conn = crear_conexion()
        if not conn: return False, "Error de conexión"
        
        # Evitar bloqueo de BD
        conn.execute("PRAGMA busy_timeout = 5000")
        
        try:
            cursor = conn.cursor()
            
            # 1. GENERAR NUMERACIÓN SECUENCIAL Y NÚMERO DE CONTROL
            if tipo_doc == "FACTURA":
                campo_contador = "proximo_nro_factura"
                prefijo = "FAC"
            else: # NOTA_ENTREGA
                campo_contador = "proximo_nro_ne"
                prefijo = "NE"
            
            # Consultamos el número actual de documento y el número de control
            cursor.execute(f"SELECT {campo_contador}, proximo_nro_control FROM configuracion LIMIT 1")
            row = cursor.fetchone()
            
            # Manejo seguro por si row es sqlite3.Row
            if row:
                secuencia = row[campo_contador] if campo_contador in row.keys() else 1
                secuencia_control = row['proximo_nro_control'] if 'proximo_nro_control' in row.keys() else 1
            else:
                secuencia = 1
                secuencia_control = 1
            
            # Generamos los strings formateados (Ej: FAC-00000001 y 00-00000001)
            nro_documento = f"{prefijo}-{str(secuencia).zfill(8)}"
            nro_control = f"00-{str(secuencia_control).zfill(8)}"

            # --- PREPARACIÓN DE DATOS DE RETENCIÓN PARA EL LIBRO DE VENTAS ---
            monto_retenido_usd = datos_pago.get('monto_retenido_usd', 0.0)
            # El SENIAT exige la retención reflejada en Bolívares
            iva_retenido_bs = monto_retenido_usd * tasa_bcv 
            comprobante_retencion = datos_pago.get('comprobante_retencion', None)

            # 2. INSERTAR CABECERA DE DOCUMENTO CON DESGLOSE DE PAGOS Y RETENCIONES
            cursor.execute("""
                INSERT INTO documentos (
                    tipo_doc, 
                    nro_documento,
                    nro_control,
                    cliente_id, 
                    fecha, 
                    tasa_cambio_momento, 
                    
                    subtotal_usd, 
                    descuento_porcentaje, 
                    descuento_monto,
                    impuesto_iva_usd, 
                    impuesto_igtf_usd, 
                    total_usd, 
                    
                    metodo_pago, 
                    monto_recibido_usd, 
                    monto_recibido_bs, 
                    monto_recibido_cop, 
                    monto_vuelto_usd, 
                    monto_vuelto_bs,
                    monto_vuelto_cop, -- CORRECCIÓN: Ahora guardamos el vuelto en Pesos

                    pago_usd_efectivo, pago_usd_zelle,
                    pago_bs_efectivo, pago_bs_punto, pago_bs_transf,
                    pago_cop_efectivo, pago_cop_transf,
                    
                    iva_retenido_bs,      -- NUEVO: Retención para el libro
                    documento_referencia  -- NUEVO: Nro Comprobante de Retención
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tipo_doc,
                nro_documento, 
                nro_control, 
                datos_pago.get('cliente_id'),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                tasa_bcv,
                
                totales['subtotal'],
                totales.get('descuento_porc', 0),   
                totales.get('descuento_monto', 0),  
                totales['iva'],                     
                totales['igtf'],
                totales['total'],
                
                datos_pago['metodo_pago'],
                datos_pago.get('recibido_usd', 0),
                datos_pago.get('recibido_bs', 0),
                datos_pago.get('recibido_cop', 0),
                datos_pago.get('vuelto_usd', 0),
                datos_pago.get('vuelto_bs', 0),
                datos_pago.get('vuelto_cop', 0), 

                datos_pago.get('pago_usd_efectivo', 0),
                datos_pago.get('pago_usd_zelle', 0),
                datos_pago.get('pago_bs_efectivo', 0),
                datos_pago.get('pago_bs_punto', 0),
                datos_pago.get('pago_bs_transf', 0),
                datos_pago.get('pago_cop_efectivo', 0),
                datos_pago.get('pago_cop_transf', 0),
                
                iva_retenido_bs,
                comprobante_retencion
            ))
            
            id_doc = cursor.lastrowid
            
            # 3. INSERTAR DETALLES, ACTUALIZAR INVENTARIO Y KARDEX DE PRODUCTOS
            for item in carrito:
                cursor.execute("""
                    INSERT INTO documento_detalles (
                        documento_id, producto_id, cantidad, precio_unitario_usd
                    ) VALUES (?, ?, ?, ?)
                """, (id_doc, item['id'], item['cantidad'], item['precio_usd']))
                
                # Descontar del Stock Físico
                cursor.execute("""
                    UPDATE productos 
                    SET stock_actual = stock_actual - ? 
                    WHERE id = ?
                """, (item['cantidad'], item['id']))
                
                # Obtener saldo para el Kardex
                cursor.execute("SELECT stock_actual FROM productos WHERE id=?", (item['id'],))
                stock_resultante = cursor.fetchone()[0]
                
                # Registro en Kardex con la Referencia Real
                cursor.execute("""
                    INSERT INTO inventario_kardex (
                        producto_id, tipo_movimiento, cantidad, stock_resultante, 
                        motivo, referencia, fecha, usuario_id
                    ) VALUES (?, 'SALIDA', ?, ?, ?, ?, ?, 1)
                """, (
                    item['id'], 
                    item['cantidad'], 
                    stock_resultante, 
                    'VENTA' if tipo_doc == 'FACTURA' else 'NOTA_ENTREGA', 
                    nro_documento, 
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

            # 4. REGISTRAR EN KARDEX DE CAJA (Auditoría Financiera para todos los docs)
            sesion = CashController.obtener_sesion_activa()
            if sesion:
                efec_usd = float(datos_pago.get('pago_usd_efectivo', 0))
                efec_bs  = float(datos_pago.get('pago_bs_efectivo', 0))
                efec_cop = float(datos_pago.get('pago_cop_efectivo', 0))
                
                v_usd = float(datos_pago.get('vuelto_usd', 0))
                v_bs  = float(datos_pago.get('vuelto_bs', 0))
                v_cop = float(datos_pago.get('vuelto_cop', 0))

                # Se pasa el cursor_externo para evitar bloqueos
                CashController.registrar_venta_en_caja(
                    sesion['id'], 
                    nro_documento, # Pasamos la denominación real (FAC o NE) 
                    efec_usd, efec_bs, efec_cop,
                    v_usd, v_bs, v_cop,
                    tipo_documento=tipo_doc, # Le avisamos qué tipo es
                    cursor_externo=cursor
                )
            
            # 5. ACTUALIZAR EL CONTADOR EN CONFIGURACIÓN
            cursor.execute(f"UPDATE configuracion SET {campo_contador} = {campo_contador} + 1, proximo_nro_control = proximo_nro_control + 1")

            # Confirmar toda la transacción junta
            conn.commit()
            
            # --- SEÑALES: AVISAR AL SISTEMA ---
            try:
                comunicacion.inventario_actualizado.emit()
                comunicacion.venta_realizada.emit()
            except Exception as e_sig:
                print(f"⚠️ Venta OK pero error en señales: {e_sig}")
            
            return True, nro_documento
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error CRÍTICO al registrar venta: {e}")
            return False, str(e)
        finally:
            conn.close()