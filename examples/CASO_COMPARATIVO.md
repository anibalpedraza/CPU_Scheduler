# Caso comparativo

## Carga

| Proceso | Llegada | Duración |
|---|---:|---:|
| A | 0 | 6 |
| B | 1 | 3 |
| C | 2 | 1 |

## Resultados de referencia

Estos resultados corresponden a un núcleo.

### FCFS

| Proceso | Finalización | Espera | Retorno |
|---|---:|---:|---:|
| A | 6 | 0 | 6 |
| B | 9 | 5 | 8 |
| C | 10 | 7 | 8 |

### SRTF

| Proceso | Finalización | Espera | Retorno |
|---|---:|---:|---:|
| A | 10 | 4 | 10 |
| B | 5 | 1 | 4 |
| C | 3 | 0 | 1 |

Utilice el simulador para completar SJF y Round Robin con *quantum* 1, 2 y 4.
Explique por qué cambian el orden de ejecución y las métricas.
