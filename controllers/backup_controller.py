import shutil
import os
from datetime import datetime

class BackupController:
    @staticmethod
    def crear_respaldo(destino_manual=None):
        """
        Copia la base de datos actual a una carpeta de respaldos.
        """
        origen = "data/pegasus_fisco.db"
        
        # Si el archivo no existe, no hay nada que respaldar
        if not os.path.exists(origen):
            return False, "Base de datos no encontrada."

        # Definir nombre del archivo con fecha y hora
        fecha_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nombre_backup = f"Pegasus_Backup_{fecha_str}.db"

        # Determinar carpeta de destino
        if destino_manual:
            ruta_final = os.path.join(destino_manual, nombre_backup)
        else:
            # Por defecto, crear carpeta 'backups' en la raíz del proyecto
            if not os.path.exists("backups"):
                os.makedirs("backups")
            ruta_final = os.path.join("backups", nombre_backup)

        try:
            shutil.copy2(origen, ruta_final)
            return True, f"Respaldo creado en: {ruta_final}"
        except Exception as e:
            return False, f"Error al respaldar: {str(e)}"