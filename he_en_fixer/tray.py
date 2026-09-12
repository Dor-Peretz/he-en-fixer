"""System tray UI."""

from __future__ import annotations

import subprocess
import sys

import pystray
from PIL import Image, ImageDraw, ImageFont

from . import startup
from .config import Settings, save_settings
from .hook import KeyboardFixer
from .paths import is_frozen, project_root


def _icon_image() -> Image.Image:
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((2, 2, size - 3, size - 3), radius=14, fill=(28, 36, 56, 255))
    draw.rounded_rectangle((6, 6, size - 7, size - 7), radius=12, fill=(47, 92, 168, 255))
    try:
        font_name = "segoeui.ttf" if sys.platform == "win32" else "Helvetica.ttc"
        font = ImageFont.truetype(font_name, 22)
    except OSError:
        font = ImageFont.load_default()
    draw.text((10, 16), "A", font=font, fill="white")
    draw.text((34, 14), "א", font=font, fill=(255, 214, 90, 255))
    return image


def _hotkey_hint() -> str:
    if sys.platform == "darwin":
        return "Convert last word / selection  (Ctrl+Shift+Space or F9)"
    return "Convert last word / selection  (Ctrl+Space, Pause, or F9)"


class TrayApp:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.fixer = KeyboardFixer(settings)
        self.icon = pystray.Icon(
            "he-en-fixer",
            _icon_image(),
            "HE↔EN Fixer",
            menu=pystray.Menu(
                pystray.MenuItem(
                    "Enabled",
                    self._toggle_enabled,
                    checked=lambda _: self.settings.enabled,
                ),
                pystray.MenuItem(
                    "Auto-fix while typing",
                    self._toggle_auto,
                    checked=lambda _: self.settings.auto_fix,
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
                pystray.MenuItem("Install / Uninstall…", self._open_installer),
                pystray.MenuItem("Quit", self._quit),
            ),
        )

    def run(self) -> None:
        if self.settings.start_with_windows and not startup.is_enabled():
            startup.set_enabled(True)
        self.fixer.start()
        self.icon.run()

    def _persist(self) -> None:
        save_settings(self.settings)
        self.icon.update_menu()

    def _toggle_enabled(self, _icon=None, _item=None) -> None:
        self.settings.enabled = not self.settings.enabled
        self._persist()

    def _toggle_auto(self, _icon=None, _item=None) -> None:
        self.settings.auto_fix = not self.settings.auto_fix
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
        if is_frozen():
            subprocess.Popen([sys.executable, "--setup"])
            return
        script = project_root() / "main.py"
        subprocess.Popen([sys.executable, str(script), "--setup"])

    def _noop(self, _icon=None, _item=None) -> None:
        return

    def _quit(self, _icon=None, _item=None) -> None:
        self.fixer.stop()
        self.icon.stop()
