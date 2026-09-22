"""Build docs/demo.gif: gibberish typed in a normal document, then auto-fixed.

The frames mock an ordinary word-processor window so the demo shows the fix
happening in the app you were already typing in, not inside this app.

The gibberish comes from the real layout mapping, so the frames always show
what the Hebrew layout would actually produce for the demo sentence.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from he_en_fixer.mapping import en_to_he  # noqa: E402

OUTPUT = ROOT / "docs" / "demo.gif"
ICON = ROOT / "he_en_fixer" / "assets" / "icon.png"

WIDTH, HEIGHT = 900, 560

SENTENCE = "hello team"
GIBBERISH = en_to_he(SENTENCE)
HEADING = "Weekly update"

DESKTOP_TOP = (222, 230, 242)
DESKTOP_BOTTOM = (198, 210, 230)
CHROME_BLUE = (43, 87, 154)
RIBBON = (243, 242, 241)
PAGE_SURROUND = (240, 240, 242)
WHITE = (255, 255, 255)
BORDER = (185, 194, 207)
HAIRLINE = (225, 225, 228)
INK = (26, 26, 26)
UI_TEXT = (68, 72, 79)
CAPTION_INK = (38, 50, 76)
SELECTION = (198, 220, 246)
CARET = (32, 32, 32)

WINDOW = (30, 18, 870, 470)
TITLE_H = 38
TABS_H = 32
TOOLBAR_H = 44
STATUS_H = 26
PAGE_BOX = (110, 146, 790, 444)
TEXT_X = 150

FONT_DIR = Path("/System/Library/Fonts")
FONT_UNICODE = FONT_DIR / "Supplemental" / "Arial Unicode.ttf"
FONT_BOLD = FONT_DIR / "Supplemental" / "Arial Bold.ttf"
FONT_REGULAR = FONT_DIR / "Supplemental" / "Arial.ttf"


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    if not path.exists():
        raise SystemExit(f"Missing font {path}")
    return ImageFont.truetype(str(path), size)


DOC = _font(FONT_UNICODE, 25)
DOC_HEADING = _font(FONT_BOLD, 25)
TITLE = _font(FONT_BOLD, 15)
TAB = _font(FONT_REGULAR, 13)
SMALL = _font(FONT_REGULAR, 12)
SMALL_BOLD = _font(FONT_BOLD, 13)
CAPTION = _font(FONT_REGULAR, 17)
TOAST_TITLE = _font(FONT_BOLD, 13)
TOAST_BODY = _font(FONT_UNICODE, 14)

TABS = ("File", "Home", "Insert", "Draw", "Layout", "Review", "View")
ACTIVE_TAB = "Home"


def _desktop() -> Image.Image:
    base = Image.new("RGB", (WIDTH, HEIGHT), DESKTOP_TOP)
    draw = ImageDraw.Draw(base)
    for y in range(HEIGHT):
        ratio = y / (HEIGHT - 1)
        draw.line(
            [(0, y), (WIDTH, y)],
            fill=tuple(
                round(top + (bottom - top) * ratio)
                for top, bottom in zip(DESKTOP_TOP, DESKTOP_BOTTOM)
            ),
        )
    return base


def _window_buttons(draw: ImageDraw.ImageDraw, right: int, mid: int) -> None:
    close_x = right - 26
    draw.line([(close_x - 5, mid - 5), (close_x + 5, mid + 5)], fill=WHITE, width=2)
    draw.line([(close_x - 5, mid + 5), (close_x + 5, mid - 5)], fill=WHITE, width=2)
    box_x = right - 60
    draw.rectangle((box_x - 5, mid - 5, box_x + 5, mid + 5), outline=WHITE, width=2)
    min_x = right - 94
    draw.line([(min_x - 5, mid), (min_x + 5, mid)], fill=WHITE, width=2)


def _toolbar(draw: ImageDraw.ImageDraw, top: int) -> None:
    mid = top + TOOLBAR_H // 2
    draw.rounded_rectangle((126, mid - 13, 232, mid + 13), radius=3, outline=HAIRLINE, width=1)
    draw.text((134, mid), "Arial", font=SMALL, fill=UI_TEXT, anchor="lm")
    draw.rounded_rectangle((240, mid - 13, 282, mid + 13), radius=3, outline=HAIRLINE, width=1)
    draw.text((248, mid), "12", font=SMALL, fill=UI_TEXT, anchor="lm")
    for offset, letter, font in ((300, "B", SMALL_BOLD), (328, "I", SMALL), (356, "U", SMALL)):
        draw.text((offset, mid), letter, font=font, fill=UI_TEXT, anchor="mm")
    draw.line([(382, mid - 12), (382, mid + 12)], fill=HAIRLINE, width=1)
    for group in (402, 452, 502):
        for row in range(3):
            width = 18 if row != 1 else 12
            y = mid - 7 + row * 7
            draw.line([(group, y), (group + width, y)], fill=UI_TEXT, width=2)


def _chrome(draw: ImageDraw.ImageDraw, *, language: str, words: int) -> None:
    left, top, right, bottom = WINDOW
    draw.rounded_rectangle((left + 3, top + 4, right + 3, bottom + 4), radius=10, fill=(176, 186, 202))
    draw.rounded_rectangle(WINDOW, radius=10, fill=WHITE, outline=BORDER, width=1)

    title_bottom = top + TITLE_H
    draw.rounded_rectangle((left, top, right, title_bottom), radius=10, fill=CHROME_BLUE)
    draw.rectangle((left, title_bottom - 12, right, title_bottom), fill=CHROME_BLUE)
    draw.text(((left + right) / 2, top + TITLE_H / 2), "Document1", font=TITLE, fill=WHITE, anchor="mm")
    _window_buttons(draw, right, top + TITLE_H // 2)

    tabs_bottom = title_bottom + TABS_H
    draw.rectangle((left + 1, title_bottom, right - 1, tabs_bottom), fill=RIBBON)
    x = left + 18
    for label in TABS:
        text_width = draw.textlength(label, font=TAB)
        if label == ACTIVE_TAB:
            draw.rounded_rectangle(
                (x - 12, title_bottom + 5, x + text_width + 12, tabs_bottom),
                radius=5,
                fill=WHITE,
            )
            draw.text((x, title_bottom + TABS_H / 2), label, font=TAB, fill=CHROME_BLUE, anchor="lm")
        else:
            draw.text((x, title_bottom + TABS_H / 2), label, font=TAB, fill=UI_TEXT, anchor="lm")
        x += text_width + 34

    _toolbar(draw, tabs_bottom)
    toolbar_bottom = tabs_bottom + TOOLBAR_H
    draw.line([(left + 1, toolbar_bottom), (right - 1, toolbar_bottom)], fill=HAIRLINE, width=1)

    status_top = bottom - STATUS_H
    draw.rectangle((left + 1, toolbar_bottom + 1, right - 1, status_top), fill=PAGE_SURROUND)
    draw.rectangle(PAGE_BOX, fill=WHITE, outline=HAIRLINE, width=1)

    draw.rounded_rectangle((left, status_top, right, bottom), radius=10, fill=CHROME_BLUE)
    draw.rectangle((left, status_top, right, status_top + 12), fill=CHROME_BLUE)
    status_mid = status_top + STATUS_H / 2
    draw.text(
        (left + 18, status_mid),
        f"Page 1 of 1     {words} words",
        font=SMALL,
        fill=WHITE,
        anchor="lm",
    )
    draw.text((right - 18, status_mid), language, font=SMALL, fill=WHITE, anchor="rm")


def _toast(draw: ImageDraw.ImageDraw, image: Image.Image) -> None:
    box = (596, 482, 862, 546)
    draw.rounded_rectangle((box[0] + 2, box[1] + 3, box[2] + 2, box[3] + 3), radius=10, fill=(176, 186, 202))
    draw.rounded_rectangle(box, radius=10, fill=WHITE, outline=BORDER, width=1)
    if ICON.exists():
        icon = Image.open(ICON).convert("RGBA").resize((30, 30), Image.Resampling.LANCZOS)
        image.paste(icon, (box[0] + 16, box[1] + 17), icon)
    draw.text((box[0] + 58, box[1] + 16), "HE \u2194 EN Fixer", font=TOAST_TITLE, fill=CAPTION_INK)
    draw.text(
        (box[0] + 58, box[1] + 36),
        f"{GIBBERISH[::-1]}  \u2192  {SENTENCE}",
        font=TOAST_BODY,
        fill=UI_TEXT,
    )


def _frame(
    *,
    typed: str,
    rtl: bool,
    caption: str,
    caret: bool = False,
    selected: bool = False,
    language: str = "Hebrew",
    toast: bool = False,
) -> Image.Image:
    image = _desktop()
    draw = ImageDraw.Draw(image)
    _chrome(draw, language=language, words=len(HEADING.split()) + len(typed.split()))

    draw.text((TEXT_X, 196), HEADING, font=DOC_HEADING, fill=INK, anchor="lm")

    baseline = 250
    # Pillow has no bidi shaper here, so the Hebrew run is drawn in visual
    # order. In an left-to-right paragraph the run stays pinned to the left
    # margin and grows rightwards, with the caret at its left edge.
    shown = typed[::-1] if rtl else typed
    text_x = TEXT_X + (16 if rtl else 0)
    width = draw.textlength(shown, font=DOC)

    if selected and shown:
        draw.rectangle((text_x - 3, baseline - 19, text_x + width + 3, baseline + 15), fill=SELECTION)
    draw.text((text_x, baseline), shown, font=DOC, fill=INK, anchor="lm")

    if caret:
        caret_x = TEXT_X + 5 if rtl else text_x + width + 5
        draw.line([(caret_x, baseline - 18), (caret_x, baseline + 14)], fill=CARET, width=2)

    draw.text((40, 502), caption, font=CAPTION, fill=CAPTION_INK)
    if toast:
        _toast(draw, image)
    return image


def _build_frames() -> list[tuple[Image.Image, int]]:
    """Return (frame, milliseconds) pairs. Every frame is distinct."""
    frames: list[tuple[Image.Image, int]] = []
    typing_caption = "Typing in any app \u2014 with the keyboard still on Hebrew"

    frames.append((_frame(typed="", rtl=True, caption=typing_caption, caret=True), 450))

    for index in range(1, len(GIBBERISH) + 1):
        frames.append(
            (
                _frame(
                    typed=GIBBERISH[:index],
                    rtl=True,
                    caption=typing_caption,
                    caret=True,
                ),
                150,
            )
        )

    waiting = "You stop typing\u2026"
    frames.append((_frame(typed=GIBBERISH, rtl=True, caption=waiting, caret=True), 450))
    frames.append((_frame(typed=GIBBERISH, rtl=True, caption=waiting), 400))
    frames.append(
        (_frame(typed=GIBBERISH, rtl=True, caption=waiting, selected=True), 130)
    )

    fixed_caption = "Fixed in place \u2014 and the keyboard switched to English"
    frames.append(
        (
            _frame(
                typed=SENTENCE,
                rtl=False,
                caption=fixed_caption,
                selected=True,
                language="English (United States)",
            ),
            130,
        )
    )
    frames.append(
        (
            _frame(
                typed=SENTENCE,
                rtl=False,
                caption=fixed_caption,
                caret=True,
                language="English (United States)",
            ),
            220,
        )
    )
    frames.append(
        (
            _frame(
                typed=SENTENCE,
                rtl=False,
                caption=fixed_caption,
                caret=True,
                language="English (United States)",
                toast=True,
            ),
            2000,
        )
    )

    return frames


def _shared_palette(frames: list[Image.Image]) -> Image.Image:
    """One palette built from every frame, so no colour drifts between them."""
    strip = Image.new("RGB", (WIDTH, HEIGHT * len(frames)))
    for index, frame in enumerate(frames):
        strip.paste(frame, (0, HEIGHT * index))
    return strip.quantize(colors=160)


def main() -> None:
    frames = _build_frames()
    palette = _shared_palette([frame for frame, _ in frames])
    flattened = [
        frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame, _ in frames
    ]
    durations = [ms for _, ms in frames]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    flattened[0].save(
        OUTPUT,
        save_all=True,
        append_images=flattened[1:],
        duration=durations,
        loop=0,
        optimize=False,
    )
    size_kb = OUTPUT.stat().st_size / 1024
    total_s = sum(durations) / 1000
    print(f"Wrote {OUTPUT} ({len(frames)} frames, {total_s:.1f}s, {size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
