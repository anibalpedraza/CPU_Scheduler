"""Menús, portapapeles y diálogos del simulador."""
from __future__ import annotations

import csv
import io
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .core import Process
from .dialogs import existing_dialog, present_dialog, remember_dialog
from .simulation_actions import SimulationActions
from .exports import ExportData, export_csv, export_excel, export_pdf, pdf_minimum_font_size
from .metadata import (APP_NAME, AUTHOR, CODE_LICENSE, CONTENT_LICENSE,
                       CONTENT_LICENSE_URL, COPYRIGHT_YEAR, REPOSITORY_URL, VERSION)


class SchedulerActions(SimulationActions):
    """Acciones de la ventana principal, sin modificar el motor de simulación."""

    def _menu_command(self, action):
        # Salir del callback del menú nativo antes de abrir ventanas o selectores.
        # Un temporizador normal evita también el bucle de dibujo idle de Tk Aqua.
        return lambda: self.master.after(0, action)

    def _build_menus(self) -> None:
        is_macos = self.master.tk.call("tk", "windowingsystem") == "aqua"
        modifier = "Command" if is_macos else "Control"
        key_label = "Command" if is_macos else "Ctrl"
        self.menu_bar = tk.Menu(self, tearoff=False)
        file_menu = tk.Menu(self.menu_bar, tearoff=False)
        file_menu.add_command(label="Nuevo", accelerator=f"{key_label}+N", command=self._menu_command(self.new_simulation))
        file_menu.add_command(label="Abrir…", accelerator=f"{key_label}+O", command=self._menu_command(self.open_document))
        file_menu.add_separator()
        file_menu.add_command(label="Guardar", accelerator=f"{key_label}+S", command=self._menu_command(self.save_document))
        file_menu.add_command(label="Guardar como…", accelerator=f"{key_label}+Mayús+S", command=self._menu_command(lambda: self.save_document(save_as=True)))
        export_menu = tk.Menu(file_menu, tearoff=False)
        export_menu.add_command(label="CSV…", command=self._menu_command(self.export_csv_dialog))
        export_menu.add_command(label="PDF…", command=self._menu_command(lambda: self.export_report("pdf")))
        export_menu.add_command(label="Excel…", command=self._menu_command(lambda: self.export_report("xlsx")))
        file_menu.add_cascade(label="Exportar", menu=export_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", accelerator="Command+Q" if is_macos else "Alt+F4", command=self._menu_command(self.close_application))
        self.menu_bar.add_cascade(label="Archivo", menu=file_menu)
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=False, postcommand=self._update_edit_menu)
        for label, shortcut, action in (("Cortar", f"{key_label}+X", "cut"), ("Copiar", f"{key_label}+C", "copy"),
                                        ("Pegar", f"{key_label}+V", "paste")):
            self.edit_menu.add_command(label=label, accelerator=shortcut,
                                       command=self._menu_command(lambda action=action: self.edit(action)))
        self.menu_bar.add_cascade(label="Edición", menu=self.edit_menu)
        help_menu = tk.Menu(self.menu_bar, tearoff=False)
        help_menu.add_command(label="GitHub CPU Scheduler", command=self._menu_command(lambda: self.open_link(REPOSITORY_URL)))
        help_menu.add_separator()
        help_menu.add_command(label="Acerca de…", command=self._menu_command(self.show_about))
        self.menu_bar.add_cascade(label="Ayuda", menu=help_menu)
        self.master.configure(menu=self.menu_bar)
        for sequence, action in ((f"<{modifier}-n>", self.new_simulation), (f"<{modifier}-o>", self.open_document),
                                 (f"<{modifier}-s>", self.save_document),
                                 (f"<{modifier}-Shift-S>", lambda: self.save_document(save_as=True))):
            self.master.bind(sequence, lambda _event, action=action: self._file_shortcut(action))
        if is_macos:
            self.master.bind("<Command-q>", lambda _event: self._file_shortcut(self.close_application))
            self.master.createcommand("tk::mac::Quit", self._menu_command(self.close_application))
        # Entry y Text conservan los atajos nativos. Treeview necesita enlaces propios.
        for table in (self.process_table, self.result_table):
            for key, action in (("x", "cut"), ("c", "copy"), ("v", "paste")):
                table.bind(f"<{modifier}-{key}>", lambda _event, action=action: self._edit_shortcut(action))
        for variable in (self.algorithm_var, self.quantum_var, self.core_count_var):
            variable.trace_add("write", self._invalidate_configuration)

    def _edit_shortcut(self, action):
        self.edit(action)
        return "break"

    def _invalidate_configuration(self, *_args) -> None:
        self._on_algorithm_change()
        if self.last_result is not None:
            self.clear_results()
            self.status_var.set("Configuración modificada. Vuelva a calcular la planificación.")
        self._update_document_title()

    def _edit_capabilities(self):
        widget = self.master.focus_get()
        if widget in (self.process_table, self.result_table):
            selected = bool(widget.selection())
            return (selected and widget is self.process_table, selected, widget is self.process_table)
        if isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Spinbox, tk.Entry, tk.Text)):
            disabled = str(widget.cget("state")) in ("disabled", "readonly")
            try:
                selected = bool(widget.tag_ranges("sel")) if isinstance(widget, tk.Text) else bool(widget.selection_present())
            except tk.TclError:
                selected = False
            return (selected and not disabled, selected, not disabled)
        return (False, False, False)

    def _update_edit_menu(self) -> None:
        for index, enabled in enumerate(self._edit_capabilities()):
            self.edit_menu.entryconfigure(index, state="normal" if enabled else "disabled")

    def edit(self, action: str) -> None:
        if not self._edit_capabilities()[{"cut": 0, "copy": 1, "paste": 2}[action]]:
            return
        widget = self.master.focus_get()
        if widget in (self.process_table, self.result_table):
            if action == "paste":
                self._paste_processes()
                return
            stream = io.StringIO(newline="")
            writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
            selected = set(widget.selection())
            # Respetar el orden visual, aunque las filas se seleccionasen al revés.
            writer.writerows(widget.item(item, "values") for item in widget.get_children() if item in selected)
            self.master.clipboard_clear()
            self.master.clipboard_append(stream.getvalue())
            if action == "cut":
                self.remove_selected()
        else:
            widget.event_generate({"cut": "<<Cut>>", "copy": "<<Copy>>", "paste": "<<Paste>>"}[action])

    def _paste_processes(self) -> None:
        try:
            text = self.master.clipboard_get()
            try:
                dialect = csv.Sniffer().sniff(text, delimiters="\t;,")
            except csv.Error:
                dialect = csv.excel_tab
            rows = [row for row in csv.reader(io.StringIO(text), dialect) if any(value.strip() for value in row)]
            if rows and [value.strip().casefold() for value in rows[0]] == ["proceso", "llegada", "duración"]:
                rows.pop(0)
            if not rows:
                raise ValueError("El portapapeles no contiene procesos.")
            existing = {p.process_id for p in self._read_processes()}
            processes = []
            for row in rows:
                if len(row) != 3:
                    raise ValueError("Pegue tres columnas: Proceso, Llegada y Duración (desde Excel, CSV o texto tabulado).")
                process = Process(row[0].strip(), int(row[1]), int(row[2]))
                if process.process_id in existing:
                    raise ValueError(f"Ya existe el proceso {process.process_id}.")
                existing.add(process.process_id)
                processes.append(process)
        except (tk.TclError, csv.Error, ValueError) as error:
            messagebox.showerror("No se pueden pegar los procesos", str(error), parent=self.master)
            return
        # Validar todas las filas antes de cambiar la tabla.
        for process in processes:
            self.process_table.insert("", "end", values=(process.process_id, process.arrival_time, process.duration_time))
        self.clear_results()
        self._suggest_process_id()
        self.status_var.set(f"{len(processes)} procesos pegados. Vuelva a calcular la planificación.")

    def _export_data(self, *, require_result=False) -> ExportData:
        processes = tuple(self._read_processes())
        if not processes:
            raise ValueError("Añada al menos un proceso antes de exportar.")
        if require_result and self.last_result is None:
            raise ValueError("Calcule la planificación antes de exportar este informe.")
        algorithm = self.algorithm_var.get()
        quantum = int(self.quantum_var.get()) if algorithm == "Round Robin" else None
        core_count = int(self.core_count_var.get())
        if core_count <= 0 or (quantum is not None and quantum <= 0):
            raise ValueError("El quantum y el número de núcleos deben ser enteros mayores que cero.")
        return ExportData(processes, algorithm, quantum, core_count, self.last_result)

    def export_csv_dialog(self) -> None:
        if existing_dialog(self, "_csv_dialog") is not None:
            return
        try:
            self._export_data()
        except ValueError as error:
            messagebox.showinfo("Exportar CSV", str(error), parent=self.master)
            return
        dialog = tk.Toplevel(self.master)
        remember_dialog(self, "_csv_dialog", dialog)
        dialog.title("Exportar como CSV")
        dialog.resizable(False, False)
        dialog.transient(self.master)
        content = ttk.Frame(dialog, padding=18)
        content.pack(fill="both", expand=True)
        ttk.Label(content, text="Seleccione las tablas que desea exportar:").pack(anchor="w", pady=(0, 10))
        processes = tk.BooleanVar(value=True)
        results = tk.BooleanVar(value=self.last_result is not None)
        ttk.Checkbutton(content, text="Tabla de procesos", variable=processes).pack(anchor="w")
        results_button = ttk.Checkbutton(content, text="Tabla de resultados", variable=results)
        results_button.pack(anchor="w")
        if self.last_result is None:
            results_button.state(["disabled"])
            ttk.Label(content, text="Calcule la planificación para incluir resultados.").pack(anchor="w", pady=6)
        ttk.Label(content, text="Cada tabla se guardará en un archivo distinto.\nSeparador: punto y coma · Codificación: UTF-8.").pack(anchor="w", pady=10)

        def save():
            selected = [name for name, enabled in (("procesos", processes.get()), ("resultados", results.get())) if enabled]
            if not selected:
                messagebox.showinfo("Exportar CSV", "Seleccione al menos una tabla.", parent=dialog)
                return
            target = filedialog.asksaveasfilename(parent=dialog, title="Guardar CSV", defaultextension=".csv",
                initialfile="cpu_scheduler.csv", filetypes=[("CSV", "*.csv")], confirmoverwrite=False)
            if not target:
                return
            base = Path(target)
            paths = [base.with_name(f"{base.stem}_{name}.csv") if len(selected) == 2 else base for name in selected]
            existing = [str(path) for path in paths if path.exists()]
            if existing and not messagebox.askyesno("Reemplazar archivos", "Ya existen estos archivos:\n" + "\n".join(existing) + "\n\n¿Desea reemplazarlos?", parent=dialog):
                return
            saved = []
            try:
                data = self._export_data(require_result="resultados" in selected)
                for name, path in zip(selected, paths):
                    export_csv(path, data, results=name == "resultados")
                    saved.append(str(path))
            except (OSError, ValueError) as error:
                detail = "\nArchivos ya guardados:\n" + "\n".join(saved) if saved else ""
                messagebox.showerror("No se ha completado la exportación", str(error) + detail, parent=dialog)
                return
            dialog.destroy()
            self.status_var.set(f"Exportación CSV completada: {len(paths)} archivo(s).")
            messagebox.showinfo("Exportación completada", "Archivos guardados:\n" + "\n".join(saved), parent=self.master)

        buttons = ttk.Frame(content)
        buttons.pack(fill="x", pady=(4, 0))
        cancel = ttk.Button(buttons, text="Cancelar", command=dialog.destroy)
        cancel.pack(side="right")
        ttk.Button(buttons, text="Exportar…", command=save).pack(side="right", padx=8)
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        present_dialog(dialog, cancel, modal=True)

    def export_report(self, kind: str) -> None:
        try:
            data = self._export_data(require_result=True)
            if kind == "pdf":
                font_size = pdf_minimum_font_size(data)
                if font_size < 6 and not messagebox.askyesno("PDF de una página",
                        f"Para incluir toda la simulación en una página A4, el texto se reducirá a unos {font_size:.1f} puntos.\n"
                        "Puede resultar difícil de leer. Excel conserva el tamaño de las celdas.\n\n¿Desea continuar con el PDF?", parent=self.master):
                    return
            else:
                # Comprobar dependencia antes de abrir el selector de archivo.
                import openpyxl  # noqa: F401
            title, file_type = ("PDF", "*.pdf") if kind == "pdf" else ("Excel", "*.xlsx")
            target = filedialog.asksaveasfilename(parent=self.master, title=f"Guardar {title}", defaultextension=f".{kind}",
                initialfile=f"cpu_scheduler.{kind}", filetypes=[(title, file_type)])
            if not target:
                return
            (export_pdf if kind == "pdf" else export_excel)(target, data)
        except ImportError:
            package = "reportlab" if kind == "pdf" else "openpyxl"
            messagebox.showerror("Falta una biblioteca de exportación",
                f"Para esta exportación, instale {package} en el entorno de la aplicación:\n\npython -m pip install -r requirements.txt", parent=self.master)
            return
        except (OSError, ValueError) as error:
            messagebox.showerror("No se puede exportar", str(error), parent=self.master)
            return
        self.status_var.set(f"Exportación {title} completada.")
        messagebox.showinfo("Exportación completada", f"Archivo guardado:\n{target}", parent=self.master)

    def open_link(self, url: str) -> None:
        try:
            opened = webbrowser.open(url, new=2)
        except webbrowser.Error:
            opened = False
        if not opened:
            messagebox.showinfo("Abrir enlace", f"Abra este enlace en su navegador:\n{url}", parent=self.master)

    def show_about(self) -> None:
        if existing_dialog(self, "_about_dialog") is not None:
            return
        dialog = tk.Toplevel(self.master)
        remember_dialog(self, "_about_dialog", dialog)
        dialog.title(f"Acerca de {APP_NAME}")
        dialog.resizable(False, False)
        dialog.transient(self.master)
        content = ttk.Frame(dialog, padding=22)
        content.pack(fill="both", expand=True)
        ttk.Label(content, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(content, text=f"Planificador interactivo de procesos · Versión {VERSION}").pack(anchor="w", pady=(4, 14))
        ttk.Label(content, text=f"© {COPYRIGHT_YEAR} {AUTHOR}").pack(anchor="w")
        ttk.Label(content, text="Universidad de Castilla-La Mancha\nRecurso educativo para estudiar la planificación de CPU.").pack(anchor="w", pady=10)
        ttk.Label(content, text=f"Código: licencia {CODE_LICENSE}\nMateriales educativos: {CONTENT_LICENSE} (Creative Commons Atribución)").pack(anchor="w", pady=(0, 10))
        license_row = ttk.Frame(content)
        license_row.pack(anchor="w", pady=(0, 10))
        badge = tk.Canvas(license_row, width=38, height=30, highlightthickness=0, bg="#f0f0f0")
        badge.pack(side="left", padx=(0, 8))
        badge.create_oval(4, 2, 32, 28, width=2, outline="#202020")
        badge.create_text(18, 15, text="CC", font=("TkDefaultFont", 9, "bold"), fill="#202020")
        ttk.Label(license_row, text="BY 4.0 · Atribución de los materiales educativos").pack(side="left")
        for label, url in (("GitHub CPU Scheduler", REPOSITORY_URL), ("Consultar CC BY 4.0", CONTENT_LICENSE_URL)):
            ttk.Button(content, text=label, command=lambda url=url: self.open_link(url)).pack(anchor="w", pady=3)
        ttk.Button(content, text="Licencias de la aplicación…",
                   command=self.show_licenses).pack(anchor="w", pady=3)
        close = ttk.Button(content, text="Cerrar", command=dialog.destroy)
        close.pack(anchor="e", pady=(14, 0))
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        dialog.bind("<Return>", lambda _event: dialog.destroy())
        present_dialog(dialog, close)


    def show_licenses(self) -> None:
        from .licensing import license_text
        if existing_dialog(self, "_licenses_dialog") is not None:
            return
        notices = license_text()
        dialog = tk.Toplevel(self.master)
        remember_dialog(self, "_licenses_dialog", dialog)
        dialog.title("Licencias de CPU Scheduler")
        dialog.geometry("800x540")
        dialog.transient(self.master)
        content = ttk.Frame(dialog, padding=12)
        content.pack(fill="both", expand=True)
        body = ttk.Frame(content)
        body.pack(fill="both", expand=True)
        text = tk.Text(body, wrap="word", bg="#f0f0f0", fg="#202020")
        scroll = ttk.Scrollbar(body, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(fill="both", expand=True)
        text.insert("1.0", notices)
        text.configure(state="disabled")
        close = ttk.Button(content, text="Cerrar", command=dialog.destroy)
        close.pack(anchor="e", pady=(8, 0))
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        present_dialog(dialog, close)
