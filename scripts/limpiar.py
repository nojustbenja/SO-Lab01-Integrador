"""Script de limpieza del laboratorio.

Uso:
    python3 scripts/limpiar.py --todo        # limpia entrada + procesados + reportes + errores
    python3 scripts/limpiar.py --procesados  # limpia solo procesados + reportes + errores
"""

import argparse
import shutil
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"

CARPETAS = {
    "entrada":    DATA / "entrada",
    "procesados": DATA / "procesados",
    "reportes":   DATA / "reportes",
    "errores":    DATA / "errores",
}


def limpiar_carpeta(ruta: Path) -> int:
    """Elimina todos los archivos de una carpeta y devuelve cuántos borró."""
    if not ruta.exists():
        return 0
    archivos = list(ruta.iterdir())
    for archivo in archivos:
        if archivo.is_file():
            archivo.unlink()
        elif archivo.is_dir():
            shutil.rmtree(archivo)
    return len(archivos)


def parsear_args():
    parser = argparse.ArgumentParser(description="Limpieza de datos del laboratorio")
    parser.add_argument(
        "--todo",
        action="store_true",
        help="Limpia entrada Y procesados",
    )
    return parser.parse_args()


def main():
    args = parsear_args()

    if args.todo:
        objetivos = ["entrada", "procesados"]
    else:
        objetivos = ["procesados"]

    total = 0
    for nombre in objetivos:
        ruta = CARPETAS[nombre]
        n = limpiar_carpeta(ruta)
        print(f"  {nombre:12} → {n} elemento(s) eliminado(s)  ({ruta})")
        total += n

    print(f"\nListo. {total} elemento(s) eliminado(s) en total.")


if __name__ == "__main__":
    main()
