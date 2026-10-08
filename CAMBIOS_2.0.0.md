# Preparación de CPU Scheduler 2.0.0

- Versión 1.0.0 → 2.0.0 en pyproject.toml y metadata.py. __version__ usa la versión de metadata.py.
- El formato JSON permanece en versión 1.
- Se añaden scripts y dependencias de empaquetado Windows, comprobaciones del ejecutable real y ZIP, manifests de integridad y avisos de terceros.
- Se habilita el seguimiento de .github/workflows y se añade la construcción automática de Windows.
- Las releases se preparan en borrador y sólo se publican tras verificar todos los adjuntos. Una prueba manual o un push a main no publica.
- Se añaden licencia MIT, notas de versión y documentación del proceso.
- No se ha creado ni enviado la etiqueta v2.0.0 ni se ha publicado una release.

## Validación local

- 59 pruebas correctas, incluidas las de interfaz, documentos, exportaciones y protección de la publicación.
- Las dos variantes Windows x64 se han construido con Python 3.10.11 y han pasado las comprobaciones desde el ejecutable y desde el ZIP final extraído.
- Workflows validados con actionlint 1.7.12. El workflow de Windows espera a la suite de Python 3.10 y 3.12 antes de construir y publicar.
- Pendiente: incorporar los cambios a GitHub, ejecutar el workflow allí y revisar el ejecutable en un equipo del alumnado sin Python. La construcción de GitHub usará Python 3.12.

## Preparación de macOS

- Se añaden paquetes arm64 y x86_64 con PyInstaller, Info.plist 2.0.0 y firma ad hoc. La compilación nativa requiere un Mac con Python 3.12.
- El ZIP macOS usa ditto, conserva enlaces y permisos, y comprueba arranque directo y mediante Launch Services antes y después de extraerlo.
- Se adaptan los menús y atajos a Command y el cierre nativo de macOS conserva el aviso de cambios sin guardar.
- El workflow desktop-release.yml sustituye al de Windows: exige pruebas y construcciones correctas en Windows, Apple Silicon e Intel antes de reunir y publicar cuatro ZIP.
- Se prepara un ZIP de fuentes pendientes y VALIDAR_MACOS.command para validar localmente sin commits ni GitHub.
- 66 pruebas locales correctas, sintaxis Python/bash y workflows validados. Windows se ha reconstruido y comprobado. Las versiones macOS están preparadas, pero no compiladas ni ejecutadas desde este equipo Windows.
- No se han hecho commits, push, etiquetas ni releases. Pendiente: compilación y revisión visual en el Mac del usuario y, después de autorizar la subida, ejecución de GitHub Actions.

## Preparación y correcciones en el Mac — 7 de octubre de 2026

- Instalación del Python 3.12.10 universal2 oficial de python.org, con Tcl/Tk; las herramientas de Xcode ya estaban disponibles.
- El lanzador prefiere el intérprete oficial y crea `.venv-build-macos`, separado del entorno de Windows copiado por OneDrive. Se añade `pip check` y se actualizan las instrucciones y exclusiones de Git.
- Corrección del fallo real de firma en OneDrive: el empaquetado elimina sólo FinderInfo y ResourceFork del bundle generado y de la copia destinada al ZIP. Mantiene la cuarentena y no sigue enlaces hacia archivos externos; una prueba nativa comprueba esas garantías.
- El subtítulo hereda el color del tema para conservar el contraste en modo oscuro.
- Las evidencias de esta validación se registran en `docs/RESULTADO_VALIDACION_MACOS_2026-10-07.md`. La validación de Intel, Gatekeeper tras descarga y GitHub Actions sigue pendiente.

## Regresiones de interfaz — 8 de octubre de 2026

