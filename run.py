"""Ejecuta la aplicación desde una copia local del repositorio."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from planificador_procesos.app import main


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--self-test":
        from planificador_procesos.packaging_check import run_check
        sys.exit(run_check(Path(sys.argv[2])))
    elif len(sys.argv) != 1:
        sys.exit(2)
    else:
        main()
