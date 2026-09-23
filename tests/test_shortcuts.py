"""Run with python -m unittest discover -s tests (Tk display required)."""
import tkinter as tk
from tkinter import ttk
import unittest
from unittest.mock import Mock, patch

from appforge import ChocoApp, KeyboardShortcuts, WingetApp


class ShortcutTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.managers = ttk.Notebook(self.root)
        self.apps = []
        mapping = {}
        for app_type in (WingetApp, ChocoApp):
            frame = ttk.Frame(self.managers)
            self.managers.add(frame, text=app_type.__name__)
            # Construct real tabs, entries and buttons without package commands.
            for name in ('_load_browse', '_load_installed', '_load_updates',
                         '_load_sources', '_load_settings_info'):
                patcher = patch.object(app_type, name)
                patcher.start()
                self.addCleanup(patcher.stop)
            app = app_type(frame)
            self.apps.append(app)
            mapping[str(frame)] = app
        for title in ('Setup', 'About'):
            self.managers.add(ttk.Frame(self.managers), text=title)
        self.shortcuts = KeyboardShortcuts(self.root, self.managers, mapping)

    def test_search_selects_text_in_active_manager_and_tab(self):
        for manager, app in enumerate(self.apps):
            self.managers.select(manager)
            for index, entry in enumerate((app.browse_search_entry, app.inst_search_entry)):
                app.notebook.select(index)
                entry.insert(0, 'sample query')
                with patch.object(entry, 'focus_set') as focus:
                    self.assertEqual(self.shortcuts.focus_search(), 'break')
                    focus.assert_called_once_with()
                self.assertEqual(entry.index('sel.first'), 0)
                self.assertEqual(entry.index('sel.last'), len('sample query'))
                self.assertEqual(entry.index(tk.INSERT), len('sample query'))

    def test_refresh_invokes_only_active_button_and_honors_disabled_state(self):
        callbacks = []
        for app in self.apps:
            for button in (app.browse_refresh_btn, app.inst_refresh_btn,
                           app.upd_refresh_btn, app.src_refresh_btn):
                callback = Mock()
                button.configure(command=callback)
                callbacks.append((button, callback))
        for manager, app in enumerate(self.apps):
            self.managers.select(manager)
            for index in range(4):
                app.notebook.select(index)
                target, callback = callbacks[manager * 4 + index]
                self.assertEqual(self.shortcuts.refresh(), 'break')
                callback.assert_called_once_with()
                target.state(['disabled'])
                self.shortcuts.refresh()
                callback.assert_called_once_with()
                target.state(['!disabled'])
                callback.reset_mock()
                self.assertTrue(all(not cb.called for _, cb in callbacks))

    def test_tabs_without_search_or_refresh_are_unchanged(self):
        for manager, app in enumerate(self.apps):
            self.managers.select(manager)
            for index in (2, 3, 4):
                app.notebook.select(index)
                self.assertIsNone(self.shortcuts.focus_search())
            self.assertIsNone(self.shortcuts.refresh())
            self.assertEqual(app.notebook.index('current'), 4)
        for index in (2, 3):
            self.managers.select(index)
            self.assertIsNone(self.shortcuts.focus_search())
            self.assertIsNone(self.shortcuts.refresh())
            self.assertEqual(self.managers.index('current'), index)

    def test_bindings_are_window_scoped(self):
        for sequence in ('<Control-f>', '<Control-F>', '<F5>'):
            self.assertTrue(self.root.bind(sequence))
            self.assertFalse(self.root.bind_all(sequence))


if __name__ == '__main__':
    unittest.main()
