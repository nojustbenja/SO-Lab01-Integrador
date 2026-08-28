# SO-Lab01-Integrador
Laboratorio Integrador — Unidad 01 · Grupo 07 · Sistemas Operativos

---

## 1. Integrantes y roles

| Nombre completo | Rol |
|---|---|
| [Nombre Apellido] | Desarrollo versión concurrente segura |
| [Nombre Apellido] | Desarrollo versión sin lock / experimental |
| [Nombre Apellido] | Análisis de resultados y evidencia |

> Reemplaza los corchetes con los nombres reales del equipo antes de entregar.

---

## 2. Requisitos

- **Python** 3.10 o superior (probado con Python 3.14.4)
- Sin dependencias externas — solo biblioteca estándar de Python:
  `pathlib`, `threading`, `queue`, `collections`, `shutil`, `datetime`

---

## 3. Instrucciones paso a paso

### Paso 1 — Clonar o posicionarse en el proyecto
```bash
cd ~/laboratorio_so
```

### Paso 2 — Generar los archivos de entrada
Los scripts leen desde `data/entrada/`. Ejecuta el generador incluido para crear los 100 archivos de prueba:
```bash
python3 scripts/generar_archivos_entrada.py
```
Esto crea `data/entrada/archivo_1.txt` … `archivo_100.txt`, cada uno con una línea de texto de ejemplo.

### Paso 3 — Ejecutar la versión deseada
Ver sección 4 para los comandos exactos de cada versión.

### Paso 4 — Revisar resultados
- Reportes individuales: `data/reportes/reporte_<nombre>.txt`
- Reporte consolidado: `data/reportes/reporte_consolidado.txt`
- Log de ejecución: `logs/sistema.log`

> **Nota:** cada ejecución mueve los archivos de `data/entrada/` a `data/procesados/`.
> Vuelve a ejecutar el generador (Paso 2) antes de cada nueva prueba.

---

## 4. Comandos de ejecución por versión

| Versión | Archivo | Comando |
|---|---|---|
| Concurrente segura (con lock) | `src/ejemplo_guiado.py` | `python3 src/ejemplo_guiado.py` |
| Concurrente sin lock | `src/ejemplo_sin_lock.py` | `python3 src/ejemplo_sin_lock.py` |
| Experimental — carrera amplificada (guiado) | `src/ejemplo_guiado_experimental.py` | `python3 src/ejemplo_guiado_experimental.py` |
| Experimental — carrera amplificada (sin lock) | `src/ejemplo_sin_lock_experimental.py` | `python3 src/ejemplo_sin_lock_experimental.py` |

---

## 5. Estructura de carpetas

```
laboratorio_so/
├── README.md                          # Este archivo
├── requirements.txt                   # Dependencias (vacío: solo stdlib)
├── src/
│   ├── ejemplo_guiado.py              # Versión concurrente con locks completos
│   ├── ejemplo_sin_lock.py            # Versión concurrente sin lock en totales
│   ├── ejemplo_guiado_experimental.py # Experimental: carrera amplificada (guiado)
│   └── ejemplo_sin_lock_experimental.py # Experimental: sin lock + sleep
├── scripts/
│   └── generar_archivos_entrada.py    # Genera los 100 archivos de prueba
├── data/
│   ├── entrada/                       # Archivos .txt listos para procesar
│   ├── procesados/                    # Archivos movidos tras procesarse
│   ├── reportes/                      # Reporte por archivo + consolidado
│   └── errores/                       # Archivos que fallaron al procesarse
├── logs/
│   └── sistema.log                    # Registro de eventos de cada ejecución
└── evidencia/
    ├── capturas/                       # Capturas de pantalla de las ejecuciones
    ├── comandos_ejecutados.txt         # Historial de comandos usados
    └── mediciones.csv                  # Tabla de resultados comparativos
```

---

## 6. Mecanismo de concurrencia aplicado

El sistema implementa el patrón **Productor-Consumidor** usando `threading` y `queue.Queue`:

- **1 hilo productor** recorre `data/entrada/` y encola cada archivo (`cola.put(ruta)`).
- **3 hilos trabajadores** consumen la cola en paralelo (`cola.get()`) y procesan cada archivo de forma independiente.
- La cola actúa como buffer sincronizado entre productor y consumidores.

### Mecanismos de sincronización (`threading.Lock`)

| Lock | Variable protegida | Propósito |
|---|---|---|
| `bloqueo_log` | `logs/sistema.log` | Evita que dos hilos escriban el log al mismo tiempo (presente en todas las versiones) |
| `bloqueo_totales` | `totales` (dict compartido) | Protege la acumulación de archivos, palabras y caracteres (solo en `ejemplo_guiado.py`) |

### Flujo de ejecución
```
Productor ──→ Queue ──→ Trabajador 1 ─┐
                     ──→ Trabajador 2 ─┤─→ data/reportes/ + data/procesados/
                     ──→ Trabajador 3 ─┘
```

---

## 7. Cómo reproducir la condición de carrera

La **condición de carrera** ocurre cuando varios hilos leen y modifican `totales["archivos"]` sin sincronización, causando que algunas actualizaciones se pierdan (el contador final es menor a 100).

### Reproducción básica — `ejemplo_sin_lock.py`
```bash
# 1. Regenerar archivos de entrada
python3 scripts/generar_archivos_entrada.py

# 2. Ejecutar la versión sin lock
python3 src/ejemplo_sin_lock.py
```
La operación `totales["archivos"] += 1` no es atómica: tres hilos pueden leer el mismo valor antes de que alguno escriba, descartando actualizaciones. El contador final puede ser menor a 100, pero el efecto puede no verse siempre.

### Reproducción amplificada — `ejemplo_sin_lock_experimental.py` (más visible)
```bash
# 1. Regenerar archivos de entrada
python3 scripts/generar_archivos_entrada.py

# 2. Ejecutar la versión experimental
python3 src/ejemplo_sin_lock_experimental.py
```
Esta versión **separa deliberadamente** la lectura y la escritura con un `time.sleep(0.001)`:
```python
valor_actual = totales["archivos"]  # lee
time.sleep(0.001)                   # pausa — otro hilo lee el mismo valor
totales["archivos"] = valor_actual + 1  # escribe — la actualización del otro hilo se pierde
```
La pausa garantiza que la pérdida de actualizaciones sea **observable en prácticamente cada ejecución**. La salida mostrará algo como:
```
Archivos contados: 47 / 100
(si es menor a 100, la condición de carrera fue visible)
```

### Comparativa esperada

| Versión | Resultado `totales["archivos"]` |
|---|---|
| `ejemplo_guiado.py` (con lock) | 100 siempre |
| `ejemplo_sin_lock.py` (sin lock) | ≤ 100, inconsistente |
| `ejemplo_sin_lock_experimental.py` (sin lock + sleep) | Notablemente < 100 |
