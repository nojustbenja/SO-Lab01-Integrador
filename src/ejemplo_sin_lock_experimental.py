from pathlib import Path
from collections import Counter
from queue import Queue
import queue
from threading import Thread, Lock
from datetime import date, datetime
import shutil
import time


BASE = Path.home() / "laboratorio_so"
ENTRADA = BASE / "data" / "entrada"
PROCESADOS = BASE / "data" / "procesados"
REPORTES = BASE / "data" / "reportes"
LOG = BASE / "logs" / "sistema.log"
cola = Queue()
bloqueo_log = Lock()
totales = {"archivos": 0, "palabras": 0, "caracteres": 0}

def registrar(mensaje):
    marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with bloqueo_log:
        with LOG.open("a", encoding="utf-8") as archivo_log:
            archivo_log.write(f"{marca_tiempo} - {mensaje}\n")

def procesar_archivo(ruta):
    contenido = ruta.read_text(encoding="utf-8")
    palabras = contenido.lower().split()
    frecuencia = Counter(palabras)
    palabra_frecuente = frecuencia.most_common(1)[0][0] if palabras else "Sin palabras"
    reporte = REPORTES / f"reporte_{ruta.stem}.txt"
    reporte.write_text(
        f"Archivo: {ruta.name}\n"
        f"Líneas: {len(contenido.splitlines())}\n"
        f"Palabras: {len(palabras)}\n"
        f"Caracteres: {len(contenido)}\n"
        f"Palabra más frecuente: {palabra_frecuente}\n",
        encoding="utf-8",
    )

    # --- VERSIÓN SIN LOCK (insegura) — DESACTIVADA para la demo ---
    # totales["archivos"] += 1
    # totales["palabras"] += len(palabras)
    # totales["caracteres"] += len(contenido)

    # --- VERSIÓN EXPERIMENTAL (condición de carrera amplificada) — ACTIVA ---
    # Sin lock y con pausa entre lectura y escritura: la pérdida de actualizaciones
    # es casi segura de observar en cada ejecución.
    valor_actual = totales["archivos"]  # type: ignore
    time.sleep(0.001)
    totales["archivos"] = valor_actual + 1  # type: ignore
    totales["palabras"] += len(palabras)
    totales["caracteres"] += len(contenido)

    shutil.move(str(ruta), PROCESADOS / ruta.name)
    registrar(f"Procesado correctamente: {ruta.name}")

def productor():
    for ruta in ENTRADA.glob("*.txt"):
        cola.put(ruta)
        registrar(f"Archivo agregado a la cola: {ruta.name}")

def trabajador(numero):
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

    registrar("=" * 60)
    registrar("### INICIO: ejemplo_sin_lock EXPERIMENTAL (sin lock + sleep)")
    registrar("=" * 60)

    cantidad_trabajadores = 3
    trabajadores = [Thread(target=trabajador, args=(i + 1,)) for i in range(cantidad_trabajadores)]
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
    registrar(f"RESULTADO FINAL — archivos: {totales['archivos']} (esperado: 100)")
    registrar("### FIN: ejemplo_sin_lock EXPERIMENTAL")
    registrar("=" * 60)
    print(f"\nProceso terminado.")
    print(f"  Archivos contados: {totales['archivos']} / 100")
    print(f"  (si es menor a 100, la condición de carrera fue visible)")

if __name__ == "__main__":
    main()
