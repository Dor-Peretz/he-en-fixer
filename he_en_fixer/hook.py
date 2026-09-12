"""Global keyboard hook that auto-fixes wrong-layout typing."""

from __future__ import annotations

import sys
import threading
import time
from typing import Callable

from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode

from . import injector
from .config import Settings
from .detector import convert_document, suggest_auto, toggle_layout
from .layout_input import char_from_vk

DELIMITERS = {Key.space, Key.enter, Key.tab}

CLEAR_KEYS = {
    Key.left,
    Key.right,
    Key.up,
    Key.down,
    Key.home,
    Key.end,
    Key.page_up,
    Key.page_down,
    Key.esc,
    Key.delete,
}


class KeyboardFixer:
    def __init__(self, settings: Settings, on_fix: Callable[[str, str], None] | None = None) -> None:
        self.settings = settings
        self.on_fix = on_fix
        self.buffer: list[str] = []
        self.injecting = False
        self._listener: keyboard.Listener | None = None
        self._mouse_listener: mouse.Listener | None = None
        self._lock = threading.Lock()
        self._ctrl_down = False
        self._alt_down = False
        self._shift_down = False
        self._win_down = False
        self._hotkey_used = False

    def start(self) -> None:
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()
        self._mouse_listener = mouse.Listener(on_click=self._on_click)
        self._mouse_listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None

    def _on_click(self, _x, _y, _button, _pressed) -> None:
        with self._lock:
            self.buffer.clear()

    def _on_press(self, key) -> None:
        try:
            self._on_press_inner(key)
        except Exception:
            return

    def _on_press_inner(self, key) -> None:
        if self.injecting:
            return

        if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
            self._ctrl_down = True
            return
        if key in (Key.alt, Key.alt_l, Key.alt_r):
            self._alt_down = True
            return
        if key in (Key.shift, Key.shift_l, Key.shift_r):
            self._shift_down = True
            return
        if key in (Key.cmd, Key.cmd_l, Key.cmd_r):
            self._win_down = True
            return

        if not self.settings.enabled:
            return

        if self._is_convert_hotkey(key):
            self._hotkey_used = True
            self._suppress()
            threading.Thread(target=self._manual_convert, daemon=True).start()
            return

        if self._ctrl_down or self._alt_down or self._win_down:
            with self._lock:
                self.buffer.clear()
            return

        if key == Key.backspace:
            with self._lock:
                if self.buffer:
                    self.buffer.pop()
            return

        if key in CLEAR_KEYS:
            with self._lock:
                self.buffer.clear()
            return

        if key in DELIMITERS:
            self._handle_delimiter(self._delimiter_char(key))
            return

        char = self._key_char(key)
        if char is None:
            with self._lock:
                self.buffer.clear()
            return

        with self._lock:
            self.buffer.append(char)

    def _on_release(self, key) -> None:
        if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
            self._ctrl_down = False
            self._hotkey_used = False
        elif key in (Key.alt, Key.alt_l, Key.alt_r):
            self._alt_down = False
        elif key in (Key.shift, Key.shift_l, Key.shift_r):
            self._shift_down = False
        elif key in (Key.cmd, Key.cmd_l, Key.cmd_r):
            self._win_down = False
        elif key == Key.pause or getattr(key, "vk", None) == 0x13:
            self._hotkey_used = False
        elif key == Key.f9:
            self._hotkey_used = False

    def _is_convert_hotkey(self, key) -> bool:
        if self._hotkey_used or self._alt_down or self._win_down:
            return False
        if key == Key.pause or getattr(key, "vk", None) == 0x13:
            return True
        if key == Key.f9:
            return True
        if sys.platform == "darwin":
            return bool(self._ctrl_down and self._shift_down and key == Key.space)
        return bool(self._ctrl_down and key == Key.space)

    def _suppress(self) -> None:
        if self._listener is not None:
            try:
                self._listener.suppress_event()
            except Exception:
                pass

    def _handle_delimiter(self, delim: str) -> None:
        with self._lock:
            word = "".join(self.buffer)
            self.buffer.clear()
        if not self.settings.auto_fix:
            return
        suggestion = suggest_auto(
            word,
            he_to_en_enabled=self.settings.he_to_en,
            en_to_he_enabled=self.settings.en_to_he,
        )
        if suggestion is None:
            return
        self._suppress()
        threading.Thread(
            target=self._replace_word,
            args=(len(word), suggestion.replacement, delim),
            daemon=True,
        ).start()

    def _replace_word(self, count: int, replacement: str, delim: str) -> None:
        time.sleep(0.01)
        self.injecting = True
        try:
            injector.replace_last(count, replacement + delim)
        finally:
            time.sleep(0.02)
            self.injecting = False
        if self.on_fix:
            self.on_fix(replacement, delim)

    def _manual_convert(self) -> None:
        time.sleep(0.02)
        with self._lock:
            word = "".join(self.buffer)
            self.buffer.clear()
        if word:
            converted = toggle_layout(word)
            if converted == word:
                return
            self.injecting = True
            try:
                injector.replace_last(len(word), converted)
                with self._lock:
                    self.buffer.extend(converted)
            finally:
                time.sleep(0.02)
                self.injecting = False
            if self.on_fix:
                self.on_fix(converted, "")
            return
        self._convert_selection()

    def _convert_selection(self) -> None:
        old = injector.get_clipboard_text()
        self.injecting = True
        try:
            injector.copy_selection()
            time.sleep(0.12)
            selected = injector.get_clipboard_text()
            if not selected or selected == old:
                return
            converted = convert_document(
                selected,
                he_to_en_enabled=self.settings.he_to_en,
                en_to_he_enabled=self.settings.en_to_he,
                force=True,
            )
            if converted == selected:
                return
            injector.set_clipboard_text(converted)
            time.sleep(0.05)
            injector.paste()
            time.sleep(0.08)
            if old is not None:
                injector.set_clipboard_text(old)
        finally:
            time.sleep(0.02)
            self.injecting = False

    @staticmethod
    def _delimiter_char(key) -> str:
        if key == Key.enter:
            return "\n"
        if key == Key.tab:
            return "\t"
        return " "

    @staticmethod
    def _key_char(key) -> str | None:
        vk = getattr(key, "vk", None)
        if vk:
            produced = char_from_vk(vk)
            if produced:
                return produced
        if isinstance(key, KeyCode):
            return key.char
        return None
