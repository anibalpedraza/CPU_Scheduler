# Validación de regresiones de interfaz — 8 de octubre de 2026

CPU Scheduler 2.0.0: corregidos el contraste de ciclos/CPU y el patrón de bloqueo de las ventanas emergentes. Fuentes y paquete macOS arm64 reconstruido comprobados en macOS 27.0.1, Python 3.12.10 y Tk 8.6.16. La evidencia del [7 de octubre](RESULTADO_VALIDACION_MACOS_2026-10-07.md) se conserva como validación anterior.

## Diagnóstico y correcciones

**Contraste.** Las celdas fijaban fondos claros para llegadas y CPU ocupada, pero heredaban el primer plano de Tk. Con texto blanco, el sombreado de llegadas tenía contraste 1,41:1. Todas las celdas usan ahora una pareja explícita de fondo claro y texto `#202020`, incluidos estados normales y CPU ociosa. Las cabeceras y controles siguen usando el tema del sistema. El distintivo CC tenía el problema complementario, trazos negros sobre el fondo oscuro de Canvas, y también fija una pareja legible.

**Ventanas emergentes.** Acerca de y CSV ejecutaban `grab_set` antes del mapeo y `wait_window` desde el callback del menú. La prueba instrumentada detectó esa espera; el patrón es compatible con las limitaciones documentadas de Tk Aqua y sus bucles anidados ([incidencia de CPython](https://github.com/python/cpython/issues/100617), [bucle de eventos de Tkinter](https://docs.python.org/3/library/tkinter.html#threading-model)). La corrección evita la espera anidada:

- Acerca de es una ventana informativa que devuelve el control inmediatamente y permite seguir usando la principal.
- CSV conserva su modalidad, pero captura la entrada sólo después de mapearse y devuelve el control al bucle principal. Al destruirse, Tk libera la captura y se cancela cualquier tarea pendiente de enfoque.
- Reabrir una ventana que ya existe la reutiliza, en lugar de crear duplicados.
- Menús, atajos de Archivo y cierre nativo macOS programan sus acciones mediante un temporizador normal. Los selectores Abrir/Guardar/Guardar como/PDF/Excel se abren después de salir del callback del menú nativo.

## Pruebas y evidencia

- **77 pruebas correctas**, sin omisiones en este Mac. Las regresiones nuevas fallaban en el código anterior y ahora pasan.
- Pruebas de colores por defecto blancos/oscuros: contraste mínimo de 4,5:1 para todas las celdas con uno y cuatro núcleos, incluidas llegadas y CPU ociosa; distintivo CC legible.
- Pruebas de apertura y reapertura, ventana única, eventos activos, captura sólo con CSV visible y liberación al cerrar; cierre por botón, cierre del sistema, Escape y Enter; destrucción anterior al mapeo sin tareas pendientes.
- Selectores de archivos comprobados con cancelación simulada para Abrir, Guardar, Guardar como, PDF y Excel; se verifica que el callback devuelve el control antes de abrirlos.
- `run.py --self-test` correcto en las fuentes (`frozen: false`).
- **Cuatro comprobaciones del ejecutable correctas** (`frozen: true`): app directa, Launch Services, ZIP extraído directo y ZIP extraído mediante Launch Services.
- El self-test de los binarios comprueba contraste con texto blanco por defecto, cuatro aperturas/cierres de Acerca de y CSV por botón/ventana/teclado, eventos activos y nuevo cálculo. También mantiene las pruebas de algoritmos, JSON, CSV, PDF y Excel.
- Revisión nativa: Acerca de se abrió, cerró y volvió a abrir mediante el menú de macOS tanto en las fuentes como en el standalone reconstruido, sin bloqueo. Se comprobó visualmente el texto oscuro de los ciclos y el distintivo CC en el tema oscuro.
- Firma ad hoc, arquitectura, permisos, enlaces simbólicos y hashes finales verificados. El aviso de Launch Services `sandbox_extension_issue_file_to_process` también apareció en esta ejecución; el proceso terminó y su informe fue satisfactorio.

Informes y registros: `build/verification/macos-arm64`. La aplicación standalone corregida se deja abierta. La sesión gráfica de prueba de las fuentes se cerró normalmente.

## Artefactos

- Aplicación: `dist/macos-arm64/CPU_Scheduler.app`.
- ZIP: `dist/packages/macos-arm64/CPU_Scheduler-2.0.0-macos-arm64.zip`.
- Tamaño: 20498023 bytes.
- SHA-256: `8997e9bb75b5c91f54ff1148464257cec40161a14d5fc8f1cb5848b77ac6b30a`.
- Manifests: `BUILD_INFO_macos-arm64.json` y `SHA256SUMS_macos-arm64.txt`.

La construcción anterior y sus informes se conservaron en `dist/validation-history/2026-10-07-antes-regresiones`. Sustituya cualquier copia anterior en Aplicaciones o procedente de otro ZIP; esas copias no reciben las correcciones del código automáticamente.

## Confirmación manual del usuario — 8 de octubre de 2026

El usuario confirma: «por lo que he probado parece que la app para macOS funciona correctamente». Se registra como validación funcional satisfactoria de la aplicación corregida en este Mac, dentro de los escenarios que ha probado. Esta confirmación complementa las pruebas automatizadas y la revisión del menú nativo descritas anteriormente.

## Windows y publicación

Las correcciones son compartidas. Las nuevas pruebas y el self-test se ejecutarán también en las dos variantes Windows, incluyendo sus ZIP finales. El [procedimiento de validación de interfaz](VALIDACION_INTERFAZ.md) contiene los comandos para las fuentes y ejecutables y la revisión en modos claro y oscuro. En Windows se omite únicamente la prueba de atributos extendidos propia de macOS; las pruebas de interfaz son comunes.

**Pendiente:** reconstruir y ejecutar Windows portable y onefile en un equipo Windows, completar la revisión manual de selectores nativos y cambios de tema, validar Intel/macOS 15 y el primer arranque descargado con Gatekeeper/SmartScreen. No se ha ejecutado Windows ni GitHub Actions desde este Mac.

No se han realizado commits, push, etiquetas ni releases. El paquete está marcado `working_tree_dirty: true` y se destina a validación local, anterior a publicación.
