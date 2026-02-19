from data.conexion import crear_conexion
from core.app_signals import comunicacion

class LogisticsController:
    @staticmethod
    def obtener_productos_simple():
        """Trae lista básica de productos para el buscador"""
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT id, codigo_interno, descripcion, stock_actual FROM productos WHERE estado = 1")
            regs = cursor.fetchall()
            conn.close()
            return regs
        except Exception as e:
            print(f"Error: {e}")
            return []

    @staticmethod
    def registrar_movimiento(datos):
        """
        datos: dict con producto_id, tipo, cantidad, motivo, 
               proveedor_id, referencia, observaciones
        """
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            
            # 1. Obtener stock actual
            cursor.execute("SELECT stock_actual FROM productos WHERE id = ?", (datos['producto_id'],))
            res = cursor.fetchone()
            if not res: return False, "Producto no encontrado"
            stock_actual = res[0]
            
            # 2. Calcular nuevo stock
            cantidad = float(datos['cantidad'])
            if datos['tipo'] == "ENTRADA":
                nuevo_stock = stock_actual + cantidad
            else:
                nuevo_stock = stock_actual - cantidad
                if nuevo_stock < 0:
                    conn.close()
                    return False, "Error: El stock no puede quedar en negativo."

            # 3. Actualizar tabla productos
            cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?", (nuevo_stock, datos['producto_id']))
            
            # 4. Registrar en Kardex
            # CORRECCIÓN: Usamos 'referencia' en vez de 'nro_referencia' y agregamos 'usuario_id'
            cursor.execute("""
                INSERT INTO inventario_kardex (
                    producto_id, tipo_movimiento, cantidad, stock_resultante, motivo, 
                    proveedor_id, referencia, observaciones, fecha, usuario_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 1)
            """, (
                datos['producto_id'], 
                datos['tipo'], 
                cantidad, 
                nuevo_stock, 
                datos['motivo'],
                datos.get('proveedor_id'), 
                datos.get('referencia'), 
                datos['observaciones']
            ))
            
            conn.commit()
            conn.close()
            
            # --- 5. AVISAR AL SISTEMA ---
            comunicacion.inventario_actualizado.emit()

            return True, "Movimiento registrado con éxito."
        except Exception as e:
            return False, str(e)
   
    @staticmethod
    def filtrar_productos(texto="", categoria_id=None, proveedor_id=None):
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            
            query = """
                SELECT p.id, p.codigo_interno, p.descripcion, p.stock_actual, 
                       c.nombre as categoria, prov.razon_social as proveedor
                FROM productos p
                LEFT JOIN categorias c ON p.categoria_id = c.id
                LEFT JOIN proveedores prov ON p.proveedor_id = prov.id
                WHERE p.estado = 1
            """
            params = []

            if texto:
                query += " AND (p.codigo_interno LIKE ? OR p.descripcion LIKE ?)"
                params.extend([f"%{texto}%", f"%{texto}%"])
            if categoria_id:
                query += " AND p.categoria_id = ?"
                params.append(categoria_id)
            if proveedor_id:
                query += " AND p.proveedor_id = ?"
                params.append(proveedor_id)

            cursor.execute(query, params)
            regs = cursor.fetchall()
            conn.close()
            return regs
        except Exception as e:
            print(f"Error filtrando: {e}")
            return []