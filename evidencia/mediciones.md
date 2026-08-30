# Mediciones de ejecución

Fecha: 2026-08-30 (UTC). Las corridas se realizaron con `python3` y en directorios temporales pasados con `--base`, para conservar intactos los artefactos del repositorio. La carga pequeña contiene 10 archivos (26 MiB) y la grande 100 archivos (253 MiB). Cada archivo contiene el mismo texto.

El estado global inicial observado con `free -h` fue: memoria total 3.3 GiB, en uso 2.3 GiB, disponible 985 MiB y swap usada 8.0 KiB.

## Especificaciones del entorno de ejecución

| Componente | Especificación detectada |
|---|---|
| Nombre del sistema | `ubuntu-so-equipo07` |
| Sistema operativo | Ubuntu 26.04.1 LTS |
| Kernel | Linux 7.0.0-30-generic |
| Arquitectura | aarch64 (ARM de 64 bits) |
| CPU disponibles | 4 CPU lógicas, 1 hilo por núcleo, 4 núcleos por clúster |
| Memoria RAM | 3.3 GiB totales |
| Swap | 3.0 GiB totales |
| Almacenamiento disponible en la raíz del proyecto | Volumen de 16 GiB; 7.3 GiB disponibles al momento de la consulta |
| Python | Python 3.14.4 |

Estas especificaciones se obtuvieron mediante `uname -a`, `/etc/os-release`,
`lscpu`, `free -h`, `df -h .` y `python3 --version`. La sesión no expone de
forma verificable la configuración de VirtualBox (por ejemplo, RAM asignada o
número de vCPU configuradas en la interfaz). Además, el enunciado solicita
Ubuntu Desktop 24.04 LTS, mientras que el entorno medido reporta Ubuntu
26.04.1 LTS; esta diferencia debe declararse en el informe técnico.

## Comparación de versiones seguras

| Carga | Versión | Archivos procesados | Palabras | Caracteres | Tiempo real (s) | CPU usuario (s) | CPU sistema (s) | RSS máximo de `time` (KiB) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 10 archivos | Secuencial | 10 | 3,500,000 | 26,500,000 | 0.64 | 0.36 | 0.28 | 63,960 |
| 10 archivos | Concurrente, 3 trabajadores | 10 | 3,500,000 | 26,500,000 | 1.16 | 0.42 | 0.76 | 158,796 |
| 100 archivos | Secuencial | 100 | 35,000,000 | 265,000,000 | 5.35 | 3.65 | 1.63 | 63,876 |
| 100 archivos | Concurrente, 3 trabajadores | 100 | 35,000,000 | 265,000,000 | 5.04 | 3.65 | 1.49 | 160,468 |

Las cuatro ejecuciones terminaron con código 0. En cada una se verificó que `data/entrada` quedó con 0 archivos, `data/procesados` y los reportes individuales quedaron con el número esperado, y el reporte consolidado tuvo los mismos totales indicados en la tabla.

## Muestras del proceso Python

El comando `ps` se ejecutó de forma periódica mientras Python estaba activo. El PID y PPID cambian en cada corrida; los siguientes son valores máximos observados en las muestras. `STAT=R` indica ejecución y `STAT=Sl` corresponde a un proceso multihilo en espera interrumpible.

| Carga | Versión | PID observado | PPID observado | STAT observado | %CPU máximo | %MEM máximo | RSS máximo muestreado (KiB) | VSZ máximo muestreado (KiB) |
|---|---|---:|---:|---|---:|---:|---:|---:|
| 10 | Secuencial | 43667 | 43664 | R | 98.4 | 1.6 | 58,696 | 67,820 |
| 10 | Concurrente | 43755 | 43754 | R, Sl | 106.0 | 4.4 | 155,044 | 428,120 |
| 100 | Secuencial | 43879 | 43876 | R | 99.2 | 1.8 | 63,436 | 72,364 |
| 100 | Concurrente | 44367 | 44364 | R | 101.0 | 4.6 | 159,820 | 429,504 |

