# Referencia de algoritmos

## Magnitudes

Para cada proceso se utilizan:

- **llegada**: instante en el que entra en el sistema;
- **duración**: ciclos de CPU necesarios;
- **finalización**: instante en el que termina;
- **retorno**: `finalización - llegada`;
- **espera**: `retorno - duración`.

El simulador calcula también las medias de espera y retorno.

## FCFS

Atiende los procesos por orden de llegada. No es apropiativo: una vez iniciada una
ráfaga, continúa hasta terminar. Es fácil de implementar, pero un proceso largo
puede retrasar a todos los posteriores.

## SJF

Entre los procesos preparados elige el de menor duración. No es apropiativo. Puede
reducir el tiempo medio de espera, pero presupone que se conoce la duración y puede
perjudicar a los procesos largos.

## SRTF

Es la variante apropiativa de SJF. En cada ciclo selecciona el proceso con menor
tiempo restante; una llegada más corta puede desalojar al proceso activo.

## Round Robin

Atiende la cola por turnos. Cada proceso puede ejecutar como máximo el número de
ciclos indicado por el *quantum*. Un *quantum* pequeño mejora el tiempo de respuesta,
pero en un sistema real aumentaría el coste de los cambios de contexto.

## Supuestos del modelo

- Una sola CPU.
- Tiempos enteros.
- Una única ráfaga de CPU por proceso.
- Cambios de contexto sin coste.
- Sin prioridades, bloqueos ni operaciones de entrada/salida.
- Los empates se resuelven conservando el orden de entrada.
