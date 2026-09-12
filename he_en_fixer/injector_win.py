"""Windows SendInput Unicode typing and clipboard."""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK_BACK = 0x08
VK_RETURN = 0x0D
VK_TAB = 0x09
VK_CONTROL = 0x11
VK_C = 0x43
VK_V = 0x56
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    )


class INPUTUNION(ctypes.Union):
    _fields_ = (("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT))


class INPUT(ctypes.Structure):
    _fields_ = (("type", wintypes.DWORD), ("union", INPUTUNION))


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
SendInput = user32.SendInput
SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
SendInput.restype = wintypes.UINT


def _send(inputs: list[INPUT]) -> None:
    if not inputs:
        return
    array = (INPUT * len(inputs))(*inputs)
    sent = SendInput(len(inputs), array, ctypes.sizeof(INPUT))
    if sent != len(inputs):
        raise OSError("SendInput failed")


def _vk_event(vk: int, up: bool = False) -> INPUT:
    event = INPUT()
    event.type = INPUT_KEYBOARD
    event.union.ki.wVk = vk
    event.union.ki.wScan = 0
    event.union.ki.dwFlags = KEYEVENTF_KEYUP if up else 0
    event.union.ki.time = 0
    event.union.ki.dwExtraInfo = 0
    return event


def _unicode_event(char: str, up: bool = False) -> INPUT:
    event = INPUT()
    event.type = INPUT_KEYBOARD
    event.union.ki.wVk = 0
    event.union.ki.wScan = ord(char)
    flags = KEYEVENTF_UNICODE
    if up:
        flags |= KEYEVENTF_KEYUP
    event.union.ki.dwFlags = flags
    event.union.ki.time = 0
    event.union.ki.dwExtraInfo = 0
    return event


def tap_vk(vk: int, times: int = 1) -> None:
    events: list[INPUT] = []
    for _ in range(times):
        events.append(_vk_event(vk, up=False))
        events.append(_vk_event(vk, up=True))
    _send(events)


def type_text(text: str) -> None:
    events: list[INPUT] = []
    for char in text:
        if char == "\n":
            events.append(_vk_event(VK_RETURN, up=False))
            events.append(_vk_event(VK_RETURN, up=True))
            continue
        if char == "\t":
            events.append(_vk_event(VK_TAB, up=False))
            events.append(_vk_event(VK_TAB, up=True))
            continue
        events.append(_unicode_event(char, up=False))
        events.append(_unicode_event(char, up=True))
    _send(events)


def backspace(count: int) -> None:
    if count > 0:
        tap_vk(VK_BACK, times=count)


def chord(vk_mod: int, vk_key: int) -> None:
    _send(
        [
            _vk_event(vk_mod, up=False),
            _vk_event(vk_key, up=False),
            _vk_event(vk_key, up=True),
            _vk_event(vk_mod, up=True),
        ]
    )


def copy_selection() -> None:
    chord(VK_CONTROL, VK_C)


def paste() -> None:
    chord(VK_CONTROL, VK_V)


def replace_last(count: int, replacement: str) -> None:
    backspace(count)
    time.sleep(0.01)
    type_text(replacement)


def get_clipboard_text() -> str | None:
    if not user32.OpenClipboard(None):
        return None
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return None
        locked = kernel32.GlobalLock(handle)
        if not locked:
            return None
        try:
            return ctypes.wstring_at(locked)
        finally:
            kernel32.GlobalUnlock(handle)
    finally:
        user32.CloseClipboard()


def set_clipboard_text(text: str) -> None:
    payload = text.encode("utf-16-le") + b"\x00\x00"
    if not user32.OpenClipboard(None):
        raise OSError("OpenClipboard failed")
    try:
        user32.EmptyClipboard()
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(payload))
        locked = kernel32.GlobalLock(handle)
        ctypes.memmove(locked, payload, len(payload))
        kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(CF_UNICODETEXT, handle):
            raise OSError("SetClipboardData failed")
    finally:
        user32.CloseClipboard()
