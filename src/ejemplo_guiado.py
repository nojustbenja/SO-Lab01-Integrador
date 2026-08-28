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
    import time
    time.sleep(5)
    contenido = ruta.read_text (encoding="utf-8")
    palabras = contenido.lower().split()
    frecuencia = Counter(palabras)
    palabra_frecuente = frecuencia.most_common(1)[0][0] if palabras else "Sin palabras"
    reporte = REPORTES / f"reporte_{ruta.stem}.txt"
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

def productor():
    for ruta in ENTRADA.glob("*.txt"):
        cola.put(ruta)
        registrar(f"Archivo agregado a la cola: {ruta.name}")
def trabajador (numero):
    while True:
        ruta = cola.get()
        if ruta is None:
            cola.task_done()
            break
        try:
            procesar_archivo(ruta)
            print(f"Trabajador {numero}: procesó {ruta.name}")
        except Exception as error:
            registrar(f"ERROR en {ruta.name}: {error}")
        finally:
            cola.task_done()

def main():
    for carpetas in [ENTRADA, PROCESADOS, REPORTES, LOG.parent]:
        carpetas.mkdir(parents=True, exist_ok=True)
    cantidad_trabajadores = 3
    trabajadores = [Thread(target=trabajador, args=(i + 1 ,)) for i in range(cantidad_trabajadores)]
    for hilo in trabajadores:
        hilo.start()
    hilo_productor = Thread(target=productor)
    hilo_productor.start()
    hilo_productor.join()
    for _ in trabajadores:
        cola.put(None)
    cola.join()
    for hilo in trabajadores:
        hilo.join()
    consolidado = REPORTES / "reporte_consolidado.txt"
    consolidado.write_text(
        f"Archivos procesados: {totales['archivos']}\n"
        f"Palabras procesadas: {totales['palabras']}\n"
        f"Caracteres procesados: {totales['caracteres']}\n",
        encoding="utf-8",
    )
    registrar("Ejecución finalizada correctamente")
    print("Proceso terminado. Revise data/reportes y logs/sistema.log")
if __name__ == "__main__":
    main()
