"""Read the character a key actually produces in the foreground app."""

from __future__ import annotations

import sys

if sys.platform != "win32":
    def foreground_is_hebrew() -> bool:
        return False

    def char_from_vk(_vk: int) -> str | None:
        return None
else:
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.c_void_p]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    user32.GetKeyboardLayout.restype = ctypes.c_void_p
    user32.MapVirtualKeyExW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p]
    user32.MapVirtualKeyExW.restype = wintypes.UINT
    user32.ToUnicodeEx.argtypes = [
        wintypes.UINT,
        wintypes.UINT,
        ctypes.POINTER(ctypes.c_ubyte),
        wintypes.LPWSTR,
        ctypes.c_int,
        wintypes.UINT,
        ctypes.c_void_p,
    ]
    user32.ToUnicodeEx.restype = ctypes.c_int
    user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
    user32.GetAsyncKeyState.restype = wintypes.SHORT
    user32.GetKeyState.argtypes = [ctypes.c_int]
    user32.GetKeyState.restype = wintypes.SHORT

    TO_UNICODE_NO_STATE_CHANGE = 0x04
    VK_CAPITAL = 0x14
    HEBREW_LANG_ID = 0x040D
    _MODIFIER_VKS = (0x10, 0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5)

    def _foreground_layout() -> int:
        hwnd = user32.GetForegroundWindow()
        tid = user32.GetWindowThreadProcessId(hwnd, None)
        return int(user32.GetKeyboardLayout(tid) or 0)

    def foreground_is_hebrew() -> bool:
        return (_foreground_layout() & 0xFFFF) == HEBREW_LANG_ID

    def _key_state(vk: int) -> ctypes.Array:
        state = (ctypes.c_ubyte * 256)()
        state[vk] = 0x80
        for modifier in _MODIFIER_VKS:
            if user32.GetAsyncKeyState(modifier) & 0x8000:
                state[modifier] = 0x80
        if user32.GetKeyState(VK_CAPITAL) & 1:
            state[VK_CAPITAL] |= 0x01
        return state

    def char_from_vk(vk: int) -> str | None:
        """Return the Unicode char the foreground keyboard layout would insert."""
        if not vk:
            return None
        try:
            hkl = _foreground_layout()
            if not hkl:
                return None
            state = _key_state(vk)
            scan = user32.MapVirtualKeyExW(vk, 0, hkl)
            buf = ctypes.create_unicode_buffer(8)
            produced = user32.ToUnicodeEx(
                vk,
                scan,
                state,
                buf,
                8,
                TO_UNICODE_NO_STATE_CHANGE,
                hkl,
            )
            if produced > 0:
                return buf.value[:produced]
        except Exception:
            return None
        return None
