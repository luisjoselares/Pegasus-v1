import sqlite3
from data.conexion import crear_conexion

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
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO proveedores (rif, razon_social, contacto) VALUES (?, ?, ?)", 
                           (rif.strip(), nombre.strip(), contacto.strip()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return "Error: El RIF ya está registrado."
        except Exception as e:
            return str(e)
            
    @staticmethod
    def actualizar_proveedor(id_prov, rif, nombre, contacto):
        """Edita proveedor validando que el RIF no pertenezca a otro"""
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            
            # Verificar duplicados excluyendo el propio ID
            cursor.execute("SELECT id FROM proveedores WHERE rif = ? AND id != ?", (rif.strip(), id_prov))
            if cursor.fetchone():
                conn.close()
                return "Error: El RIF ya pertenece a otro proveedor."

            cursor.execute("""
                UPDATE proveedores SET rif = ?, razon_social = ?, contacto = ? WHERE id = ?
            """, (rif.strip(), nombre.strip(), contacto.strip(), id_prov))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return str(e)

    # --- GESTIÓN DE CLIENTES ---
    @staticmethod
    def añadir_cliente(cedula_rif, nombre, direccion="", telefono=""):
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clientes (cedula_rif, nombre, direccion, telefono) 
                VALUES (?, ?, ?, ?)
            """, (cedula_rif.strip().upper(), nombre.strip().upper(), direccion.strip(), telefono.strip()))
            conn.commit()
            id_nuevo = cursor.lastrowid
            conn.close()
            return True, id_nuevo
        except sqlite3.IntegrityError:
            return False, "La Cédula/RIF ya existe en el sistema."
        except Exception as e:
            return False, str(e)
            
    @staticmethod
    def buscar_cliente_por_cedula(cedula):
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            cursor.execute("SELECT id, cedula_rif, nombre FROM clientes WHERE cedula_rif = ?", (cedula.strip().upper(),))
            res = cursor.fetchone()
            conn.close()
            return res
        except:
            return None
            
    @staticmethod
    def actualizar_cliente(id_cliente, cedula_rif, nombre, direccion="", telefono=""):
        """SOLUCIÓN: Edita cliente verificando duplicados externos"""
        try:
            conn = crear_conexion()
            cursor = conn.cursor()
            
            # Validación: ¿Existe esta cédula en OTRO cliente que no soy yo?
            cursor.execute("SELECT id FROM clientes WHERE cedula_rif = ? AND id != ?", 
                           (cedula_rif.strip().upper(), id_cliente))
            
            if cursor.fetchone():
                conn.close()
                return False, "La Cédula/RIF ya pertenece a otro cliente."

            cursor.execute("""
                UPDATE clientes SET cedula_rif = ?, nombre = ?, direccion = ?, telefono = ?
                WHERE id = ?
            """, (cedula_rif.strip().upper(), nombre.strip().upper(), direccion.strip(), telefono.strip(), id_cliente))
            
            conn.commit()
            conn.close()
            return True, "Cliente actualizado correctamente."
        except Exception as e:
            return False, str(e)