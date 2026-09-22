"""Keyboard layout conversion (backward-compatible Hebrew exports)."""

from __future__ import annotations

from .layouts import (
    DEFAULT_LANGUAGE,
    GERESH,
    GERSHAYIM,
    LATIN_LETTERS,
    KeyboardLayout,
    LAYOUTS,
    get_layout,
    language_choices,
)

# Physical US QWERTY key -> character on Israeli Hebrew layout (legacy names).
EN_TO_HE = dict(LAYOUTS["he"].en_to_other)
HE_TO_EN = LAYOUTS["he"].other_to_en_table()
HEBREW_LETTERS = LAYOUTS["he"].letter_chars


def he_to_en(text: str) -> str:
    return get_layout("he").other_to_en_text(text)


def en_to_he(text: str) -> str:
    return get_layout("he").en_to_other_text(text)


def other_to_en(text: str, language: str = DEFAULT_LANGUAGE) -> str:
    return get_layout(language).other_to_en_text(text)


def en_to_other(text: str, language: str = DEFAULT_LANGUAGE) -> str:
    return get_layout(language).en_to_other_text(text)


def script_counts(text: str, language: str = DEFAULT_LANGUAGE) -> tuple[int, int]:
    return get_layout(language).script_counts(text)


def dominant_script(text: str, language: str = DEFAULT_LANGUAGE) -> str | None:
    return get_layout(language).dominant_script(text)


__all__ = [
    "DEFAULT_LANGUAGE",
    "EN_TO_HE",
    "GERESH",
    "GERSHAYIM",
    "HEBREW_LETTERS",
    "HE_TO_EN",
    "KeyboardLayout",
    "LATIN_LETTERS",
    "LAYOUTS",
    "dominant_script",
    "en_to_he",
    "en_to_other",
    "get_layout",
    "he_to_en",
    "language_choices",
    "other_to_en",
    "script_counts",
]
