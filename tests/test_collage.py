from pathlib import Path

import pytest
from PIL import Image

from collagify.collage import (
    IMAGE_EXTENSIONS,
    build_collage,
    create_collage,
    find_images,
    load_image,
)


def make_image(path: Path, size: tuple[int, int], color: str = "red") -> Path:
    Image.new("RGB", size, color=color).save(path)
    return path


class TestFindImages:
    def test_raises_if_not_a_directory(self, tmp_path: Path) -> None:
        missing = tmp_path / "does-not-exist"
        with pytest.raises(NotADirectoryError):
            find_images(missing)

    def test_raises_if_path_is_a_file(self, tmp_path: Path) -> None:
        file_path = make_image(tmp_path / "a.png", (10, 10))
        with pytest.raises(NotADirectoryError):
            find_images(file_path)

    def test_returns_empty_list_for_empty_directory(self, tmp_path: Path) -> None:
        assert find_images(tmp_path) == []

    def test_finds_all_supported_extensions(self, tmp_path: Path) -> None:
        for ext in IMAGE_EXTENSIONS:
            make_image(tmp_path / f"img{ext}", (10, 10))

        found = find_images(tmp_path)

        assert len(found) == len(IMAGE_EXTENSIONS)

    def test_ignores_unsupported_extensions(self, tmp_path: Path) -> None:
        make_image(tmp_path / "a.png", (10, 10))
        (tmp_path / "notes.txt").write_text("hello")

        found = find_images(tmp_path)

        assert found == [tmp_path / "a.png"]

    def test_extension_matching_is_case_insensitive(self, tmp_path: Path) -> None:
        make_image(tmp_path / "a.PNG", (10, 10))

        found = find_images(tmp_path)

        assert found == [tmp_path / "a.PNG"]

    def test_results_are_sorted_by_filename(self, tmp_path: Path) -> None:
        make_image(tmp_path / "c.png", (10, 10))
        make_image(tmp_path / "a.png", (10, 10))
        make_image(tmp_path / "b.png", (10, 10))

        found = find_images(tmp_path)

        assert found == [tmp_path / "a.png", tmp_path / "b.png", tmp_path / "c.png"]

    def test_ignores_subdirectories(self, tmp_path: Path) -> None:
        make_image(tmp_path / "a.png", (10, 10))
        (tmp_path / "subdir").mkdir()

        found = find_images(tmp_path)

        assert found == [tmp_path / "a.png"]


