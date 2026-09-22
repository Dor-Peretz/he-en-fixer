"""Global keyboard hook that auto-fixes wrong-layout typing."""

from __future__ import annotations

import sys
import threading
import time
from typing import Callable

from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode

from . import injector, layout_switch
from .config import Settings
from .detector import convert_document, fix_burst, toggle_layout
from .layout_input import char_from_vk
from .layouts import get_layout
from .mapping import dominant_script

# Typed alongside words, so they stay in the burst instead of ending it.
TEXT_KEYS = {Key.space: " ", Key.tab: "\t"}

# How often the idle watcher wakes up to see whether typing has stopped.
IDLE_POLL_SECONDS = 0.1

# macOS builds of pynput have no Key.pause, and vk 0x13 is the "2" key there.
PAUSE_KEY = getattr(Key, "pause", None)


def _is_pause(key) -> bool:
    if PAUSE_KEY is not None and key == PAUSE_KEY:
        return True
    return sys.platform == "win32" and getattr(key, "vk", None) == 0x13

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
        self._idle_thread: threading.Thread | None = None
        self._stopping = threading.Event()
        self._last_key = 0.0
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
        self._stopping.clear()
        self._idle_thread = threading.Thread(target=self._idle_loop, daemon=True)
        self._idle_thread.start()

    def stop(self) -> None:
        self._stopping.set()
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None
        self._idle_thread = None

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
                self._last_key = time.monotonic()
            return

        # Enter usually submits the text, so there is nothing left to rewrite.
        if key == Key.enter or key in CLEAR_KEYS:
            with self._lock:
                self.buffer.clear()
            return

        char = TEXT_KEYS.get(key) or self._key_char(key)
        if char is None:
            with self._lock:
                self.buffer.clear()
            return

        with self._lock:
            self.buffer.append(char)
            self._last_key = time.monotonic()

    def _on_release(self, key) -> None:
        try:
            self._on_release_inner(key)
        except Exception:
            return

    def _on_release_inner(self, key) -> None:
        if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
            self._ctrl_down = False
            self._hotkey_used = False
        elif key in (Key.alt, Key.alt_l, Key.alt_r):
            self._alt_down = False
        elif key in (Key.shift, Key.shift_l, Key.shift_r):
            self._shift_down = False
        elif key in (Key.cmd, Key.cmd_l, Key.cmd_r):
            self._win_down = False
        elif _is_pause(key):
            self._hotkey_used = False
        elif key == Key.f9:
            self._hotkey_used = False

    def _is_convert_hotkey(self, key) -> bool:
        if self._hotkey_used or self._alt_down or self._win_down:
            return False
        if _is_pause(key):
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

    def _idle_loop(self) -> None:
        while not self._stopping.wait(IDLE_POLL_SECONDS):
            try:
                self._fix_if_idle()
            except Exception:
                continue

    def _fix_if_idle(self) -> None:
        if self.injecting or not self.settings.enabled or not self.settings.auto_fix:
            return
        with self._lock:
            if not self.buffer:
                return
            if time.monotonic() - self._last_key < self.settings.idle_fix_delay:
                return
            typed = "".join(self.buffer)
            self.buffer.clear()

        result = fix_burst(
            typed,
            language=self.settings.language,
            other_to_en_enabled=self.settings.other_to_en,
            en_to_other_enabled=self.settings.en_to_other,
        )
        if result.text == typed or result.direction is None:
            return

        self.injecting = True
        try:
            injector.replace_last(len(typed), result.text)
        finally:
            time.sleep(0.02)
            self.injecting = False

        self._switch_language(
            layout_switch.language_for(result.direction, language=self.settings.language)
        )
        if self.on_fix:
            self.on_fix(result.text, "")

    def _switch_language(self, lang: str | None) -> None:
        if lang is None or not self.settings.switch_layout:
            return
        try:
            layout_switch.set_language(lang)
        except Exception:
            return

    def _manual_convert(self) -> None:
        time.sleep(0.02)
        with self._lock:
            word = "".join(self.buffer)
            self.buffer.clear()
        if word:
            converted = toggle_layout(word, language=self.settings.language)
            if converted == word:
                return
            self.injecting = True
            try:
                injector.replace_last(len(word), converted)
                with self._lock:
                    self.buffer.extend(converted)
                    self._last_key = time.monotonic()
            finally:
                time.sleep(0.02)
                self.injecting = False
            layout = get_layout(self.settings.language)
            script = dominant_script(word, language=self.settings.language)
            if script == layout.code:
                self._switch_language("en")
            elif script == "en":
                self._switch_language(layout.code)
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
                language=self.settings.language,
                other_to_en_enabled=self.settings.other_to_en,
                en_to_other_enabled=self.settings.en_to_other,
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
    def _key_char(key) -> str | None:
        vk = getattr(key, "vk", None)
        if vk:
            produced = char_from_vk(vk)
            if produced:
                return produced
        if isinstance(key, KeyCode):
            return key.char
        return None
