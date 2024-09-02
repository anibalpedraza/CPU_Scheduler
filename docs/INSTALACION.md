# Instalación

## Requisitos

- Python 3.10 o posterior.
- Tkinter. En Windows y macOS suele formar parte de la instalación oficial de
  Python. En algunas distribuciones GNU/Linux debe instalarse con el gestor de
  paquetes del sistema.

## Entorno virtual

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py
```

### GNU/Linux o macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py
```

## Comprobación de Tkinter

```bash
python -c "import tkinter; print(tkinter.TkVersion)"
```

Si el comando muestra una versión y no produce errores, el entorno gráfico está
disponible.

## Solución de problemas de Tcl/Tk

Si al abrir la aplicación aparece `Can't find a usable init.tcl`, la instalación de
Python no puede cargar los archivos de Tcl/Tk aunque el módulo `tkinter` exista.
Repárela o reinstale Python desde <https://www.python.org/>, asegurándose de incluir
**Tcl/Tk and IDLE**. El problema pertenece al entorno de Python, no al simulador.
