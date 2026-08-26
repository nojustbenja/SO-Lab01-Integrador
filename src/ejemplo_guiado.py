from pathlib import Path
from collections import Counter
from queue import Queue
import queue
from threading import Thread, Lock
from datetime import date, datetime
import shutil

BASE = Path.home() / "laboratorio_so"
ENTRADA = BASE / "data" / "entrada"
PROCESADOS = BASE / "data" / "procesados"
REPORTES = BASE / "data" / "reportes"
LOG = BASE / "logs" / "sistema.log"
cola = Queue()
bloqueo_log = Lock()
bloqueo_totales = Lock()
totales = {"archivos": 0, "palabras": 0, "caracteres": 0}
def registrar (mensaje):
    marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with bloqueo_log:
        with LOG.open("a", encoding="utf-8") as archivo_log:
            archivo_log.write(f"{marca_tiempo} - {mensaje}\n")

def procesar_archivo(ruta):
    contenido = ruta.read_text (encoding="utf-8")
    palabras = contenido.lower().split()
    frecuencia = Counter(palabras)
    palabra_frecuente = frecuencia.most_common(1)[0][0] if palabras else "Sin palabras"
    reporte = REPORTES / f"reporte_(ruta.stem}.txt"
    reporte.write_text(
        f"Archivo: {ruta.name}\n"
        f"Líneas: {len(contenido.splitlines())}\n"
        f"Palabras: {len (palabras) }\n"
        f"Caracteres: {len(contenido)}\n"
        f"Palabra más frecuente: {palabra_frecuente}\n",
        encoding="utf-8",
    )
    with bloqueo_totales:
        totales ["archivos"] += 1
        totales["palabras"] += len(palabras)
        totales["caracteres"] += len(contenido)
    shutil. move(str(ruta), PROCESADOS / ruta.name)
    registrar(f"Procesado correctamente: {ruta.name}")
