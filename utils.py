# proyecto/utils.py

import os
import sys
import shutil
from pathlib import Path

SEMESTRE_MAPA = {
    "1°": "PRIMER",
    "2°": "SEGUNDO",
    "3°": "TERCERO",
    "4°": "CUARTO",
    "5°": "QUINTO",
    "6°": "SEXTO",
    "7°": "SÉPTIMO",
    "8°": "OCTAVO",
}

def _base_ejecucion() -> str:
    """
    Carpeta base para datos persistentes y archivos generados.
    - Frozen: carpeta del ejecutable.
    - Dev: carpeta del archivo utils.py (no el cwd).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return str(Path(__file__).resolve().parent)

def _base_recursos() -> str:
    """
    Carpeta base para recursos empaquetados (onefile).
    - Frozen: sys._MEIPASS
    - Dev: carpeta del archivo utils.py
    """
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return str(Path(__file__).resolve().parent)

def obtener_directorio_base() -> str:
    """
    Carpeta base para operaciones de lectura/escritura persistentes:
    - En desarrollo: carpeta del proyecto (donde está utils.py).
    - En frozen: carpeta del ejecutable.
    """
    return _base_ejecucion()

def obtener_ruta(relativa: str) -> str:
    """
    Devuelve la ruta absoluta para archivos persistentes/generados:
    - Frozen: junto al exe.
    - Dev: junto a los .py (carpeta del proyecto).
    Úsala para: bds/, CSV/, LISTAS/, etc.
    """
    return os.path.join(_base_ejecucion(), relativa)

def obtener_ruta_recurso(relativa: str) -> str:
    """
    Devuelve la ruta absoluta a un recurso empaquetado:
    - Frozen: desde sys._MEIPASS
    - Dev: desde la carpeta del proyecto
    Úsala para: iconos, imágenes, fuentes empaquetadas, etc.
    """
    return os.path.join(_base_recursos(), relativa)

def cargar_env():
    """
    Carga .env empaquetado (onefile) desde sys._MEIPASS.
    En dev, carga .env desde la carpeta del proyecto.
    """
    try:
        from dotenv import load_dotenv
    except Exception as e:
        print(f"[WARN] python-dotenv no disponible: {e}")
        return False

    env_path = obtener_ruta_recurso(".env")
    if os.path.exists(env_path):
        return load_dotenv(env_path, override=True)

    print(f"[WARN] No se encontró .env empaquetado en: {env_path}")
    return False

def obtener_ruta_bd() -> str:
    """
    BD persistente EXTERNA (NO empaquetada):
    - Frozen: <carpeta_exe>/bds/estudiantes.db
      Si no existe, se crea vacía.
    - Dev: <carpeta_proyecto>/bds/estudiantes.db
      Si no existe, se crea vacía.
    """
    destino_dir = os.path.join(_base_ejecucion(), "bds")
    os.makedirs(destino_dir, exist_ok=True)
    destino_bd = os.path.join(destino_dir, "estudiantes.db")

    # Si no existe, créala vacía (SQLite la inicializa al conectar)
    if not os.path.exists(destino_bd):
        try:
            import sqlite3
            conn = sqlite3.connect(destino_bd)
            conn.close()
        except Exception as e:
            raise RuntimeError(f"No se pudo crear la BD en {destino_bd}: {e}")

    return destino_bd
