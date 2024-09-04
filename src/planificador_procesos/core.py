"""Motor puro de simulación de algoritmos de planificación mononúcleo."""

from __future__ import annotations

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
        if self.arrival_time < 0:
            raise ValueError("El tiempo de llegada no puede ser negativo.")
        if self.duration_time <= 0:
            raise ValueError("La duración debe ser mayor que cero.")


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
    """Resultado completo, incluidas métricas y línea temporal."""

    algorithm: str
    processes: tuple[ProcessResult, ...]
    timeline: dict[str, tuple[str, ...]]
    makespan: int

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
) -> SimulationResult:
    """Simula una carga en una CPU con la política seleccionada."""

    process_list = list(processes)
    _validate_processes(process_list)
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Algoritmo no compatible: {algorithm}.")
    if algorithm == "Round Robin" and (quantum is None or quantum <= 0):
        raise ValueError("Round Robin requiere un quantum mayor que cero.")

    if not process_list:
        return SimulationResult(algorithm, (), {}, 0)

    if algorithm == "FCFS":
        completed, timeline, makespan = _simulate_non_preemptive(process_list, shortest=False)
    elif algorithm == "SJF":
        completed, timeline, makespan = _simulate_non_preemptive(process_list, shortest=True)
    elif algorithm == "SRTF":
        completed, timeline, makespan = _simulate_srtf(process_list)
    else:
        completed, timeline, makespan = _simulate_round_robin(process_list, quantum or 1)

    by_id = {item.process_id: item for item in completed}
    ordered = tuple(by_id[item.process_id] for item in process_list)
    frozen_timeline = {key: tuple(values) for key, values in timeline.items()}
    return SimulationResult(algorithm, ordered, frozen_timeline, makespan)


def _validate_processes(processes: Sequence[Process]) -> None:
    process_ids = [item.process_id for item in processes]
    if len(process_ids) != len(set(process_ids)):
        raise ValueError("Los identificadores de proceso deben ser únicos.")


def _blank_timeline(processes: Sequence[Process]) -> dict[str, list[str]]:
    return {item.process_id: [] for item in processes}


def _mark_cycle(
    timeline: dict[str, list[str]],
    processes_by_id: dict[str, Process],
    cycle: int,
    running_id: str | None,
    queued_ids: set[str],
) -> None:
    for process_id, cells in timeline.items():
        while len(cells) < cycle:
            cells.append("")
        if process_id == running_id:
            cells[cycle - 1] = "X"
        elif process_id in queued_ids and processes_by_id[process_id].arrival_time < cycle:
            cells[cycle - 1] = "O"


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


def _simulate_non_preemptive(
    processes: Sequence[Process],
    *,
    shortest: bool,
) -> tuple[list[ProcessResult], dict[str, list[str]], int]:
    pending = list(enumerate(processes))
    queue: list[tuple[int, Process]] = []
    completed: list[ProcessResult] = []
    timeline = _blank_timeline(processes)
    process_map = {item.process_id: item for item in processes}
    time = 0

    def add_arrivals() -> None:
        for indexed in pending[:]:
            if indexed[1].arrival_time <= time:
                queue.append(indexed)
                pending.remove(indexed)
        if shortest:
            queue.sort(key=lambda item: (item[1].duration_time, item[1].arrival_time, item[0]))

    add_arrivals()
    while pending or queue:
        if not queue:
            time += 1
            add_arrivals()
            _mark_cycle(timeline, process_map, time, None, {item[1].process_id for item in queue})
            continue

        _, process = queue.pop(0)
        for _ in range(process.duration_time):
            time += 1
            add_arrivals()
            _mark_cycle(
                timeline,
                process_map,
                time,
                process.process_id,
                {item[1].process_id for item in queue},
            )
        completed.append(_result(process, time))

    return completed, timeline, time


def _simulate_srtf(
    processes: Sequence[Process],
) -> tuple[list[ProcessResult], dict[str, list[str]], int]:
    pending = list(enumerate(processes))
    queue: list[tuple[int, Process]] = []
    remaining = {item.process_id: item.duration_time for item in processes}
    completed: list[ProcessResult] = []
    timeline = _blank_timeline(processes)
    process_map = {item.process_id: item for item in processes}
    time = 0

    def add_arrivals() -> None:
        for indexed in pending[:]:
            if indexed[1].arrival_time <= time:
                queue.append(indexed)
                pending.remove(indexed)
        queue.sort(
            key=lambda item: (
                remaining[item[1].process_id],
                item[1].arrival_time,
                item[0],
            )
        )

    add_arrivals()
    while pending or queue:
        if not queue:
            time += 1
            add_arrivals()
            _mark_cycle(timeline, process_map, time, None, {item[1].process_id for item in queue})
            continue

        indexed = queue.pop(0)
        process = indexed[1]
        time += 1
        remaining[process.process_id] -= 1
        add_arrivals()
        _mark_cycle(
            timeline,
            process_map,
            time,
            process.process_id,
            {item[1].process_id for item in queue},
        )
        if remaining[process.process_id] == 0:
            completed.append(_result(process, time))
        else:
            queue.append(indexed)
            queue.sort(
                key=lambda item: (
                    remaining[item[1].process_id],
                    item[1].arrival_time,
                    item[0],
                )
            )

    return completed, timeline, time


def _simulate_round_robin(
    processes: Sequence[Process],
    quantum: int,
) -> tuple[list[ProcessResult], dict[str, list[str]], int]:
    pending = list(enumerate(processes))
    queue: list[tuple[int, Process]] = []
    remaining = {item.process_id: item.duration_time for item in processes}
    completed: list[ProcessResult] = []
    timeline = _blank_timeline(processes)
    process_map = {item.process_id: item for item in processes}
    time = 0

    def add_arrivals() -> None:
        for indexed in pending[:]:
            if indexed[1].arrival_time <= time:
                queue.append(indexed)
                pending.remove(indexed)

    add_arrivals()
    while pending or queue:
        if not queue:
            time += 1
            add_arrivals()
            _mark_cycle(timeline, process_map, time, None, {item[1].process_id for item in queue})
            continue

        indexed = queue.pop(0)
        process = indexed[1]
        executed = 0
        while executed < quantum and remaining[process.process_id] > 0:
            time += 1
            add_arrivals()
            remaining[process.process_id] -= 1
            executed += 1
            _mark_cycle(
                timeline,
                process_map,
                time,
                process.process_id,
                {item[1].process_id for item in queue},
            )

        if remaining[process.process_id] == 0:
            completed.append(_result(process, time))
        else:
            queue.append(indexed)

    return completed, timeline, time
