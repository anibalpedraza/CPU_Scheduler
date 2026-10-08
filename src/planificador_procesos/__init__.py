"""Motor y aplicación educativa del planificador de procesos."""

from .core import Process, ProcessResult, SimulationResult, simulate

__all__ = ["Process", "ProcessResult", "SimulationResult", "simulate"]
from .metadata import VERSION as __version__
