# SO-Lab01-Integrador

Laboratorio Integrador — Unidad 01 · Grupo 07 · Sistemas Operativos

## Integrantes y roles

| Nombre | Rol |
|---|---|
| BENJAMIN ZAMORA CUEVAS | Desarrollo |
| JOSE PALMA MIRANDA | Desarrollo |
| THOMAS MARQUEZ ITURRIAGA | Análisis de resultados y evidencia |

## Requisitos para ejecutar el proyecto

| Requisito | Detalle |
|---|---|
| Python | Python 3.14.4+ |
| Dependencias externas | Ninguna — solo biblioteca estándar (`pathlib`, `threading`, `queue`, `collections`, `datetime`, `shutil`, `time`) |
| Sistema operativo | Linux |


## Instrucciones paso a paso de ejecución

> Todos los comandos se ejecutan desde la terminal. Los pasos 3 y 4 se repiten cada vez que se quiera correr una versión distinta.

**Paso 1 — Obtener el repositorio**

```bash
git clone https://github.com/nojustbenja/SO-Lab01-Integrador
cd laboratorio_so
```

**Paso 2 — Crear y activar el entorno virtual**

Desde la raíz del proyecto (`laboratorio_so/`):

```bash
# Crear el entorno virtual
python3 -m venv venv

# Activar (macOS / Linux)
source venv/bin/activate
```

El prompt cambiará a algo como `(venv) $` para confirmar que está activo.

**Paso 3 — Generar los archivos de entrada**

Este script crea 100 archivos `.txt` en `data/entrada/`. Debe ejecutarse desde la raíz del proyecto (`laboratorio_so/`).

```bash
python3 scripts/generar_archivos_entrada.py
```

**Paso 4 — Moverse a `src/`**

Las versiones del procesador importan el módulo `procesador` directamente (sin paquete), por lo que deben ejecutarse desde la carpeta `src/` para que Python lo encuentre.

```bash
cd src
```

**Paso 5 — Ejecutar la versión deseada** (ver sección siguiente)

**Paso 6 — Limpiar para volver a ejecutar** *(opcional)*

Los archivos procesados se mueven a `data/procesados/`. Para restaurar el estado inicial sin regenerar los de entrada, ejecute desde la raíz:

```bash
# Desde laboratorio_so/
python3 scripts/limpiar.py            # limpia solo data/procesados
python3 scripts/limpiar.py --todo     # limpia entrada + procesados
```

Luego repita el paso 3 si eligió `--todo`.

## Comandos utilizados para ejecutar cada versión

> Ejecutar desde `laboratorio_so/src/`.

### Versión secuencial

Procesa los archivos uno tras otro, sin hilos.

```bash
python3 version_secuencial.py
```

### Versión concurrente

Un hilo productor + N hilos trabajadores (mínimo 3). Por defecto usa 3 trabajadores.

```bash
# Con 3 trabajadores (valor por defecto)
python3 version_concurrente.py

# Con una cantidad distinta de trabajadores
python3 version_concurrente.py --trabajadores 5
```

## Cómo reproducir el experimento de condición de carrera
### Versión experimental sin lock *(condición de carrera)*

Versión deliberadamente insegura para demostrar *lost updates* en sección crítica sin `Lock`. Solo para el experimento del Criterio 5.

```bash
# Con 3 trabajadores (valor por defecto)
python3 version_sincronizacion_experimental.py

# Con más trabajadores para ampliar la ventana de intercalado
python3 version_sincronizacion_experimental.py --trabajadores 8
```

> **Nota:** Al comparar los `RESUMEN` de la versión concurrente y la experimental sobre el mismo conjunto de entrada, la experimental suele mostrar conteos menores de archivos/palabras/caracteres debido a actualizaciones perdidas.

## Estructura de carpetas

```text
laboratorio_so/
├── README.md
├── requirements.txt
├── src/
│   ├── ejemplos/
│   ├── ejemplo_guiado.py
│   ├── procesador.py
│   ├── version_secuencial.py
│   ├── version_concurrente.py
│   └── version_sincronizacion_experimental.py
├── scripts/
│   ├── generar_archivos_entrada.py
│   ├── limpiar.py
│   └── registrar_evidencias.py
├── logs/
│   └── sistema.log
├── evidencia/
│   ├── capturas/
│   ├── resultados/
│   ├── comandos_ejecutados.txt
│   └── mediciones.md
└── data/
    ├── entrada/
    ├── errores/
    ├── procesados/
    └── reportes/
```

## Mecanismo de concurrencia aplicado

Se usó el patrón **Productor–Consumidor** con tres primitivas de la biblioteca estándar de Python:

| Elemento | Rol en el proyecto |
|---|---|
| `queue.Queue` | Cola compartida y thread-safe donde el productor deposita las rutas de los archivos |
| `threading.Thread` | Un hilo productor + N hilos trabajadores (mínimo 3) que consumen la cola en paralelo |
| `threading.Lock` (`bloqueo_totales`) | Protege la sección crítica: la actualización del diccionario `totales` compartido |

**Flujo de ejecución:**

1. El hilo productor recorre `data/entrada/` y deposita cada ruta en la `Queue`.
2. Los N hilos trabajadores compiten por sacar rutas de la cola y procesarlas en paralelo.
3. Al terminar cada archivo, el trabajador entra a la sección crítica con `with bloqueo_totales:` para acumular en el contador compartido — ningún otro hilo puede modificar `totales` hasta que ese bloque termine.
4. El productor señala el fin insertando N centinelas `None` en la cola (uno por trabajador); cada hilo al recibirlo termina su bucle.

La clase `Bitacora` también usa su propio `Lock` interno para que dos hilos no mezclen líneas al escribir el log de forma simultánea.
