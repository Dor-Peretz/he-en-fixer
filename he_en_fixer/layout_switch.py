"""Switch the active keyboard language after a correction (best effort)."""

from __future__ import annotations

import sys

# Matched as prefixes, so Hebrew-QWERTY and ABC-QWERTZ variants count too.
_MAC_SOURCES = {
    "en": ("com.apple.keylayout.ABC", "com.apple.keylayout.US"),
    "he": ("com.apple.keylayout.Hebrew",),
}

_WIN_LAYOUTS = {"en": "00000409", "he": "0000040D"}


if sys.platform == "darwin":
    import ctypes
    from ctypes import c_char_p, c_int, c_long, c_void_p, create_string_buffer

    _CF_UTF8 = 0x08000100

    try:
        _carbon = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/Carbon.framework/Carbon"
        )
        _cf = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
        )
        _carbon.TISCreateInputSourceList.argtypes = [c_void_p, c_int]
        _carbon.TISCreateInputSourceList.restype = c_void_p
        _carbon.TISGetInputSourceProperty.argtypes = [c_void_p, c_void_p]
        _carbon.TISGetInputSourceProperty.restype = c_void_p
        _carbon.TISSelectInputSource.argtypes = [c_void_p]
        _carbon.TISSelectInputSource.restype = c_int
        _cf.CFArrayGetCount.argtypes = [c_void_p]
        _cf.CFArrayGetCount.restype = c_long
        _cf.CFArrayGetValueAtIndex.argtypes = [c_void_p, c_long]
        _cf.CFArrayGetValueAtIndex.restype = c_void_p
        _cf.CFStringGetCString.argtypes = [c_void_p, c_char_p, c_long, c_int]
        _cf.CFStringGetCString.restype = c_int
        _cf.CFRelease.argtypes = [c_void_p]
        _SOURCE_ID = c_void_p.in_dll(_carbon, "kTISPropertyInputSourceID")
    except (OSError, ValueError):  # pragma: no cover - unusual macOS build
        _carbon = None

    def _source_id(source) -> str | None:
        ref = _carbon.TISGetInputSourceProperty(source, _SOURCE_ID)
        if not ref:
            return None
        buf = create_string_buffer(256)
        if not _cf.CFStringGetCString(ref, buf, 256, _CF_UTF8):
            return None
        return buf.value.decode("utf-8", "replace")

    def set_language(lang: str) -> bool:
        wanted = _MAC_SOURCES.get(lang)
        if _carbon is None or not wanted:
            return False
        sources = _carbon.TISCreateInputSourceList(None, False)
        if not sources:
            return False
        try:
            for index in range(_cf.CFArrayGetCount(sources)):
                source = _cf.CFArrayGetValueAtIndex(sources, index)
                source_id = _source_id(source)
                if source_id and source_id.startswith(wanted):
                    return _carbon.TISSelectInputSource(source) == 0
        except Exception:
            return False
        finally:
            _cf.CFRelease(sources)
        return False

elif sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.windll.user32
    _user32.LoadKeyboardLayoutW.argtypes = [wintypes.LPCWSTR, wintypes.UINT]
    _user32.LoadKeyboardLayoutW.restype = ctypes.c_void_p
    _user32.GetForegroundWindow.restype = wintypes.HWND
    _user32.PostMessageW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        ctypes.c_void_p,
    ]

    _KLF_ACTIVATE = 0x00000001
    _WM_INPUTLANGCHANGEREQUEST = 0x0050

    def set_language(lang: str) -> bool:
        layout = _WIN_LAYOUTS.get(lang)
        if not layout:
            return False
        try:
            hkl = _user32.LoadKeyboardLayoutW(layout, _KLF_ACTIVATE)
            hwnd = _user32.GetForegroundWindow()
            if not hkl or not hwnd:
                return False
            return bool(
                _user32.PostMessageW(hwnd, _WM_INPUTLANGCHANGEREQUEST, 0, hkl)
            )
        except Exception:
            return False

else:

    def set_language(_lang: str) -> bool:
        return False


def language_for(direction: str) -> str | None:
    """The language the user meant to type, given the correction that was applied."""
    if direction == "he_to_en":
        return "en"
    if direction == "en_to_he":
        return "he"
    return None