- Las celdas de ciclos, llegadas y CPU fijan juntos fondo claro y texto oscuro, evitando heredar letras blancas del modo oscuro. Se corrige también el contraste del distintivo CC.
- Acerca de pasa a ser una ventana informativa sin espera anidada ni captura de entrada. CSV mantiene modalidad, pero captura sólo después del mapeo y devuelve el control inmediatamente. Se reutilizan las ventanas ya abiertas y se cancelan las tareas de enfoque al destruirlas.
- Las acciones de los menús y atajos se programan con un temporizador normal, tras devolver el control al callback nativo. Se aplica también al cierre nativo de macOS y a los selectores de archivos y exportación.
- Se añaden pruebas de contraste, eventos activos, ventanas únicas, cierre y reapertura, Escape/Enter y selectores. El mismo self-test ampliado se incluye en macOS y Windows, tanto en los ejecutables como en los ZIP finales extraídos.
- Procedimiento manual y de comprobación Windows en `docs/VALIDACION_INTERFAZ.md`. El informe del 7 de octubre se conserva como evidencia histórica; estas correcciones requieren reconstruir Windows antes de darlo por validado.
- 77 pruebas correctas, self-test de fuentes y cuatro comprobaciones correctas de app/ZIP arm64. Acerca de se abrió, cerró y reabrió por el menú nativo en fuentes y standalone sin bloqueo. Resultados y artefactos en `docs/RESULTADO_VALIDACION_MACOS_2026-10-08.md`.
- El 8 de octubre el usuario confirma que la aplicación macOS funciona correctamente en sus pruebas. Se registra la validación funcional manual en el informe, conservando los pendientes específicos de Windows, Intel y primer arranque descargado.

## Revisión cruzada y reconstrucción Windows — 8 de octubre de 2026

- Se confirma que las correcciones de contraste, diálogos y callbacks están en el código compartido. Los paquetes Windows anteriores deben reconstruirse.
- La suite inicial y el self-test de fuentes pasan en Windows; sólo se omite la prueba de atributos extendidos nativos de macOS.
- Se añade source_sha256 a los manifests nuevos y a la copia de fuentes. Se normalizan rutas y finales de línea para comparar Windows/macOS. Se impide mezclar revisiones locales distintas y completar una construcción si cambian las fuentes.
- La publicación comprueba la huella contra el código definitivo. Los manifests antiguos sin huella no se etiquetan retrospectivamente; se conservan y se reconstruyen antes de la release.
- Los workflows usan las dependencias fijadas y pip check; los errores de instalación bloquean la construcción.
- No ha sido necesario modificar nuevamente la interfaz validada en el Mac. La prueba macOS arm64 y la confirmación manual del usuario conservan su alcance. Intel/macOS 15 y los jobs reales de GitHub siguen pendientes.
- Se conserva un historial reversible de los paquetes y ejecutables Windows anteriores antes de generar las variantes actuales.

- Se detectó WinError 5 al limpiar localpycs de una construcción anterior en OneDrive. El empaquetador Windows usa ahora temporales y caché por ejecución fuera de OneDrive; los informes propios se separan en build/verification/windows-x64. No se borraron ni se cambiaron permisos de las carpetas antiguas.

- Resultado final Windows: 81 pruebas (80 correctas y una omisión nativa de Mac), self-test de fuentes y cuatro self-tests de ejecutables/ZIP correctos. Hashes y huella comprobados. Informe: docs/RESULTADO_VALIDACION_WINDOWS_2026-10-08.md.

## Publicación autorizada — formato final

- El usuario autoriza los commits, push, GitHub Actions y la release automatizada 2.0.
- Se simplifican los adjuntos a un EXE Windows x64, dos ZIP Mac con sólo la .app, BUILD_INFO.json y SHA256SUMS.txt.
- Se conserva la variante Windows en carpeta como validación interna.
- Las guías quedan en el repositorio. Las licencias se integran como recursos de las aplicaciones y se consultan desde Acerca de.
- Se validará primero el push a main y sólo después se enviará v2.0.0, que activa la publicación automatizada.
