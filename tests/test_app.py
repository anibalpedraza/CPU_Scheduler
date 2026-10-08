import tkinter as tk
import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from planificador_procesos.app import SchedulerApp


class SchedulerAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest(f"Tkinter no disponible: {error}") from error
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        discard = patch("planificador_procesos.simulation_actions.messagebox.askyesnocancel", return_value=False)
        discard.start()
        self.addCleanup(discard.stop)
        self.app = SchedulerApp(self.root)
        self.app.load_example()

    def tearDown(self):
        self.app.destroy()

    def test_multicore_calculation_and_cpu_rows_for_all_algorithms(self):
        self.app.core_count_var.set("2")
        for algorithm, completion in (
            ("FCFS", [6, 4, 5]), ("SJF", [6, 4, 5]),
            ("SRTF", [7, 4, 3]), ("Round Robin", [7, 4, 3]),
        ):
            with self.subTest(algorithm=algorithm):
                self.app.algorithm_var.set(algorithm)
                self.app._on_algorithm_change()
                self.app.calculate()
                values = [self.app.result_table.item(i, "values") for i in self.app.result_table.get_children()]
                self.assertEqual([int(row[3]) for row in values], completion)
                self.assertIn("2 núcleos", self.app.status_var.get())
                labels = [str(widget.cget("text")) for widget in self.app.timeline_grid.winfo_children()]
                self.assertEqual(labels.count("CPU 1"), 1)
                self.assertEqual(labels.count("CPU 2"), 1)
                self.assertNotIn("CPU 3", labels)
                self.assertEqual(self.app.quantum_entry.instate(["disabled"]), algorithm != "Round Robin")

    def test_switching_back_to_one_core_replaces_results(self):
        self.app.core_count_var.set("2")
        self.app.calculate()
        self.app.core_count_var.set("1")
        self.app.calculate()
        values = [self.app.result_table.item(i, "values") for i in self.app.result_table.get_children()]
        self.assertEqual([int(row[3]) for row in values], [6, 9, 10])
        self.assertIn("10 ciclos", self.app.status_var.get())
        labels = [str(widget.cget("text")) for widget in self.app.timeline_grid.winfo_children()]
        self.assertNotIn("CPU 2", labels)

    def test_invalid_core_count_shows_error_without_results(self):
        for value in ("0", "-2", "1.5", "abc"):
            with self.subTest(value=value), patch("planificador_procesos.app.messagebox.showerror") as error:
                self.app.core_count_var.set(value)
                self.app.calculate()
                error.assert_called_once()
                self.assertFalse(self.app.result_table.get_children())

    def test_clear_results_removes_cpu_rows_and_keeps_configuration(self):
        self.app.core_count_var.set("3")
        self.app.calculate()
        self.app.clear_results()
        self.assertFalse(self.app.timeline_grid.winfo_children())
        self.assertFalse(self.app.result_table.get_children())
        self.assertEqual(self.app.average_waiting_var.get(), "—")
        self.assertEqual(self.app.core_count_var.get(), "3")
        self.assertEqual(len(self.app.process_table.get_children()), 3)


    def test_new_simulation_restores_all_initial_settings(self):
        self.app.algorithm_var.set("Round Robin")
        self.app.quantum_var.set("3")
        self.app.core_count_var.set("2")
        self.app.calculate()
        self.app.new_simulation()
        self.assertFalse(self.app.process_table.get_children())
        self.assertFalse(self.app.result_table.get_children())
        self.assertFalse(self.app.timeline_grid.winfo_children())
        self.assertIsNone(self.app.last_result)
        self.assertEqual(self.app.algorithm_var.get(), "FCFS")
        self.assertEqual(self.app.quantum_var.get(), "2")
        self.assertEqual(self.app.core_count_var.get(), "1")
        self.assertEqual(self.app.process_id_var.get(), "A")
        self.assertTrue(self.app.quantum_entry.instate(["disabled"]))

    def test_changed_configuration_or_processes_invalidates_exportable_results(self):
        for variable, value in ((self.app.algorithm_var, "SRTF"),
                                (self.app.quantum_var, "3"), (self.app.core_count_var, "2")):
            self.app.calculate()
            variable.set(value)
            self.assertIsNone(self.app.last_result)
            self.assertFalse(self.app.result_table.get_children())
        self.app.calculate()
        self.app.add_process()
        self.assertIsNone(self.app.last_result)
        self.assertFalse(self.app.result_table.get_children())

    def test_paste_validates_whole_block_before_inserting(self):
        with patch.object(self.root, "clipboard_get", return_value="D\t0\t2\nA\t0\t1\n"), \
                patch("planificador_procesos.actions.messagebox.showerror") as error:
            self.app._paste_processes()
        error.assert_called_once()
        self.assertEqual(len(self.app.process_table.get_children()), 3)
        self.app.calculate()
        with patch.object(self.root, "clipboard_get", return_value="Proceso\tLlegada\tDuración\nD\t0\t2\nE\t2\t4\n"):
            self.app._paste_processes()
        self.assertEqual(len(self.app.process_table.get_children()), 5)
        self.assertEqual(self.app.process_id_var.get(), "F")
        self.assertIsNone(self.app.last_result)

    def test_copy_and_cut_process_rows_and_copy_results(self):
        selected = self.app.process_table.get_children()[0]
        self.app.process_table.selection_set(selected)
        with patch.object(self.root, "focus_get", return_value=self.app.process_table), \
                patch.object(self.root, "clipboard_clear"), patch.object(self.root, "clipboard_append") as clipboard:
            self.app.edit("copy")
            clipboard.assert_called_with("A\t0\t6\n")
            self.app.calculate()
            self.app.edit("cut")
        self.assertEqual(len(self.app.process_table.get_children()), 2)
        self.assertIsNone(self.app.last_result)
        self.app.calculate()
        selected = self.app.result_table.get_children()[0]
        self.app.result_table.selection_set(selected)
        with patch.object(self.root, "focus_get", return_value=self.app.result_table), \
                patch.object(self.root, "clipboard_clear"), patch.object(self.root, "clipboard_append") as clipboard:
            self.app.edit("copy")
            self.assertEqual(len(clipboard.call_args.args[0].strip().split("\t")), 6)
            self.app.edit("cut")
        self.assertEqual(len(self.app.result_table.get_children()), 2)

    def test_csv_dialog_exports_both_tables_to_distinct_files(self):
        self.app.calculate()
        callback_errors = []
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "simulation.csv"

            def invoke_export():
                dialogs = [widget for widget in self.root.winfo_children() if isinstance(widget, tk.Toplevel)]
                try:
                    def descendants(widget):
                        for child in widget.winfo_children():
                            yield child
                            yield from descendants(child)
                    button = next(widget for widget in descendants(dialogs[-1])
                                  if isinstance(widget, tk.ttk.Button) and widget.cget("text") == "Exportar…")
                    button.invoke()
                except Exception as error:
                    callback_errors.append(error)
                finally:
                    for dialog in dialogs:
                        if dialog.winfo_exists():
                            dialog.destroy()

            with patch("planificador_procesos.actions.filedialog.asksaveasfilename", return_value=str(target)), \
                    patch("planificador_procesos.actions.messagebox.showinfo"):
                self.app.export_csv_dialog()
                invoke_export()
            self.assertFalse(callback_errors, str(callback_errors))
            paths = sorted(Path(directory).glob("*.csv"))
            self.assertEqual([path.name for path in paths], ["simulation_procesos.csv", "simulation_resultados.csv"])
            for path, width in zip(paths, (3, 6)):
                with path.open(encoding="utf-8-sig", newline="") as stream:
                    rows = list(csv.reader(stream, delimiter=";"))
                self.assertEqual(len(rows[3]), width)

    def test_report_cancel_does_not_export_or_change_result(self):
        self.app.calculate()
        previous = self.app.last_result
        with patch("planificador_procesos.actions.filedialog.asksaveasfilename", return_value=""), \
                patch("planificador_procesos.actions.export_pdf") as export:
            self.app.export_report("pdf")
        export.assert_not_called()
        self.assertIs(self.app.last_result, previous)


if __name__ == "__main__":
    unittest.main()
