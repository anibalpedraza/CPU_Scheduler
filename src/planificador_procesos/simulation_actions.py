"""Acciones de Archivo para conservar y retomar una simulación."""
from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

from .core import SUPPORTED_ALGORITHMS, simulate
from .persistence import SimulationDocument, document_from_dict, load_simulation, save_simulation


class SimulationActions:
    def _initialize_document(self) -> None:
        self.current_file: Path | None = None
        self._saved_state = self._document_state()
        for variable in (self.process_id_var, self.arrival_var, self.duration_var):
            variable.trace_add("write", lambda *_args: self._update_document_title())
        self.master.protocol("WM_DELETE_WINDOW", self.close_application)
        self._update_document_title()

    def _document_state(self) -> tuple:
        return (
            self.algorithm_var.get(), self.quantum_var.get(), self.core_count_var.get(),
            tuple(tuple(self.process_table.item(item, "values")) for item in self.process_table.get_children()),
            self.process_id_var.get(), self.arrival_var.get(), self.duration_var.get(),
            self.last_result is not None,
        )

    def _is_modified(self) -> bool:
        return hasattr(self, "_saved_state") and self._document_state() != self._saved_state

    def _update_document_title(self) -> None:
        if not hasattr(self, "_saved_state"):
            return
        name = self.current_file.name if self.current_file else "Sin título"
        prefix = "* " if self._is_modified() else ""
        self.master.title(f"{prefix}{name} · Planificador interactivo de procesos")

    def _confirm_save_changes(self) -> bool:
        if not self._is_modified():
            return True
        answer = messagebox.askyesnocancel("Cambios sin guardar",
            "La simulación tiene cambios sin guardar.\n¿Desea guardarlos antes de continuar?", parent=self.master)
        if answer is None:
            return False
        return self.save_document() if answer else True

    def new_simulation(self) -> bool:
        if not self._confirm_save_changes():
            return False
        self.reset_all()
        self.algorithm_var.set(SUPPORTED_ALGORITHMS[0])
        self.quantum_var.set("2")
        self.core_count_var.set("1")
        self._on_algorithm_change()
        self.timeline_canvas.xview_moveto(0)
        self.timeline_canvas.yview_moveto(0)
        self.current_file = None
        self._saved_state = self._document_state()
        self._update_document_title()
        self.status_var.set("Nueva simulación. Añada procesos y seleccione un algoritmo.")
        return True

    def _simulation_document(self) -> SimulationDocument:
        try:
            quantum = int(self.quantum_var.get())
            cores = int(self.core_count_var.get())
        except ValueError as error:
            raise ValueError("El quantum y el número de núcleos deben ser enteros mayores que cero.") from error
        return SimulationDocument(tuple(self._read_processes()), self.algorithm_var.get(), quantum,
                                  cores, self.last_result is not None,
                                  (self.process_id_var.get(), self.arrival_var.get(), self.duration_var.get()))

    def save_document(self, *, save_as: bool = False) -> bool:
        try:
            document = self._simulation_document()
            # Validar antes de solicitar un destino o reemplazar un archivo.
            document_from_dict(document.to_dict())
            target = self.current_file
            if save_as or target is None:
                options = {"parent": self.master, "title": "Guardar simulación como",
                           "defaultextension": ".json", "filetypes": [("Simulación CPU Scheduler", "*.json")],
                           "initialfile": target.name if target else "cpu_scheduler.json"}
                if target is not None:
                    options["initialdir"] = str(target.parent)
                selected = filedialog.asksaveasfilename(**options)
                if not selected:
                    return False
                target = Path(selected)
            save_simulation(target, document)
        except (OSError, ValueError) as error:
            messagebox.showerror("No se puede guardar la simulación", str(error), parent=self.master)
            return False
        self.current_file = target
        self._saved_state = self._document_state()
        self._update_document_title()
        self.status_var.set(f"Simulación guardada: {target.name}")
        return True

    def open_document(self) -> bool:
        selected = filedialog.askopenfilename(parent=self.master, title="Abrir simulación",
            filetypes=[("Simulación CPU Scheduler", "*.json"), ("Todos los archivos", "*.*")])
        if not selected:
            return False
        target = Path(selected)
        try:
            document = load_simulation(target)
            if not self._confirm_save_changes():
                return False
            # Guardar en el aviso puede haber actualizado el mismo archivo elegido.
            if self.current_file is not None and self.current_file.resolve() == target.resolve():
                document = load_simulation(target)
            # Preparar los resultados antes de sustituir el estado de la ventana.
            result = simulate(document.processes, document.algorithm, quantum=document.quantum,
                              core_count=document.core_count) if document.calculated else None
        except (OSError, ValueError) as error:
            messagebox.showerror("No se puede abrir la simulación", str(error), parent=self.master)
            return False
        self.reset_all()
        self.algorithm_var.set(document.algorithm)
        self.quantum_var.set(str(document.quantum))
        self.core_count_var.set(str(document.core_count))
        for process in document.processes:
            self.process_table.insert("", "end", values=(process.process_id, process.arrival_time, process.duration_time))
        if result is not None:
            self._show_result(result, list(document.processes))
        self.process_id_var.set(document.draft[0])
        self.arrival_var.set(document.draft[1])
        self.duration_var.set(document.draft[2])
        self.timeline_canvas.xview_moveto(0)
        self.timeline_canvas.yview_moveto(0)
        self.current_file = target
        self._saved_state = self._document_state()
        self._update_document_title()
        if result is None:
            self.status_var.set(f"Simulación abierta: {target.name}. Calcule la planificación cuando lo desee.")
        return True

    def close_application(self) -> bool:
        if not self._confirm_save_changes():
            return False
        self.master.destroy()
        return True

    def _file_shortcut(self, action):
        self.master.after(0, action)
        return "break"
