"""Comprobaciones del formato de simulación y las acciones de Archivo."""
import json
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from planificador_procesos.app import SchedulerApp
from planificador_procesos.core import Process, simulate
from planificador_procesos.persistence import (SimulationDocument, document_from_dict,
                                             load_simulation, save_simulation)


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "simulation.json"
        self.document = SimulationDocument((Process("Á;\n=1", 0, 6), Process("001", 1, 3)),
                                            "Round Robin", 3, 2, True, ("C", "", "pending"))

    def test_round_trip_preserves_unicode_order_configuration_and_incomplete_form(self):
        save_simulation(self.path, self.document)
        self.assertEqual(load_simulation(self.path), self.document)
        self.assertIn("Á", self.path.read_text(encoding="utf-8"))
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(raw["version"], 1)
        self.assertNotIn("results", raw)

    def test_empty_simulation_can_be_saved_and_loaded(self):
        document = SimulationDocument(())
        save_simulation(self.path, document)
        self.assertEqual(load_simulation(self.path), document)

    def test_invalid_documents_are_rejected(self):
        variants = [None, [], {}, {**self.document.to_dict(), "version": 2},
                    {**self.document.to_dict(), "version": True},
                    {**self.document.to_dict(), "format": "other"},
                    {**self.document.to_dict(), "processes": [{"id": "A", "arrival": 0, "duration": 0}]},
                    {**self.document.to_dict(), "processes": [{"id": "A", "arrival": True, "duration": 1}]},
                    {**self.document.to_dict(), "processes": [{"id": "A", "arrival": 0, "duration": 1}] * 2},
                    {**self.document.to_dict(), "settings": {"algorithm": "other", "quantum": 2, "core_count": 1}},
                    {**self.document.to_dict(), "settings": {"algorithm": "FCFS", "quantum": 0, "core_count": 1}},
                    {**self.document.to_dict(), "calculated": "yes"},
                    {**self.document.to_dict(), "processes": []},
                    {**self.document.to_dict(), "draft": {"id": 1, "arrival": "0", "duration": "1"}}]
        for raw in variants:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                document_from_dict(raw)

    def test_malformed_json_and_wrong_encoding_are_rejected(self):
        for raw in (b'{"format":', b'\xff\xfeinvalid'):
            self.path.write_bytes(raw)
            with self.assertRaises(ValueError):
                load_simulation(self.path)

    def test_failed_save_does_not_destroy_existing_file(self):
        self.path.write_text("original", encoding="utf-8")
        with patch("planificador_procesos.fileio.os.replace", side_effect=PermissionError("locked")):
            with self.assertRaises(PermissionError):
                save_simulation(self.path, self.document)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "original")
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])


