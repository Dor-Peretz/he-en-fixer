"""Decide whether typed text was produced on the wrong keyboard layout."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from .layouts import GERESH, GERSHAYIM, LATIN_LETTERS, KeyboardLayout, get_layout
from .mapping import DEFAULT_LANGUAGE

try:
    from wordfreq import zipf_frequency
except ImportError:  # pragma: no cover
    def zipf_frequency(word: str, lang: str, wordlist: str = "best") -> float:
        return 0.0


_WORD_RE = re.compile(
    r"[A-Za-z\u0590-\u05FF\u0600-\u06FF\u0400-\u04FF';"
    + GERESH
    + GERSHAYIM
    + r"]+"
)

# zipf >= this is a reasonably common word in wordfreq.
REAL_WORD_ZIPF = 3.2
# The other layout must be clearly better, not a near-tie.
MIN_SCORE_GAP = 0.4

# Word lists spell ג'ינס with an ASCII apostrophe, not the Hebrew geresh.
_QUOTE_NORMALISATION = str.maketrans({GERESH: "'", GERSHAYIM: '"'})


@dataclass(frozen=True)
class Suggestion:
    original: str
    replacement: str
    direction: str
    original_score: float
    replacement_score: float


def _zipf(word: str, lang: str) -> float:
    cleaned = word.strip().lower().translate(_QUOTE_NORMALISATION)
    if not cleaned:
        return 0.0
    if cleaned[0] in "'\"":
        return 0.0
    return float(zipf_frequency(cleaned, lang))


def _letters_only(text: str, layout: KeyboardLayout) -> str:
    extra = ("'", GERESH, GERSHAYIM) if layout.code == "he" else ("'",)
    return "".join(
        ch
        for ch in text
        if ch in layout.letter_chars or ch in LATIN_LETTERS or ch in extra
    )


def _looks_like_word(score: float) -> bool:
    return score >= REAL_WORD_ZIPF


def _should_auto_remap(original_score: float, replacement_score: float) -> bool:
    if not _looks_like_word(replacement_score):
        return False
    if _looks_like_word(original_score):
        return False
    return replacement_score > original_score + MIN_SCORE_GAP


def toggle_layout(text: str, *, language: str = DEFAULT_LANGUAGE) -> str:
    """Unconditionally remap a token to the other layout."""
    layout = get_layout(language)
    script = layout.dominant_script(text)
    if script == layout.code:
        return layout.other_to_en_text(text)
    if script == "en":
        return layout.en_to_other_text(text)
    converted = layout.other_to_en_text(text)
    if converted != text:
        return converted
    return layout.en_to_other_text(text)


def _readings(
    text: str,
    layout: KeyboardLayout,
    *,
    other_to_en_enabled: bool = True,
    en_to_other_enabled: bool = True,
) -> list[Suggestion]:
    if not text or text.isspace():
        return []

    letters = _letters_only(text, layout)
    if len(letters) < 2:
        return []

    other_count, en_count = layout.script_counts(text)
    if other_count == 0 and en_count == 0:
        return []

    found: list[Suggestion] = []
    other_lang = layout.wordfreq_lang

    if other_to_en_enabled and other_count > 0 and other_count >= en_count:
        mapped = layout.other_to_en_text(text)
        if mapped != text:
            orig = _zipf(letters, other_lang)
            new = _zipf(_letters_only(mapped, layout), "en")
            if _looks_like_word(new):
                found.append(
                    Suggestion(text, mapped, layout.direction_to_en(), orig, new)
                )

    if en_to_other_enabled and en_count > 0 and en_count >= other_count:
        mapped = layout.en_to_other_text(text)
        if mapped != text:
            orig = _zipf(letters, "en")
            new = _zipf(_letters_only(mapped, layout), other_lang)
            if _looks_like_word(new):
                found.append(
                    Suggestion(text, mapped, layout.direction_to_other(), orig, new)
                )

    return found


def _confident(readings: list[Suggestion]) -> Suggestion | None:
    for reading in readings:
        if _should_auto_remap(reading.original_score, reading.replacement_score):
            return reading
    return None


def suggest_auto(
    text: str,
    *,
    language: str = DEFAULT_LANGUAGE,
    other_to_en_enabled: bool = True,
    en_to_other_enabled: bool = True,
    he_to_en_enabled: bool | None = None,
    en_to_he_enabled: bool | None = None,
) -> Suggestion | None:
    """Return a correction only when the typed token looks like layout-gibberish."""
    if he_to_en_enabled is not None:
        other_to_en_enabled = he_to_en_enabled
    if en_to_he_enabled is not None:
        en_to_other_enabled = en_to_he_enabled
    layout = get_layout(language)
    return _confident(
        _readings(
            text,
            layout,
            other_to_en_enabled=other_to_en_enabled,
            en_to_other_enabled=en_to_other_enabled,
        )
    )


def _phrase_direction(directions: list[str]) -> str | None:
    if not directions:
        return None
    ranked = Counter(directions).most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None
    return ranked[0][0]


def _certain_language(
    text: str,
    layout: KeyboardLayout,
    readings: list[Suggestion],
    fix: Suggestion | None,
) -> str | None:
    if fix is not None:
        return layout.target_lang_for_direction(fix.direction)
    if readings:
        return None
    script = layout.dominant_script(text)
    if script is None:
        return None
    lang = layout.wordfreq_lang if script == layout.code else "en"
    if not _looks_like_word(_zipf(_letters_only(text, layout), lang)):
        return None
    return script


def _nearest_language(languages: list[str | None], index: int) -> str | None:
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


def _fix_words(
    text: str,
    layout: KeyboardLayout,
    *,
    other_to_en_enabled: bool = True,
    en_to_other_enabled: bool = True,
) -> tuple[str, str | None]:
    matches = list(_WORD_RE.finditer(text))
    readings = [
        _readings(
            match.group(0),
            layout,
            other_to_en_enabled=other_to_en_enabled,
            en_to_other_enabled=en_to_other_enabled,
        )
        for match in matches
    ]
    fixes = [_confident(options) for options in readings]
    languages = [
        _certain_language(match.group(0), layout, options, fix)
        for match, options, fix in zip(matches, readings, fixes)
    ]

    for index, options in enumerate(readings):
        if fixes[index] is not None or not options:
            continue
        wanted = _nearest_language(languages, index)
        if wanted is None:
            continue
        fixes[index] = next(
            (
                option
                for option in options
                if layout.target_lang_for_direction(option.direction) == wanted
            ),
            None,
        )

    pieces: list[str] = []
    applied: list[str] = []
    cursor = 0
    for match, fix in zip(matches, fixes):
        pieces.append(text[cursor : match.start()])
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
    direction: str | None


def fix_burst(
    text: str,
    *,
    language: str = DEFAULT_LANGUAGE,
    other_to_en_enabled: bool = True,
    en_to_other_enabled: bool = True,
    he_to_en_enabled: bool | None = None,
    en_to_he_enabled: bool | None = None,
) -> BurstFix:
    if he_to_en_enabled is not None:
        other_to_en_enabled = he_to_en_enabled
    if en_to_he_enabled is not None:
        en_to_other_enabled = en_to_he_enabled
    layout = get_layout(language)
    fixed, direction = _fix_words(
        text,
        layout,
        other_to_en_enabled=other_to_en_enabled,
        en_to_other_enabled=en_to_other_enabled,
    )
    return BurstFix(fixed, direction)


def convert_document(
    text: str,
    *,
    language: str = DEFAULT_LANGUAGE,
    other_to_en_enabled: bool = True,
    en_to_other_enabled: bool = True,
    he_to_en_enabled: bool | None = None,
    en_to_he_enabled: bool | None = None,
    force: bool = False,
) -> str:
    if he_to_en_enabled is not None:
        other_to_en_enabled = he_to_en_enabled
    if en_to_he_enabled is not None:
        en_to_other_enabled = en_to_he_enabled
    layout = get_layout(language)
    if force:

        def replace(match: re.Match[str]) -> str:
            token = match.group(0)
            converted = toggle_layout(token, language=language)
            return converted if converted else token

        return _WORD_RE.sub(replace, text)

    fixed, _ = _fix_words(
        text,
        layout,
        other_to_en_enabled=other_to_en_enabled,
        en_to_other_enabled=en_to_other_enabled,
    )
    return fixed
