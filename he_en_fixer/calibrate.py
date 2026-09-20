"""Turn a sample of typing into an idle-fix wait time."""

from __future__ import annotations

from dataclasses import dataclass

MIN_IDLE_FIX_DELAY = 0.3
MAX_IDLE_FIX_DELAY = 3.0

# Ignore a gap this long — the typist likely stopped and came back.
MAX_USEFUL_GAP = 4.0

CALIBRATE_SENTENCE = "the cat sat on the mat"

_MIN_LETTER_GAPS = 8
_MIN_WORD_GAPS = 2


@dataclass(frozen=True)
class CalibrationResult:
    idle_fix_delay: float
    letter_gap: float
    word_gap: float


class CalibrationError(ValueError):
    pass


def _percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * (pct / 100.0)
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    frac = rank - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def _gaps(events: list[tuple[str, float]]) -> tuple[list[float], list[float]]:
    letter_gaps: list[float] = []
    word_gaps: list[float] = []
    for index in range(1, len(events)):
        prev_char, prev_time = events[index - 1]
        char, now = events[index]
        gap = now - prev_time
        if gap <= 0 or gap > MAX_USEFUL_GAP:
            continue
        if prev_char.isspace() or char.isspace():
            word_gaps.append(gap)
        elif prev_char.isalpha() and char.isalpha():
            letter_gaps.append(gap)
    return letter_gaps, word_gaps


def delay_from_typing(events: list[tuple[str, float]]) -> CalibrationResult:
    """Estimate how long to wait after the last key before auto-fix.

    Letter gaps tell us how fast keys land inside a word. Word gaps (around
    spaces) tell us how long the typist pauses between words. Auto-fix must
    wait longer than both, or it will fire in the middle of a sentence.
    """
    letter_gaps, word_gaps = _gaps(events)
    if len(letter_gaps) < _MIN_LETTER_GAPS:
        raise CalibrationError("Type a few more letters at your usual speed.")
    if len(word_gaps) < _MIN_WORD_GAPS:
        raise CalibrationError("Type a short sentence with spaces between the words.")

    letter_slow = _percentile(letter_gaps, 95)
    word_typical = _percentile(word_gaps, 80)
    # Stay above almost every in-word gap, and above the usual between-word pause.
    wait = max(letter_slow * 2.5, word_typical * 1.8) + 0.15
    delay = round(max(MIN_IDLE_FIX_DELAY, min(MAX_IDLE_FIX_DELAY, wait)), 1)
    return CalibrationResult(
        idle_fix_delay=delay,
        letter_gap=round(letter_slow, 3),
        word_gap=round(word_typical, 3),
    )
