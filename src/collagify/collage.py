"""Core collage-building logic, kept UI-agnostic so it can be reused by the CLI and the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import IO

from PIL import Image, ImageOps

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff"}


def find_images(input_dir: Path) -> list[Path]:
    """Return image files in `input_dir`, sorted by filename for a stable layout."""
    if not input_dir.is_dir():
        raise NotADirectoryError(f"{input_dir} is not a directory")

    return sorted(
        p for p in input_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS
    )


def load_image(source: Path | IO[bytes]) -> Image.Image:
    """Open an image from a path or file-like object, normalized for tiling.

    Applies EXIF-orientation transposition and converts to RGB, so callers
    never need to think about source rotation or color mode.
    """
    with Image.open(source) as img:
        img = ImageOps.exif_transpose(img)
        return img.convert("RGB")


def build_collage(
    images: list[Image.Image],
    target_height: int = 400,
    spacing: int = 10,
    background: str = "white",
) -> Image.Image:
    """Tile already-loaded images left-to-right into a single row, scaled to a common height.

    Each image is resized (preserving aspect ratio) to `target_height`, then
    pasted side by side with `spacing` pixels between them.
    """
    if not images:
        raise ValueError("No images provided to build_collage")

    resized = []
    for img in images:
        ratio = target_height / img.height
        new_width = max(1, round(img.width * ratio))
        resized.append(img.resize((new_width, target_height)))

    total_width = sum(img.width for img in resized) + spacing * (len(resized) - 1)
    collage = Image.new("RGB", (total_width, target_height), color=background)

    x = 0
    for img in resized:
        collage.paste(img, (x, 0))
        x += img.width + spacing

    return collage


def create_collage(
    image_paths: list[Path],
    output_path: Path,
    target_height: int = 400,
    spacing: int = 10,
    background: str = "white",
) -> Path:
    """Load images from disk, tile them, and save the result to `output_path`."""
    if not image_paths:
        raise ValueError("No images provided to create_collage")

    images = [load_image(path) for path in image_paths]
    collage = build_collage(
        images, target_height=target_height, spacing=spacing, background=background
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    collage.save(output_path)
    return output_path
