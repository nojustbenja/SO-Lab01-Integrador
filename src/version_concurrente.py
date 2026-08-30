"""Versión concurrente del Procesador Concurrente de Archivos (Grupo07).

Un hilo productor deja las rutas de ``data/entrada`` en una ``queue.Queue`` y
N hilos trabajadores las consumen. El acceso a los totales compartidos se
protege con un ``threading.Lock`` dentro del núcleo (módulo ``procesador``).
Comparte ese núcleo con la versión secuencial para mantenerlas sincronizadas.
"""

import argparse
import queue
import sys
import threading
import time

MIN_TRABAJADORES = 3  # el laboratorio exige "al menos tres hilos trabajadores"

from procesador import (
    Bitacora,
    escribir_consolidado,
    nuevos_totales,
    preparar_directorios,
    procesar_archivo,
    resolver_rutas,
)


def parsear_args():
    parser = argparse.ArgumentParser(description="Procesador de archivos (concurrente)")
    parser.add_argument("--base", default=None, help="Raíz alternativa del proyecto")
    parser.add_argument(
        "--trabajadores", type=int, default=3, help="Cantidad de hilos trabajadores"
    )
    return parser.parse_args()


def main():
    args = parsear_args()
    rutas = resolver_rutas(args.base)
    preparar_directorios(rutas)

    bitacora = Bitacora(rutas)
    totales = nuevos_totales()
    bloqueo_totales = threading.Lock()

    N = args.trabajadores
    if N < MIN_TRABAJADORES:
        print(
            f"Advertencia: --trabajadores={N} es menor que el mínimo "
            f"requerido ({MIN_TRABAJADORES}); se usan {MIN_TRABAJADORES}.",
            file=sys.stderr,
        )
        N = MIN_TRABAJADORES
    cola = queue.Queue()

    def productor():
        for ruta in sorted(rutas.entrada.glob("*.txt")):
            cola.put(ruta)
            bitacora.evento(f"Archivo agregado a la cola: {ruta.name}")

    def trabajador(numero):
        while True:
            ruta = cola.get()
            if ruta is None:
                cola.task_done()
                break
            try:
                procesar_archivo(ruta, totales, bloqueo_totales, bitacora, rutas)
                print(f"Trabajador {numero}: {ruta.name}")
            except Exception as e:  # noqa: BLE001 - se registra y se continúa
                try:
                    bitacora.error(ruta.name, e)
                except Exception:  # noqa: BLE001 - un fallo al registrar no
                    pass          # debe matar al trabajador antes de drenar la cola
            finally:
                cola.task_done()

    bitacora.evento("Inicio versión concurrente")
    t0 = time.perf_counter()

    trabajadores = [
        threading.Thread(target=trabajador, args=(i + 1,)) for i in range(N)
    ]
    for hilo in trabajadores:
        hilo.start()

    hilo_productor = threading.Thread(target=productor)
    hilo_productor.start()
    hilo_productor.join()

    for _ in range(N):
        cola.put(None)
    cola.join()
    for hilo in trabajadores:
        hilo.join()

    escribir_consolidado(totales, rutas)
    bitacora.evento("Ejecución finalizada correctamente")

    dt = time.perf_counter() - t0
    print(
        "RESUMEN: modo=concurrente "
        f"trabajadores={N} "
        f"archivos={totales['archivos']} "
        f"palabras={totales['palabras']} "
        f"caracteres={totales['caracteres']} "
        f"tiempo={dt:.4f}s"
    )


if __name__ == "__main__":
    main()
