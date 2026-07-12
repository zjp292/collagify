from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from collagify.cli import app

runner = CliRunner()


def make_image(path: Path, size: tuple[int, int] = (100, 100)) -> Path:
    Image.new("RGB", size, color="red").save(path)
    return path


def test_errors_when_no_images_found(tmp_path: Path) -> None:
    empty_dir = tmp_path / "images"
    empty_dir.mkdir()

    result = runner.invoke(app, ["--input-dir", str(empty_dir)])

    assert result.exit_code == 1
    assert "No images found" in result.stdout


def test_creates_collage_with_default_options(tmp_path: Path) -> None:
    input_dir = tmp_path / "images"
    input_dir.mkdir()
    make_image(input_dir / "a.png")
    make_image(input_dir / "b.png")
    output = tmp_path / "output" / "collage.png"

    result = runner.invoke(
        app, ["--input-dir", str(input_dir), "--output", str(output)]
    )

    assert result.exit_code == 0
    assert "Found" in result.stdout
    assert "Collage saved to" in result.stdout
    assert output.exists()


def test_respects_custom_height_spacing_and_background(tmp_path: Path) -> None:
    input_dir = tmp_path / "images"
    input_dir.mkdir()
    make_image(input_dir / "a.png", (100, 100))
    make_image(input_dir / "b.png", (100, 100))
    output = tmp_path / "collage.png"

    result = runner.invoke(
        app,
        [
            "--input-dir",
            str(input_dir),
            "--output",
            str(output),
            "--height",
            "20",
            "--spacing",
            "5",
            "--background",
            "blue",
        ],
    )

    assert result.exit_code == 0
    with Image.open(output) as collage:
        assert collage.height == 20
        assert collage.width == 20 + 5 + 20


def test_short_option_flags(tmp_path: Path) -> None:
    input_dir = tmp_path / "images"
    input_dir.mkdir()
    make_image(input_dir / "a.png")
    output = tmp_path / "collage.png"

    result = runner.invoke(
        app,
        [
            "-i",
            str(input_dir),
            "-o",
            str(output),
            "-h",
            "30",
            "-s",
            "2",
            "-b",
            "white",
        ],
    )

    assert result.exit_code == 0
    assert output.exists()
