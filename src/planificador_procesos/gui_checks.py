"""Regresiones comprobadas también dentro de los ejecutables distribuidos."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def check_timeline_contrast(app) -> None:
    def luminance(color):
        channels = [value / 65535 for value in app.master.winfo_rgb(color)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
                  for value in channels]
        return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    for cell in app.timeline_grid.winfo_children():
        if isinstance(cell, tk.Label):
            low, high = sorted((luminance(cell.cget("fg")), luminance(cell.cget("bg"))))
            if (high + 0.05) / (low + 0.05) < 4.5:
                raise RuntimeError(f"Contraste insuficiente en {cell.cget('text')!r}")


def check_dialog_lifecycle(app) -> None:
    """Ejercita los menús, el mapeo real y el cierre manteniendo eventos activos."""
    root = app.master
    root.deiconify()
    root.update()

    def menu(label):
        return root.nametowidget(app.menu_bar.entrycget(label, "menu"))

    def heartbeat():
        pulse = []
        root.after(0, lambda: pulse.append(True))
        root.update()
        if pulse != [True]:
            raise RuntimeError("El bucle de eventos no responde con una ventana abierta")

    def button(dialog, label):
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        return next(widget for widget in descendants(dialog)
                    if isinstance(widget, ttk.Button) and widget.cget("text") == label)

    for attempt in range(4):
        menu("Ayuda").invoke("Acerca de…")
        if getattr(app, "_about_dialog", None) is not None:
            raise RuntimeError("Acerca de se abrió dentro del callback del menú")
        root.update()
        about = app._about_dialog
        if about is None or not about.winfo_ismapped() or root.grab_current() is not None:
            raise RuntimeError("Acerca de no es visible o bloquea la ventana principal")
        app.show_about()
        if app._about_dialog is not about:
            raise RuntimeError("Se han creado ventanas Acerca de duplicadas")
        heartbeat()
        if attempt >= 2:
            about.focus_force()
            root.update()
            about.event_generate("<KeyPress-Escape>" if attempt == 2 else "<KeyPress-Return>")
        elif attempt == 1:
            root.tk.call(about.protocol("WM_DELETE_WINDOW"))
        else:
            button(about, "Cerrar").invoke()
        root.update()
        if app._about_dialog is not None:
            raise RuntimeError("Acerca de no se ha cerrado")

        exports = root.nametowidget(menu("Archivo").entrycget("Exportar", "menu"))
        exports.invoke("CSV…")
        if getattr(app, "_csv_dialog", None) is not None:
            raise RuntimeError("CSV se abrió dentro del callback del menú")
        root.update()
        dialog = app._csv_dialog
        if dialog is None or not dialog.winfo_ismapped() or root.grab_current() is not dialog:
            raise RuntimeError("La captura de entrada CSV no corresponde a una ventana visible")
        heartbeat()
        if attempt >= 2:
            dialog.focus_force()
            root.update()
            dialog.event_generate("<KeyPress-Escape>")
        elif attempt == 1:
            root.tk.call(dialog.protocol("WM_DELETE_WINDOW"))
        else:
            button(dialog, "Cancelar").invoke()
        root.update()
        if app._csv_dialog is not None or root.grab_current() is not None:
            raise RuntimeError("CSV no ha liberado la ventana principal al cerrarse")
        app.calculate()
        if app.last_result is None:
            raise RuntimeError("No se puede volver a calcular tras cerrar los diálogos")
    root.withdraw()
