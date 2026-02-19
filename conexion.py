import sqlite3
import hashlib
import os

# --- CONFIGURACIÓN CENTRAL ---
DB_NAME = "pegasus_fisco.db"
DB_PATH = os.path.join("data", DB_NAME)

def crear_conexion():
    """Crea y retorna una conexión a la base de datos."""
    try:
        if not os.path.exists('data'):
            os.makedirs('data')
            
        # 1. Agregamos timeout=10 (espera hasta 10 seg en lugar de fallar de inmediato)
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        conn.row_factory = sqlite3.Row 
        conn.execute("PRAGMA foreign_keys = ON") 
        
        # 2. Habilitamos modo WAL (Write-Ahead Logging) permite lecturas y escrituras simultáneas
        conn.execute("PRAGMA journal_mode = WAL") 
        
        return conn
    except sqlite3.Error as e:
        print(f"❌ Error de conexión: {e}")
        return None

def sistema_esta_configurado():
    """Verifica si el sistema tiene usuarios y empresa configurada."""
    conn = crear_conexion()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0] > 0
        cursor.execute("SELECT COUNT(*) FROM configuracion WHERE rif IS NOT NULL")
        empresa = cursor.fetchone()[0] > 0
        return usuarios and empresa
    except:
        return False
    finally:
        conn.close()

# --- FUNCIÓN DE MANTENIMIENTO ---
def verificar_columna(cursor, tabla, columna, definicion_sql):
    """
    Intenta seleccionar una columna. Si falla, la crea automáticamente.
    """
    try:
        cursor.execute(f"SELECT {columna} FROM {tabla} LIMIT 1")
    except sqlite3.OperationalError:
        try:
            print(f"🛠️ Migración: Agregando columna '{columna}' a tabla '{tabla}'...")
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion_sql}")
        except Exception as e:
            print(f"⚠️ Error agregando {columna}: {e}")

