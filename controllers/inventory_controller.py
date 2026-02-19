import sqlite3
from data.conexion import crear_conexion
from datetime import datetime

class InventoryController:
    
    @staticmethod
    def obtener_tasas():
        """Retorna un dict con las tasas actuales: {'bcv': float, 'cop': float}"""
        conn = crear_conexion()
        if not conn: return {'bcv': 0, 'cop': 0}
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT tasa_bcv, tasa_cop FROM configuracion LIMIT 1")
            row = cursor.fetchone()
            if row:
                return {'bcv': row[0] or 0.0, 'cop': row[1] or 0.0}
            return {'bcv': 0.0, 'cop': 0.0}
        except:
            return {'bcv': 0.0, 'cop': 0.0}
        finally:
            conn.close()

    @staticmethod
    def obtener_todos():
        """Devuelve productos con cálculos de moneda incluidos."""
        conn = crear_conexion()
        if not conn: return []
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            
            # 1. Obtenemos tasas primero
            cursor.execute("SELECT tasa_bcv, tasa_cop FROM configuracion LIMIT 1")
            config = cursor.fetchone()
            tasa_bcv = config['tasa_bcv'] if config else 0
            tasa_cop = config['tasa_cop'] if config else 0

            # 2. Obtenemos productos
            cursor.execute("""
                SELECT p.*, c.nombre as categoria_nombre, pr.razon_social as proveedor_nombre
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
                WHERE p.estado = 1
                ORDER BY p.descripcion ASC
            """)
            
            productos = []
            for row in cursor.fetchall():
                d = dict(row)
                d['codigo'] = d['codigo_interno'] 
                d['categoria'] = d['categoria_nombre']
                d['proveedor'] = d['proveedor_nombre']
                
                # CÁLCULOS MULTIMONEDA
                precio_usd = d['precio_usd']
                d['precio_bs'] = precio_usd * tasa_bcv
                d['precio_cop'] = precio_usd * tasa_cop
                
                productos.append(d)
                
            return productos
        finally:
            conn.close()

    @staticmethod
    def añadir_producto(datos):
        conn = crear_conexion()
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM productos WHERE codigo_interno = ? AND estado = 1", (datos['codigo'],))
            if cursor.fetchone():
                return False

            # FORZAMOS STOCK 0 (Regla de negocio: Todo entra por Logística)
            stock_inicial = 0

            cursor.execute("""
                INSERT INTO productos (
                    codigo_interno, descripcion, precio_usd, stock_actual, 
                    stock_minimo, es_exento, categoria_id, proveedor_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datos['codigo'], datos['descripcion'], datos['precio_usd'], 
                stock_inicial, datos['stock_minimo'], datos['es_exento'],
                datos['categoria_id'], datos['proveedor_id']
            ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error añadiendo producto: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def actualizar_producto(id_producto, datos):
        conn = crear_conexion()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE productos SET 
                    descripcion=?, precio_usd=?, stock_minimo=?, es_exento=?, 
                    categoria_id=?, proveedor_id=?
                WHERE id=?
            """, (
                datos['descripcion'], datos['precio_usd'], datos['stock_minimo'], 
                datos['es_exento'], datos['categoria_id'], datos['proveedor_id'], id_producto
            ))
            conn.commit()
            return True
        except: return False
        finally: conn.close()