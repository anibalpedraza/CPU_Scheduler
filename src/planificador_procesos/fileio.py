"""Escritura atómica de los archivos generados por la aplicación."""
from contextlib import contextmanager
import os
from pathlib import Path
import tempfile


@contextmanager
def atomic_destination(path: str | Path):
    destination = Path(path)
    fd, temporary = tempfile.mkstemp(prefix=".cpu-scheduler-", suffix=destination.suffix,
                                     dir=destination.parent)
    os.close(fd)
    try:
        yield Path(temporary)
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
