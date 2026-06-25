from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
LOGO_DIR = ASSETS / "app_logo"
BACKGROUND = (252, 250, 247, 255)


def contain(image, canvas_size, maximum_ratio):
    image = image.convert("RGBA")
    maximum = int(canvas_size * maximum_ratio)
    scale = min(maximum / image.width, maximum / image.height)
    resized = image.resize(
        (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
        Image.Resampling.LANCZOS,
    )
    canvas = Image.new("RGBA", (canvas_size, canvas_size), BACKGROUND)
    x = (canvas_size - resized.width) // 2
    y = (canvas_size - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas


def main():
    mark = Image.open(LOGO_DIR / "app_findy_logo_mark.png")
    vertical = Image.open(LOGO_DIR / "app_findy_logo_vertical.png")

    contain(mark, 1024, 0.72).convert("RGB").save(
        ASSETS / "icon.png",
        "PNG",
        optimize=True,
    )
    contain(vertical, 1536, 0.48).convert("RGB").save(
        ASSETS / "splash.png",
        "PNG",
        optimize=True,
    )
    print("Generated assets/icon.png and assets/splash.png")


if __name__ == "__main__":
    main()
