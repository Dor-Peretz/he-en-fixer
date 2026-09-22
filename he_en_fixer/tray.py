"""System tray UI."""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from dataclasses import fields

import pystray

from . import startup
from .config import SETTINGS_PATH, Settings, load_settings, save_settings
from .hook import KeyboardFixer
from .icon import tray_icon
from .layouts import get_layout, language_choices
from .paths import is_frozen, project_root

if sys.platform == "darwin":
    from . import tray_macos
else:
    tray_macos = None


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
            tray_icon(settings.enabled),
            self._title(),
            menu=self._make_menu(),
        )

    def _direction_labels(self) -> tuple[str, str]:
        name = get_layout(self.settings.language).display_name
        return (f"{name} → English", f"English → {name}")

    def _make_menu(self) -> pystray.Menu:
        other_to_en_label, en_to_other_label = self._direction_labels()
        language_menu = pystray.Menu(
            *[
                pystray.MenuItem(
                    label,
                    self._set_language,
                    checked=lambda _item, code=code: self.settings.language == code,
                    radio=True,
                )
                for code, label in language_choices()
            ]
        )
        return pystray.Menu(
            pystray.MenuItem(
                "Fixer is on",
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
            pystray.MenuItem("Keyboard language", language_menu),
            pystray.MenuItem(
                other_to_en_label,
                self._toggle_other_to_en,
                checked=lambda _: self.settings.other_to_en,
            ),
            pystray.MenuItem(
                en_to_other_label,
                self._toggle_en_to_other,
                checked=lambda _: self.settings.en_to_other,
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
        )

    def _refresh_menu(self) -> None:
        self.icon.menu = self._make_menu()
        self.icon.update_menu()

    def run(self) -> None:
        if self.settings.start_with_windows and not startup.is_enabled():
            startup.set_enabled(True)
        self.fixer.start()
        threading.Thread(target=self._watch_settings, daemon=True).start()
        self.icon.run(setup=self._on_ready)

    def _title(self) -> str:
        return "HE↔EN Fixer — on" if self.settings.enabled else "HE↔EN Fixer — off"

    def _on_ready(self, icon) -> None:
        icon.visible = True
        self._refresh_icon()
        if tray_macos is None:
            return
        tray_macos.pin_menu_bar_position(icon)
        time.sleep(0.5)
        if tray_macos.is_hidden_behind_notch(icon):
            self._warn_icon_hidden()

    def _refresh_icon(self) -> None:
        image = tray_icon(self.settings.enabled)
        self.icon.title = self._title()
        if tray_macos is not None and tray_macos.set_menu_bar_image(self.icon, image):
            return
        self.icon.icon = image

    def _warn_icon_hidden(self) -> None:
        try:
            self.icon.notify(
                "HE↔EN Fixer is running, but your menu bar is full, so macOS hides "
                "its icon behind the camera notch. Remove a menu bar icon to see it.",
                "HE↔EN Fixer",
            )
        except Exception:
            return

    def _watch_settings(self) -> None:
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
            for field in fields(Settings):
                setattr(self.settings, field.name, getattr(fresh, field.name))
            self._refresh_menu()
            self._refresh_icon()

    @staticmethod
    def _settings_mtime() -> float:
        try:
            return SETTINGS_PATH.stat().st_mtime
        except OSError:
            return 0.0

    def _persist(self) -> None:
        save_settings(self.settings)
        self._refresh_menu()
        self._refresh_icon()

    def _toggle_enabled(self, _icon=None, _item=None) -> None:
        self.settings.enabled = not self.settings.enabled
        self._persist()

    def _toggle_auto(self, _icon=None, _item=None) -> None:
        self.settings.auto_fix = not self.settings.auto_fix
        self._persist()

    def _toggle_switch_layout(self, _icon=None, _item=None) -> None:
        self.settings.switch_layout = not self.settings.switch_layout
        self._persist()

    def _toggle_other_to_en(self, _icon=None, _item=None) -> None:
        self.settings.other_to_en = not self.settings.other_to_en
        self._persist()

    def _toggle_en_to_other(self, _icon=None, _item=None) -> None:
        self.settings.en_to_other = not self.settings.en_to_other
        self._persist()

    def _set_language(self, _icon, item) -> None:
        selected = getattr(item, "text", None)
        if not selected:
            return
        for lang_code, label in language_choices():
            if label == selected:
                self.settings.language = lang_code
                self._persist()
                return

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
