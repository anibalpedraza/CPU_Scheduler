"""Formato JSON versionado para guardar y recuperar simulaciones."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .core import Process, SUPPORTED_ALGORITHMS
from .fileio import atomic_destination

FORMAT = "cpu-scheduler-simulation"
FORMAT_VERSION = 1


@dataclass(frozen=True)
class SimulationDocument:
    processes: tuple[Process, ...]
    algorithm: str = "FCFS"
    quantum: int = 2
    core_count: int = 1
    calculated: bool = False
    draft: tuple[str, str, str] = ("A", "0", "1")

    def to_dict(self) -> dict:
        return {
            "format": FORMAT,
            "version": FORMAT_VERSION,
            "settings": {"algorithm": self.algorithm, "quantum": self.quantum, "core_count": self.core_count},
            "processes": [{"id": p.process_id, "arrival": p.arrival_time, "duration": p.duration_time}
                          for p in self.processes],
            "calculated": self.calculated,
            "draft": {"id": self.draft[0], "arrival": self.draft[1], "duration": self.draft[2]},
        }


def _integer(value, name: str, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} debe ser un entero mayor o igual que {minimum}.")
    return value


def document_from_dict(raw: object) -> SimulationDocument:
    if not isinstance(raw, dict) or raw.get("format") != FORMAT:
        raise ValueError("El archivo no es una simulación de CPU Scheduler.")
    if type(raw.get("version")) is not int or raw["version"] != FORMAT_VERSION:
        raise ValueError("Versión de formato no compatible. Este programa admite la versión 1.")
    settings = raw.get("settings")
    if not isinstance(settings, dict):
        raise ValueError("Falta la configuración de la simulación.")
    algorithm = settings.get("algorithm")
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError("La política de planificación no es compatible.")
    quantum = _integer(settings.get("quantum"), "Quantum", 1)
    core_count = _integer(settings.get("core_count"), "Número de núcleos", 1)
    rows = raw.get("processes")
    if not isinstance(rows, list):
        raise ValueError("Falta la lista de procesos.")
    processes = []
    identifiers = set()
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise ValueError("Cada proceso debe tener un identificador de texto.")
        process = Process(row["id"], _integer(row.get("arrival"), "Llegada", 0),
                          _integer(row.get("duration"), "Duración", 1))
        if process.process_id in identifiers:
            raise ValueError(f"Identificador de proceso duplicado: {process.process_id}.")
        identifiers.add(process.process_id)
        processes.append(process)
    calculated = raw.get("calculated", False)
    if type(calculated) is not bool or (calculated and not processes):
        raise ValueError("El estado de cálculo no es válido.")
    draft = raw.get("draft", {"id": "A", "arrival": "0", "duration": "1"})
    if not isinstance(draft, dict) or any(not isinstance(draft.get(key), str) for key in ("id", "arrival", "duration")):
        raise ValueError("Los campos del formulario deben ser texto.")
    return SimulationDocument(tuple(processes), algorithm, quantum, core_count, calculated,
                              (draft["id"], draft["arrival"], draft["duration"]))


def save_simulation(path: str | Path, document: SimulationDocument) -> None:
    raw = document.to_dict()
    document_from_dict(raw)  # Validar también los documentos construidos desde la interfaz.
    with atomic_destination(path) as temporary:
        temporary.write_text(json.dumps(raw, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def load_simulation(path: str | Path) -> SimulationDocument:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("El archivo no contiene un JSON válido de simulación.") from error
    return document_from_dict(raw)
