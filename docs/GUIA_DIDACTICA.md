# Guía didáctica

## Finalidad

El simulador permite observar cómo una misma carga de procesos produce resultados
distintos según el algoritmo de planificación. Está dirigido a asignaturas
introductorias de Informática y Sistemas Operativos en titulaciones de Ingeniería.

## Resultados de aprendizaje

Tras utilizar el recurso, el alumnado debería poder:

- diferenciar algoritmos apropiativos y no apropiativos;
- calcular tiempos de finalización, espera y retorno;
- explicar el efecto del instante de llegada y la duración;
- analizar el compromiso entre tiempo medio, equidad y tiempo de respuesta;
- comparar FCFS, SJF, SRTF y Round Robin con una misma carga.

## Uso básico

1. Seleccione un algoritmo.
2. Introduzca para cada proceso un identificador, su instante de llegada y su
   duración.
3. Para Round Robin, indique el *quantum*.
4. Pulse **Calcular**.
5. Compare la tabla de resultados y la tabla de ciclos.

En la tabla de ciclos:

- `X` indica que el proceso usa la CPU;
- `O` indica que el proceso espera en la cola;
- el sombreado marca el instante de llegada.

## Actividad propuesta

Introduzca esta carga:

| Proceso | Llegada | Duración |
|---|---:|---:|
| P1 | 0 | 6 |
| P2 | 1 | 3 |
| P3 | 2 | 1 |

Ejecute los cuatro algoritmos y responda:

1. ¿Qué algoritmo minimiza el tiempo medio de espera?
2. ¿En cuáles se interrumpe un proceso ya iniciado?
3. ¿Cómo cambia Round Robin con *quantum* 1, 2 y 4?
4. ¿Qué criterio elegiría para un sistema interactivo? Justifique la respuesta.

## Limitaciones

La versión estable simula una única CPU, tiempos enteros, ráfagas exclusivamente
de CPU y coste nulo de cambio de contexto. La rama experimental multinúcleo no
debe utilizarse para obtener resultados docentes validados.