def inicializar_base_de_datos():
    conn = crear_conexion()
    if not conn: return
    cursor = conn.cursor()

    # ==========================================
    # 1. CREACIÓN DE TABLAS (ESTRUCTURA BASE)
    # ==========================================

    # Seguridad
    cursor.execute('''CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, 
        rol_id INTEGER, estado INTEGER DEFAULT 1, FOREIGN KEY(rol_id) REFERENCES roles(id)
    )''')

    # Configuración
    cursor.execute('''CREATE TABLE IF NOT EXISTS configuracion (
        id INTEGER PRIMARY KEY, rif TEXT, razon_social TEXT, direccion_fiscal TEXT,
        tasa_bcv REAL DEFAULT 1.0, tasa_cop REAL DEFAULT 0.0,
        es_contribuyente_especial INTEGER DEFAULT 0, porcentaje_igtf REAL DEFAULT 3.0,
        proximo_nro_control INTEGER DEFAULT 1, proximo_nro_nc INTEGER DEFAULT 1,
        proximo_nro_factura INTEGER DEFAULT 1, proximo_nro_ne INTEGER DEFAULT 1,
        proximo_nro_z INTEGER DEFAULT 1
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS historial_tasas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha DATETIME DEFAULT CURRENT_TIMESTAMP, moneda TEXT, 
        tasa_anterior REAL, tasa_nueva REAL, usuario_id INTEGER
    )''')

    # Maestros
    cursor.execute('''CREATE TABLE IF NOT EXISTS categorias (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS proveedores (id INTEGER PRIMARY KEY AUTOINCREMENT, rif TEXT UNIQUE NOT NULL, razon_social TEXT NOT NULL, contacto TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cedula_rif TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL, 
        direccion TEXT, telefono TEXT, saldo_favor REAL DEFAULT 0
    )''')
    
    # Compras
    cursor.execute('''CREATE TABLE IF NOT EXISTS compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proveedor_id INTEGER,
        nro_factura TEXT NOT NULL,
        nro_control TEXT,
        fecha_emision DATE,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        tasa_cambio REAL,
        total_compra_bs REAL,
        base_imponible_bs REAL,
        monto_exento_bs REAL,
        impuesto_iva_bs REAL,
        iva_retenido_bs REAL DEFAULT 0,
        igtf_pagado_bs REAL DEFAULT 0,
        tipo_transaccion TEXT DEFAULT '01-REG',
        factura_afectada TEXT,
        observaciones TEXT,
        FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
    )''')

    # Inventario
    cursor.execute('''CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, codigo_interno TEXT UNIQUE NOT NULL, descripcion TEXT NOT NULL, 
        precio_usd REAL NOT NULL, iva_tipo TEXT DEFAULT 'GENERAL', iva_porcentaje REAL DEFAULT 16.0, 
        stock_actual REAL DEFAULT 0, stock_minimo REAL DEFAULT 5, es_exento INTEGER DEFAULT 0, 
        categoria_id INTEGER, proveedor_id INTEGER, estado INTEGER DEFAULT 1,
        FOREIGN KEY(categoria_id) REFERENCES categorias(id), FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
    )''')

    # KARDEX
    cursor.execute('''CREATE TABLE IF NOT EXISTS inventario_kardex (
        id INTEGER PRIMARY KEY AUTOINCREMENT, producto_id INTEGER, tipo_movimiento TEXT, cantidad REAL, 
        stock_resultante REAL DEFAULT 0, motivo TEXT, fecha DATETIME DEFAULT CURRENT_TIMESTAMP, 
        usuario_id INTEGER, proveedor_id INTEGER, referencia TEXT, observaciones TEXT,
        FOREIGN KEY(producto_id) REFERENCES productos(id)
    )''')

    # Ventas y Documentos
    cursor.execute('''CREATE TABLE IF NOT EXISTS documentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tipo_doc TEXT, nro_documento TEXT UNIQUE, nro_control TEXT,
        cliente_id INTEGER, fecha DATETIME DEFAULT CURRENT_TIMESTAMP, tasa_cambio_momento REAL,
        
        subtotal_usd REAL, descuento_porcentaje REAL DEFAULT 0, descuento_monto REAL DEFAULT 0,
        impuesto_iva_usd REAL, impuesto_igtf_usd REAL, total_usd REAL,
        
        metodo_pago TEXT, 
        monto_recibido_usd REAL DEFAULT 0, monto_recibido_bs REAL DEFAULT 0, monto_recibido_cop REAL DEFAULT 0,
        monto_vuelto_usd REAL DEFAULT 0, monto_vuelto_bs REAL DEFAULT 0, monto_vuelto_cop REAL DEFAULT 0,

        pago_usd_efectivo REAL DEFAULT 0, pago_usd_zelle REAL DEFAULT 0,
        pago_bs_efectivo REAL DEFAULT 0, pago_bs_punto REAL DEFAULT 0, pago_bs_transf REAL DEFAULT 0,
        pago_cop_efectivo REAL DEFAULT 0, pago_cop_transf REAL DEFAULT 0,

        estado TEXT DEFAULT 'PROCESADO',
        documento_referencia TEXT, motivo_anulacion TEXT, iva_retenido_bs REAL DEFAULT 0,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )''')

    # SE AÑADE cantidad_devuelta AL DETALLE DEL DOCUMENTO
    cursor.execute('''CREATE TABLE IF NOT EXISTS documento_detalles (
        id INTEGER PRIMARY KEY AUTOINCREMENT, documento_id INTEGER, producto_id INTEGER, 
        cantidad REAL, precio_unitario_usd REAL, subtotal_usd REAL DEFAULT 0,
        cantidad_devuelta REAL DEFAULT 0,
        FOREIGN KEY(documento_id) REFERENCES documentos(id)
    )''')

    # Caja
    cursor.execute('''CREATE TABLE IF NOT EXISTS caja_sesiones (
        id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, 
        fecha_apertura DATETIME DEFAULT CURRENT_TIMESTAMP, fecha_cierre DATETIME,
        monto_inicial_usd REAL DEFAULT 0, monto_inicial_bs REAL DEFAULT 0, monto_inicial_cop REAL DEFAULT 0,
        monto_final_usd REAL DEFAULT 0, monto_final_bs REAL DEFAULT 0, monto_final_cop REAL DEFAULT 0,
        monto_sistema_usd REAL DEFAULT 0, monto_sistema_bs REAL DEFAULT 0, monto_sistema_cop REAL DEFAULT 0,
        diferencia_usd REAL DEFAULT 0, diferencia_bs REAL DEFAULT 0, diferencia_cop REAL DEFAULT 0,
        estado TEXT DEFAULT 'ABIERTA', observaciones TEXT,
        FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS caja_movimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sesion_id INTEGER, tipo TEXT, 
        monto_usd REAL DEFAULT 0, monto_bs REAL DEFAULT 0, monto_cop REAL DEFAULT 0,
        motivo TEXT, fecha DATETIME DEFAULT CURRENT_TIMESTAMP, usuario_id INTEGER,
        FOREIGN KEY(sesion_id) REFERENCES caja_sesiones(id)
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS caja_kardex (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sesion_id INTEGER, operacion TEXT, 
        entrada_usd REAL DEFAULT 0, salida_usd REAL DEFAULT 0, saldo_usd REAL DEFAULT 0,
        entrada_bs REAL DEFAULT 0, salida_bs REAL DEFAULT 0, saldo_bs REAL DEFAULT 0,
        entrada_cop REAL DEFAULT 0, salida_cop REAL DEFAULT 0, saldo_cop REAL DEFAULT 0,
        descripcion TEXT, referencia_doc TEXT, fecha DATETIME DEFAULT CURRENT_TIMESTAMP, 
        usuario_id INTEGER, FOREIGN KEY(sesion_id) REFERENCES caja_sesiones(id)
    )''')

    # ==========================================
    # 2. AUTO-REPARACIÓN (MIGRACIONES)
    # ==========================================
    
    # Configuracion
    verificar_columna(cursor, 'configuracion', 'proximo_nro_nc', 'INTEGER DEFAULT 1')
    verificar_columna(cursor, 'configuracion', 'proximo_nro_factura', 'INTEGER DEFAULT 1')
    verificar_columna(cursor, 'configuracion', 'proximo_nro_ne', 'INTEGER DEFAULT 1')
    verificar_columna(cursor, 'configuracion', 'proximo_nro_z', 'INTEGER DEFAULT 1')
    
    # Clientes
    verificar_columna(cursor, 'clientes', 'saldo_favor', 'REAL DEFAULT 0')
    
    # Kardex
    verificar_columna(cursor, 'inventario_kardex', 'referencia', 'TEXT')
    verificar_columna(cursor, 'inventario_kardex', 'stock_resultante', 'REAL DEFAULT 0')
    
    # Documentos
    verificar_columna(cursor, 'documentos', 'descuento_porcentaje', 'REAL DEFAULT 0')
    verificar_columna(cursor, 'documentos', 'descuento_monto', 'REAL DEFAULT 0')
    verificar_columna(cursor, 'documentos', 'documento_referencia', 'TEXT')
    verificar_columna(cursor, 'documentos', 'motivo_anulacion', 'TEXT')
    verificar_columna(cursor, 'documentos', 'iva_retenido_bs', 'REAL DEFAULT 0')
    verificar_columna(cursor, 'documentos', 'monto_vuelto_cop', 'REAL DEFAULT 0')
    verificar_columna(cursor, 'documentos', 'estado', "TEXT DEFAULT 'PROCESADO'")

    # Documento Detalles (NUEVA MIGRACIÓN AQUÍ)
    verificar_columna(cursor, 'documento_detalles', 'subtotal_usd', 'REAL DEFAULT 0')
    verificar_columna(cursor, 'documento_detalles', 'cantidad_devuelta', 'REAL DEFAULT 0')
    
    # Pagos Detallados
    cols_pago = [
        'pago_usd_efectivo', 'pago_usd_zelle',
        'pago_bs_efectivo', 'pago_bs_punto', 'pago_bs_transf',
        'pago_cop_efectivo', 'pago_cop_transf'
    ]
    for col in cols_pago:
        verificar_columna(cursor, 'documentos', col, 'REAL DEFAULT 0')

    # Caja
    cols_caja = ['monto_inicial_cop', 'monto_final_cop', 'monto_sistema_cop', 'diferencia_cop']
    for col in cols_caja:
        verificar_columna(cursor, 'caja_sesiones', col, 'REAL DEFAULT 0')
    
    verificar_columna(cursor, 'caja_movimientos', 'monto_cop', 'REAL DEFAULT 0')

    cols_kardex_caja = ['entrada_cop', 'salida_cop', 'saldo_cop']
    for col in cols_kardex_caja:
        verificar_columna(cursor, 'caja_kardex', col, 'REAL DEFAULT 0')

    # ==========================================
    # 3. DATOS INICIALES
    # ==========================================
    cursor.execute("INSERT OR IGNORE INTO roles (id, nombre) VALUES (1, 'Administrador'), (2, 'Cajero'), (3, 'Almacenista')")
    hash_clave = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute("INSERT OR IGNORE INTO usuarios (username, password_hash, rol_id) VALUES (?, ?, ?)", 
                   ('admin', hash_clave, 1))
    cursor.execute("INSERT OR IGNORE INTO configuracion (id, tasa_bcv, tasa_cop) VALUES (1, 36.50, 3900.0)")
    cursor.execute("INSERT OR IGNORE INTO clientes (id, cedula_rif, nombre) VALUES (1, '00000000', 'CONSUMIDOR FINAL')")

    conn.commit()
    conn.close()
    print("✅ Base de datos verificada, optimizada y lista.")

if __name__ == "__main__":
    inicializar_base_de_datos()