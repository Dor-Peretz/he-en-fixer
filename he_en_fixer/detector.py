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

# The language a correction lands in.
_DIRECTION_TARGET = {"he_to_en": "en", "en_to_he": "he"}


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


def _readings(text: str, *, he_to_en_enabled: bool = True, en_to_he_enabled: bool = True) -> list[Suggestion]:
    """Every other-layout reading of a token that is a real word in the other language."""
    if not text or text.isspace():
        return []

    letters = _letters_only(text)
    if len(letters) < 2:
        return []

    he_count, en_count = script_counts(text)
    if he_count == 0 and en_count == 0:
        return []

    found: list[Suggestion] = []

    if he_to_en_enabled and he_count > 0 and he_count >= en_count:
        mapped = he_to_en(text)
        if mapped != text:
            orig = _zipf(letters, "he")
            new = _zipf(_letters_only(mapped), "en")
            if _looks_like_word(new):
                found.append(Suggestion(text, mapped, "he_to_en", orig, new))

    if en_to_he_enabled and en_count > 0 and en_count >= he_count:
        mapped = en_to_he(text)
        if mapped != text:
            orig = _zipf(letters, "en")
            new = _zipf(_letters_only(mapped), "he")
            if _looks_like_word(new):
                found.append(Suggestion(text, mapped, "en_to_he", orig, new))

    return found


def _confident(readings: list[Suggestion]) -> Suggestion | None:
    for reading in readings:
        if _should_auto_remap(reading.original_score, reading.replacement_score):
            return reading
    return None


def suggest_auto(text: str, *, he_to_en_enabled: bool = True, en_to_he_enabled: bool = True) -> Suggestion | None:
    """Return a correction only when the typed token looks like layout-gibberish."""
    return _confident(
        _readings(text, he_to_en_enabled=he_to_en_enabled, en_to_he_enabled=en_to_he_enabled)
    )


def _phrase_direction(directions: list[str]) -> str | None:
    """The one layout mistake the phrase clearly points to, if there is one."""
    if not directions:
        return None
    ranked = Counter(directions).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None
    return ranked[0][0]


def _certain_language(text: str, readings: list[Suggestion], fix: Suggestion | None) -> str | None:
    """The language a word is definitely in, or None when it could be either.

    A word is certain when the other layout turned it into gibberish (so it was
    typed in the language it reads as) or when it *was* gibberish and one layout
    rescued it. Words that read as real both ways are left for their neighbours.
    """
    if fix is not None:
        return _DIRECTION_TARGET.get(fix.direction)
    if readings:
        return None
    script = dominant_script(text)
    if script is None:
        return None
    if not _looks_like_word(_zipf(_letters_only(text), script)):
        return None
    return script


def _nearest_language(languages: list[str | None], index: int) -> str | None:
    """The language of the closest certain word on either side of a bilingual word.

    Both sides are searched together, so the answer comes from the nearest evidence
    in the phrase. When the two closest neighbours disagree the word sits on a
    language boundary and keeps whatever was typed.
    """
    for distance in range(1, len(languages)):
        before = languages[index - distance] if index - distance >= 0 else None
        after = languages[index + distance] if index + distance < len(languages) else None
        if before is not None and after is not None:
            return before if before == after else None
        if before is not None:
            return before
        if after is not None:
            return after
    return None


def _fix_words(text: str, *, he_to_en_enabled: bool = True, en_to_he_enabled: bool = True) -> tuple[str, str | None]:
    """Fix wrong-layout words, settling the bilingual ones from their neighbours.

    A word like "to" (אם) or "cut" (בוא) is real in both layouts, so nothing about
    the word itself says which one was meant. Those get a rule of their own: follow
    the nearest word whose language is certain. That turns "cut brtv to zv gucs"
    into a whole Hebrew sentence, while the stray Hebrew word in "we need to fix zv"
    cannot drag "to" along, because "need" and "fix" sit closer to it.
    """
    matches = list(_WORD_RE.finditer(text))
    readings = [
        _readings(match.group(0), he_to_en_enabled=he_to_en_enabled, en_to_he_enabled=en_to_he_enabled)
        for match in matches
    ]
    fixes = [_confident(options) for options in readings]
    languages = [
        _certain_language(match.group(0), options, fix)
        for match, options, fix in zip(matches, readings, fixes)
    ]

    for index, options in enumerate(readings):
        if fixes[index] is not None or not options:
            continue
        wanted = _nearest_language(languages, index)
        if wanted is None:
            continue
        # Readings always map away from the typed layout, so asking for the language
        # the word is already in finds nothing and leaves it as typed.
        fixes[index] = next(
            (option for option in options if _DIRECTION_TARGET.get(option.direction) == wanted),
            None,
        )

    pieces: list[str] = []
    applied: list[str] = []
    cursor = 0
    for match, fix in zip(matches, fixes):
        pieces.append(text[cursor:match.start()])
        pieces.append(match.group(0) if fix is None else fix.replacement)
        cursor = match.end()
        if fix is not None:
            applied.append(fix.direction)
    pieces.append(text[cursor:])

    if not applied:
        return text, None
    return "".join(pieces), _phrase_direction(applied)


@dataclass(frozen=True)
class BurstFix:
    text: str
    direction: str | None  # "he_to_en" | "en_to_he" | None when nothing changed


def fix_burst(text: str, *, he_to_en_enabled: bool = True, en_to_he_enabled: bool = True) -> BurstFix:
    """Correct every wrong-layout word in a burst of typing, keeping spacing intact.

    The reported direction is the one that applied to most words, so the caller can
    switch the keyboard to the language the user was actually aiming for.
    """
    fixed, direction = _fix_words(
        text,
        he_to_en_enabled=he_to_en_enabled,
        en_to_he_enabled=en_to_he_enabled,
    )
    return BurstFix(fixed, direction)


def convert_document(text: str, *, he_to_en_enabled: bool = True, en_to_he_enabled: bool = True, force: bool = False) -> str:
    """Convert words in a whole string (selection / clipboard)."""
    if force:
        def replace(match: re.Match[str]) -> str:
            token = match.group(0)
            converted = toggle_layout(token)
            return converted if converted else token

        return _WORD_RE.sub(replace, text)

    fixed, _ = _fix_words(
        text,
        he_to_en_enabled=he_to_en_enabled,
        en_to_he_enabled=en_to_he_enabled,
    )
    return fixed
