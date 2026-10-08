# Comprobar contraste y ventanas en macOS y Windows

Estas comprobaciones cubren las regresiones detectadas el 8 de octubre de 2026 tanto al ejecutar las fuentes como al usar los paquetes. Deben repetirse después de reconstruir Windows; los ejecutables anteriores no incorporan las correcciones ni las comprobaciones nuevas.

## Comprobación automática de las fuentes

En macOS, desde la raíz del proyecto:

```bash
.venv-build-macos/bin/python -m unittest discover -s tests -v
.venv-build-macos/bin/python run.py --self-test build/verification/fuentes-macos.json
```

En Windows PowerShell, con las dependencias de `requirements-build.txt` y el paquete instalado en `.venv-build`:

```powershell
.\.venv-build\Scripts\python.exe -m unittest discover -s tests -v
.\.venv-build\Scripts\python.exe run.py --self-test build/verification/fuentes-windows.json
```

El informe de las fuentes debe indicar `success: true` y `frozen: false`. El informe del ejecutable debe indicar `success: true` y `frozen: true`. El modo `--self-test` muestra y cierra ventanas de prueba automáticamente; no necesita que el usuario pulse botones.

La suite simula texto blanco y fondos oscuros por defecto, y exige contraste de al menos 4,5:1 en las celdas de ciclos, llegadas y asignación/ocio de CPU. Comprueba también el distintivo CC, el retorno de los callbacks antes de abrir selectores nativos, ventanas únicas, eventos activos, reapertura y liberación de la captura de entrada.

## Comprobación de los paquetes reconstruidos

Conserve o mueva primero la carpeta de paquetes anterior: `dist/packages/macos-arm64`, `dist/packages/macos-x86_64` o `dist/packages/windows-x64`. Los scripts requieren esa carpeta vacía.

```bash
.venv-build-macos/bin/python tools/build_macos.py
```

```powershell
.\.venv-build\Scripts\python.exe tools/build_windows.py
```

Ambos empaquetadores ejecutan el mismo `--self-test` ampliado en los binarios y en los ZIP finales extraídos. macOS añade el arranque mediante Launch Services; Windows comprueba tanto onefile como portable. Para revisar un Windows ya reconstruido, por ejemplo:

```powershell
.\dist\onedir\CPU_Scheduler\CPU_Scheduler.exe --self-test "$PWD\build\verification\manual-windows-portable.json"
.\dist\onefile\CPU_Scheduler.exe --self-test "$PWD\build\verification\manual-windows-onefile.json"
```

El informe debe incluir los controles de **contraste de ciclos y CPU** y **Acerca de y CSV: apertura, eventos, cierre y reapertura sin bloqueo**, además de los algoritmos y exportaciones. Los workflows existentes ejecutan también las nuevas pruebas; no es necesario publicar una release para validarlos.

## Revisión manual en cada sistema

Realice esta secuencia en modo claro y oscuro, desde las fuentes y desde el ZIP extraído, sin reutilizar una aplicación antigua que siga abierta:

1. Cargar ejemplo y calcular con uno, dos y cuatro núcleos. Comprobar letras X/O, sombreado de llegadas, asignaciones y CPU ociosa: el texto de todas las celdas debe ser oscuro sobre los fondos claros. Las cabeceras y controles mantienen el tema del sistema. Cambiar de tema con la aplicación abierta no debe dejar letras blancas sobre esos fondos.
2. Abrir **Ayuda → Acerca de** varias veces. Debe existir una sola ventana y la principal debe seguir respondiendo. Cerrar alternativamente con **Cerrar**, Escape, Enter y el botón de cierre del sistema; volver a calcular después de cada cierre. Comprobar el distintivo CC.
3. Abrir **Archivo → Exportar → CSV**. La ventana se comporta como modal mientras es visible; **Cancelar**, Escape y el cierre del sistema deben liberar la principal. Repetir, exportar ambas tablas y comprobar que se puede volver a calcular.
4. Abrir y cancelar los selectores de **Abrir**, **Guardar**, **Guardar como**, PDF y Excel, primero por menú y luego por atajo cuando exista. Después, guardar y exportar realmente en una carpeta con espacios y tildes.
5. Comprobar Nuevo y Salir con cambios sin guardar: Guardar, Descartar y Cancelar. Usar los atajos Command en macOS y Control en Windows, incluido Command+Q en macOS.

Las pruebas automáticas de Tk no sustituyen toda la interacción del menú nativo ni el primer arranque descargado con Gatekeeper/SmartScreen. Si hay un bloqueo, conserve el informe y registre el sistema, versión de Python/Tk y si se ejecutó la fuente, portable, onefile o `.app`.
