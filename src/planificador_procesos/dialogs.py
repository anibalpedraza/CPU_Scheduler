"""Ventanas que usan el bucle principal, sin esperas anidadas de Tk Aqua."""
from __future__ import annotations

import tkinter as tk


def present_dialog(dialog: tk.Toplevel, focus: tk.Widget, *, modal: bool = False) -> None:
    """Captura y enfoca sólo después del mapeo; devuelve el control inmediatamente."""
    pending = None
    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    def activate():
        nonlocal pending
        pending = None
        if not dialog.winfo_exists():
            return
        if modal:
            dialog.grab_set()
        focus.focus_set()

    def mapped(event):
        nonlocal pending
        if event.widget is dialog and pending is None:
            pending = dialog.after(0, activate)

    def destroyed(event):
        nonlocal pending
        if event.widget is dialog and pending is not None:
            dialog.after_cancel(pending)
            pending = None

    dialog.bind("<Map>", mapped, add="+")
    dialog.bind("<Destroy>", destroyed, add="+")


def existing_dialog(owner, attribute: str) -> tk.Toplevel | None:
    dialog = getattr(owner, attribute, None)
    if dialog is not None and dialog.winfo_exists():
        dialog.deiconify()
        dialog.lift()
        return dialog
    return None


def remember_dialog(owner, attribute: str, dialog: tk.Toplevel) -> None:
    setattr(owner, attribute, dialog)

    def forget(event):
        if event.widget is dialog and getattr(owner, attribute, None) is dialog:
            setattr(owner, attribute, None)

    dialog.bind("<Destroy>", forget, add="+")
