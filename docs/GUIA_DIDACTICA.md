# Guía didáctica

## Finalidad

El simulador permite observar cómo una misma carga de procesos produce resultados
distintos según el algoritmo de planificación. Está dirigido a asignaturas
introductorias de Informática y Sistemas Operativos en titulaciones de Ingeniería.

## Resultados de aprendizaje

Tras utilizar el recurso, el alumnado debería poder:

- Diferenciar algoritmos apropiativos y no apropiativos (con/sin expulsión).
- Calcular tiempos de finalización, espera y retorno.
- Explicar el efecto del instante de llegada y la duración.
- Analizar el compromiso entre tiempo medio y tiempo de respuesta.
- Comparar FCFS, SJF, SRTF y Round Robin con una misma carga.

## Uso básico

1. Seleccione un algoritmo y el número de núcleos (1 para el modo mononúcleo).
2. Introduzca para cada proceso un identificador, su instante de llegada y su
   duración.
3. Para Round Robin, indique el *quantum*.
4. Pulse **Calcular planificación**.
5. Compare la tabla de resultados y la tabla de ciclos.

En la tabla de ciclos:

- `X` indica que el proceso usa la CPU.
- `O` indica que el proceso espera en la cola.
- El sombreado marca el instante de llegada.
- Las filas CPU muestran qué proceso ejecuta en cada núcleo (`—` indica un núcleo libre).

## Actividad propuesta

Introduzca esta carga:

| Proceso | Llegada | Duración |
|---|---:|---:|
| A | 0 | 6 |
| B | 1 | 3 |
| C | 2 | 1 |

Con un núcleo, ejecute los cuatro algoritmos y responda:

1. ¿Qué algoritmo minimiza el tiempo medio de espera?
2. ¿En cuáles se interrumpe un proceso ya iniciado?
3. ¿Cómo cambia Round Robin con *quantum* 1, 2 y 4?
4. ¿Qué criterio elegiría para un sistema interactivo? Justifique la respuesta.
5. Repita con dos núcleos. ¿Qué procesos se solapan? ¿Por qué un proceso aislado
   no termina antes aunque se añadan más núcleos?
