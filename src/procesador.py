"""Núcleo compartido del Procesador Concurrente de Archivos (Grupo07).

Este módulo concentra la lógica común usada por las tres versiones del
laboratorio (secuencial, concurrente y experimental sin bloqueo). Mantener
aquí el comportamiento asegura que la versión secuencial y la concurrente
"se mantengan sincronizadas": ambas llaman exactamente a las mismas
funciones y solo cambian en cómo orquestan el trabajo.

Solo se usa biblioteca estándar.
"""

from collections import Counter
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import shutil
import threading
import traceback


# Raíz del proyecto: carpeta que contiene "src" (padre de este archivo, y su
# padre). Se calcula una sola vez al importar el módulo.
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent


def resolver_rutas(base=None):
    """Devuelve un espacio de nombres con todas las rutas del proyecto.

    ``base`` por defecto es la raíz del proyecto; las pruebas y el flag
    ``--base`` de la línea de comandos pueden pasar una ruta alternativa.
    """
    if base is None:
        base = RAIZ_PROYECTO
    base = Path(base)
    return SimpleNamespace(
        base=base,
        entrada=base / "data" / "entrada",
        procesados=base / "data" / "procesados",
        errores=base / "data" / "errores",
        reportes=base / "data" / "reportes",
        log=base / "logs" / "sistema.log",
    )


def preparar_directorios(rutas):
    """Crea las carpetas de trabajo y la carpeta del log si no existen."""
    for carpeta in (
        rutas.entrada,
        rutas.procesados,
        rutas.errores,
        rutas.reportes,
        rutas.log.parent,
    ):
        carpeta.mkdir(parents=True, exist_ok=True)


class Bitacora:
    """Registrador de eventos y errores seguro para hilos."""

    def __init__(self, rutas):
        self.rutas = rutas
        self.bloqueo = threading.Lock()

    def _marca_tiempo(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def evento(self, mensaje):
        """Agrega una línea de evento al log, protegida por el bloqueo."""
        marca_tiempo = self._marca_tiempo()
        with self.bloqueo:
            with self.rutas.log.open("a", encoding="utf-8") as archivo_log:
                archivo_log.write(f"{marca_tiempo} - {mensaje}\n")

    def error(self, nombre_archivo, excepcion):
        """Registra un error en el log y el detalle completo en data/errores."""
        marca_tiempo = self._marca_tiempo()
        detalle = "".join(
            traceback.format_exception(
                type(excepcion), excepcion, excepcion.__traceback__
            )
        )
        with self.bloqueo:
            with self.rutas.log.open("a", encoding="utf-8") as archivo_log:
                archivo_log.write(
                    f"{marca_tiempo} - ERROR en {nombre_archivo}: {excepcion}\n"
                )
            # El detalle también se escribe bajo el mismo bloqueo para que
            # dos errores del mismo archivo no se intercalen.
            archivo_detalle = self.rutas.errores / f"{nombre_archivo}.error.txt"
            with archivo_detalle.open("a", encoding="utf-8") as salida:
                salida.write(f"{marca_tiempo} - {nombre_archivo}\n")
                salida.write(f"{repr(excepcion)}\n")
                salida.write(detalle)
                salida.write("\n")


def analizar(texto):
    """Devuelve las métricas básicas de un texto."""
    palabras = texto.lower().split()
    frecuencia = Counter(palabras)
    if palabras:
        palabra_frecuente = frecuencia.most_common(1)[0][0]
    else:
        palabra_frecuente = "Sin palabras"
    return {
        "lineas": len(texto.splitlines()),
        "palabras": len(texto.split()),
        "caracteres": len(texto),
        "palabra_frecuente": palabra_frecuente,
    }


def procesar_archivo(ruta, totales, bloqueo_totales, bitacora, rutas):
    """Procesa un archivo de entrada de principio a fin.

    Puede lanzar excepciones (por ejemplo si el destino ya existe en
    procesados); quien la llama debe envolver la invocación.
    """
    contenido = ruta.read_text(encoding="utf-8")
    m = analizar(contenido)

    # La comprobación de duplicado va PRIMERO: si el destino ya existe no se
    # escribe el reporte individual ni se tocan los totales, así el
    # consolidado nunca cuenta un archivo que quedó en data/entrada.
    destino = rutas.procesados / ruta.name
    if destino.exists():
        raise FileExistsError(f"ya existe en procesados: {ruta.name}")

    reporte = rutas.reportes / f"reporte_{ruta.stem}.txt"
    reporte.write_text(
        f"Archivo: {ruta.name}\n"
        f"Líneas: {m['lineas']}\n"
        f"Palabras: {m['palabras']}\n"
        f"Caracteres: {m['caracteres']}\n"
        f"Palabra más frecuente: {m['palabra_frecuente']}\n",
        encoding="utf-8",
    )

    with bloqueo_totales:
        totales["archivos"] += 1
        totales["palabras"] += m["palabras"]
        totales["caracteres"] += m["caracteres"]

    shutil.move(str(ruta), str(destino))

    bitacora.evento(f"Procesado correctamente: {ruta.name}")


def escribir_consolidado(totales, rutas):
    """Escribe el reporte consolidado con los totales acumulados."""
    consolidado = rutas.reportes / "reporte_consolidado.txt"
    consolidado.write_text(
        f"Archivos procesados: {totales['archivos']}\n"
        f"Palabras procesadas: {totales['palabras']}\n"
        f"Caracteres procesados: {totales['caracteres']}\n",
        encoding="utf-8",
    )


def nuevos_totales():
    """Estructura de totales en cero."""
    return {"archivos": 0, "palabras": 0, "caracteres": 0}
