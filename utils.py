# proyecto/utils.py

import os
import sys
import shutil

SEMESTRE_MAPA = {
    "1°": "PRIMER",
    "2°": "SEGUNDO",
    "3°": "TERCER",
    "4°": "CUARTO",
    "5°": "QUINTO",
    "6°": "SEXTO",
    "7°": "SÉPTIMO",
    "8°": "OCTAVO",
}

def obtener_ruta_bd():
    if getattr(sys, 'frozen', False):
        # Base en el ejecutable para la BD persistente
        base_path = os.path.dirname(sys.executable)
        destino_dir = os.path.join(base_path, "bds")
        os.makedirs(destino_dir, exist_ok=True)
        destino_bd = os.path.join(destino_dir, "estudiantes.db")
        if not os.path.exists(destino_bd):
            origen_bd = os.path.join(sys._MEIPASS, "bds", "estudiantes.db")
            try:
                shutil.copy(origen_bd, destino_bd)
            except Exception as e:
                print(f"Error al copiar la BD desde {origen_bd} a {destino_bd}: {e}")
        return destino_bd
    else:
        return os.path.join(os.path.abspath("."), "bds", "estudiantes.db")


def obtener_ruta(relativa: str) -> str:
    """
    Devuelve la ruta absoluta a un recurso externo:
    - En desarrollo (no frozen): busca en el cwd.
    - En onefile/aplicación congelada: sube un nivel desde 'dist/' para usar las carpetas externas.
    """
    if getattr(sys, 'frozen', False):
        # sys.executable == <...>/dist/MiApp.exe
        exe_folder = os.path.dirname(sys.executable)
        # Proyecto está un nivel arriba de dist/
        base_path = os.path.abspath(os.path.join(exe_folder, os.pardir))
    else:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relativa)


def obtener_directorio_base() -> str:
    """
    Carpeta base para operaciones de lectura/escritura:
    - En desarrollo: carpeta del script.
    - En frozen: carpeta del ejecutable.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath('.')
