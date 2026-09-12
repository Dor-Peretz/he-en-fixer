"""Command-line preview of layout conversion."""

from __future__ import annotations

import argparse
import sys

from .detector import convert_document, suggest_auto, toggle_layout
from .mapping import en_to_he, he_to_en


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Preview Hebrew/English keyboard-layout conversion."
    )
    parser.add_argument("text", nargs="+", help="Text to convert")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Always remap keys, even if the word looks real",
    )
    args = parser.parse_args(argv)
    text = " ".join(args.text)
    if args.force:
        print(toggle_layout(text) if " " not in text else convert_document(text, force=True))
        return 0

    suggestion = suggest_auto(text)
    if suggestion:
        print(suggestion.replacement)
        print(
            f"# {suggestion.direction}  "
            f"scores {suggestion.original_score:.2f} -> {suggestion.replacement_score:.2f}",
            file=sys.stderr,
        )
        return 0

    print(convert_document(text) if any(ch.isspace() for ch in text) else text)
    print("# no automatic change (word looks real, or not in dictionary)", file=sys.stderr)
    print(f"# he->en {he_to_en(text)}", file=sys.stderr)
    print(f"# en->he {en_to_he(text)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
