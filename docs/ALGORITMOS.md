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
tiempo restante. Por tanto, una llegada más corta puede desalojar al proceso activo.

## Round Robin

Atiende la cola por turnos. Cada proceso puede ejecutar como máximo el número de
ciclos indicado por el *quantum*. Un *quantum* pequeño mejora el tiempo de respuesta,
pero en un sistema real aumentaría el coste de los cambios de contexto.

## Planificación multinúcleo

El número de núcleos es configurable, de manera que todos comparten una cola
global. Un proceso solo puede ejecutar en un núcleo por ciclo. La implementación
se ha realizado según estas consideraciones:

- FCFS y SJF conservan cada proceso en su núcleo hasta terminar. Un núcleo libre
  toma inmediatamente el siguiente proceso preparado según la política, priorizando
  el instante de llegada en FCFS y el menor tiempo de duración en SJF.
- SRTF elige en cada ciclo hasta N procesos con menor tiempo restante, donde N
  es el número de núcleos. Los seleccionados que ya se ejecutaban mantienen su núcleo.
  Posteriormente, podrían ser desalojados y reanudarse en otro núcleo.
- Round Robin utiliza un *quantum* independiente para cada proceso que entra en cada núcleo.
  Cuando vence, el proceso vuelve al final de la cola global. Las llegadas en un
  determinado instante entran antes a la cola que los procesos cuyo *quantum* vence
  en ese mismo instante. Si varios turnos vencen a la vez, los procesos vuelven a la
  cola por orden de núcleo. Si varios procesos llegan a la vez, entran a la cola
  por orden de entrada en la tabla.

El ciclo mostrado como 1 representa el intervalo [0, 1). Un proceso que llega en
el instante t puede ejecutar desde [t, t+1). La finalización es el extremo final
del último intervalo ejecutado. Las filas CPU muestran el proceso asignado a cada
núcleo (un guion indica que está libre). Los procesos indican con el
símbolo *X* cuando están en ejecución y con *O* cuando están en espera.

## Supuestos del modelo de procesador

- Uno o varios núcleos (un núcleo por defecto).
- Tiempos enteros.
- Un único proceso ejecutado por núcleo.
- Cambios de contexto sin coste.
- Sin prioridades, bloqueos ni operaciones de entrada/salida.
- En FCFS se ordena por llegada. En SJF y SRTF se ordena por duración o tiempo
  restante, después por llegada. Los empates restantes conservan el orden de entrada.
