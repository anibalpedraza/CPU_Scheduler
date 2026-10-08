# Empaquetado Windows/macOS y publicación

La versión de la aplicación es **2.0.0**. El formato de documentos JSON sigue siendo 1.

## Validar antes de commits o GitHub

Windows se puede construir y comprobar en este equipo. Para macOS se requiere ejecutar el empaquetado en un Mac; no se genera una .app válida compilando desde Windows.

La copia de fuentes actual se prepara con:

```powershell
.\.venv-build\Scripts\python.exe tools/prepare_validation.py
```

El resultado es dist/validation/CPU_Scheduler-2.0.0-fuentes-validacion.zip. Incluye cambios sin commit y un lanzador para el Mac, sin .git ni entornos. Consulte [VALIDAR_MACOS.md](VALIDAR_MACOS.md). **No es un ZIP con binarios macOS precompilados.**

Este paso no crea commits, no hace push ni publica releases.

## Construcción local en Windows x64

Desde la raíz del proyecto, con Python 3.10 o posterior y Tcl/Tk:

```powershell
python -m venv .venv-build
.\.venv-build\Scripts\python.exe -m pip install -r requirements-build.txt -e .
.\.venv-build\Scripts\python.exe -m unittest discover -s tests -v
.\.venv-build\Scripts\python.exe tools/build_windows.py
```

Los ZIP y manifests quedan en dist/packages/windows-x64. Las aplicaciones sin comprimir quedan en dist/onedir y dist/onefile.

## Construcción local en macOS

En la copia del proyecto, con Python 3.12 de python.org, Tcl/Tk y herramientas de Xcode:

```bash
bash VALIDAR_MACOS.command
```

También puede ejecutar los pasos manualmente:

```bash
python3.12 -m venv .venv-build-macos
.venv-build-macos/bin/python -m pip install -r requirements-build.txt -e .
.venv-build-macos/bin/python -m pip check
.venv-build-macos/bin/python -m unittest discover -s tests -v
.venv-build-macos/bin/python tools/build_macos.py
```

El script detecta la arquitectura del intérprete: arm64 o x86_64. Los paquetes quedan en dist/packages/macos-ARQUITECTURA. La .app queda en dist/macos-ARQUITECTURA/CPU_Scheduler.app.

macOS usa `.venv-build-macos` para conservar separado el entorno `.venv-build` de Windows si la carpeta está sincronizada. Los entornos virtuales no se pueden trasladar entre sistemas; créelos en cada equipo. El lanzador prefiere Python 3.12 de python.org cuando está instalado, aunque Homebrew proporcione otro Python en el PATH.

Los scripts se detienen si el directorio de paquetes contiene archivos. Conserve o mueva la construcción anterior antes de repetir.

Las dependencias se fijan en requirements-build.txt, con condiciones para instalar las bibliotecas de Windows sólo en ese sistema. Las versiones usadas quedan registradas; no se prometen binarios idénticos byte a byte entre ejecuciones.

## Prueba en GitHub Actions sin release

Después de revisar y subir los cambios cuando se autorice, el workflow **Escritorio - Windows, macOS y release** permite **Run workflow**. Push a main y pull requests también lo ejecutan. Estos eventos no publican.

El flujo espera a las pruebas Python 3.10 y 3.12, construye Windows y ambos Mac, y reúne únicamente paquetes del mismo commit y versión.

Las máquinas configuradas son windows-latest, macos-15 (Apple Silicon) y macos-15-intel (Intel), con Python 3.12. No se promete compatibilidad con sistemas macOS anteriores no probados.

Artifacts:

- **packages-windows-x64**: un EXE autónomo y sus manifests. La carpeta Windows se valida internamente.
- **packages-macos-arm64** y **packages-macos-x86_64**: un ZIP con sólo la .app y manifests por arquitectura.
- **verification-PLATAFORMA**: informes de ejecución y dependencias.
- **desktop-release**: los tres aplicaciones y BUILD_INFO.json/SHA256SUMS.txt consolidados, sólo si todo ha pasado.

## Comprobaciones obligatorias

Cada plataforma debe abrir Tkinter y ejecutar toda la suite. Cada paquete se ejecuta fuera del repositorio y sin PYTHONPATH ni variables externas de Tcl/Tk.

El modo interno --self-test comprueba interfaz y menús, los cuatro algoritmos con uno y dos núcleos, JSON, CSV, PDF y Excel. Se repite tras extraer el ZIP final.

También comprueba contraste de las celdas con texto blanco por defecto y apertura, eventos, cierre por botón/ventana/teclado y reapertura de Acerca de y CSV. Estas comprobaciones se ejecutan en los binarios Windows (onefile y portable) y macOS. Consulte [VALIDACION_INTERFAZ.md](VALIDACION_INTERFAZ.md) para fuentes, paquetes y revisión manual en los dos sistemas.