class DocumentActionTests(unittest.TestCase):
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
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "first.json"
        self.app = SchedulerApp(self.root)
        self.app.load_example()

    def tearDown(self):
        self.app.destroy()

    def save_first(self):
        with patch("planificador_procesos.simulation_actions.filedialog.asksaveasfilename", return_value=str(self.path)):
            self.assertTrue(self.app.save_document())

    def test_save_then_save_updates_same_file_without_file_picker(self):
        self.save_first()
        self.assertFalse(self.app._is_modified())
        self.assertEqual(self.app.current_file, self.path)
        self.app.core_count_var.set("2")
        self.assertTrue(self.app._is_modified())
        self.assertTrue(self.root.title().startswith("* "))
        with patch("planificador_procesos.simulation_actions.filedialog.asksaveasfilename") as picker:
            self.assertTrue(self.app.save_document())
        picker.assert_not_called()
        self.assertEqual(load_simulation(self.path).core_count, 2)
        self.assertFalse(self.app._is_modified())
        self.assertFalse(self.root.title().startswith("* "))

    def test_save_as_switches_active_path_and_keeps_original(self):
        self.save_first()
        second = self.path.with_name("second.json")
        self.app.core_count_var.set("2")
        with patch("planificador_procesos.simulation_actions.filedialog.asksaveasfilename", return_value=str(second)):
            self.assertTrue(self.app.save_document(save_as=True))
        self.assertEqual(self.app.current_file, second)
        self.assertEqual(load_simulation(self.path).core_count, 1)
        self.assertEqual(load_simulation(second).core_count, 2)

    def test_open_restores_calculation_and_draft(self):
        processes = (Process("A", 0, 6), Process("B", 1, 3), Process("C", 2, 1))
        document = SimulationDocument(processes, "Round Robin", 2, 2, True, ("D", "", "5"))
        save_simulation(self.path, document)
        with patch("planificador_procesos.simulation_actions.filedialog.askopenfilename", return_value=str(self.path)), \
                patch("planificador_procesos.simulation_actions.messagebox.askyesnocancel", return_value=False):
            self.assertTrue(self.app.open_document())
        self.assertEqual(self.app.last_result, simulate(processes, "Round Robin", quantum=2, core_count=2))
        self.assertEqual(len(self.app.result_table.get_children()), 3)
        self.assertTrue(self.app.quantum_entry.instate(["!disabled"]))
        self.assertEqual(self.app.arrival_var.get(), "")
        self.assertEqual(self.app.current_file, self.path)
        self.assertFalse(self.app._is_modified())

    def test_open_active_file_after_saving_changes_reads_updated_content(self):
        self.save_first()
        self.app.core_count_var.set("2")
        with patch("planificador_procesos.simulation_actions.filedialog.askopenfilename", return_value=str(self.path)), \
                patch("planificador_procesos.simulation_actions.messagebox.askyesnocancel", return_value=True):
            self.assertTrue(self.app.open_document())
        self.assertEqual(self.app.core_count_var.get(), "2")
        self.assertEqual(load_simulation(self.path).core_count, 2)
        self.assertFalse(self.app._is_modified())

    def test_open_uncalculated_empty_document_clears_old_results(self):
        self.app.calculate()
        save_simulation(self.path, SimulationDocument((), "SJF", 4, 3))
        with patch("planificador_procesos.simulation_actions.filedialog.askopenfilename", return_value=str(self.path)), \
                patch("planificador_procesos.simulation_actions.messagebox.askyesnocancel", return_value=False):
            self.assertTrue(self.app.open_document())
        self.assertFalse(self.app.process_table.get_children())
        self.assertIsNone(self.app.last_result)
        self.assertEqual(self.app.core_count_var.get(), "3")
        self.assertFalse(self.app._is_modified())

    def test_invalid_open_keeps_current_simulation_and_path(self):
        self.save_first()
        self.app.calculate()
        before = self.app._document_state()
        previous_result = self.app.last_result
        broken = self.path.with_name("broken.json")
        broken.write_text("{}", encoding="utf-8")
        with patch("planificador_procesos.simulation_actions.filedialog.askopenfilename", return_value=str(broken)), \
                patch("planificador_procesos.simulation_actions.messagebox.showerror") as error, \
                patch("planificador_procesos.simulation_actions.messagebox.askyesnocancel") as confirm:
            self.assertFalse(self.app.open_document())
        error.assert_called_once()
        confirm.assert_not_called()
        self.assertEqual(self.app._document_state(), before)
        self.assertIs(self.app.last_result, previous_result)
        self.assertEqual(self.app.current_file, self.path)

    def test_cancel_save_as_keeps_active_file_and_dirty_state(self):
        self.save_first()
        self.app.core_count_var.set("3")
        with patch("planificador_procesos.simulation_actions.filedialog.asksaveasfilename", return_value=""):
            self.assertFalse(self.app.save_document(save_as=True))
        self.assertEqual(self.app.current_file, self.path)
        self.assertTrue(self.app._is_modified())
        self.assertEqual(load_simulation(self.path).core_count, 1)

    def test_new_cancel_and_discard(self):
        before = self.app._document_state()
        with patch("planificador_procesos.simulation_actions.messagebox.askyesnocancel", return_value=None):
            self.assertFalse(self.app.new_simulation())
        self.assertEqual(self.app._document_state(), before)
        with patch("planificador_procesos.simulation_actions.messagebox.askyesnocancel", return_value=False):
            self.assertTrue(self.app.new_simulation())
        self.assertIsNone(self.app.current_file)
        self.assertFalse(self.app._is_modified())
        self.assertFalse(self.app.process_table.get_children())

    def test_cancel_save_while_creating_new_keeps_work(self):
        before = self.app._document_state()
        with patch("planificador_procesos.simulation_actions.messagebox.askyesnocancel", return_value=True), \
                patch("planificador_procesos.simulation_actions.filedialog.asksaveasfilename", return_value=""):
            self.assertFalse(self.app.new_simulation())
        self.assertEqual(self.app._document_state(), before)

    def test_exit_waits_for_successful_save_and_cancellation_keeps_window(self):
        with patch.object(self.root, "destroy") as destroy, \
                patch("planificador_procesos.simulation_actions.messagebox.askyesnocancel", return_value=None):
            self.assertFalse(self.app.close_application())
            destroy.assert_not_called()
        with patch.object(self.root, "destroy") as destroy, \
                patch("planificador_procesos.simulation_actions.messagebox.askyesnocancel", return_value=True), \
                patch("planificador_procesos.simulation_actions.filedialog.asksaveasfilename", return_value=str(self.path)):
            self.assertTrue(self.app.close_application())
            destroy.assert_called_once()
        self.assertEqual(len(load_simulation(self.path).processes), 3)

    def test_failed_save_keeps_original_path_and_dirty_state(self):
        self.save_first()
        self.app.core_count_var.set("2")
        with patch("planificador_procesos.simulation_actions.save_simulation", side_effect=PermissionError("locked")), \
                patch("planificador_procesos.simulation_actions.messagebox.showerror"):
            self.assertFalse(self.app.save_document())
        self.assertTrue(self.app._is_modified())
        self.assertEqual(self.app.current_file, self.path)
        self.assertEqual(load_simulation(self.path).core_count, 1)


if __name__ == "__main__":
    unittest.main()
