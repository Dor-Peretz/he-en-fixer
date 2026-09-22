"""Physical-key keyboard layouts paired with US QWERTY."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

LATIN_LETTERS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Israeli Hebrew — Microsoft kbdheb / standard Israeli Hebrew keyboard.
_EN_TO_HE: dict[str, str] = {
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

# Arabic 101 — common PC layout (Microsoft Arabic 101).
_EN_TO_AR: dict[str, str] = {
    "q": "ض",
    "w": "ص",
    "e": "ث",
    "r": "ق",
    "t": "ف",
    "y": "غ",
    "u": "ع",
    "i": "ه",
    "o": "خ",
    "p": "ح",
    "[": "ج",
    "]": "د",
    "a": "ش",
    "s": "س",
    "d": "ي",
    "f": "ب",
    "g": "ل",
    "h": "ا",
    "j": "ت",
    "k": "ن",
    "l": "م",
    ";": "ك",
    "'": "ط",
    "z": "ئ",
    "x": "ء",
    "c": "ؤ",
    "v": "ر",
    "b": "لا",
    "n": "ى",
    "m": "ة",
    ",": "و",
    ".": "ز",
    "/": "ظ",
    "`": "ذ",
}

# Russian ЙЦУКЕН — standard Russian typewriter layout.
_EN_TO_RU: dict[str, str] = {
    "q": "й",
    "w": "ц",
    "e": "у",
    "r": "к",
    "t": "е",
    "y": "н",
    "u": "г",
    "i": "ш",
    "o": "щ",
    "p": "з",
    "[": "х",
    "]": "ъ",
    "a": "ф",
    "s": "ы",
    "d": "в",
    "f": "а",
    "g": "п",
    "h": "р",
    "j": "о",
    "k": "л",
    "l": "д",
    ";": "ж",
    "'": "э",
    "z": "я",
    "x": "ч",
    "c": "с",
    "v": "м",
    "b": "и",
    "n": "т",
    "m": "ь",
    ",": "б",
    ".": "ю",
    "/": ".",
    "`": "ё",
}


def _invert(table: dict[str, str]) -> dict[str, str]:
    inverted: dict[str, str] = {}
    for en, other in table.items():
        if other in inverted and inverted[other] != en:
            continue
        inverted[other] = en
    return inverted


def _map_char(ch: str, table: dict[str, str]) -> str:
    lower = ch.lower()
    mapped = table.get(ch) or table.get(lower)
    if mapped is None:
        return ch
    if ch.isupper() and mapped.isalpha() and mapped.isascii():
        return mapped.upper()
    return mapped


def _map_text(text: str, table: dict[str, str]) -> str:
    return "".join(_map_char(ch, table) for ch in text)


@dataclass(frozen=True)
class KeyboardLayout:
    """One non-English layout paired with US QWERTY."""

    code: str
    display_name: str
    wordfreq_lang: str
    en_to_other: dict[str, str]
    other_to_en_extra: dict[str, str] = field(default_factory=dict)
    letter_chars: frozenset[str] = field(default_factory=frozenset)
    word_pattern: str = ""
    extra_letter_chars: Callable[[str], bool] | None = None

    def other_to_en_table(self) -> dict[str, str]:
        table = _invert(self.en_to_other)
        table.update(self.other_to_en_extra)
        return table

    def en_to_other_text(self, text: str) -> str:
        return _map_text(text, self.en_to_other)

    def other_to_en_text(self, text: str) -> str:
        return _map_text(text, self.other_to_en_table())

    def script_counts(self, text: str) -> tuple[int, int]:
        other = sum(1 for ch in text if ch in self.letter_chars)
        en = sum(1 for ch in text if ch in LATIN_LETTERS)
        return other, en

    def dominant_script(self, text: str) -> str | None:
        other_count, en_count = self.script_counts(text)
        if other_count == 0 and en_count == 0:
            return None
        if other_count > 0 and en_count == 0:
            return self.code
        if en_count > 0 and other_count == 0:
            return "en"
        if other_count >= en_count:
            return self.code
        return "en"

    def direction_to_en(self) -> str:
        return f"{self.code}_to_en"

    def direction_to_other(self) -> str:
        return f"en_to_{self.code}"

    def target_lang_for_direction(self, direction: str) -> str | None:
        if direction == self.direction_to_en():
            return "en"
        if direction == self.direction_to_other():
            return self.code
        return None


GERESH = "\u05f3"
GERSHAYIM = "\u05f4"

_HEBREW_LETTERS = frozenset("אבגדהוזחטיכלמנסעפצקרשתךםןףץ")
_HE_TO_EN_EXTRA = {
    "ך": "l",
    "ם": "o",
    "ן": "i",
    "ף": ";",
    "ץ": ".",
    GERESH: "w",
    GERSHAYIM: "W",
}

_ARABIC_LETTERS = frozenset(
    "ابتثجحخدذرزسشصضطظعغفقكلمنهوىيءئؤةلا"
)

_RUSSIAN_LETTERS = frozenset("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")


LAYOUTS: dict[str, KeyboardLayout] = {
    "he": KeyboardLayout(
        code="he",
        display_name="Hebrew",
        wordfreq_lang="he",
        en_to_other=_EN_TO_HE,
        other_to_en_extra=_HE_TO_EN_EXTRA,
        letter_chars=_HEBREW_LETTERS,
        word_pattern=r"\u0590-\u05FF",
    ),
    "ar": KeyboardLayout(
        code="ar",
        display_name="Arabic",
        wordfreq_lang="ar",
        en_to_other=_EN_TO_AR,
        letter_chars=_ARABIC_LETTERS,
        word_pattern=r"\u0600-\u06FF",
    ),
    "ru": KeyboardLayout(
        code="ru",
        display_name="Russian",
        wordfreq_lang="ru",
        en_to_other=_EN_TO_RU,
        letter_chars=_RUSSIAN_LETTERS,
        word_pattern=r"\u0400-\u04FF",
    ),
}

DEFAULT_LANGUAGE = "he"


def get_layout(code: str | None = None) -> KeyboardLayout:
    key = (code or DEFAULT_LANGUAGE).lower()
    layout = LAYOUTS.get(key)
    if layout is None:
        return LAYOUTS[DEFAULT_LANGUAGE]
    return layout


def language_choices() -> list[tuple[str, str]]:
    return [(code, layout.display_name) for code, layout in LAYOUTS.items()]
