# Planificador interactivo de procesos

[![DOI](https://zenodo.org/badge/1310969507.svg)](https://doi.org/10.5281/zenodo.21533095)

Aplicación educativa de escritorio para estudiar algoritmos clásicos de planificación
de CPU. Permite introducir procesos, ejecutar distintas políticas y comparar sus
tiempos de finalización, espera y retorno mediante una tabla de ciclos interactiva.

Desarrollada por Aníbal Pedraza para la asignatura Informática de 1er curso de los Grados en Ingeniería Industrial.

## Funcionalidades

- First-Come, First-Served (FCFS).
- Shortest Job First (SJF).
- Shortest Remaining Time First (SRTF).
- Round Robin con *quantum* configurable.
- Validación de identificadores, llegadas y duraciones.
- Métricas individuales y valores medios.
- Línea temporal con ejecución (`X`), espera (`O`) y llegadas sombreadas.
- Caso de ejemplo precargado.
- Motor independiente de la interfaz y probado automáticamente.

La versión estable representa una CPU. El trabajo multinúcleo permanece aislado en
la rama `experimental/multicore-scheduling` porque todavía no está validado.

## Ejecución rápida

Requiere Python 3.10 o posterior con Tkinter:

```powershell
python run.py
```

La guía completa se encuentra en [docs/INSTALACION.md](docs/INSTALACION.md).
También puede instalarse en modo editable:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
planificador-procesos
```

No requiere bibliotecas externas durante la ejecución.

## Verificación

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
```

Las pruebas comprueban validación, métricas, apropiación en SRTF y rotación de
Round Robin.

## Uso docente

La [guía didáctica](docs/GUIA_DIDACTICA.md) incluye resultados de aprendizaje,
una actividad comparativa y las limitaciones del modelo. La
[referencia de algoritmos](docs/ALGORITMOS.md) resume las decisiones de cada
política y las métricas calculadas.

## Cita

Pedraza Dorado, Aníbal. (2024). *Planificador interactivo de procesos*.
Zenodo. [![DOI](https://zenodo.org/badge/1310969507.svg)](https://doi.org/10.5281/zenodo.21533095)

## Estructura

```text
src/planificador_procesos/  motor y aplicación estable
tests/                      pruebas automatizadas
docs/                       instalación y guía didáctica
```

## Licencia

El código se distribuye bajo licencia MIT. La guía y los contenidos educativos se publican bajo CC BY 4.0.
