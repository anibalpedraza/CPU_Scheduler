"""Motor puro de simulación de planificación con uno o varios núcleos."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import fmean
from typing import Iterable, Sequence


SUPPORTED_ALGORITHMS = ("FCFS", "SJF", "SRTF", "Round Robin")


@dataclass(frozen=True, slots=True)
class Process:
    """Proceso de entrada de la simulación."""

    process_id: str
    arrival_time: int
    duration_time: int

    def __post_init__(self) -> None:
        if not self.process_id.strip():
            raise ValueError("El identificador del proceso no puede estar vacío.")
        if type(self.arrival_time) is not int or self.arrival_time < 0:
            raise ValueError("El tiempo de llegada debe ser un entero no negativo.")
        if type(self.duration_time) is not int or self.duration_time <= 0:
            raise ValueError("La duración debe ser un entero mayor que cero.")


@dataclass(frozen=True, slots=True)
class ProcessResult:
    """Métricas obtenidas para un proceso."""

    process_id: str
    arrival_time: int
    duration_time: int
    completed_time: int
    waiting_time: int
    turnaround_time: int


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Métricas, estados por proceso y asignaciones por núcleo y ciclo."""

    algorithm: str
    processes: tuple[ProcessResult, ...]
    timeline: dict[str, tuple[str, ...]]
    makespan: int
    core_count: int = 1
    core_timeline: tuple[tuple[str | None, ...], ...] = ()

    @property
    def average_waiting_time(self) -> float:
        return fmean(item.waiting_time for item in self.processes) if self.processes else 0.0

    @property
    def average_turnaround_time(self) -> float:
        return fmean(item.turnaround_time for item in self.processes) if self.processes else 0.0


def simulate(
    processes: Iterable[Process],
    algorithm: str,
    *,
    quantum: int | None = None,
    core_count: int = 1,
) -> SimulationResult:
    """Simula núcleos idénticos con cola global y cambios de contexto sin coste.

    Cada proceso ocupa como máximo un núcleo por ciclo. Las llegadas en t
    pueden ejecutar en [t, t+1). En RR entran antes de los turnos vencidos en t.
    """

    process_list = list(processes)
    _validate_processes(process_list)
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Algoritmo no compatible: {algorithm}.")
    if type(core_count) is not int or core_count <= 0:
        raise ValueError("El número de núcleos debe ser un entero mayor que cero.")
    if algorithm == "Round Robin" and (type(quantum) is not int or quantum <= 0):
        raise ValueError("Round Robin requiere un quantum entero mayor que cero.")

    return _simulate(process_list, algorithm, core_count, quantum)


def _validate_processes(processes: Sequence[Process]) -> None:
    process_ids = [item.process_id for item in processes]
    if len(process_ids) != len(set(process_ids)):
        raise ValueError("Los identificadores de proceso deben ser únicos.")


def _result(process: Process, completed_time: int) -> ProcessResult:
    turnaround = completed_time - process.arrival_time
    return ProcessResult(
        process.process_id,
        process.arrival_time,
        process.duration_time,
        completed_time,
        turnaround - process.duration_time,
        turnaround,
    )


def _simulate(
    processes: Sequence[Process],
    algorithm: str,
    core_count: int,
    quantum: int | None,
) -> SimulationResult:
    # Los índices preservan el orden de entrada al desempatar y al devolver métricas.
    pending = deque(sorted(range(len(processes)), key=lambda i: (processes[i].arrival_time, i)))
    ready: deque[int] = deque()
    running: list[int | None] = [None] * core_count
    slices = [0] * core_count
    expired: list[int] = []
    remaining = [item.duration_time for item in processes]
    completed: dict[int, int] = {}
    timeline: dict[str, list[str]] = {item.process_id: [] for item in processes}
    core_timeline: list[list[str | None]] = [[] for _ in range(core_count)]
    time = 0

    while pending or ready or expired or any(i is not None for i in running):
        while pending and processes[pending[0]].arrival_time <= time:
            ready.append(pending.popleft())
        ready.extend(expired)
        expired.clear()

        if algorithm in ("SJF", "SRTF"):
            candidates = list(ready)
            if algorithm == "SRTF":
                candidates.extend(i for i in running if i is not None)
            candidates.sort(key=lambda i: (remaining[i], processes[i].arrival_time, i))
            if algorithm == "SRTF":
                # Mantener en su núcleo los seleccionados que ya estaban ejecutando.
                selected = set(candidates[:core_count])
                for core, index in enumerate(running):
                    if index not in selected:
                        running[core] = None
                active = {i for i in running if i is not None}
                ready = deque(i for i in candidates if i not in active)
            else:
                ready = deque(candidates)

        for core, index in enumerate(running):
            if index is None and ready:
                running[core] = ready.popleft()
                slices[core] = 0

        active = {i for i in running if i is not None}
        queued = set(ready)
        for index, process in enumerate(processes):
            timeline[process.process_id].append(
                "X" if index in active else "O" if index in queued else ""
            )
        for core, index in enumerate(running):
            core_timeline[core].append(processes[index].process_id if index is not None else None)

        time += 1
        for core, index in enumerate(running):
            if index is None:
                continue
            remaining[index] -= 1
            slices[core] += 1
            if remaining[index] == 0:
                completed[index] = time
                running[core] = None
            elif algorithm == "Round Robin" and slices[core] == quantum:
                # Al inicio del siguiente ciclo, las llegadas preceden a estos turnos.
                expired.append(index)
                running[core] = None

    return SimulationResult(
        algorithm=algorithm,
        processes=tuple(_result(item, completed[i]) for i, item in enumerate(processes)),
        timeline={key: tuple(values) for key, values in timeline.items()},
        makespan=time,
        core_count=core_count,
        core_timeline=tuple(tuple(cells) for cells in core_timeline),
    )
