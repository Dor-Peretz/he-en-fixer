"""Create packaging/icon.ico from the tray artwork."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "packaging"
OUT.mkdir(parents=True, exist_ok=True)


def make_image(size: int) -> Image.Image:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = max(1, size // 32)
    draw.rounded_rectangle(
        (margin, margin, size - margin - 1, size - margin - 1),
        radius=size // 5,
        fill=(47, 92, 168, 255),
    )
    try:
        font = ImageFont.truetype("segoeui.ttf", max(10, size // 3))
    except OSError:
        font = ImageFont.load_default()
    draw.text((size * 0.14, size * 0.28), "A", font=font, fill="white")
    draw.text((size * 0.50, size * 0.22), "א", font=font, fill=(255, 214, 90, 255))
    return image


def main() -> None:
    images = [make_image(s) for s in (16, 32, 48, 64, 128, 256)]
    images[0].save(
        OUT / "icon.ico",
        format="ICO",
        sizes=[(s, s) for s in (16, 32, 48, 64, 128, 256)],
        append_images=images[1:],
    )
    make_image(256).save(OUT / "icon.png")
    print(f"Wrote {OUT / 'icon.ico'}")


if __name__ == "__main__":
    main()
