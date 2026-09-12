"""pynput-based typing/clipboard for macOS (and other non-Windows)."""

from __future__ import annotations

import subprocess
import sys
import time

from pynput.keyboard import Controller, Key

_controller: Controller | None = None


def _kb() -> Controller:
    global _controller
    if _controller is None:
        _controller = Controller()
    return _controller


def type_text(text: str) -> None:
    _kb().type(text)


def backspace(count: int) -> None:
    kb = _kb()
    for _ in range(max(0, count)):
        kb.tap(Key.backspace)


def _mod_key():
    return Key.cmd if sys.platform == "darwin" else Key.ctrl


def copy_selection() -> None:
    kb = _kb()
    with kb.pressed(_mod_key()):
        kb.tap("c")


def paste() -> None:
    kb = _kb()
    with kb.pressed(_mod_key()):
        kb.tap("v")


def replace_last(count: int, replacement: str) -> None:
    backspace(count)
    time.sleep(0.01)
    type_text(replacement)


def get_clipboard_text() -> str | None:
    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        return result.stdout.decode("utf-8")
    except OSError:
        return None


def set_clipboard_text(text: str) -> None:
    subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