macOS además comprueba arquitectura, versión de Info.plist, firma ad hoc y permisos; usa ditto para conservar enlaces simbólicos. Comprueba arranque directo y mediante Launch Services antes y después de archivar.

Una prueba fallida bloquea la reunión de paquetes y la publicación. Estas comprobaciones no sustituyen la revisión visual, los atajos ni el primer arranque descargado en equipos del alumnado.

## Publicación futura

No cree primero la release en la web. Sólo después de validar y autorizar los commits/push, se podrá subir la etiqueta definitiva:

```powershell
git tag -a v2.0.0 -m "CPU Scheduler 2.0.0"
git push origin v2.0.0
```

GitHub Actions valida la etiqueta, prueba y construye las tres plataformas, comprueba las tres aplicaciones y sus manifests, crea una release en borrador, adjunta los archivos, los descarga y verifica sus hashes. Sólo después publica y comprueba los adjuntos.

Si falla antes de publicar, la release queda ausente o en borrador. No se sobrescriben releases publicadas. Los paquetes locales con cambios sin commit no se pueden publicar mediante el script.

El job de publicación utiliza GITHUB_TOKEN con contents: write. No requiere un token personal, pero las políticas del repositorio/organización deben permitir el workflow y ese permiso.

## Reunir construcciones ya terminadas

```bash
python tools/assemble_release.py --source dist/packages --output dist/release
```

Requiere una construcción de cada plataforma, de la misma versión y commit. Para pruebas locales desde fuentes sin .git, todos los paquetes deben proceder de esa copia; no mezcle una copia sin commit con otra que tenga un commit distinto. El output debe estar vacío.

## Versiones y licencias

Actualice pyproject.toml y metadata.py, añada docs/RELEASE_X.Y.Z.md y publique vX.Y.Z cuando esté listo. __version__ toma el valor de metadata.py. No cambie FORMAT_VERSION salvo que cambie el formato de simulaciones.

Las aplicaciones incluyen licencia MIT y avisos de terceros, consultables desde Acerca de. Las guías CC BY 4.0 permanecen en el repositorio. Los workflows se versionan; dist/, build/ y .venv-build/ quedan fuera de Git.

Windows no tiene firma Authenticode. macOS usa firma ad hoc, sin Developer ID ni notarización. SHA-256 comprueba integridad, pero no acredita la identidad del editor. Para la autorización local de macOS, consulte [Apple](https://support.apple.com/es-es/102445).

## Identificar la misma revisión antes de dar el visto bueno

Los manifests nuevos incluyen **source_sha256**: SHA-256 de run.py y los módulos Python de src/planificador_procesos, con rutas relativas y finales de línea normalizados. La huella es independiente de Windows/macOS y de CRLF/LF.

Ambos empaquetadores calculan la huella antes de construir y la comprueban al terminar. Si cambia una fuente durante el proceso, no crean un manifest satisfactorio. La reunión exige el mismo commit, versión y huella en las tres plataformas; la publicación exige además que la huella coincida con el código del checkout definitivo.

Un mismo número 2.0.0 y un commit base con cambios locales no bastan para acreditar que dos paquetes contienen el mismo código. Los paquetes de validación anteriores, sin huella, se conservan como evidencia histórica y se reconstruirán para la release. No se les añade retrospectivamente una huella que no se registró al compilar.

Las correcciones macOS de contraste, ventanas y temporizadores están en módulos compartidos y necesitan reconstrucción de Windows. La limpieza de FinderInfo/ResourceFork y la firma son específicas del empaquetado Mac. Las mejoras de trazabilidad no cambian el código de la interfaz ya validado en el Mac.

## Temporales e informes de Windows

El empaquetador Windows crea un directorio temporal único para cada variante y una caché propia de PyInstaller fuera de OneDrive. Así evita limpiar cachés compartidas o carpetas antiguas sincronizadas con atributos de sólo lectura. Las versiones macOS conservan su limpieza limitada de metadatos de Finder.

Los informes nuevos de los ejecutables Windows y los avisos del empaquetador están en build/verification/windows-x64. La construcción no cambia el código de interfaz del Mac ya validado.

## Formato definitivo de la release 2.0.0

Se publican exactamente cinco adjuntos: CPU_Scheduler-2.0.0-windows-x64.exe, CPU_Scheduler-2.0.0-macos-arm64.zip, CPU_Scheduler-2.0.0-macos-x86_64.zip, BUILD_INFO.json y SHA256SUMS.txt.

Los ZIP Mac contienen sólo CPU_Scheduler.app; las licencias van dentro de sus recursos firmados. Windows integra las licencias dentro del EXE y las muestra desde Acerca de. No se publica un ZIP Windows ni su variante en carpeta, aunque esta última se sigue usando para las comprobaciones internas.

La primera subida a main ejecuta validación y construcción sin publicar. Se sube v2.0.0 sólo cuando ese workflow termina correctamente; el workflow de la etiqueta reconstruye y publica automáticamente tras verificar las tres plataformas y los cinco adjuntos.
