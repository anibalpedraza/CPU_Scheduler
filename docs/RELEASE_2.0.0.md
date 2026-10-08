# CPU Scheduler 2.0.0

Simulador educativo de planificación de CPU con FCFS, SJF, SRTF y Round Robin, quantum configurable y varios núcleos.

## Novedades

- Menús Archivo, Edición y Ayuda, con autoría y licencias consultables.
- Guardar y abrir simulaciones JSON, con protección de cambios sin guardar.
- Exportaciones CSV, PDF y Excel.
- Cortar, copiar y pegar procesos, y copiar resultados.
- Correcciones de contraste y ventanas emergentes en macOS/Windows.
- Aplicaciones autónomas de Windows x64 y macOS Apple Silicon/Intel.

## Descargar y abrir

- **CPU_Scheduler-2.0.0-windows-x64.exe**: descargar y abrir directamente en Windows.
- **CPU_Scheduler-2.0.0-macos-arm64.zip**: Mac Apple Silicon, M1 y posteriores.
- **CPU_Scheduler-2.0.0-macos-x86_64.zip**: Mac Intel.

En Mac, descomprima el ZIP y abra CPU_Scheduler.app; puede arrastrarla a Aplicaciones. Los ZIP contienen sólo la aplicación, incluidos sus recursos internos. No necesita instalar Python ni Excel para generar XLSX.

Las guías se encuentran en el [repositorio](https://github.com/anibalpedraza/CPU_Scheduler/tree/v2.0.0/docs). Los avisos de licencia están integrados y se consultan en Ayuda → Acerca de → Licencias de la aplicación.

Windows no tiene firma Authenticode. macOS usa firma ad hoc, sin Developer ID ni notarización; el sistema puede pedir confirmación o bloquear el primer arranque. Para aplicaciones de origen comprobado, consulte [Apple](https://support.apple.com/es-es/102445).

Los paquetes se verifican automáticamente antes de publicar: interfaz, licencias, algoritmos, JSON, CSV, PDF y Excel. Windows se comprueba también en carpeta como prueba interna; esa variante no se publica. Mac comprueba firma, arquitectura, permisos, enlaces y arranque mediante Launch Services antes y después de extraer el ZIP.

SHA256SUMS.txt verifica la integridad de las tres aplicaciones y BUILD_INFO.json. El manifest identifica el mismo commit y huella de código en las tres plataformas.

Las pruebas de GitHub usan Python 3.10/3.12; los binarios se construyen con Python 3.12. Mac se comprueba en macOS 15; sistemas anteriores necesitan validación específica.

El JSON mantiene el formato 1, compatible con las simulaciones guardadas anteriormente.

Código MIT. Guías y contenidos docentes CC BY 4.0.
