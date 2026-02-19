import sqlite3
from data.conexion import crear_conexion
from controllers.customer_controller import CustomerController

class MasterDataController:
    
    # --- GESTIÓN DE CATEGORÍAS ---
    @staticmethod
    def obtener_categorias():
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categorias ORDER BY nombre ASC")
            regs = cursor.fetchall()
            conn.close()
            return regs
        except Exception as e:
            print(f"Error: {e}")
            return []

    @staticmethod
    def añadir_categoria(nombre):
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre.strip(),))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return "Error: La categoría ya existe."
        except Exception as e:
            return str(e)

    # --- GESTIÓN DE PROVEEDORES ---
    @staticmethod
    def obtener_proveedores():
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT id, rif, razon_social, contacto FROM proveedores ORDER BY razon_social ASC")
            regs = cursor.fetchall()
            conn.close()
            return regs
        except Exception as e:
            print(f"Error: {e}")
            return []

    @staticmethod
    def añadir_proveedor(rif, nombre, contacto):
        rif_limpio = CustomerController.normalizar_cedula(rif)
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO proveedores (rif, razon_social, contacto) VALUES (?, ?, ?)", 
                           (rif_limpio, nombre.strip(), contacto.strip()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return "Error: El RIF ya está registrado."
        except Exception as e:
            return str(e)
            
    @staticmethod
    def actualizar_proveedor(id_prov, rif, nombre, contacto):
        rif_limpio = CustomerController.normalizar_cedula(rif)
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM proveedores WHERE rif = ? AND id != ?", (rif_limpio, id_prov))
            if cursor.fetchone():
                conn.close()
                return "Error: El RIF ya pertenece a otro proveedor."

            cursor.execute("""
                UPDATE proveedores SET rif = ?, razon_social = ?, contacto = ? WHERE id = ?
            """, (rif_limpio, nombre.strip(), contacto.strip(), id_prov))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return str(e)

    # --- GESTIÓN DE CLIENTES ---
    @staticmethod
    def añadir_cliente(cedula_rif, nombre, direccion="", telefono=""):
        cedula_limpia = CustomerController.normalizar_cedula(cedula_rif)
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clientes (cedula_rif, nombre, direccion, telefono) 
                VALUES (?, ?, ?, ?)
            """, (cedula_limpia, nombre.strip().upper(), direccion.strip(), telefono.strip()))
            conn.commit()
            id_nuevo = cursor.lastrowid
            conn.close()
            return True, id_nuevo
        except sqlite3.IntegrityError:
            return False, f"La Cédula/RIF {cedula_limpia} ya existe en el sistema."
        except Exception as e:
            return False, str(e)
            
    @staticmethod
    def buscar_cliente_por_cedula(cedula):
        cedula_limpia = CustomerController.normalizar_cedula(cedula)
        
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            
            # BÚSQUEDA 1: Estricta. Si escribieron la letra (Ej: J-12345678) o si era cliente antiguo sin formato.
            cursor.execute("SELECT id, cedula_rif, nombre FROM clientes WHERE cedula_rif = ?", (cedula_limpia,))
            res = cursor.fetchone()
            
            # BÚSQUEDA 2 (INTELIGENTE): Si no lo halla, y el cajero tecleó SOLO números.
            if not res and cedula_limpia.isdigit():
                # Buscamos cualquier letra combinada con esos números (Ej: %12345678)
                cursor.execute("SELECT id, cedula_rif, nombre FROM clientes WHERE cedula_rif LIKE ?", (f"%{cedula_limpia}",))
                matches = cursor.fetchall()
                if matches:
                    # En caso de que exista un J-12345678 y un V-12345678, damos prioridad a la V. 
                    # Si no hay V, retornamos el J o el E que hayamos encontrado.
                    res = next((m for m in matches if str(m['cedula_rif']).startswith('V-')), matches[0])
                    
            conn.close()
            return res
        except Exception as e:
            print(f"🚨 ERROR CRÍTICO EN LA BÚSQUEDA DE CLIENTE: {e}")
            return None
            
    @staticmethod
    def actualizar_cliente(id_cliente, cedula_rif, nombre, direccion="", telefono=""):
        cedula_limpia = CustomerController.normalizar_cedula(cedula_rif)
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM clientes WHERE cedula_rif = ? AND id != ?", 
                           (cedula_limpia, id_cliente))
            
            if cursor.fetchone():
                conn.close()
                return False, f"La Cédula/RIF {cedula_limpia} ya pertenece a otro cliente."

            cursor.execute("""
                UPDATE clientes SET cedula_rif = ?, nombre = ?, direccion = ?, telefono = ?
                WHERE id = ?
            """, (cedula_limpia, nombre.strip().upper(), direccion.strip(), telefono.strip(), id_cliente))
            
            conn.commit()
            conn.close()
            return True, "Cliente actualizado correctamente."
        except Exception as e:
            return False, str(e)