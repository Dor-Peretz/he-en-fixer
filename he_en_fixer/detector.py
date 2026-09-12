"""Decide whether typed text was produced on the wrong keyboard layout."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .mapping import dominant_script, en_to_he, he_to_en, script_counts

try:
    from wordfreq import zipf_frequency
except ImportError:  # pragma: no cover
    def zipf_frequency(word: str, lang: str, wordlist: str = "best") -> float:
        return 0.0


_WORD_RE = re.compile(r"[A-Za-z\u0590-\u05FF';]+")

# zipf >= ~3.2 is a reasonably common word.
MIN_TARGET_WORD = 3.2
# If the typed token is already a real word in its script, never auto-fix it.
TYPED_REAL_WORD = 3.5


@dataclass(frozen=True)
class Suggestion:
    original: str
    replacement: str
    direction: str  # "he_to_en" | "en_to_he"
    original_score: float
    replacement_score: float


def _zipf(word: str, lang: str) -> float:
    cleaned = word.strip().lower()
    if not cleaned:
        return 0.0
    return float(zipf_frequency(cleaned, lang))


def _letters_only(text: str) -> str:
    return "".join(ch for ch in text if ch.isalpha() or ch in "'")


def toggle_layout(text: str) -> str:
    """Unconditionally remap a token to the other layout."""
    script = dominant_script(text)
    if script == "he":
        return he_to_en(text)
    if script == "en":
        return en_to_he(text)
    # Mixed or punctuation-only: prefer Hebrew->English, then the reverse if nothing changed.
    converted = he_to_en(text)
    if converted != text:
        return converted
    return en_to_he(text)


def suggest_auto(text: str, *, he_to_en_enabled: bool = True, en_to_he_enabled: bool = True) -> Suggestion | None:
    """Return a correction only when the typed token looks like layout-gibberish."""
    if not text or text.isspace():
        return None

    letters = _letters_only(text)
    if len(letters) < 2:
        return None

    he_count, en_count = script_counts(text)
    if he_count == 0 and en_count == 0:
        return None

    if he_to_en_enabled and he_count > 0 and he_count >= en_count:
        mapped = he_to_en(text)
        if mapped != text:
            orig = _zipf(letters, "he")
            new = _zipf(_letters_only(mapped), "en")
            if orig < TYPED_REAL_WORD and new >= MIN_TARGET_WORD and new > orig + 0.4:
                return Suggestion(text, mapped, "he_to_en", orig, new)

    if en_to_he_enabled and en_count > 0 and en_count >= he_count:
        mapped = en_to_he(text)
        if mapped != text:
            orig = _zipf(letters, "en")
            new = _zipf(_letters_only(mapped), "he")
            if orig < TYPED_REAL_WORD and new >= MIN_TARGET_WORD and new > orig + 0.4:
                return Suggestion(text, mapped, "en_to_he", orig, new)

    return None


def convert_document(text: str, *, he_to_en_enabled: bool = True, en_to_he_enabled: bool = True, force: bool = False) -> str:
    """Convert words in a whole string (selection / clipboard)."""

    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        if force:
            converted = toggle_layout(token)
            return converted if converted else token
        suggestion = suggest_auto(
            token,
            he_to_en_enabled=he_to_en_enabled,
            en_to_he_enabled=en_to_he_enabled,
        )
        return suggestion.replacement if suggestion else token

    return _WORD_RE.sub(replace, text)
