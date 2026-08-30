"""Versión EXPERIMENTAL, deliberadamente insegura (Grupo07).

===========================================================================
ADVERTENCIA
===========================================================================
Este archivo NO forma parte de la solución "buena". Existe solo para el
experimento del Criterio 5 del laboratorio: demostrar una condición de
carrera.

A diferencia de ``version_concurrente.py``, aquí la actualización de los
totales compartidos se hace SIN ``threading.Lock``. Además la lectura y la
escritura de cada total se separan con un ``time.sleep`` minúsculo para
ampliar la ventana de intercalado entre hilos y así hacer visible la
pérdida de actualizaciones ("lost update").

Para no contaminar el camino seguro del núcleo, este archivo define su
propia copia local de la lógica de procesamiento
(``procesar_archivo_inseguro``). El resto (análisis, reportes, consolidado,
bitácora) se reutiliza del módulo ``procesador``.

Resultado esperado del experimento: al ejecutar varias veces, el
``RESUMEN`` de esta versión suele mostrar ``archivos``/``palabras``/
``caracteres`` MENORES que los de la versión secuencial o concurrente sobre
el mismo conjunto de entrada.
===========================================================================
"""

import argparse
import queue
import sys
import threading
import time

MIN_TRABAJADORES = 3  # el laboratorio exige "al menos tres hilos trabajadores"

from procesador import (
    Bitacora,
    analizar,
    escribir_consolidado,
    nuevos_totales,
    preparar_directorios,
    resolver_rutas,
)


def parsear_args():
    parser = argparse.ArgumentParser(
        description="Procesador de archivos (experimental, sin lock - inseguro)"
    )
    parser.add_argument("--base", default=None, help="Raíz alternativa del proyecto")
    parser.add_argument(
        "--trabajadores", type=int, default=3, help="Cantidad de hilos trabajadores"
    )
    return parser.parse_args()


def procesar_archivo_inseguro(ruta, totales, bitacora, rutas):
    """Igual que ``procesador.procesar_archivo`` pero con la sección crítica
    de totales SIN protección. Uso exclusivo del experimento de Criterio 5.
    """
    contenido = ruta.read_text(encoding="utf-8")
    m = analizar(contenido)

    reporte = rutas.reportes / f"reporte_{ruta.stem}.txt"
    reporte.write_text(
        f"Archivo: {ruta.name}\n"
        f"Líneas: {m['lineas']}\n"
        f"Palabras: {m['palabras']}\n"
        f"Caracteres: {m['caracteres']}\n"
        f"Palabra más frecuente: {m['palabra_frecuente']}\n",
        encoding="utf-8",
    )

    # SECCIÓN CRÍTICA SIN PROTECCIÓN (demostración de condición de carrera)
    actual = totales["archivos"]
    time.sleep(0.001)
    totales["archivos"] = actual + 1
    actual_p = totales["palabras"]; time.sleep(0.0005); totales["palabras"] = actual_p + m["palabras"]
    actual_c = totales["caracteres"]; time.sleep(0.0005); totales["caracteres"] = actual_c + m["caracteres"]

    import shutil

    destino = rutas.procesados / ruta.name
    if destino.exists():
        raise FileExistsError(f"ya existe en procesados: {ruta.name}")
    shutil.move(str(ruta), str(destino))

    bitacora.evento(f"Procesado correctamente: {ruta.name}")


def main():
    args = parsear_args()
    rutas = resolver_rutas(args.base)
    preparar_directorios(rutas)

    bitacora = Bitacora(rutas)
    totales = nuevos_totales()

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
                procesar_archivo_inseguro(ruta, totales, bitacora, rutas)
                print(f"Trabajador {numero}: {ruta.name}")
            except Exception as e:  # noqa: BLE001 - se registra y se continúa
                try:
                    bitacora.error(ruta.name, e)
                except Exception:  # noqa: BLE001 - un fallo al registrar no
                    pass          # debe matar al trabajador antes de drenar la cola
            finally:
                cola.task_done()

    bitacora.evento("Inicio versión experimental sin lock")
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
        "RESUMEN: modo=experimental-sin-lock "
        f"trabajadores={N} "
        f"archivos={totales['archivos']} "
        f"palabras={totales['palabras']} "
        f"caracteres={totales['caracteres']} "
        f"tiempo={dt:.4f}s"
    )


if __name__ == "__main__":
    main()
