# Planificador interactivo de procesos

[![DOI](https://zenodo.org/badge/1310969507.svg)](https://doi.org/10.5281/zenodo.21533095)

Aplicación educativa de escritorio para estudiar algoritmos clásicos de planificación
de CPU. Permite introducir procesos, ejecutar distintas políticas y comparar sus
tiempos de finalización, espera y retorno mediante una tabla de ciclos interactiva.

Desarrollada por Aníbal Pedraza para la asignatura Informática de primer curso de los Grados en Ingeniería Industrial.

## Funcionalidades

- First-Come, First-Served (FCFS).
- Shortest Job First (SJF).
- Shortest Remaining Time First (SRTF).
- Round Robin con *quantum* configurable.
- Número de núcleos configurable y asignación por CPU en la tabla de ciclos.
- Validación de identificadores, llegadas y duraciones.
- Métricas individuales y valores medios.
- Línea temporal con ejecución (`X`), espera (`O`) y llegadas sombreadas.
- Caso de ejemplo precargado en la aplicación.
- Menús Archivo, Edición y Ayuda; ventana de autoría/licencias.
- Guardar y abrir simulaciones en JSON, con aviso de cambios sin guardar.
- Exportación CSV por tabla, PDF de una página y Excel con una única pestaña.
- Cortar/copiar procesos, copiar resultados y pegar procesos desde Excel o texto tabulado.

## Ejecución rápida

Requiere Python 3.10 o posterior con Tkinter:

```powershell
python -m pip install -r requirements.txt
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

Tkinter y el CSV usan la biblioteca estándar. La exportación PDF requiere ReportLab y la de Excel, openpyxl; ambas se incluyen en `requirements.txt` y en la instalación del paquete.

## Menús y exportaciones

- **Archivo → Nuevo** (`Ctrl+N`) vacía procesos, resultados y diagramas, restaura FCFS, quantum 2 y un núcleo, y empieza un documento sin nombre. El botón Vaciar conserva la configuración y el archivo activo.
- **Abrir** (`Ctrl+O`) recupera una simulación JSON; si estaba calculada, reconstruye los resultados y diagramas. Un archivo inválido o una versión incompatible no sustituye la simulación actual.
- **Guardar** (`Ctrl+S`) actualiza el archivo activo y solicita un nombre la primera vez. **Guardar como** (`Ctrl+Mayús+S`) guarda en otro destino y lo convierte en el archivo activo.
- El título muestra el nombre del archivo y un asterisco si hay cambios. Nuevo, Abrir y Salir (incluido el cierre de la ventana) permiten guardar, descartar o cancelar. Si se cancela el guardado o falla la escritura, se conserva el trabajo.
- **Archivo → Exportar → CSV** permite elegir procesos, resultados o ambas tablas. Si selecciona ambas, se generan archivos con sufijos `_procesos.csv` y `_resultados.csv`. La celda A1 contiene política, quantum cuando corresponde y núcleos; las cabeceras están en la fila 3. Se usa UTF-8 con BOM y punto y coma para facilitar la apertura en Excel en español. Los identificadores que empiezan por signos de fórmula llevan un apóstrofo protector en CSV.
- **Archivo → Exportar → PDF** incluye procesos, resultados, medias, tabla de ciclos y diagrama de núcleos en una página A4 horizontal. Se avisa antes de exportar si la escala reduce demasiado la legibilidad.
- **Archivo → Exportar → Excel** incluye el mismo contenido en una pestaña, con números editables, colores y encabezado en A1. Los identificadores se conservan como texto.
- PDF y Excel necesitan una planificación calculada. Cambiar procesos, política, quantum o núcleos invalida los resultados para evitar exportar datos desactualizados.
- **Edición** actúa sobre el campo o la tabla que tiene el foco. `Ctrl+X/C/V` mantiene el comportamiento habitual de los campos. En Procesos se pueden cortar/copiar filas y pegar tres columnas (Proceso, Llegada, Duración), opcionalmente con cabecera. Se valida todo el bloque antes de insertarlo; no se aceptan identificadores duplicados. En Resultados se pueden copiar filas.
- **Ayuda** abre el repositorio y muestra versión, autoría y licencias. Los textos se centralizan en `metadata.py` para poder ajustarlos.

## Formato de simulación

Los documentos usan JSON UTF-8 con extensión `.json`, identificador
`cpu-scheduler-simulation` y versión de formato `1`. Conservan la lista ordenada de
procesos, política, quantum, núcleos, estado de cálculo y campos del formulario,
incluso si aún están incompletos. Se pueden guardar simulaciones vacías o pendientes
de calcular. Los resultados se recalculan al abrir si el documento indica que
estaban calculados, evitando guardar métricas redundantes.

Guardar conserva un documento para retomarlo; Exportar genera CSV, PDF o Excel
para consultar o compartir. Estas exportaciones no cambian el archivo activo ni
marcan la simulación como guardada. El formato JSON usa únicamente la biblioteca
estándar de Python. El guardado prepara un archivo temporal y sólo reemplaza el
destino cuando ha terminado correctamente.

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
src/planificador_procesos/  motor y aplicación
tests/                      pruebas automatizadas
docs/                       instalación y guía didáctica
```

## Licencia

El código se distribuye bajo licencia MIT. La guía y los contenidos educativos se publican bajo CC BY 4.0.
