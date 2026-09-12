"""App icon loading for tray, installer, and shortcuts."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

from .paths import is_frozen, project_root


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
