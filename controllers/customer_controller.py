from data.conexion import crear_conexion

class CustomerController:
    
    @staticmethod
    def normalizar_cedula(texto):
        """
        Limpia y estandariza la cédula/RIF sin forzar prefijos para permitir búsquedas universales.
        Ejemplo: 'j 12.345.678' -> 'J-12345678', '12345678' -> '12345678'
        """
        t = str(texto).upper().replace(" ", "").replace(".", "").replace("-", "")
        
        # Si explícitamente empieza por letra y le siguen números, le inyectamos el guion legal
        if len(t) > 1 and t[0] in "VJEGP" and t[1:].isdigit():
            return f"{t[0]}-{t[1:]}"
            
        return t

    @staticmethod
    def obtener_todos():
        conn = crear_conexion()
        if not conn: return []
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clientes ORDER BY nombre ASC")
            filas = cursor.fetchall()
            return [dict(fila) for fila in filas]
        except Exception as e:
            print(f"Error cargando clientes: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def guardar_cliente(datos):
        conn = crear_conexion()
        if not conn: return False, "Sin conexión"
        try:
            cursor = conn.cursor()
            
            cedula_limpia = CustomerController.normalizar_cedula(datos['cedula_rif'])
            nombre_limpio = datos['nombre'].strip().upper()
            
            cursor.execute("SELECT id FROM clientes WHERE cedula_rif = ?", (cedula_limpia,))
            if cursor.fetchone():
                return False, f"El RIF/Cédula {cedula_limpia} ya está registrado."

            cursor.execute("""
                INSERT INTO clientes (cedula_rif, nombre, direccion, telefono)
                VALUES (?, ?, ?, ?)
            """, (cedula_limpia, nombre_limpio, datos['direccion'], datos['telefono']))
            
            conn.commit()
            return True, "Guardado"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def actualizar_cliente(id_cliente, datos):
        conn = crear_conexion()
        try:
            cursor = conn.cursor()
            
            cedula_limpia = CustomerController.normalizar_cedula(datos['cedula_rif'])
            nombre_limpio = datos['nombre'].strip().upper()
            
            cursor.execute("SELECT id FROM clientes WHERE cedula_rif = ? AND id != ?", (cedula_limpia, id_cliente))
            if cursor.fetchone():
                return False, f"El RIF/Cédula {cedula_limpia} pertenece a otro cliente."

            cursor.execute("""
                UPDATE clientes SET cedula_rif=?, nombre=?, direccion=?, telefono=?
                WHERE id=?
            """, (cedula_limpia, nombre_limpio, datos['direccion'], datos['telefono'], id_cliente))
            
            conn.commit()
            return True, "Actualizado"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def buscar_cliente(texto):
        conn = crear_conexion()
        try:
            cursor = conn.cursor()
            
            texto_crudo = texto.strip().upper()
            cedula_busqueda = CustomerController.normalizar_cedula(texto)
            
            filtro_nombre = f"%{texto_crudo}%"
            # Al no forzar la V, buscar '1234' traerá coincidencias de V-1234, J-1234, E-1234, etc.
            filtro_cedula = f"%{cedula_busqueda}%" 
            
            cursor.execute("""
                SELECT * FROM clientes 
                WHERE cedula_rif LIKE ? OR nombre LIKE ? 
                ORDER BY nombre ASC
            """, (filtro_cedula, filtro_nombre))
            
            filas = cursor.fetchall()
            
            if not filas and texto_crudo != cedula_busqueda:
                cursor.execute("""
                    SELECT * FROM clientes 
                    WHERE cedula_rif LIKE ? OR nombre LIKE ? 
                    ORDER BY nombre ASC
                """, (filtro_nombre, filtro_nombre))
                filas = cursor.fetchall()
                
            return [dict(fila) for fila in filas]
        finally:
            conn.close()