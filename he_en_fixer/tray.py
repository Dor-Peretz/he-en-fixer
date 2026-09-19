"""System tray UI."""

from __future__ import annotations

import subprocess
import sys
import threading
from dataclasses import fields

import pystray

from . import startup
from .config import SETTINGS_PATH, Settings, load_settings, save_settings
from .hook import KeyboardFixer
from .icon import load_icon
from .paths import is_frozen, project_root


def _hotkey_hint() -> str:
    if sys.platform == "darwin":
        return "Convert what I just typed / selection  (Ctrl+Shift+Space or F9)"
    return "Convert what I just typed / selection  (Ctrl+Space, Pause, or F9)"


class TrayApp:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.fixer = KeyboardFixer(settings)
        self._stop_watch = threading.Event()
        self.icon = pystray.Icon(
            "he-en-fixer",
            load_icon(64),
            "HE↔EN Fixer",
            menu=pystray.Menu(
                pystray.MenuItem(
                    "Enabled",
                    self._toggle_enabled,
                    checked=lambda _: self.settings.enabled,
                ),
                pystray.MenuItem(
                    "Auto-fix when I stop typing",
                    self._toggle_auto,
                    checked=lambda _: self.settings.auto_fix,
                ),
                pystray.MenuItem(
                    "Switch keyboard language after a fix",
                    self._toggle_switch_layout,
                    checked=lambda _: self.settings.switch_layout,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Hebrew → English",
                    self._toggle_he_to_en,
                    checked=lambda _: self.settings.he_to_en,
                ),
                pystray.MenuItem(
                    "English → Hebrew",
                    self._toggle_en_to_he,
                    checked=lambda _: self.settings.en_to_he,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(
                    "Start when I log in",
                    self._toggle_startup,
                    checked=lambda _: self.settings.start_with_windows,
                ),
                pystray.MenuItem(_hotkey_hint(), self._noop, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Settings…", self._open_settings),
                pystray.MenuItem("Install / Uninstall…", self._open_installer),
                pystray.MenuItem("Quit", self._quit),
            ),
        )

    def run(self) -> None:
        if self.settings.start_with_windows and not startup.is_enabled():
            startup.set_enabled(True)
        self.fixer.start()
        threading.Thread(target=self._watch_settings, daemon=True).start()
        self.icon.run()

    def _watch_settings(self) -> None:
        """Pick up changes made by the settings window, which runs as its own process."""
        last = self._settings_mtime()
        while not self._stop_watch.wait(1.0):
            current = self._settings_mtime()
            if current == last:
                continue
            last = current
            try:
                fresh = load_settings()
            except Exception:
                continue
            # Mutated in place so the running hook sees the new values.
            for field in fields(Settings):
                setattr(self.settings, field.name, getattr(fresh, field.name))
            self.icon.update_menu()

    @staticmethod
    def _settings_mtime() -> float:
        try:
            return SETTINGS_PATH.stat().st_mtime
        except OSError:
            return 0.0

    def _persist(self) -> None:
        save_settings(self.settings)
        self.icon.update_menu()

    def _toggle_enabled(self, _icon=None, _item=None) -> None:
        self.settings.enabled = not self.settings.enabled
        self._persist()

    def _toggle_auto(self, _icon=None, _item=None) -> None:
        self.settings.auto_fix = not self.settings.auto_fix
        self._persist()

    def _toggle_switch_layout(self, _icon=None, _item=None) -> None:
        self.settings.switch_layout = not self.settings.switch_layout
        self._persist()

    def _toggle_he_to_en(self, _icon=None, _item=None) -> None:
        self.settings.he_to_en = not self.settings.he_to_en
        self._persist()

    def _toggle_en_to_he(self, _icon=None, _item=None) -> None:
        self.settings.en_to_he = not self.settings.en_to_he
        self._persist()

    def _toggle_startup(self, _icon=None, _item=None) -> None:
        self.settings.start_with_windows = not self.settings.start_with_windows
        startup.set_enabled(self.settings.start_with_windows)
        self._persist()

    def _open_installer(self, _icon=None, _item=None) -> None:
        self._open_window("--setup")

    def _open_settings(self, _icon=None, _item=None) -> None:
        self._open_window("--settings")

    @staticmethod
    def _open_window(flag: str) -> None:
        if is_frozen():
            subprocess.Popen([sys.executable, flag])
            return
        script = project_root() / "main.py"
        subprocess.Popen([sys.executable, str(script), flag])

    def _noop(self, _icon=None, _item=None) -> None:
        return

    def _quit(self, _icon=None, _item=None) -> None:
        self._stop_watch.set()
        self.fixer.stop()
        self.icon.stop()
