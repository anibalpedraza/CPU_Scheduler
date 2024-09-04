"""Ejecuta la aplicación desde una copia local del repositorio."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from planificador_procesos.app import main


if __name__ == "__main__":
    main()
