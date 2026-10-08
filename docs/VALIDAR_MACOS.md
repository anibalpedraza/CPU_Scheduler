# Validar macOS antes de hacer commits o publicar

La validación local del Mac Apple Silicon del 7 de octubre de 2026 está registrada en [RESULTADO_VALIDACION_MACOS_2026-10-07.md](RESULTADO_VALIDACION_MACOS_2026-10-07.md), con resultados, incidencias corregidas y pendientes de publicación.

La comprobación posterior de contraste y ventanas emergentes, con el paquete reconstruido el 8 de octubre, está en [RESULTADO_VALIDACION_MACOS_2026-10-08.md](RESULTADO_VALIDACION_MACOS_2026-10-08.md).

Puede usar el ZIP **CPU_Scheduler-2.0.0-fuentes-validacion.zip** para trasladar el estado actual del proyecto al Mac. Incluye los cambios pendientes; no incluye .git, entornos Python ni binarios de Windows. **Este ZIP contiene fuentes, no una aplicación macOS ya compilada.**

## Preparar el Mac

1. Descomprima el ZIP en Finder.
2. Instale Python 3.12 desde [python.org](https://www.python.org/downloads/macos/), con su Tcl/Tk. El Python del sistema o uno sin Tkinter no sirve para construir la aplicación.
3. Las herramientas de línea de comandos de Xcode deben estar disponibles. Si faltan, ejecute `xcode-select --install` y complete el instalador.

## Construir sin GitHub

Abra **VALIDAR_MACOS.command** en la carpeta descomprimida. También puede ejecutarlo desde Terminal:

```bash
bash VALIDAR_MACOS.command
```

El lanzador crea .venv-build-macos, instala y comprueba las dependencias, comprueba Tkinter, ejecuta todas las pruebas y construye la aplicación. Necesita Internet para instalar dependencias la primera vez. No hace commits, no envía cambios a GitHub y no publica una release.

Puede usar directamente la copia del repositorio en el Mac, sin preparar el ZIP de fuentes. Si comparte la carpeta por OneDrive, `.venv-build-macos` mantiene separado el entorno `.venv-build` de Windows. No reutilice un entorno virtual creado en otro sistema. El lanzador prefiere el Python 3.12 de `/Library/Frameworks/Python.framework` instalado desde python.org.

Para trabajar con las fuentes una vez preparado el entorno:

```bash
.venv-build-macos/bin/python run.py
```

La arquitectura se toma del intérprete Python. En un Mac Apple Silicon con Python nativo genera **arm64**; en un Mac Intel, **x86_64**. Si Terminal/Python se ejecuta mediante Rosetta, el resultado puede ser Intel. Para validar las dos variantes de forma nativa se necesitan ambos tipos de Mac, o después los dos runners de GitHub Actions.

El resultado queda en:

- dist/packages/macos-arm64/CPU_Scheduler-2.0.0-macos-arm64.zip, o
- dist/packages/macos-x86_64/CPU_Scheduler-2.0.0-macos-x86_64.zip.

La .app sin comprimir queda en dist/macos-ARQUITECTURA/CPU_Scheduler.app. Los informes se guardan en build/verification/macos-ARQUITECTURA.

Para repetir la construcción, conserve o mueva primero dist/packages/macos-ARQUITECTURA; el script no mezcla paquetes antiguos.

## Qué se comprueba automáticamente

- Coincidencia de versión y arquitectura.
- Versión en Info.plist, permisos y firma ad hoc del bundle.
- Arranque directo y mediante Launch Services (la misma vía que utiliza Finder).
- Interfaz y menús, cuatro algoritmos con uno y dos núcleos, JSON, CSV, PDF y Excel.
- ZIP creado y extraído con ditto, conservando enlaces simbólicos y permisos.
- Arranque directo y mediante Launch Services desde el ZIP extraído.
- Hashes SHA-256, dependencias y sistema macOS usado para construir.

## Revisión manual

Para las regresiones de contraste y ventanas detectadas después de la primera validación, siga también [VALIDACION_INTERFAZ.md](VALIDACION_INTERFAZ.md); incluye las comprobaciones equivalentes de los ejecutables Windows.

Descomprima el ZIP resultante usando Finder y abra CPU_Scheduler.app. Compruebe:

1. Menús, ventana, tablas, diagramas y legibilidad.
2. Atajos ⌘N/O/S, ⌘⇧S y ⌘X/C/V.
3. Guardado/apertura y exportaciones en una carpeta con espacios y tildes.
4. Salida con ⌘Q y botón de cierre, incluido el aviso de cambios sin guardar.
5. Arrastrar la .app a Aplicaciones y volver a abrirla.

Los paquetes sólo tienen firma ad hoc; no están firmados con Developer ID ni notarizados. macOS puede bloquearlos. Para autorizar una aplicación de origen comprobado siga [las instrucciones de Apple](https://support.apple.com/es-es/102445); no hace falta desactivar globalmente Gatekeeper.

Las pruebas locales sin descarga/quarantena no verifican por sí solas el comportamiento de Gatekeeper al descargar desde Internet. No se promete compatibilidad con versiones de macOS distintas de las efectivamente probadas. GitHub Actions está configurado para probar ambas arquitecturas en macOS 15.

## Si falla

Conserve la salida de Terminal y los JSON de build/verification/macos-ARQUITECTURA. Si una comprobación falla, no se genera un paquete marcado como correcto ni se publica nada. Los ZIP parciales que queden tras un fallo no deben distribuirse.

En carpetas sincronizadas, como OneDrive, Finder puede añadir `com.apple.FinderInfo` a los frameworks de la aplicación recién construida. macOS rechaza esos metadatos al comprobar la firma ([explicación de Apple](https://developer.apple.com/library/archive/qa/qa1940/_index.html)). El script retira exclusivamente `com.apple.FinderInfo` y `com.apple.ResourceFork` del bundle generado y de su copia para el ZIP, sin seguir enlaces hacia destinos externos ni eliminar la cuarentena. La firma se vuelve a comprobar antes de ejecutar o archivar la aplicación.
