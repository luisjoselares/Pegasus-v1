import hashlib
import sqlite3
import os
from data.conexion import crear_conexion

class AuthController:
    # Variable de clase para mantener la sesión del usuario en memoria mientras el programa corre
    session = None 

    @staticmethod
    def _encriptar(password):
        """Convierte texto plano en un hash SHA-256 (Capa de seguridad 1)."""
        return hashlib.sha256(password.encode()).hexdigest()

    # --- SECCIÓN 1: ASISTENTE DE CONFIGURACIÓN (SETUP) ---

    @staticmethod
    def verificar_si_necesita_setup():
        """
        Determina si es la primera vez que se abre el sistema.
        Busca si ya hay un RIF registrado en la configuración.
        """
        conn = crear_conexion()
        if not conn: return True # Por seguridad, si falla la conexión, asumimos setup
        
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT rif FROM configuracion WHERE id = 1")
            resultado = cursor.fetchone()
            # Si el RIF es None o está vacío, el sistema no ha sido configurado
            return resultado is None or resultado[0] is None
        except:
            return True
        finally:
            conn.close()

    @classmethod
    def configurar_sistema_inicial(cls, datos_empresa, datos_admin):
        """
        Realiza la carga inicial del sistema. 
        datos_empresa: dict {rif, razon_social, direccion, tasa_bcv, es_especial}
        datos_admin: dict {nombre_real, cedula, username, password}
        """
        conn = crear_conexion()
        if not conn: return False, "Fallo de conexión."
        
        cursor = conn.cursor()
        try:
            # 1. Actualizar configuración fiscal
            cursor.execute("""
                UPDATE configuracion SET 
                    rif = ?, razon_social = ?, direccion_fiscal = ?, 
                    tasa_bcv = ?, es_contribuyente_especial = ?
                WHERE id = 1
            """, (
                datos_empresa['rif'], 
                datos_empresa['razon_social'], 
                datos_empresa['direccion'],
                datos_empresa['tasa_bcv'],
                datos_empresa['es_especial']
            ))

            # 2. Crear al Super-Administrador
            pw_hash = cls._encriptar(datos_admin['password'])
            
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, rol_id, estado)
                VALUES (?, ?, ?, ?)
            """, (datos_admin['username'], pw_hash, 1, 1)) # rol_id 1 = Administrador

            conn.commit()
            return True, "Sistema configurado exitosamente."
        except Exception as e:
            conn.rollback()
            return False, f"Error crítico: {str(e)}"
        finally:
            conn.close()

    # --- SECCIÓN 2: SEGURIDAD Y LOGIN ---

    @classmethod
    def login(cls, username, password):
        """Valida credenciales y crea una sesión segura."""
        conn = crear_conexion()
        if not conn: return False, "Error de base de datos."

        try:
            cursor = conn.cursor()
            query = """
                SELECT u.id, u.username, u.password_hash, u.estado, r.nombre 
                FROM usuarios u
                JOIN roles r ON u.rol_id = r.id
                WHERE u.username = ?
            """
            cursor.execute(query, (username,))
            user_data = cursor.fetchone()

            if not user_data:
                return False, "Credenciales inválidas." # Ofuscación por seguridad

            u_id, u_name, db_hash, estado, rol_name = user_data

            if estado == 0:
                return False, "Usuario inactivo. Contacte al administrador."

            if cls._encriptar(password) == db_hash:
                cls.session = {
                    "id": u_id,
                    "username": u_name,
                    "rol": rol_name
                }
                return True, "Acceso concedido."
            
            return False, "Credenciales inválidas."
        finally:
            conn.close()

    @classmethod
    def logout(cls):
        """Cierra la sesión actual."""
        cls.session = None

    @classmethod
    def obtener_usuario_actual(cls):
        """Retorna los datos del usuario logueado."""
        return cls.session