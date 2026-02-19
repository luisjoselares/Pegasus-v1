import sys
import os
from datetime import datetime # <--- IMPORTANTE: Necesario para registrar la fecha del cambio

# Agregamos la carpeta raíz al path para que Python encuentre la carpeta 'data'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Importamos usando la ruta del paquete
    from data.conexion import crear_conexion
except ImportError:
    # En caso de que se ejecute desde la raíz directamente
    from data.conexion import crear_conexion
    
class ConfigController:
    @staticmethod
    def obtener_configuracion():
        """Obtiene la fila única de configuración usando la conexión profesional"""
        conn = crear_conexion()
        if not conn: 
            return None
        try:
            # Esto permite acceder a las columnas por nombre (ej: config['tasa_bcv'])
            conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM configuracion WHERE id = 1")
            return cursor.fetchone()
        finally:
            conn.close()

    @staticmethod
    def actualizar_tasas(tasa_bcv, tasa_cop):
        """Actualiza las tasas y deja registro en el historial si cambiaron"""
        conn = crear_conexion()
        if not conn: 
            return False
        try:
            cursor = conn.cursor()
            
            # 1. OBTENER TASAS ANTERIORES (Para el historial)
            cursor.execute("SELECT tasa_bcv, tasa_cop FROM configuracion WHERE id = 1")
            actual = cursor.fetchone()
            
            # Validación por si es la primera vez (base de datos vacía)
            tasa_bcv_anterior = actual[0] if actual else 0.0
            tasa_cop_anterior = actual[1] if actual else 0.0
            
            # 2. REGISTRAR EN HISTORIAL (Solo si el valor cambió)
            # Detectar cambio en Dólar BCV
            if float(tasa_bcv) != float(tasa_bcv_anterior):
                cursor.execute("""
                    INSERT INTO historial_tasas (fecha, moneda, tasa_anterior, tasa_nueva, usuario_id)
                    VALUES (?, 'BCV', ?, ?, ?)
                """, (datetime.now(), tasa_bcv_anterior, tasa_bcv, 1)) # Asumimos usuario 1 (Admin)

            # Detectar cambio en Pesos COP
            if float(tasa_cop) != float(tasa_cop_anterior):
                cursor.execute("""
                    INSERT INTO historial_tasas (fecha, moneda, tasa_anterior, tasa_nueva, usuario_id)
                    VALUES (?, 'COP', ?, ?, ?)
                """, (datetime.now(), tasa_cop_anterior, tasa_cop, 1))

            # 3. ACTUALIZAR CONFIGURACIÓN (Tu código original)
            cursor.execute("""
                UPDATE configuracion 
                SET tasa_bcv = ?, tasa_cop = ? 
                WHERE id = 1
            """, (tasa_bcv, tasa_cop))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al actualizar tasas: {e}")
            return False
        finally:
            conn.close()

    # --- MÉTODO EXTRA ---
    # He añadido este método por si necesitas guardar RIF, Nombre, Dirección, etc.
    # Si tu vista de configuración lo usa, aquí lo tienes listo.
    @staticmethod
    def guardar_configuracion(datos):
        conn = crear_conexion()
        if not conn: return False
        try:
            cursor = conn.cursor()
            # Verificar si existe o se crea
            cursor.execute("SELECT count(*) FROM configuracion WHERE id = 1")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO configuracion (id, rif, razon_social, direccion_fiscal, porcentaje_igtf) 
                    VALUES (1, ?, ?, ?, ?)
                """, (datos['rif'], datos['razon_social'], datos['direccion'], datos['igtf']))
            else:
                cursor.execute("""
                    UPDATE configuracion SET rif=?, razon_social=?, direccion_fiscal=?, porcentaje_igtf=? 
                    WHERE id=1
                """, (datos['rif'], datos['razon_social'], datos['direccion'], datos['igtf']))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al guardar datos empresa: {e}")
            return False
        finally:
            conn.close()