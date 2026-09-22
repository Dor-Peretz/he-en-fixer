"""App icon loading for tray, installer, and shortcuts."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .paths import is_frozen, project_root

# Fonts that carry both Latin and Hebrew, best first.
_GLYPH_FONTS = (
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial Hebrew.ttc",
    "/System/Library/Fonts/ArialHB.ttc",
)

# Alpha of the glyph when the fixer is switched off.
_OFF_ALPHA = 90


def assets_dir() -> Path:
    bundled = Path(__file__).resolve().parent / "assets"
    if getattr(sys, "_MEIPASS", None):
        meipass = Path(sys._MEIPASS) / "he_en_fixer" / "assets"
        if meipass.exists():
            return meipass
    if is_frozen():
        frozen = Path(sys.executable).resolve().parent / "he_en_fixer" / "assets"
        if frozen.exists():
            return frozen
    if bundled.exists():
        return bundled
    return project_root() / "he_en_fixer" / "assets"


def icon_png_path() -> Path | None:
    path = assets_dir() / "icon.png"
    return path if path.exists() else None


def icon_ico_path() -> Path | None:
    path = assets_dir() / "icon.ico"
    return path if path.exists() else None


def load_icon(size: int | None = None) -> Image.Image:
    path = icon_png_path()
    if path is None:
        image = Image.new("RGBA", (size or 64, size or 64), (47, 92, 168, 255))
        return image
    image = Image.open(path).convert("RGBA")
    if size:
        image = image.resize((size, size), Image.Resampling.LANCZOS)
    return image


def _glyph_font(size: int) -> ImageFont.FreeTypeFont | None:
    for candidate in _GLYPH_FONTS:
        if not Path(candidate).exists():
            continue
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return None


def _letter_image(letter: str, target_height: int, alpha: int) -> Image.Image | None:
    """Render one letter tightly cropped, scaled so every letter shares a height."""
    font = _glyph_font(int(target_height * 1.4))
    if font is None:
        return None
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    left, top, right, bottom = probe.textbbox((0, 0), letter, font=font)
    if right <= left or bottom <= top:
        return None
    tile = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((-left, -top), letter, font=font, fill=(0, 0, 0, alpha))
    width = max(1, round(tile.width * target_height / tile.height))
    return tile.resize((width, target_height), Image.Resampling.LANCZOS)


def menu_bar_icon(enabled: bool, height: int = 22, scale: int = 2) -> Image.Image:
    """A monochrome 'Aא' glyph for the macOS menu bar, faded when the fixer is off.

    Rendered as a template image, so macOS recolours it for light and dark menu bars.
    """
    h = height * scale
    alpha = 255 if enabled else _OFF_ALPHA
    letter_height = round(h * 0.5)
    gap = round(h * 0.16)

    letters = [_letter_image(letter, letter_height, alpha) for letter in ("A", "א")]
    if any(tile is None for tile in letters):
        # No usable font: a filled/hollow square still shows the state.
        image = Image.new("RGBA", (h, h), (0, 0, 0, 0))
        pad = h * 0.18
        ImageDraw.Draw(image).rounded_rectangle(
            (pad, pad, h - pad, h - pad),
            radius=h * 0.2,
            fill=(0, 0, 0, alpha) if enabled else None,
            outline=(0, 0, 0, alpha),
            width=max(1, scale),
        )
        return image

    width = sum(tile.width for tile in letters) + gap
    image = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    x = 0
    for tile in letters:
        image.alpha_composite(tile, (x, (h - tile.height) // 2))
        x += tile.width + gap
    if not enabled:
        _strike_through(image, scale)
    return image


def _strike_through(image: Image.Image, scale: int) -> None:
    """A slash across the glyph, so 'off' reads at a glance and not just as faded."""
    # Drawn oversized and scaled down, because PIL lines have no anti-aliasing.
    ss = 4
    layer = Image.new("RGBA", (image.width * ss, image.height * ss), (0, 0, 0, 0))
    inset = layer.height * 0.12
    ImageDraw.Draw(layer).line(
        (inset, layer.height - inset, layer.width - inset, inset),
        fill=(0, 0, 0, 255),
        width=max(2, round(1.5 * scale)) * ss,
    )
    image.alpha_composite(layer.resize(image.size, Image.Resampling.LANCZOS))


def tray_icon(enabled: bool) -> Image.Image:
    """Tray image for the current platform, reflecting whether the fixer is on."""
    if sys.platform == "darwin":
        return menu_bar_icon(enabled)
    image = load_icon(64)
    if enabled:
        return image
    faded = image.copy()
    alpha = faded.getchannel("A").point(lambda value: value * _OFF_ALPHA // 255)
    faded.putalpha(alpha)
    return faded
