import sqlite3
from datetime import datetime

class DashboardController:
    @staticmethod
    def obtener_resumen_hoy():
        """Consulta los totales de ventas del día actual."""
        conn = sqlite3.connect('data/pegasus_fisco.db')
        cursor = conn.cursor()
        
        # Obtenemos la fecha actual en formato YYYY-MM-DD
        hoy = datetime.now().strftime('%Y-%m-%d')
        
        query = """
            SELECT 
                SUM(pago_usd), 
                SUM(pago_ves), 
                SUM(pago_cop), 
                SUM(total_ves) 
            FROM ventas 
            WHERE date(fecha) = ?
        """
        
        try:
            cursor.execute(query, (hoy,))
            resultado = cursor.fetchone()
            
            # Si no hay ventas, devolvemos ceros
            resumen = {
                'usd': resultado[0] if resultado[0] else 0.0,
                'ves': resultado[1] if resultado[1] else 0.0,
                'cop': resultado[2] if resultado[2] else 0.0,
                'fiscal': resultado[3] if resultado[3] else 0.0
            }
        except Exception as e:
            print(f"Error al consultar dashboard: {e}")
            resumen = {'usd': 0, 'ves': 0, 'cop': 0, 'fiscal': 0}
        finally:
            conn.close()
            
        return resumen