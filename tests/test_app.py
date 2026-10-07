import tkinter as tk
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


if __name__ == "__main__":
    unittest.main()