`RSS` es la memoria física residente que el proceso está usando. `VSZ` es el espacio de memoria virtual reservado por el proceso. La versión concurrente mostró un RSS y VSZ mayores: los trabajadores procesan archivos en paralelo y mantienen más contenido/estructuras de trabajo en memoria. Con 100 archivos, la concurrencia redujo el tiempo real de 5.35 s a 5.04 s (aprox. 5.8 %), pero con 10 archivos fue más lenta por el costo de crear y coordinar hilos, cola y bloqueos. El uso de CPU se mantuvo cercano a un núcleo, coherente con trabajo predominantemente realizado por Python y coordinación de E/S.

## Experimento de condición de carrera

La versión experimental se ejecutó tres veces con 100 archivos y 3 trabajadores. Para hacer reproducible la pérdida de actualizaciones, esa versión separa la lectura y escritura de los contadores compartidos con una pausa breve y no usa `threading.Lock`.

| Intento | Archivos esperados | Archivos consolidados | Palabras esperadas | Palabras consolidadas | Caracteres esperados | Caracteres consolidados | Tiempo real (s) | RSS máximo (KiB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 100 | 66 | 3,500,000 | 2,660,000 | 26,500,000 | 19,610,000 | 0.53 | 34,960 |
| 2 | 100 | 64 | 3,500,000 | 2,520,000 | 26,500,000 | 20,140,000 | 0.53 | 25,476 |
| 3 | 100 | 65 | 3,500,000 | 2,555,000 | 26,500,000 | 19,345,000 | 0.55 | 28,016 |

Todos los archivos fueron movidos y tuvieron reporte individual, pero los totales consolidados fueron menores e inconsistentes: varios hilos leyeron el mismo valor de un contador y sobrescribieron incrementos de otros hilos. La versión concurrente segura, ejecutada con la misma carga, consolidó los 100 archivos y los totales completos gracias a `with bloqueo_totales:`.

## Sistema de archivos

En la corrida concurrente de 100 archivos se verificó que el reporte consolidado y el log tienen permisos `-rw-rw-r--`. Sus tamaños fueron 88 B y 13 KiB respectivamente. Las carpetas `entrada`, `procesados`, `reportes` y `errores` fueron creadas y usadas; no quedaron archivos `.txt` en `entrada` y se registraron 202 líneas en el log de la corrida de 100 archivos.

## Repetición manual registrada en el historial Bash

Se repitieron las tres versiones desde una sesión Bash interactiva y se forzó
la persistencia de cada comando con `history -a`. La copia actualizada está en
`evidencia/historial_bash.txt`; allí aparecen los comandos de `time` de las
líneas 257, 261 y 265, además de la preparación de sus bases temporales.

| Versión | Archivos consolidados | Tiempo real (s) | RSS máximo (KiB) | PID observado | PPID observado | STAT | %CPU | RSS de la muestra (KiB) | VSZ de la muestra (KiB) |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| Secuencial | 100 | 3.88 | 64,260 | 2999 | 2996 | R | 100.0 | 12,588 | 21,156 |
| Concurrente, 3 trabajadores | 100 | 4.17 | 160,236 | 3017 | 3014 | R | 100.0 | 11,832 | 20,552 |
| Experimental sin `Lock`, 3 trabajadores | 70 de 100 | 0.49 | 30,164 | 3038 | 3036 | R | 0.0 | 11,844 | 21,112 |

La repetición mantuvo los resultados funcionales correctos de las versiones
seguras y volvió a mostrar un consolidado inconsistente en la experimental:
70 archivos contabilizados de 100 procesados. El valor de `%CPU` corresponde
a la muestra instantánea tomada con `ps`, mientras que el RSS máximo proviene
de `/usr/bin/time` durante toda la ejecución.
