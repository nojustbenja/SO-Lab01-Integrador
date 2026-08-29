"""Versión secuencial del Procesador Concurrente de Archivos (Grupo07).

Procesa todos los archivos ``*.txt`` de ``data/entrada`` uno tras otro, sin
hilos. Comparte el núcleo con la versión concurrente (módulo ``procesador``)
para que ambas se mantengan sincronizadas.
"""

import argparse
import threading
import time

from procesador import (
    Bitacora,
    escribir_consolidado,
    nuevos_totales,
    preparar_directorios,
    procesar_archivo,
    resolver_rutas,
)


def parsear_args():
    parser = argparse.ArgumentParser(description="Procesador de archivos (secuencial)")
    parser.add_argument("--base", default=None, help="Raíz alternativa del proyecto")
    return parser.parse_args()


def main():
    args = parsear_args()
    rutas = resolver_rutas(args.base)
    preparar_directorios(rutas)

    bitacora = Bitacora(rutas)
    totales = nuevos_totales()
    bloqueo = threading.Lock()  # simetría de API; aquí no hay contención

    bitacora.evento("Inicio versión secuencial")
    t0 = time.perf_counter()

    for ruta in sorted(rutas.entrada.glob("*.txt")):
        try:
            procesar_archivo(ruta, totales, bloqueo, bitacora, rutas)
            print(f"Procesado: {ruta.name}")
        except Exception as e:  # noqa: BLE001 - se registra y se continúa
            bitacora.error(ruta.name, e)

    escribir_consolidado(totales, rutas)
    bitacora.evento("Ejecución finalizada correctamente")

    dt = time.perf_counter() - t0
    print(
        "RESUMEN: modo=secuencial "
        f"archivos={totales['archivos']} "
        f"palabras={totales['palabras']} "
        f"caracteres={totales['caracteres']} "
        f"tiempo={dt:.4f}s"
    )


if __name__ == "__main__":
    main()
