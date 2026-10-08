#!/bin/bash
set -eu
cd "$(dirname "$0")"
if [ "$(uname -s)" != "Darwin" ]; then
    echo "Ejecuta este lanzador en macOS."
    exit 1
fi
if [ -x /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12 ]; then
    PYTHON_BUILD=/Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12
elif command -v python3.12 >/dev/null 2>&1; then
    PYTHON_BUILD="$(command -v python3.12)"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BUILD="$(command -v python3)"
else
    echo "Instala Python 3.12 con Tcl/Tk desde python.org y vuelve a ejecutar este archivo."
    exit 1
fi
"$PYTHON_BUILD" -c 'import sys; assert sys.version_info[:2] == (3, 12), "Para esta validación instale Python 3.12 desde python.org"'
# La copia sincronizada puede contener .venv-build de Windows. No se reutiliza.
"$PYTHON_BUILD" -m venv .venv-build-macos
.venv-build-macos/bin/python -m pip install -r requirements-build.txt -e .
.venv-build-macos/bin/python -m pip check
.venv-build-macos/bin/python -c 'import tkinter as tk; root=tk.Tk(); root.withdraw(); root.destroy()'
.venv-build-macos/bin/python -m unittest discover -s tests -v
.venv-build-macos/bin/python tools/build_macos.py
echo "Validación terminada. Los archivos están en dist/packages/macos-arm64 o macos-x86_64."
