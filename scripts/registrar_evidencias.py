"""Ejecuta y registra evidencias reproducibles del laboratorio.

Cada corrida se realiza en una base aislada bajo ``evidencia/resultados``:
no modifica los archivos de trabajo del repositorio. Registra el entorno,
memoria global antes/después, tiempo, RSS máximo, muestras de ``ps``, salida
del programa y la verificación de los archivos generados.

Ejemplo:
    python3 scripts/registrar_evidencias.py --cargas 10,100 --lineas-por-archivo 25000
"""

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone


RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "evidencia" / "resultados"
VERSIONES = {
    "secuencial": ("src/version_secuencial.py", []),
    "concurrente": ("src/version_concurrente.py", ["--trabajadores", "3"]),
    "experimental": (
        "src/version_sincronizacion_experimental.py",
        ["--trabajadores", "3"],
    ),
}


def argumentos():
    parser = argparse.ArgumentParser(description="Registra evidencias del laboratorio")
    parser.add_argument(
        "--cargas", default="10,100", help="Cantidades de archivos, separadas por coma"
    )
    parser.add_argument(
        "--lineas-por-archivo", type=int, default=1,
        help="Líneas repetidas en cada archivo (25000 permite observar ps con claridad)",
    )
    parser.add_argument(
        "--intervalo-ps", type=float, default=0.05, help="Segundos entre muestras ps"
    )
    parser.add_argument(
        "--repeticiones-experimental", type=int, default=3,
        help="Número de corridas sin Lock para evidenciar la condición de carrera",
    )
    return parser.parse_args()


def ejecutar(comando, cwd=RAIZ):
    return subprocess.run(comando, cwd=cwd, text=True, capture_output=True, check=False)


def memoria_global():
    resultado = ejecutar(["free", "-h"])
    return resultado.stdout.strip() if resultado.returncode == 0 else "No disponible"


def crear_entrada(base, cantidad, lineas):
    entrada = base / "data" / "entrada"
    entrada.mkdir(parents=True, exist_ok=True)
    texto = ("uno dos tres cuatro cinco procesos hilos memoria\n" * lineas)
    for numero in range(1, cantidad + 1):
        (entrada / f"archivo_{numero:03d}.txt").write_text(texto, encoding="utf-8")
    return {
        "archivos_esperados": cantidad,
        "palabras_esperadas": cantidad * lineas * 8,
        "caracteres_esperados": cantidad * len(texto),
        "bytes_entrada": cantidad * len(texto.encode("utf-8")),
    }


def leer_consolidado(ruta):
    datos = {}
    if not ruta.exists():
        return datos
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        clave, separador, valor = linea.partition(":")
        if separador:
            datos[clave.strip()] = int(valor.strip())
    return datos


def contar(ruta, patron):
    return len(list(ruta.glob(patron))) if ruta.exists() else 0


def ejecutar_version(base, nombre, esperado, intervalo):
    script, extra = VERSIONES[nombre]
    tiempo = base / "tiempo.txt"
    comando = [
        "/usr/bin/time", "-f",
        "real_s=%e\nuser_s=%U\nsys_s=%S\nrss_max_kib=%M\nexit=%x",
        "-o", str(tiempo), sys.executable, script, "--base", str(base), *extra,
    ]
    antes = memoria_global()
    inicio = time.monotonic()
    proceso = subprocess.Popen(comando, cwd=RAIZ, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    muestras = []
    while proceso.poll() is None:
        muestra = ejecutar([
            "ps", "-o", "pid=,ppid=,stat=,%cpu=,%mem=,rss=,vsz=,comm=", "-p", str(proceso.pid)
        ]).stdout.strip()
        if muestra:
            muestras.append({"segundo": round(time.monotonic() - inicio, 3), "ps": muestra})
        time.sleep(intervalo)
    salida, errores = proceso.communicate()
    despues = memoria_global()
    consolidado = leer_consolidado(base / "data" / "reportes" / "reporte_consolidado.txt")
    artefactos = {
        "entrada_txt": contar(base / "data" / "entrada", "*.txt"),
        "procesados_txt": contar(base / "data" / "procesados", "*.txt"),
        "reportes_individuales": contar(base / "data" / "reportes", "reporte_archivo_*.txt"),
        "lineas_log": len((base / "logs" / "sistema.log").read_text(encoding="utf-8").splitlines())
        if (base / "logs" / "sistema.log").exists() else 0,
    }
    valido_archivos = (
        proceso.returncode == 0 and artefactos["entrada_txt"] == 0
        and artefactos["procesados_txt"] == esperado["archivos_esperados"]
        and artefactos["reportes_individuales"] == esperado["archivos_esperados"]
    )
    valido_totales = consolidado == {
        "Archivos procesados": esperado["archivos_esperados"],
        "Palabras procesadas": esperado["palabras_esperadas"],
        "Caracteres procesados": esperado["caracteres_esperados"],
    }
    return {
        "version": nombre,
        "comando": comando,
        "codigo_salida": proceso.returncode,
        "memoria_antes": antes,
        "memoria_despues": despues,
        "medicion_time": tiempo.read_text(encoding="utf-8").strip() if tiempo.exists() else "No disponible",
        "muestras_ps": muestras,
        "salida": salida,
        "stderr": errores,
        "consolidado": consolidado,
        "artefactos": artefactos,
        "validacion": {
            "archivos_y_reportes": valido_archivos,
            "totales_correctos": valido_totales,
            "resultado_esperado": (not valido_totales) if nombre == "experimental" else (valido_archivos and valido_totales),
        },
    }


def main():
    args = argumentos()
    if args.lineas_por_archivo < 1 or args.intervalo_ps <= 0 or args.repeticiones_experimental < 1:
        raise SystemExit("Los valores numéricos deben ser positivos.")
    try:
        cargas = [int(valor) for valor in args.cargas.split(",")]
    except ValueError as error:
        raise SystemExit("--cargas debe tener enteros separados por coma.") from error
    if not cargas or any(carga < 1 for carga in cargas):
        raise SystemExit("Cada carga debe ser un entero positivo.")

    marca = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destino = RESULTADOS / marca
    destino.mkdir(parents=True)
    informe = {
        "fecha_utc": marca,
        "entorno": {"python": sys.version, "sistema": platform.platform(), "cpu_logicas": os.cpu_count()},
        "configuracion": vars(args), "corridas": [],
    }
    for carga in cargas:
        for version in ("secuencial", "concurrente", "experimental"):
            repeticiones = args.repeticiones_experimental if version == "experimental" else 1
            for intento in range(1, repeticiones + 1):
                base = destino / f"{carga}_archivos" / f"{version}_{intento}"
                esperado = crear_entrada(base, carga, args.lineas_por_archivo)
                corrida = ejecutar_version(base, version, esperado, args.intervalo_ps)
                corrida.update({"carga_archivos": carga, "intento": intento, "esperado": esperado, "base": str(base)})
                informe["corridas"].append(corrida)
                estado = "OK" if corrida["validacion"]["resultado_esperado"] else "REVISAR"
                print(f"{estado}: carga={carga} versión={version} intento={intento}")
    (destino / "mediciones.json").write_text(json.dumps(informe, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Evidencias guardadas en: {destino}")


if __name__ == "__main__":
    main()
