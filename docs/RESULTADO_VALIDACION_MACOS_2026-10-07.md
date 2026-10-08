# Resultado de validación macOS — 7 de octubre de 2026

CPU Scheduler **2.0.0**: entorno de desarrollo preparado y paquete **macos-arm64** construido y comprobado en este Mac. Validación local anterior a commits o publicación; no se ha enviado ningún cambio a GitHub.

## Entorno

- macOS 27.0.1, Apple Silicon arm64.
- Python 3.12.10 universal2 de python.org, ejecutado de forma nativa; Tcl 8.6.16 y Tkinter disponibles. Instalador con firma de Python Software Foundation y notarización verificadas por macOS.
- Herramientas de línea de comandos de Xcode disponibles en `/Library/Developer/CommandLineTools`.
- Entorno `.venv-build-macos`, separado del entorno Windows `.venv-build` conservado en la carpeta sincronizada.
- Dependencias de `requirements-build.txt` instaladas; `pip check` correcto. Versiones completas en `build/verification/macos-arm64/pip-freeze.txt`.

## Resultado automático

- **67 pruebas correctas**, sin omisiones, sobre las fuentes finales.
- Cuatro informes con `success: true`, `frozen: true`, versión 2.0.0 y arquitectura arm64: `app-direct.json`, `app-finder.json`, `zip-direct.json` y `zip-finder.json`.
- Cada ejecución comprueba interfaz y menús, FCFS/SJF/SRTF/Round Robin con uno y dos núcleos, guardado y recuperación JSON, CSV, PDF y Excel.
- Arquitectura, versiones de Info.plist, permisos de ejecución y firma ad hoc comprobados. ZIP extraído con ditto y enlaces simbólicos conservados.
- Arranque desde un directorio temporal ajeno al repositorio, sin PYTHONPATH ni variables externas de Tcl/Tk.
- SHA-256 del ZIP y de BUILD_INFO comprobados de nuevo al cerrar esta validación.

Los informes y registros están en `build/verification/macos-arm64`. El arranque mediante Launch Services del ZIP extraído emitió un aviso `sandbox_extension_issue_file_to_process`; aun así, terminó correctamente y generó su informe satisfactorio. Las URLs ficticias impresas al final de la suite proceden de las pruebas simuladas de publicación; no se publicó nada.

## Incidencias corregidas

1. El entorno copiado de Windows no es utilizable en macOS. El lanzador ahora crea `.venv-build-macos`, prefiere Python 3.12 de python.org y comprueba las dependencias.
2. La primera construcción falló al verificar la firma por FinderInfo añadido al framework de Python dentro de OneDrive. El script elimina sólo `com.apple.FinderInfo` y `com.apple.ResourceFork` del bundle generado y de su copia para el ZIP. La prueba nativa comprueba que conserva la cuarentena, el contenido y los enlaces, y no modifica sus destinos externos.
3. El subtítulo gris fijo era difícil de leer en modo oscuro. Ahora hereda el color del tema. Se regeneró el paquete y se verificó visualmente el contraste corregido.

La construcción anterior al ajuste visual se conservó en `dist/validation-history/macos-arm64-antes-ajuste-visual`; use el paquete final de `dist/packages`.

## Artefactos finales

- Aplicación: `dist/macos-arm64/CPU_Scheduler.app`.
- ZIP: `dist/packages/macos-arm64/CPU_Scheduler-2.0.0-macos-arm64.zip`.
- Tamaño: 20485672 bytes.
- SHA-256: `544072fd093462d36aa7621ab3cc30893a52bcd05250aeda59f4a590dd37c1b3`.
- Manifests: `BUILD_INFO_macos-arm64.json` y `SHA256SUMS_macos-arm64.txt`, junto al ZIP.

La aplicación final se abrió en modo normal y se revisaron la ventana, los menús y el contraste del subtítulo en modo oscuro. Se deja abierta para continuar la revisión. La revisión interactiva completa de simulaciones y atajos sigue pendiente; las pruebas automáticas sí ejercitaron las simulaciones y exportaciones.

## Continuar la validación

Para trabajar con el código:

```bash
.venv-build-macos/bin/python run.py
```

Para repetir pruebas:

```bash
.venv-build-macos/bin/python -m unittest discover -s tests -v
```

Para volver a empaquetar, conserve o mueva primero `dist/packages/macos-arm64` y ejecute `bash VALIDAR_MACOS.command`. El empaquetador exige un directorio de paquetes vacío.

Antes de publicar:

- Completar la [revisión manual](VALIDAR_MACOS.md#revisión-manual): ejemplo calculado, menús, diagramas, atajos Command, guardado y exportación en rutas con espacios/tildes, aviso de cambios sin guardar y arranque tras copiar a Aplicaciones.
- Validar primer arranque de una descarga real con cuarentena/Gatekeeper. La aplicación usa firma ad hoc, sin Developer ID ni notarización.
- Validar macOS Intel y la compatibilidad en macOS 15: este Mac sólo acredita arm64 en macOS 27.0.1.
- Revisar los cambios, incorporar los commits y ejecutar el workflow de GitHub sin etiqueta para reconstruir Windows y los dos Mac desde el mismo commit final. La corrección visual común también debe comprobarse en Windows.
- Sólo tras esas comprobaciones y la autorización de publicación, seguir [EMPAQUETADO.md](EMPAQUETADO.md) para la etiqueta v2.0.0 y la release.

El manifest identifica el commit base `6ec0e5e2f23219ccbca8a560298522341a7d51d6` y `working_tree_dirty: true`. Este paquete es de validación local y no debe utilizarse como paquete definitivo de publicación.
