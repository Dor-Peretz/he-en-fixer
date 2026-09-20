from __future__ import annotations

import unittest

from he_en_fixer.calibrate import CalibrationError, delay_from_typing
from he_en_fixer.detector import convert_document, fix_burst, suggest_auto, toggle_layout
from he_en_fixer.layout_switch import language_for
from he_en_fixer.mapping import en_to_he, he_to_en
from he_en_fixer.paths import install_dir


class MappingTests(unittest.TestCase):
    def test_hello_roundtrip(self) -> None:
        self.assertEqual(en_to_he("hello"), "יקךךם")
        self.assertEqual(he_to_en("יקךךם"), "hello")

    def test_world(self) -> None:
        self.assertEqual(en_to_he("world"), "'םרךג")
        self.assertEqual(he_to_en("'םרךג"), "world")

    def test_python(self) -> None:
        self.assertEqual(en_to_he("python"), "פטאיםמ")
        self.assertEqual(he_to_en("פטאיםמ"), "python")

    def test_the(self) -> None:
        self.assertEqual(en_to_he("the"), "איק")
        self.assertEqual(he_to_en("איק"), "the")

    def test_preserves_latin_case_in_hebrew_to_english(self) -> None:
        self.assertEqual(he_to_en("Hקךךם"), "Hello")


class DetectorTests(unittest.TestCase):
    def test_auto_fixes_hebrew_gibberish_to_english(self) -> None:
        suggestion = suggest_auto("יקךךם")
        self.assertIsNotNone(suggestion)
        assert suggestion is not None
        self.assertEqual(suggestion.replacement, "hello")
        self.assertEqual(suggestion.direction, "he_to_en")

    def test_auto_fixes_the(self) -> None:
        suggestion = suggest_auto("איק")
        self.assertIsNotNone(suggestion)
        assert suggestion is not None
        self.assertEqual(suggestion.replacement, "the")

    def test_does_not_replace_real_hebrew(self) -> None:
        self.assertIsNone(suggest_auto("שלום"))
        self.assertIsNone(suggest_auto("אם"))

    def test_does_not_replace_real_english(self) -> None:
        self.assertIsNone(suggest_auto("hello"))
        self.assertIsNone(suggest_auto("to"))

    def test_leaves_words_that_are_real_in_both_layouts(self) -> None:
        # Typed Hebrew that is also a real English word on the other layout.
        self.assertIsNone(suggest_auto("אם"))  # to
        self.assertIsNone(suggest_auto("גם"))  # do
        self.assertIsNone(suggest_auto("עם"))  # go
        self.assertIsNone(suggest_auto("דם"))  # so
        self.assertIsNone(suggest_auto("כשבא"))  # fact
        self.assertIsNone(suggest_auto("פורק"))  # pure
        # Typed English that is also a real Hebrew word on the other layout.
        self.assertIsNone(suggest_auto("to"))
        self.assertIsNone(suggest_auto("do"))
        self.assertIsNone(suggest_auto("go"))
        self.assertIsNone(suggest_auto("so"))
        self.assertIsNone(suggest_auto("fact"))
        self.assertIsNone(suggest_auto("dusk"))  # גודל
        self.assertIsNone(suggest_auto("nv"))  # מה

    def test_auto_fixes_english_gibberish_to_hebrew(self) -> None:
        suggestion = suggest_auto("akuo")
        self.assertIsNotNone(suggestion)
        assert suggestion is not None
        self.assertEqual(suggestion.replacement, "שלום")
        self.assertEqual(suggestion.direction, "en_to_he")

    def test_toggle_is_reversible(self) -> None:
        self.assertEqual(toggle_layout("יקךךם"), "hello")
        self.assertEqual(toggle_layout("hello"), "יקךךם")

    def test_convert_sentence(self) -> None:
        text = "יקךךם 'םרךג"
        self.assertEqual(convert_document(text), "hello world")

    def test_convert_document_leaves_bilingual_words(self) -> None:
        self.assertEqual(convert_document("אם כשבא יקךךם"), "אם כשבא hello")
        self.assertEqual(convert_document("to fact akuo"), "to fact שלום")


class BurstTests(unittest.TestCase):
    def test_fixes_whole_burst_and_reports_direction(self) -> None:
        result = fix_burst("יקךךם 'םרךג")
        self.assertEqual(result.text, "hello world")
        self.assertEqual(result.direction, "he_to_en")

    def test_keeps_spacing(self) -> None:
        self.assertEqual(fix_burst("יקךךם  'םרךג ").text, "hello  world ")

    def test_real_text_is_left_alone(self) -> None:
        result = fix_burst("שלום עולם")
        self.assertEqual(result.text, "שלום עולם")
        self.assertIsNone(result.direction)

    def test_direction_follows_the_majority_of_fixed_words(self) -> None:
        # Two Hebrew-layout words, one English-layout word.
        result = fix_burst("יקךךם 'םרךג akuo")
        self.assertEqual(result.direction, "he_to_en")

    def test_language_for_direction(self) -> None:
        self.assertEqual(language_for("he_to_en"), "en")
        self.assertEqual(language_for("en_to_he"), "he")
        self.assertIsNone(language_for("nonsense"))


def _typed(text: str, letter: float, word: float) -> list[tuple[str, float]]:
    stamp = 1.0
    events: list[tuple[str, float]] = []
    previous = ""
    for char in text:
        if events:
            stamp += word if previous.isspace() or char.isspace() else letter
        events.append((char, stamp))
        previous = char
    return events


class CalibrationTests(unittest.TestCase):
    def test_faster_typing_waits_less_than_slower_typing(self) -> None:
        sentence = "the cat sat on the mat"
        fast = delay_from_typing(_typed(sentence, letter=0.08, word=0.2))
        slow = delay_from_typing(_typed(sentence, letter=0.25, word=0.9))
        self.assertLess(fast.idle_fix_delay, slow.idle_fix_delay)
        self.assertGreaterEqual(fast.idle_fix_delay, 0.3)
        self.assertLessEqual(slow.idle_fix_delay, 3.0)

    def test_needs_a_sentence_not_one_word(self) -> None:
        with self.assertRaises(CalibrationError):
            delay_from_typing(_typed("hello", letter=0.1, word=0.4))

    def test_ignores_a_long_interruption(self) -> None:
        events = _typed("the cat sat on the mat", letter=0.1, word=0.3)
        events.insert(4, (" ", 100.0))
        result = delay_from_typing(events)
        self.assertLess(result.idle_fix_delay, 2.0)


class InstallSafetyTests(unittest.TestCase):
    def test_install_dir_stays_inside_home(self) -> None:
        from pathlib import Path

        home = Path.home().resolve()
        dest = install_dir().resolve()
        self.assertEqual(dest.anchor, home.anchor)
        self.assertTrue(dest.is_relative_to(home))


if __name__ == "__main__":
    unittest.main()
