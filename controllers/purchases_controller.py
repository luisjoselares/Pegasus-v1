import sqlite3
from datetime import datetime
from data.conexion import crear_conexion
from core.app_signals import comunicacion

class PurchasesController:
    
    @staticmethod
    def inicializar_tabla_detalles():
        """Auto-migración: Crea la tabla de detalles de compra si no existe."""
        conn = crear_conexion()
        if conn:
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS compra_detalles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        compra_id INTEGER,
                        producto_id INTEGER,
                        cantidad REAL,
                        costo_unitario_bs REAL,
                        FOREIGN KEY(compra_id) REFERENCES compras(id)
                    )
                """)
                conn.commit()
            except Exception as e:
                print(f"Error en migración de compras: {e}")
            finally:
                conn.close()

    @staticmethod
    def registrar_compra(datos_compra, carrito_productos):
        """
        Guarda la factura del proveedor para el Libro de Compras 
        e inyecta el stock automáticamente al inventario.
        """
        PurchasesController.inicializar_tabla_detalles()
        
        conn = crear_conexion()
        if not conn: return False, "Error de conexión con la base de datos."
        
        conn.execute("PRAGMA busy_timeout = 5000")
        
        try:
            cursor = conn.cursor()
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 1. INSERTAR LA CABECERA FISCAL (Para el Libro de Compras)
            cursor.execute("""
                INSERT INTO compras (
                    proveedor_id, nro_factura, nro_control, fecha_emision, fecha_registro,
                    tasa_cambio, total_compra_bs, base_imponible_bs, 
                    monto_exento_bs, impuesto_iva_bs, tipo_transaccion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '01-REG')
            """, (
                datos_compra['proveedor_id'], 
                datos_compra['nro_factura'], 
                datos_compra['nro_control'], 
                datos_compra['fecha_emision'], # Fecha que trae el papel físico
                fecha_actual,                  # Fecha en la que lo estás registrando
                datos_compra['tasa_cambio'], 
                datos_compra['total_compra_bs'],
                datos_compra['base_imponible_bs'], 
                datos_compra['monto_exento_bs'],
                datos_compra['impuesto_iva_bs']
            ))
            
            compra_id = cursor.lastrowid
            
            # 2. INSERTAR DETALLES Y ALIMENTAR INVENTARIO
            for item in carrito_productos:
                
                # A) Guardar qué se compró y a qué precio
                cursor.execute("""
                    INSERT INTO compra_detalles (compra_id, producto_id, cantidad, costo_unitario_bs)
                    VALUES (?, ?, ?, ?)
                """, (compra_id, item['id'], item['cantidad'], item['costo_bs']))
                
                # B) Sumar la mercancía física al estante
                cursor.execute("""
                    UPDATE productos 
                    SET stock_actual = stock_actual + ? 
                    WHERE id = ?
                """, (item['cantidad'], item['id']))
                
                # C) Consultar cómo quedó el estante tras sumar
                cursor.execute("SELECT stock_actual FROM productos WHERE id=?", (item['id'],))
                nuevo_stock = cursor.fetchone()[0]
                
                # D) Asentar la operación en el Libro Mayor de Inventario (Kardex)
                cursor.execute("""
                    INSERT INTO inventario_kardex (
                        producto_id, tipo_movimiento, cantidad, stock_resultante, 
                        motivo, referencia, proveedor_id, fecha, usuario_id
                    ) VALUES (?, 'ENTRADA', ?, ?, 'COMPRA', ?, ?, ?, 1)
                """, (
                    item['id'], item['cantidad'], nuevo_stock, 
                    datos_compra['nro_factura'], datos_compra['proveedor_id'], 
                    fecha_actual
                ))

            conn.commit()
            
            # Avisar al resto del sistema (Ventana de ventas, etc.) que hay mercancía nueva
            try:
                comunicacion.inventario_actualizado.emit()
            except Exception as e_sig:
                print(f"Compra registrada, pero error en señal: {e_sig}")
            
            return True, "Factura de compra registrada e inventario actualizado."
            
        except sqlite3.IntegrityError:
            conn.rollback()
            return False, "Error: Verifique que no esté registrando una factura duplicada."
        except Exception as e:
            conn.rollback()
            return False, f"Error crítico al guardar la compra: {e}"
        finally:
            conn.close()