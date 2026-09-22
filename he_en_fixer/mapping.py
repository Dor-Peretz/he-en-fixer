"""Standard Windows Israeli Hebrew <-> US QWERTY physical-key mapping."""

from __future__ import annotations

# Physical US QWERTY key -> character produced on the Israeli Hebrew layout.
# Source: Microsoft kbdheb / standard Israeli Hebrew keyboard.
EN_TO_HE = {
    "q": "/",
    "w": "'",
    "e": "ק",
    "r": "ר",
    "t": "א",
    "y": "ט",
    "u": "ו",
    "i": "ן",
    "o": "ם",
    "p": "פ",
    "a": "ש",
    "s": "ד",
    "d": "ג",
    "f": "כ",
    "g": "ע",
    "h": "י",
    "j": "ח",
    "k": "ל",
    "l": "ך",
    ";": "ף",
    "z": "ז",
    "x": "ס",
    "c": "ב",
    "v": "ה",
    "b": "נ",
    "n": "מ",
    "m": "צ",
    ",": "ת",
    ".": "ץ",
    "/": ".",
    "'": ",",
    "[": "]",
    "]": "[",
    "`": ";",
}

HE_TO_EN = {he: en for en, he in EN_TO_HE.items()}

# Final-form letters that some keyboards / IMEs emit instead of the mapped finals.
HE_TO_EN.update(
    {
        "ך": "l",
        "ם": "o",
        "ן": "i",
        "ף": ";",
        "ץ": ".",
    }
)

# Hebrew Standard (Windows) and macOS Hebrew put the punctuation geresh on the
# W key and gershayim on Shift+W, where the legacy layout emits ' and ".
GERESH = "\u05f3"
GERSHAYIM = "\u05f4"
HE_TO_EN.update(
    {
        GERESH: "w",
        GERSHAYIM: "W",
    }
)

HEBREW_LETTERS = frozenset("אבגדהוזחטיכלמנסעפצקרשתךםןףץ")
LATIN_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")


def _map_char(ch: str, table: dict[str, str]) -> str:
    lower = ch.lower()
    mapped = table.get(ch) or table.get(lower)
    if mapped is None:
        return ch
    if ch.isupper() and mapped.isalpha() and mapped.isascii():
        return mapped.upper()
    return mapped


def he_to_en(text: str) -> str:
    return "".join(_map_char(ch, HE_TO_EN) for ch in text)


def en_to_he(text: str) -> str:
    return "".join(_map_char(ch, EN_TO_HE) for ch in text)


def script_counts(text: str) -> tuple[int, int]:
    he = sum(1 for ch in text if ch in HEBREW_LETTERS)
    en = sum(1 for ch in text if ch in LATIN_LETTERS)
    return he, en


def dominant_script(text: str) -> str | None:
    he, en = script_counts(text)
    if he == 0 and en == 0:
        return None
    if he > 0 and en == 0:
        return "he"
    if en > 0 and he == 0:
        return "en"
    if he >= en:
        return "he"
    return "en"
