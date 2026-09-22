"""Decide whether typed text was produced on the wrong keyboard layout."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from .mapping import GERESH, GERSHAYIM, dominant_script, en_to_he, he_to_en, script_counts

try:
    from wordfreq import zipf_frequency
except ImportError:  # pragma: no cover
    def zipf_frequency(word: str, lang: str, wordlist: str = "best") -> float:
        return 0.0


_WORD_RE = re.compile(r"[A-Za-z\u0590-\u05FF';]+")

# zipf >= this is a reasonably common word in wordfreq.
REAL_WORD_ZIPF = 3.2
# The other layout must be clearly better, not a near-tie.
MIN_SCORE_GAP = 0.4


@dataclass(frozen=True)
class Suggestion:
    original: str
    replacement: str
    direction: str  # "he_to_en" | "en_to_he"
    original_score: float
    replacement_score: float


# Word lists spell ג'ינס with an ASCII apostrophe, not the Hebrew geresh.
_QUOTE_NORMALISATION = str.maketrans({GERESH: "'", GERSHAYIM: '"'})


def _zipf(word: str, lang: str) -> float:
    cleaned = word.strip().lower().translate(_QUOTE_NORMALISATION)
    if not cleaned:
        return 0.0
    # Neither language starts a word with a quote, but wordfreq drops a leading
    # one and scores the rest, which makes 'שמא (want) look like a real word.
    if cleaned[0] in "'\"":
        return 0.0
    return float(zipf_frequency(cleaned, lang))


def _letters_only(text: str) -> str:
    return "".join(ch for ch in text if ch.isalpha() or ch in ("'", GERESH, GERSHAYIM))


def _looks_like_word(score: float) -> bool:
    return score >= REAL_WORD_ZIPF


def _should_auto_remap(original_score: float, replacement_score: float) -> bool:
    """Auto-fix only when the typed token is gibberish and the other layout is a word.

    Some physical-key sequences are real words in *both* languages after remap
    (אם↔to, כשבא↔fact, dusk↔גודל). Leave those as typed; force-convert can still
    flip them.
    """
    if not _looks_like_word(replacement_score):
        return False
    if _looks_like_word(original_score):
        return False
    return replacement_score > original_score + MIN_SCORE_GAP


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
            if _should_auto_remap(orig, new):
                return Suggestion(text, mapped, "he_to_en", orig, new)

    if en_to_he_enabled and en_count > 0 and en_count >= he_count:
        mapped = en_to_he(text)
        if mapped != text:
            orig = _zipf(letters, "en")
            new = _zipf(_letters_only(mapped), "he")
            if _should_auto_remap(orig, new):
                return Suggestion(text, mapped, "en_to_he", orig, new)

    return None


@dataclass(frozen=True)
class BurstFix:
    text: str
    direction: str | None  # "he_to_en" | "en_to_he" | None when nothing changed


def fix_burst(text: str, *, he_to_en_enabled: bool = True, en_to_he_enabled: bool = True) -> BurstFix:
    """Correct every wrong-layout word in a burst of typing, keeping spacing intact.

    The reported direction is the one that applied to most words, so the caller can
    switch the keyboard to the language the user was actually aiming for.
    """
    directions: list[str] = []

    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        suggestion = suggest_auto(
            token,
            he_to_en_enabled=he_to_en_enabled,
            en_to_he_enabled=en_to_he_enabled,
        )
        if suggestion is None:
            return token
        directions.append(suggestion.direction)
        return suggestion.replacement

    fixed = _WORD_RE.sub(replace, text)
    if not directions:
        return BurstFix(text, None)
    return BurstFix(fixed, Counter(directions).most_common(1)[0][0])


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