class TestCreateCollage:
    def test_raises_on_empty_image_list(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError):
            create_collage([], tmp_path / "out.png")

    def test_creates_output_parent_directories(self, tmp_path: Path) -> None:
        image = make_image(tmp_path / "a.png", (100, 200))
        output = tmp_path / "nested" / "dir" / "out.png"

        result = create_collage([image], output)

        assert result == output
        assert output.exists()

    def test_returns_output_path(self, tmp_path: Path) -> None:
        image = make_image(tmp_path / "a.png", (100, 200))
        output = tmp_path / "out.png"

        result = create_collage([image], output)

        assert result == output

    def test_resizes_each_image_to_target_height_preserving_aspect(
        self, tmp_path: Path
    ) -> None:
        # 100x200 (portrait) and 400x100 (landscape) source images
        img_a = make_image(tmp_path / "a.png", (100, 200))
        img_b = make_image(tmp_path / "b.png", (400, 100))
        output = tmp_path / "out.png"

        create_collage([img_a, img_b], output, target_height=50, spacing=0)

        with Image.open(output) as collage:
            # a: 100x200 -> height 50 => width round(100 * 50/200) = 25
            # b: 400x100 -> height 50 => width round(400 * 50/100) = 200
            assert collage.height == 50
            assert collage.width == 25 + 200

    def test_applies_spacing_between_images(self, tmp_path: Path) -> None:
        img_a = make_image(tmp_path / "a.png", (100, 100))
        img_b = make_image(tmp_path / "b.png", (100, 100))
        output = tmp_path / "out.png"

        create_collage([img_a, img_b], output, target_height=50, spacing=20)

        with Image.open(output) as collage:
            # each image resizes to 50x50, plus one gap of 20
            assert collage.width == 50 + 20 + 50

    def test_single_image_has_no_spacing_applied(self, tmp_path: Path) -> None:
        img_a = make_image(tmp_path / "a.png", (100, 100))
        output = tmp_path / "out.png"

        create_collage([img_a], output, target_height=50, spacing=20)

        with Image.open(output) as collage:
            assert collage.width == 50

    def test_background_color_fills_gaps(self, tmp_path: Path) -> None:
        img_a = make_image(tmp_path / "a.png", (50, 100), color="red")
        img_b = make_image(tmp_path / "b.png", (50, 100), color="red")
        output = tmp_path / "out.png"

        create_collage(
            [img_a, img_b], output, target_height=50, spacing=10, background="blue"
        )

        with Image.open(output) as collage:
            # midpoint of the spacing gap should be the background color
            mid_x = 25 + 5  # end of first resized image + half the gap
            assert collage.getpixel((mid_x, 25)) == (0, 0, 255)

    def test_narrow_image_clamps_width_to_at_least_one_pixel(
        self, tmp_path: Path
    ) -> None:
        # Very wide/short image scaled down to a tiny target height could
        # round down to 0 width; ensure it's clamped to 1.
        img_a = make_image(tmp_path / "a.png", (1, 1000))
        output = tmp_path / "out.png"

        create_collage([img_a], output, target_height=1, spacing=0)

        with Image.open(output) as collage:
            assert collage.width >= 1
            assert collage.height == 1

    def test_respects_exif_orientation(self, tmp_path: Path) -> None:
        # Build a 100x50 image with EXIF orientation 6 (rotate 90 CW),
        # so after exif_transpose it should render as 50x100.
        base = Image.new("RGB", (100, 50), color="green")
        exif = base.getexif()
        exif[0x0112] = 6  # Orientation tag
        path = tmp_path / "rotated.jpg"
        base.save(path, exif=exif)
        output = tmp_path / "out.png"

        create_collage([path], output, target_height=100, spacing=0)

        with Image.open(output) as collage:
            # after exif_transpose, source becomes 50x100; scaled to
            # target_height=100 keeps it 50x100
            assert collage.height == 100
            assert collage.width == 50

    def test_converts_non_rgb_images_to_rgb(self, tmp_path: Path) -> None:
        path = tmp_path / "a.png"
        Image.new("RGBA", (100, 100), color=(255, 0, 0, 128)).save(path)
        output = tmp_path / "out.png"

        create_collage([path], output, target_height=50, spacing=0)

        with Image.open(output) as collage:
            assert collage.mode == "RGB"


class TestLoadImage:
    def test_loads_from_path(self, tmp_path: Path) -> None:
        path = make_image(tmp_path / "a.png", (100, 100))

        img = load_image(path)

        assert img.size == (100, 100)
        assert img.mode == "RGB"

    def test_loads_from_file_like_object(self, tmp_path: Path) -> None:
        path = make_image(tmp_path / "a.png", (100, 100))

        with path.open("rb") as f:
            img = load_image(f)

        assert img.size == (100, 100)
        assert img.mode == "RGB"

    def test_converts_to_rgb(self, tmp_path: Path) -> None:
        path = tmp_path / "a.png"
        Image.new("RGBA", (10, 10), color=(255, 0, 0, 128)).save(path)

        img = load_image(path)

        assert img.mode == "RGB"


class TestBuildCollage:
    def test_raises_on_empty_image_list(self) -> None:
        with pytest.raises(ValueError):
            build_collage([])

    def test_tiles_pre_loaded_images(self, tmp_path: Path) -> None:
        img_a = load_image(make_image(tmp_path / "a.png", (100, 100)))
        img_b = load_image(make_image(tmp_path / "b.png", (100, 100)))

        collage = build_collage([img_a, img_b], target_height=50, spacing=10)

        assert collage.size == (50 + 10 + 50, 50)
