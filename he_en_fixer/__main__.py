"""Command-line preview of layout conversion."""

from __future__ import annotations

import argparse
import sys

from .detector import convert_document, suggest_auto, toggle_layout
from .layouts import LAYOUTS, get_layout
from .mapping import DEFAULT_LANGUAGE, en_to_other, other_to_en


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Preview keyboard-layout conversion between English and Hebrew, Arabic, or Russian."
    )
    parser.add_argument("text", nargs="+", help="Text to convert")
    parser.add_argument(
        "--language",
        choices=sorted(LAYOUTS),
        default=DEFAULT_LANGUAGE,
        help="Non-English language paired with English (default: he)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Always remap keys, even if the word looks real",
    )
    args = parser.parse_args(argv)
    text = " ".join(args.text)
    language = args.language
    layout = get_layout(language)
    if args.force:
        print(toggle_layout(text, language=language) if " " not in text else convert_document(text, language=language, force=True))
        return 0

    suggestion = suggest_auto(text, language=language)
    if suggestion:
        print(suggestion.replacement)
        print(
            f"# {suggestion.direction}  "
            f"scores {suggestion.original_score:.2f} -> {suggestion.replacement_score:.2f}",
            file=sys.stderr,
        )
        return 0

    print(convert_document(text, language=language) if any(ch.isspace() for ch in text) else text)
    print("# no automatic change (word looks real, or not in dictionary)", file=sys.stderr)
    print(f"# {layout.code}->en {other_to_en(text, language)}", file=sys.stderr)
    print(f"# en->{layout.code} {en_to_other(text, language)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
