# Revisión cruzada y validación Windows — 8 de octubre de 2026

CPU Scheduler **2.0.0**: las correcciones realizadas en el Mac están incorporadas a las dos variantes Windows reconstruidas. No ha sido necesario cambiar nuevamente el código de la interfaz que el usuario validó en macOS.

## Qué afectaba a Windows

- El contraste del subtítulo, ciclos, llegadas, CPU y distintivo CC se implementa en app.py/actions.py: código compartido.
- El ciclo de vida de Acerca de/CSV, la captura tras el mapeo y la ejecución diferida de menús/selectores están en dialogs.py/actions.py/simulation_actions.py: código compartido.
- Las regresiones y el self-test ampliado de gui_checks.py/packaging_check.py se ejecutan también dentro de los binarios Windows.
- La limpieza FinderInfo/ResourceFork, firma ad hoc y .venv-build-macos son específicos de macOS.

Por tanto, los Windows anteriores no servían para aprobar las últimas correcciones. Se han conservado y sustituido por las construcciones de esta revisión.

## Resultado automático en Windows

- Suite completa: **81 pruebas**, **80 correctas** y **1 omisión intencionada** (atributos extendidos nativos de macOS).
- pip check: sin incompatibilidades.
- Self-test de las fuentes satisfactorio, incluyendo contraste con texto blanco por defecto y reapertura de diálogos.
- **Cuatro self-tests satisfactorios**: portable directo, portable extraído de ZIP, onefile directo y onefile extraído de ZIP. Todos indican frozen: true, success: true y versión 2.0.0.
- Cada self-test comprueba cuatro algoritmos con uno/dos núcleos, contraste, Acerca de/CSV con eventos activos y cierre por botón/sistema/teclado, JSON, CSV, PDF y Excel.
- Tamaños y hashes de los ZIP y manifests comprobados después de construir.
- Workflows validados con actionlint; Python y lanzador bash validados sintácticamente.

Entorno local: Windows-10-10.0.19045-SP0, Python 3.10.11, PyInstaller 6.16.0. GitHub Actions usará Python 3.12.

Registros: build/verification/tests-windows-2026-10-08.log, build/verification/build-windows-2026-10-08.log y build/verification/windows-x64/*.json.

## Incidencia de construcción resuelta

El primer intento falló con WinError 5 al limpiar localpycs de una construcción anterior en OneDrive. Windows usa ahora temporales y caché propios de cada ejecución fuera de la carpeta sincronizada. No se borraron las carpetas antiguas ni se cambiaron sus permisos. La reconstrucción aislada terminó correctamente.

## Paquetes Windows actuales

- **CPU_Scheduler-2.0.0-windows-x64-portable.zip**: 21218254 bytes; SHA-256 `5b64623dd91f7f049d46d0b53bddb06d7e663a8f8ed2154d180ca1f1e72118d3`.
- **CPU_Scheduler-2.0.0-windows-x64-onefile.zip**: 20853414 bytes; SHA-256 `2ead09c3331e1e1bc8eb2980735a987803d4e562abc4f99695d7c0409c049985`.

- Ejecutable único para revisión: dist/onefile/CPU_Scheduler.exe.
- Ejecutable portable para revisión: dist/onedir/CPU_Scheduler/CPU_Scheduler.exe.
- ZIP y manifests: dist/packages/windows-x64.
- Huella del código compartido: `cf883d71389707706309d7227bcafe4596ebc5982c9a35f5076eb4a3063083c0`.
- Historial anterior: `dist/validation-history/2026-10-08-windows-antes-correcciones-5b237b31`.

No reutilice copias de los ZIP anteriores ni procesos antiguos que sigan abiertos.

## Garantizar la misma revisión

Los manifests nuevos registran source_sha256. Los empaquetadores detectan cambios de fuentes durante la construcción; la reunión exige misma versión, commit y huella; la publicación exige además que la huella coincida con el checkout definitivo.

La normalización de LF/CRLF permite comparar Windows y macOS sin falsos cambios por Git. Los tests adicionales comprueban estas garantías y rechazan mezclar paquetes con mismo número de versión/commit pero diferente contenido de código.

El paquete arm64 que el usuario validó conserva su hash `8997e9bb75b5c91f54ff1148464257cec40161a14d5fc8f1cb5848b77ac6b30a`. No se ha modificado ni se le ha atribuido retrospectivamente una huella de fuentes. Su evidencia funcional sigue en [RESULTADO_VALIDACION_MACOS_2026-10-08.md](RESULTADO_VALIDACION_MACOS_2026-10-08.md). Para la release se reconstruirá con los manifests nuevos, desde el mismo commit que Windows e Intel.

## Visto bueno y siguientes pasos

**Visto bueno técnico local para continuar la revisión final y preparar los commits:** fuentes y paquetes Windows correctos; macOS arm64 cuenta con la validación automática previa y la confirmación manual del usuario.

Antes de publicar:

1. Completar la revisión interactiva de Windows con [VALIDACION_INTERFAZ.md](VALIDACION_INTERFAZ.md), en especial selectores nativos, temas y cambios sin guardar. No se afirma una revisión visual manual completa desde este agente.
2. Cuando el usuario autorice los commits/push, ejecutar el workflow sin etiqueta. Debe pasar en Windows, macOS arm64 y macOS Intel/macOS 15 y producir los cuatro paquetes del mismo commit y huella.
3. Revisar esos artifacts antes de subir v2.0.0. El primer arranque descargado con SmartScreen/Gatekeeper se mantiene como comprobación de distribución, distinta de ejecutar un paquete construido localmente.

No se han realizado commits, push, etiquetas ni releases en esta revisión. Los paquetes actuales siguen marcados working_tree_dirty: true y son para validación local.
