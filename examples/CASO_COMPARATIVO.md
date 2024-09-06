# Caso comparativo

## Carga

| Proceso | Llegada | Duración |
|---|---:|---:|
| P1 | 0 | 6 |
| P2 | 1 | 3 |
| P3 | 2 | 1 |

## Resultados de referencia

### FCFS

| Proceso | Finalización | Espera | Retorno |
|---|---:|---:|---:|
| P1 | 6 | 0 | 6 |
| P2 | 9 | 5 | 8 |
| P3 | 10 | 7 | 8 |

### SRTF

| Proceso | Finalización | Espera | Retorno |
|---|---:|---:|---:|
| P1 | 10 | 4 | 10 |
| P2 | 5 | 1 | 4 |
| P3 | 3 | 0 | 1 |

Utilice el simulador para completar SJF y Round Robin con *quantum* 1, 2 y 4.
Explique por qué cambian el orden de ejecución y las métricas.
