import sqlite3
from data.conexion import crear_conexion
from datetime import datetime, timedelta

class StatsController:
    
    @staticmethod
    def obtener_kpis_hoy():
        """Devuelve las métricas clave del día actual."""
        hoy = datetime.now().strftime("%Y-%m-%d")
        conn = crear_conexion()
        if not conn: return None
        
        try:
            cursor = conn.cursor()
            
            # 1. Ventas Totales ($) (Solo Facturas para dinero real)
            cursor.execute("""
                SELECT SUM(total_usd), COUNT(*) 
                FROM documentos 
                WHERE date(fecha) = ? AND tipo_doc = 'FACTURA'
            """, (hoy,))
            res_ventas = cursor.fetchone()
            ventas_hoy = res_ventas[0] if res_ventas[0] else 0
            
            # 2. Transacciones (Facturas + Notas)
            cursor.execute("SELECT COUNT(*) FROM documentos WHERE date(fecha) = ?", (hoy,))
            transacciones = cursor.fetchone()[0]
            
            # 3. Ganancia Estimada (Venta - Costo)
            ganancia_estimada = ventas_hoy * 0.30 
            
            # 4. Productos con Stock Crítico
            cursor.execute("SELECT COUNT(*) FROM productos WHERE stock_actual <= stock_minimo AND estado=1")
            stock_bajo = cursor.fetchone()[0]
            
            return {
                'ventas': ventas_hoy,
                'transacciones': transacciones,
                'ganancia': ganancia_estimada,
                'stock_bajo': stock_bajo
            }
            
        except Exception as e:
            print(f"Error KPIs: {e}")
            return {'ventas': 0, 'transacciones': 0, 'ganancia': 0, 'stock_bajo': 0}
        finally:
            conn.close()

    @staticmethod
    def obtener_ventas_semana():
        """Devuelve las ventas ($) de los últimos 7 días (SOLO FACTURAS)."""
        fechas = []
        montos = []
        conn = crear_conexion()
        if not conn: return [], []
        
        try:
            cursor = conn.cursor()
            
            # Generamos los últimos 7 días para asegurar que existan en la gráfica
            for i in range(6, -1, -1):
                fecha = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                
                cursor.execute("""
                    SELECT SUM(total_usd) FROM documentos 
                    WHERE date(fecha) = ? AND tipo_doc = 'FACTURA'
                """, (fecha,))
                
                res = cursor.fetchone()
                monto = res[0] if res and res[0] else 0
                
                # Formato corto DD/MM
                fechas.append(datetime.strptime(fecha, "%Y-%m-%d").strftime("%d/%m"))
                montos.append(monto)
                
            return fechas, montos
        except Exception as e:
            print(f"Error Gráfico: {e}")
            return [], []
        finally:
            conn.close()

    @staticmethod
    def obtener_metodos_pago():
        """Devuelve desglose por método de pago para gráfico de torta."""
        conn = crear_conexion()
        if not conn: return [], []
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT metodo_pago, COUNT(*) as cantidad 
                FROM documentos 
                WHERE tipo_doc = 'FACTURA'
                GROUP BY metodo_pago
            """)
            filas = cursor.fetchall()
            
            labels = [f[0] for f in filas]
            values = [f[1] for f in filas]
            return labels, values
        except Exception as e:
            print(f"Error Pie: {e}")
            return [], []
        finally:
            conn.close()

    @staticmethod
    def obtener_top_productos(limite=5):
        """Los 5 productos más vendidos."""
        conn = crear_conexion()
        try:
            cursor = conn.cursor()
            # --- ÚNICA MODIFICACIÓN AQUÍ ---
            # Agregamos p.codigo_interno al SELECT para que SalesView pueda usarlo
            cursor.execute("""
                SELECT p.codigo_interno, p.descripcion, SUM(d.cantidad) as total_vendido
                FROM documento_detalles d
                JOIN productos p ON d.producto_id = p.id
                GROUP BY d.producto_id
                ORDER BY total_vendido DESC
                LIMIT ?
            """, (limite,))
            return cursor.fetchall()
        except Exception as e:
            print(f"Error Top: {e}")
            return []
        finally:
            conn.close()