"""Interfaz Tkinter del simulador educativo."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .core import Process, SUPPORTED_ALGORITHMS, SimulationResult, simulate


EXAMPLE_PROCESSES = (
    Process("P1", 0, 6),
    Process("P2", 1, 3),
    Process("P3", 2, 1),
)


class SchedulerApp(ttk.Frame):
    """Ventana principal y coordinación entre formularios, motor y resultados."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=12)
        self.master = master
        self.pack(fill="both", expand=True)
        self._configure_window()
        self._build_controls()
        self._build_process_table()
        self._build_result_area()

    def _configure_window(self) -> None:
        self.master.title("Planificador interactivo de procesos")
        self.master.minsize(920, 680)
        self.master.geometry("1100x760")
        style = ttk.Style(self.master)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("TkDefaultFont", 16, "bold"))
        style.configure("Subtitle.TLabel", foreground="#444444")

    def _build_controls(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Planificador interactivo de procesos", style="Title.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            header,
            text="Compare FCFS, SJF, SRTF y Round Robin con una misma carga.",
            style="Subtitle.TLabel",
        ).pack(anchor="w")

        controls = ttk.LabelFrame(self, text="Configuración", padding=10)
        controls.pack(fill="x")

        ttk.Label(controls, text="Algoritmo").grid(row=0, column=0, sticky="w")
        self.algorithm_var = tk.StringVar(value=SUPPORTED_ALGORITHMS[0])
        self.algorithm_selector = ttk.Combobox(
            controls,
            textvariable=self.algorithm_var,
            values=SUPPORTED_ALGORITHMS,
            state="readonly",
            width=18,
        )
        self.algorithm_selector.grid(row=1, column=0, padx=(0, 12), sticky="ew")
        self.algorithm_selector.bind("<<ComboboxSelected>>", self._on_algorithm_change)

        ttk.Label(controls, text="Quantum").grid(row=0, column=1, sticky="w")
        self.quantum_var = tk.StringVar(value="2")
        self.quantum_entry = ttk.Entry(controls, textvariable=self.quantum_var, width=10)
        self.quantum_entry.grid(row=1, column=1, padx=(0, 18), sticky="ew")
        self.quantum_entry.state(["disabled"])

        ttk.Label(controls, text="ID").grid(row=0, column=2, sticky="w")
        ttk.Label(controls, text="Llegada").grid(row=0, column=3, sticky="w")
        ttk.Label(controls, text="Duración").grid(row=0, column=4, sticky="w")
        self.process_id_var = tk.StringVar()
        self.arrival_var = tk.StringVar(value="0")
        self.duration_var = tk.StringVar(value="1")
        ttk.Entry(controls, textvariable=self.process_id_var, width=12).grid(
            row=1, column=2, padx=(0, 8), sticky="ew"
        )
        ttk.Entry(controls, textvariable=self.arrival_var, width=10).grid(
            row=1, column=3, padx=(0, 8), sticky="ew"
        )
        duration_entry = ttk.Entry(controls, textvariable=self.duration_var, width=10)
        duration_entry.grid(row=1, column=4, padx=(0, 8), sticky="ew")
        duration_entry.bind("<Return>", lambda _event: self.add_process())

        ttk.Button(controls, text="Añadir proceso", command=self.add_process).grid(
            row=1, column=5, padx=(4, 0)
        )
        ttk.Button(controls, text="Cargar ejemplo", command=self.load_example).grid(
            row=1, column=6, padx=(8, 0)
        )

        for column in range(7):
            controls.grid_columnconfigure(column, weight=1 if column in (0, 2, 3, 4) else 0)

    def _build_process_table(self) -> None:
        section = ttk.LabelFrame(self, text="Procesos", padding=8)
        section.pack(fill="x", pady=10)
        columns = ("id", "arrival", "duration")
        self.process_table = ttk.Treeview(section, columns=columns, show="headings", height=5)
        self.process_table.heading("id", text="Proceso")
        self.process_table.heading("arrival", text="Llegada")
        self.process_table.heading("duration", text="Duración")
        self.process_table.column("id", width=180, anchor="center")
        self.process_table.column("arrival", width=120, anchor="center")
        self.process_table.column("duration", width=120, anchor="center")
        self.process_table.pack(side="left", fill="x", expand=True)

        actions = ttk.Frame(section)
        actions.pack(side="right", fill="y", padx=(8, 0))
        ttk.Button(actions, text="Eliminar seleccionado", command=self.remove_selected).pack(
            fill="x", pady=(0, 6)
        )
        ttk.Button(actions, text="Vaciar", command=self.reset_all).pack(fill="x")

    def _build_result_area(self) -> None:
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(0, 8))
        ttk.Button(actions, text="Calcular planificación", command=self.calculate).pack(side="left")
        ttk.Button(actions, text="Limpiar resultados", command=self.clear_results).pack(
            side="left", padx=8
        )
        self.status_var = tk.StringVar(value="Añada procesos y seleccione un algoritmo.")
        ttk.Label(actions, textvariable=self.status_var).pack(side="right")

        results = ttk.LabelFrame(self, text="Resultados", padding=8)
        results.pack(fill="x")
        columns = ("id", "arrival", "duration", "completed", "waiting", "turnaround")
        self.result_table = ttk.Treeview(results, columns=columns, show="headings", height=5)
        headings = {
            "id": "Proceso",
            "arrival": "Llegada",
            "duration": "Duración",
            "completed": "Finalización",
            "waiting": "Espera",
            "turnaround": "Retorno",
        }
        for column, label in headings.items():
            self.result_table.heading(column, text=label)
            self.result_table.column(column, width=115, anchor="center")
        self.result_table.pack(fill="x")

        metrics = ttk.Frame(results)
        metrics.pack(fill="x", pady=(8, 0))
        self.average_waiting_var = tk.StringVar(value="—")
        self.average_turnaround_var = tk.StringVar(value="—")
        ttk.Label(metrics, text="Espera media:").pack(side="left")
        ttk.Label(metrics, textvariable=self.average_waiting_var).pack(side="left", padx=(4, 24))
        ttk.Label(metrics, text="Retorno medio:").pack(side="left")
        ttk.Label(metrics, textvariable=self.average_turnaround_var).pack(side="left", padx=4)

        timeline = ttk.LabelFrame(self, text="Tabla de ciclos · X: ejecuta · O: espera", padding=8)
        timeline.pack(fill="both", expand=True, pady=(10, 0))
        self.timeline_canvas = tk.Canvas(timeline, highlightthickness=0)
        horizontal = ttk.Scrollbar(
            timeline, orient="horizontal", command=self.timeline_canvas.xview
        )
        vertical = ttk.Scrollbar(timeline, orient="vertical", command=self.timeline_canvas.yview)
        self.timeline_canvas.configure(
            xscrollcommand=horizontal.set,
            yscrollcommand=vertical.set,
        )
        self.timeline_canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        timeline.grid_rowconfigure(0, weight=1)
        timeline.grid_columnconfigure(0, weight=1)
        self.timeline_grid = ttk.Frame(self.timeline_canvas)
        self.timeline_window = self.timeline_canvas.create_window(
            (0, 0), window=self.timeline_grid, anchor="nw"
        )
        self.timeline_grid.bind("<Configure>", self._update_scroll_region)

    def _on_algorithm_change(self, _event: object | None = None) -> None:
        if self.algorithm_var.get() == "Round Robin":
            self.quantum_entry.state(["!disabled"])
        else:
            self.quantum_entry.state(["disabled"])

    def add_process(self) -> None:
        try:
            process = Process(
                self.process_id_var.get(),
                int(self.arrival_var.get()),
                int(self.duration_var.get()),
            )
            existing = {
                str(self.process_table.item(item_id, "values")[0])
                for item_id in self.process_table.get_children()
            }
            if process.process_id in existing:
                raise ValueError("Ya existe un proceso con ese identificador.")
        except ValueError as error:
            messagebox.showerror("Datos no válidos", str(error), parent=self.master)
            return

        self.process_table.insert(
            "",
            "end",
            values=(process.process_id, process.arrival_time, process.duration_time),
        )
        self.process_id_var.set("")
        self.process_id_var.set(f"P{len(self.process_table.get_children()) + 1}")

    def remove_selected(self) -> None:
        selected = self.process_table.selection()
        if not selected:
            messagebox.showinfo("Procesos", "Seleccione al menos un proceso.", parent=self.master)
            return
        for item_id in selected:
            self.process_table.delete(item_id)
        self.clear_results()

    def load_example(self) -> None:
        self.reset_all()
        for process in EXAMPLE_PROCESSES:
            self.process_table.insert(
                "",
                "end",
                values=(process.process_id, process.arrival_time, process.duration_time),
            )
        self.process_id_var.set("P4")
        self.status_var.set("Ejemplo cargado. Pruebe los cuatro algoritmos.")

    def _read_processes(self) -> list[Process]:
        return [
            Process(str(values[0]), int(values[1]), int(values[2]))
            for item_id in self.process_table.get_children()
            for values in (self.process_table.item(item_id, "values"),)
        ]

    def calculate(self) -> None:
        try:
            processes = self._read_processes()
            if not processes:
                raise ValueError("Añada al menos un proceso.")
            quantum = None
            if self.algorithm_var.get() == "Round Robin":
                quantum = int(self.quantum_var.get())
            result = simulate(processes, self.algorithm_var.get(), quantum=quantum)
        except ValueError as error:
            messagebox.showerror("No se puede calcular", str(error), parent=self.master)
            return
        self._show_result(result, processes)

    def _show_result(self, result: SimulationResult, processes: list[Process]) -> None:
        self.clear_results()
        for item in result.processes:
            self.result_table.insert(
                "",
                "end",
                values=(
                    item.process_id,
                    item.arrival_time,
                    item.duration_time,
                    item.completed_time,
                    item.waiting_time,
                    item.turnaround_time,
                ),
            )
        self.average_waiting_var.set(f"{result.average_waiting_time:.2f}")
        self.average_turnaround_var.set(f"{result.average_turnaround_time:.2f}")
        self.status_var.set(f"{result.algorithm} · {len(result.processes)} procesos")
        self._render_timeline(result, processes)

    def _render_timeline(self, result: SimulationResult, processes: list[Process]) -> None:
        process_map = {item.process_id: item for item in processes}
        ttk.Label(self.timeline_grid, text=result.algorithm, width=14, anchor="w").grid(
            row=0, column=0, sticky="nsew"
        )
        for cycle in range(1, result.makespan + 1):
            ttk.Label(self.timeline_grid, text=str(cycle), width=3, anchor="center").grid(
                row=0, column=cycle, sticky="nsew"
            )
        for row, (process_id, cells) in enumerate(result.timeline.items(), start=1):
            arrival = process_map[process_id].arrival_time
            name = tk.Label(
                self.timeline_grid,
                text=process_id,
                width=14,
                anchor="w",
                relief="groove",
                bg="#d9d9d9" if arrival == 0 else "SystemButtonFace",
            )
            name.grid(row=row, column=0, sticky="nsew")
            for cycle in range(1, result.makespan + 1):
                value = cells[cycle - 1] if cycle - 1 < len(cells) else ""
                cell = tk.Label(
                    self.timeline_grid,
                    text=value,
                    width=3,
                    relief="groove",
                    bg="#d9d9d9" if arrival == cycle else "SystemButtonFace",
                )
                cell.grid(row=row, column=cycle, sticky="nsew")

    def clear_results(self) -> None:
        for item_id in self.result_table.get_children():
            self.result_table.delete(item_id)
        for widget in self.timeline_grid.winfo_children():
            widget.destroy()
        self.average_waiting_var.set("—")
        self.average_turnaround_var.set("—")
        self.status_var.set("Resultados limpiados.")

    def reset_all(self) -> None:
        for item_id in self.process_table.get_children():
            self.process_table.delete(item_id)
        self.clear_results()
        self.process_id_var.set("P1")
        self.arrival_var.set("0")
        self.duration_var.set("1")

    def _update_scroll_region(self, _event: object | None = None) -> None:
        self.timeline_canvas.configure(scrollregion=self.timeline_canvas.bbox("all"))


def main() -> None:
    root = tk.Tk()
    SchedulerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
