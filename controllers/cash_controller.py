import sqlite3
from data.conexion import crear_conexion
from datetime import datetime

class CashController:

    @staticmethod
    def _obtener_ultimo_saldo(cursor, sesion_id):
        """Función interna para saber cuánto dinero había antes de la operación actual"""
        cursor.execute("""
            SELECT saldo_usd, saldo_bs, saldo_cop 
            FROM caja_kardex 
            WHERE sesion_id = ? 
            ORDER BY id DESC LIMIT 1
        """, (sesion_id,))
        last = cursor.fetchone()
        
        # 1. Si hay Kardex, retornamos su saldo exacto
        if last:
            return last['saldo_usd'], last['saldo_bs'], last['saldo_cop']
            
        # CORRECCIÓN: Se eliminó la consulta a caja_sesiones. 
        # Si no hay Kardex aún (es la apertura), el saldo previo es CERO.
        return 0.0, 0.0, 0.0

    @staticmethod
    def _registrar_kardex(cursor, sesion_id, operacion, in_usd, out_usd, in_bs, out_bs, in_cop, out_cop, desc, ref):
        """Registra una línea en el libro mayor de caja"""
        prev_usd, prev_bs, prev_cop = CashController._obtener_ultimo_saldo(cursor, sesion_id)
        
        nuevo_usd = prev_usd + in_usd - out_usd
        nuevo_bs = prev_bs + in_bs - out_bs
        nuevo_cop = prev_cop + in_cop - out_cop
        
        cursor.execute("""
            INSERT INTO caja_kardex (
                sesion_id, operacion, 
                entrada_usd, salida_usd, saldo_usd,
                entrada_bs, salida_bs, saldo_bs,
                entrada_cop, salida_cop, saldo_cop,
                descripcion, referencia_doc, fecha, usuario_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            sesion_id, operacion,
            in_usd, out_usd, nuevo_usd,
            in_bs, out_bs, nuevo_bs,
            in_cop, out_cop, nuevo_cop,
            desc, ref, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    @staticmethod
    def obtener_sesion_activa(usuario_id=1):
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM caja_sesiones WHERE usuario_id = ? AND estado = 'ABIERTA'", (usuario_id,))
            sesion = cursor.fetchone()
            conn.close()
            return sesion
        except Exception as e:
            print(f"Error buscando sesión: {e}")
            return None

    @staticmethod
    def abrir_caja(usuario_id, inicial_usd, inicial_bs, inicial_cop):
        if CashController.obtener_sesion_activa(usuario_id):
            return False, "Ya tienes una caja abierta."

        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            
            # 1. Crear Sesión
            cursor.execute("""
                INSERT INTO caja_sesiones (
                    usuario_id, fecha_apertura, 
                    monto_inicial_usd, monto_inicial_bs, monto_inicial_cop,
                    estado
                ) VALUES (?, ?, ?, ?, ?, 'ABIERTA')
            """, (
                usuario_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                inicial_usd, inicial_bs, inicial_cop
            ))
            sesion_id = cursor.lastrowid
            
            # 2. Kardex: Asiento de Apertura
            CashController._registrar_kardex(
                cursor, sesion_id, "APERTURA",
                inicial_usd, 0, inicial_bs, 0, inicial_cop, 0,
                "Fondo Inicial de Caja", f"SES-{sesion_id}"
            )
            
            conn.commit()
            conn.close()
            return True, "Caja abierta correctamente."
        except Exception as e:
            return False, f"Error al abrir: {e}"

    @staticmethod
    def registrar_movimiento(sesion_id, tipo, monto_usd, monto_bs, monto_cop, motivo, usuario_id=1):
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            
            # 1. Guardar Movimiento
            cursor.execute("""
                INSERT INTO caja_movimientos (
                    sesion_id, tipo, monto_usd, monto_bs, monto_cop, motivo, 
                    fecha, usuario_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sesion_id, tipo, monto_usd, monto_bs, monto_cop, motivo,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), usuario_id
            ))
            mov_id = cursor.lastrowid
            
            # 2. Kardex: Asiento de Movimiento
            in_usd = monto_usd if tipo == 'INGRESO' else 0
            out_usd = monto_usd if tipo == 'EGRESO' else 0
            in_bs = monto_bs if tipo == 'INGRESO' else 0
            out_bs = monto_bs if tipo == 'EGRESO' else 0
            in_cop = monto_cop if tipo == 'INGRESO' else 0
            out_cop = monto_cop if tipo == 'EGRESO' else 0
            
            CashController._registrar_kardex(
                cursor, sesion_id, tipo,
                in_usd, out_usd, in_bs, out_bs, in_cop, out_cop,
                motivo, f"MOV-{mov_id}"
            )

            conn.commit()
            conn.close()
            return True, "Movimiento registrado."
        except Exception as e:
            return False, str(e)
            
    @staticmethod
    def registrar_venta_en_caja(sesion_id, nro_documento, recibido_usd, recibido_bs, recibido_cop, vuelto_usd, vuelto_bs, vuelto_cop=0, tipo_documento="FACTURA", cursor_externo=None):
        """Registra el flujo de efectivo físico de una venta o nota de entrega en el Kardex"""
        try:
            if cursor_externo:
                cursor = cursor_externo
                conn = None
            else:
                conn = crear_conexion()
                cursor = conn.cursor()
            
            neto_usd = recibido_usd - vuelto_usd
            neto_bs = recibido_bs - vuelto_bs
            neto_cop = recibido_cop - vuelto_cop 
            
            if neto_usd != 0 or neto_bs != 0 or neto_cop != 0:
                # Determinamos la etiqueta visual y contable para aislar fiscalmente
                operacion_etiqueta = "VENTA" if tipo_documento == "FACTURA" else "NOTA_ENTREGA"
                desc_etiqueta = "Venta Factura" if tipo_documento == "FACTURA" else "Cobro Nota Entrega"
                
                CashController._registrar_kardex(
                    cursor, sesion_id, operacion_etiqueta,
                    max(0, neto_usd), max(0, -neto_usd), 
                    max(0, neto_bs), max(0, -neto_bs),
                    max(0, neto_cop), max(0, -neto_cop),
                    f"{desc_etiqueta} {nro_documento}", nro_documento
                )
                
                if conn:
                    conn.commit()
                    
            if conn:
                conn.close()
            return True
        except Exception as e:
            print(f"Error registrando venta en caja: {e}")
            return False

    @staticmethod
    def obtener_resumen_caja(sesion_id):
        conn = crear_conexion()
        if not conn: return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM caja_sesiones WHERE id=?", (sesion_id,))
            sesion = cursor.fetchone()
            if not sesion: return None
            
            # AHORA LA CONSULTA SUMA EL DINERO TANTO DE VENTAS COMO DE NOTAS DE ENTREGA
            cursor.execute("""
                SELECT 
                    SUM(entrada_usd - salida_usd) as neto_usd,
                    SUM(entrada_bs - salida_bs) as neto_bs,
                    SUM(entrada_cop - salida_cop) as neto_cop
                FROM caja_kardex 
                WHERE sesion_id = ? AND operacion IN ('VENTA', 'NOTA_ENTREGA')
            """, (sesion_id,))
            
            v = cursor.fetchone()
            v_usd = v['neto_usd'] if v and v['neto_usd'] is not None else 0
            v_bs = v['neto_bs'] if v and v['neto_bs'] is not None else 0
            v_cop = v['neto_cop'] if v and v['neto_cop'] is not None else 0
            
            cursor.execute("SELECT saldo_usd, saldo_bs, saldo_cop FROM caja_kardex WHERE sesion_id = ? ORDER BY id DESC LIMIT 1", (sesion_id,))
            last = cursor.fetchone()
            
            sis_usd = last['saldo_usd'] if last else sesion['monto_inicial_usd']
            sis_bs = last['saldo_bs'] if last else sesion['monto_inicial_bs']
            sis_cop = last['saldo_cop'] if last else sesion['monto_inicial_cop']
            
            return {
                'inicial_usd': sesion['monto_inicial_usd'], 'inicial_bs': sesion['monto_inicial_bs'], 'inicial_cop': sesion['monto_inicial_cop'],
                'ventas_usd': v_usd, 'ventas_bs': v_bs, 'ventas_cop': v_cop,
                'sistema_usd': sis_usd, 'sistema_bs': sis_bs, 'sistema_cop': sis_cop
            }
        finally: 
            conn.close()

    @staticmethod
    def cerrar_caja(sesion_id, f_usd, f_bs, f_cop, observaciones):
        resumen = CashController.obtener_resumen_caja(sesion_id)
        if not resumen: return False, "Error calculando."
        dif_usd = f_usd - resumen['sistema_usd']
        dif_bs = f_bs - resumen['sistema_bs']
        dif_cop = f_cop - resumen['sistema_cop']
        
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE caja_sesiones SET fecha_cierre=?, estado='CERRADA', observaciones=?,
                monto_final_usd=?, monto_final_bs=?, monto_final_cop=?,
                monto_sistema_usd=?, monto_sistema_bs=?, monto_sistema_cop=?,
                diferencia_usd=?, diferencia_bs=?, diferencia_cop=?
                WHERE id=?
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), observaciones, f_usd, f_bs, f_cop, resumen['sistema_usd'], resumen['sistema_bs'], resumen['sistema_cop'], dif_usd, dif_bs, dif_cop, sesion_id))
            
            CashController._registrar_kardex(
                cursor, sesion_id, "CIERRE", 0, 0, 0, 0, 0, 0,
                f"Cierre de Turno. Arqueo: ${f_usd} / Bs{f_bs} / COP{f_cop}", f"SES-{sesion_id}"
            )
            
            conn.commit()
            conn.close()
            return True, "Caja cerrada."
        except Exception as e: return False, str(e)

    @staticmethod
    def obtener_saldos_actuales():
        """Devuelve el dinero exacto que hay en la caja en este instante."""
        sesion = CashController.obtener_sesion_activa()
        if not sesion: return 0.0, 0.0, 0.0
        
        conn = crear_conexion()
        if not conn: return 0.0, 0.0, 0.0
        try:
            cursor = conn.cursor()
            u, b, c = CashController._obtener_ultimo_saldo(cursor, sesion['id'])
            return u, b, c
        finally:
            conn.close()