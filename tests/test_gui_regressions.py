"""Regresiones de contraste y ventanas emergentes en macOS y Windows."""
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import patch

from planificador_procesos.app import SchedulerApp


def contrast(widget, foreground, background):
    def luminance(color):
        channels = [value / 65535 for value in widget.winfo_rgb(color)]
        linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
                  for value in channels]
        return sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
    low, high = sorted((luminance(foreground), luminance(background)))
    return (high + 0.05) / (low + 0.05)


class GuiRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest(str(error)) from error
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.app = SchedulerApp(self.root)
        self.app.load_example()

    def tearDown(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()
        self.app.destroy()
        self.root.option_clear()
        self.root.withdraw()
        self.root.update()


    def test_license_window_has_text_and_reuses_window_without_grab(self):
        self.root.deiconify()
        self.app.show_licenses()
        dialog = self.app._licenses_dialog
        self.root.update()
        self.app.show_licenses()
        self.assertIs(self.app._licenses_dialog, dialog)
        self.assertTrue(dialog.winfo_ismapped())
        self.assertIsNone(self.root.grab_current())
        body = next(child for frame in dialog.winfo_children()
                    for inner in frame.winfo_children() for child in inner.winfo_children()
                    if isinstance(child, tk.Text))
        self.assertIn("MIT License", body.get("1.0", "end"))
        dialog.destroy()
        self.root.update()
        self.assertIsNone(self.app._licenses_dialog)

    def test_cycle_and_cpu_cells_remain_readable_with_white_default_text(self):
        self.root.option_add("*Label.foreground", "#ffffff")
        self.root.option_add("*Label.background", "#303030")
        for cores in (1, 4):
            with self.subTest(cores=cores):
                self.app.core_count_var.set(str(cores))
                self.app.calculate()
                cells = [widget for widget in self.app.timeline_grid.winfo_children()
                         if isinstance(widget, tk.Label)]
                self.assertTrue(cells)
                for cell in cells:
                    self.assertGreaterEqual(contrast(cell, cell.cget("fg"), cell.cget("bg")), 4.5,
                                            f"Texto ilegible: {cell.cget('text')!r}")

    def test_about_and_csv_return_without_a_nested_event_loop(self):
        self.app.calculate()
        with patch.object(tk.Toplevel, "wait_window", side_effect=AssertionError("Espera dentro del callback")), \
                patch.object(tk.Toplevel, "wait_visibility", side_effect=AssertionError("Espera de visibilidad")):
            self.app.show_about()
            self.app.export_csv_dialog()
        dialogs = [widget for widget in self.root.winfo_children() if isinstance(widget, tk.Toplevel)]
        self.assertEqual(len(dialogs), 2)
        self.assertIsNone(self.root.grab_current())  # No se captura una ventana aún sin mapear.

    def test_file_menu_returns_before_opening_a_native_dialog(self):
        menu = self.root.nametowidget(self.app.menu_bar.entrycget("Archivo", "menu"))
        with patch("planificador_procesos.simulation_actions.filedialog.askopenfilename", return_value="") as picker:
            menu.invoke("Abrir…")
            picker.assert_not_called()
            self.root.update()
            picker.assert_called_once()

    def test_about_can_reopen_without_duplicates_or_grabbing_the_main_window(self):
        self.root.deiconify()
        for _ in range(3):
            self.app.show_about()
            dialog = self.app._about_dialog
            self.app.show_about()
            self.assertIs(self.app._about_dialog, dialog)
            self.root.update()
            self.assertTrue(dialog.winfo_ismapped())
            self.assertIsNone(self.root.grab_current())
            pulse = []
            self.root.after(0, lambda: pulse.append(True))
            self.root.update()
            self.assertEqual(pulse, [True])
            self.root.tk.call(dialog.protocol("WM_DELETE_WINDOW"))
            self.assertIsNone(self.app._about_dialog)
        self.app.calculate()
        self.assertIsNotNone(self.app.last_result)

    def test_save_and_report_menus_defer_their_native_file_pickers(self):
        self.app.calculate()
        file_menu = self.root.nametowidget(self.app.menu_bar.entrycget("Archivo", "menu"))
        exports = self.root.nametowidget(file_menu.entrycget("Exportar", "menu"))
        for menu, label in ((file_menu, "Guardar"), (file_menu, "Guardar como…"),
                            (exports, "PDF…"), (exports, "Excel…")):
            with self.subTest(action=label), \
                    patch("planificador_procesos.simulation_actions.filedialog.asksaveasfilename", return_value="") as picker:
                menu.invoke(label)
                picker.assert_not_called()
                self.root.update()
                picker.assert_called_once()

    def test_file_shortcuts_return_before_the_action_runs(self):
        calls = []
        self.assertEqual(self.app._file_shortcut(lambda: calls.append(True)), "break")
        self.assertEqual(calls, [])
        self.root.update()
        self.assertEqual(calls, [True])

    def test_csv_captures_only_a_visible_window_and_releases_on_close(self):
        self.root.deiconify()
        self.app.calculate()
        for _ in range(3):
            self.app.export_csv_dialog()
            dialog = self.app._csv_dialog
            self.app.export_csv_dialog()
            self.assertIs(self.app._csv_dialog, dialog)
            self.root.update()
            self.assertTrue(dialog.winfo_ismapped())
            self.assertIs(self.root.grab_current(), dialog)
            pulse = []
            self.root.after(0, lambda: pulse.append(True))
            self.root.update()
            self.assertEqual(pulse, [True])
            self.root.tk.call(dialog.protocol("WM_DELETE_WINDOW"))
            self.assertIsNone(self.root.grab_current())
            self.assertIsNone(self.app._csv_dialog)

    def test_dialog_can_close_before_mapping_without_a_pending_focus_callback(self):
        for show, attribute in ((self.app.show_about, "_about_dialog"),
                                (self.app.export_csv_dialog, "_csv_dialog")):
            show()
            getattr(self.app, attribute).destroy()
            self.root.update()
            self.assertIsNone(getattr(self.app, attribute))
        self.assertIsNone(self.root.grab_current())

    def test_license_badge_remains_readable_with_a_dark_default_canvas(self):
        self.root.option_add("*Canvas.background", "#303030")
        self.app.show_about()
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        badge = next(widget for widget in descendants(self.app._about_dialog) if isinstance(widget, tk.Canvas))
        for item in badge.find_all():
            foreground = badge.itemcget(item, "fill" if badge.type(item) == "text" else "outline")
            self.assertGreaterEqual(contrast(badge, foreground, badge.cget("bg")), 4.5)

    def test_about_closes_with_escape_and_return_and_csv_with_escape(self):
        self.root.deiconify()
        for show, attribute, key in ((self.app.show_about, "_about_dialog", "Escape"),
                                     (self.app.show_about, "_about_dialog", "Return"),
                                     (self.app.export_csv_dialog, "_csv_dialog", "Escape")):
            with self.subTest(dialog=attribute, key=key):
                show()
                dialog = getattr(self.app, attribute)
                self.root.update()
                dialog.focus_force()
                self.root.update()
                dialog.event_generate(f"<KeyPress-{key}>")
                self.root.update()
                self.assertIsNone(getattr(self.app, attribute))
                self.assertIsNone(self.root.grab_current())


if __name__ == "__main__":
    unittest.main()
