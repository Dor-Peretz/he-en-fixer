"""Build icon.png / icon.ico from the master artwork."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "he_en_fixer" / "assets"
PACKAGING = ROOT / "packaging"
SIZES = (16, 24, 32, 48, 64, 128, 256)


def _knockout_white(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    pixels = image.load()
    width, height = image.size
    assert pixels is not None
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if red > 248 and green > 248 and blue > 248:
                pixels[x, y] = (red, green, blue, 0)
    return image


def main() -> None:
    source = ASSETS / "icon-source.png"
    if not source.exists():
        raise SystemExit(f"Missing {source}")
    ASSETS.mkdir(parents=True, exist_ok=True)
    PACKAGING.mkdir(parents=True, exist_ok=True)

    master = _knockout_white(Image.open(source))
    master.save(ASSETS / "icon.png", format="PNG")
    PACKAGING.joinpath("icon.png").write_bytes((ASSETS / "icon.png").read_bytes())

    ico_base = master.resize((256, 256), Image.Resampling.LANCZOS)
    ico_base.save(
        ASSETS / "icon.ico",
        format="ICO",
        sizes=[(size, size) for size in SIZES],
    )
    (PACKAGING / "icon.ico").write_bytes((ASSETS / "icon.ico").read_bytes())
    print(f"Wrote {ASSETS / 'icon.png'} and {ASSETS / 'icon.ico'}")


if __name__ == "__main__":
    main()
