"""Avisos de licencia incluidos en las aplicaciones autónomas."""
from pathlib import Path
import sys


def license_text() -> str:
    directory = Path(__file__).resolve().parent / "licenses"
    if directory.is_dir():
        return "\n\n".join((directory / name).read_text(encoding="utf-8")
                              for name in ("LICENSE.txt", "THIRD_PARTY_NOTICES.txt"))
    if getattr(sys, "frozen", False):
        raise RuntimeError("El paquete no contiene los avisos de licencia")
    source = Path(__file__).resolve().parents[2] / "LICENSE"
    return source.read_text(encoding="utf-8") + (
        "\n\nLos avisos de componentes de terceros se incorporan al construir la aplicación.\n")
