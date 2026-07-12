from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).parent.parent / "src" / "collagify" / "app.py"
IMAGES_DIR = Path(__file__).parent.parent / "images"


def run_app() -> AppTest:
    at = AppTest.from_file(str(APP_PATH), default_timeout=30)
    at.run()
    return at


def upload_sample_images(at: AppTest) -> AppTest:
    files = [
        (path.name, path.read_bytes(), "image/png")
        for path in sorted(IMAGES_DIR.glob("*.png"))
    ]
    at.file_uploader[0].set_value(files).run()
    return at


def test_shows_empty_state_with_no_uploads() -> None:
    at = run_app()

    assert not at.exception
    assert len(at.info) == 1
    assert "Upload two or more images" in at.info[0].value
    assert len(at.image) == 0


def test_renders_collage_after_upload() -> None:
    at = upload_sample_images(run_app())

    assert not at.exception
    assert len(at.image) == 1
    assert len(at.download_button) == 1
    assert at.download_button[0].label == "Download collage"


def test_collage_dimensions_reflect_slider_values() -> None:
    at = run_app()
    at.slider[0].set_value(200).run()  # height
    at = upload_sample_images(at)

    caption = at.image[0].captions[0]
    assert "200" in caption


def test_defaults_are_sane() -> None:
    at = run_app()

    assert [s.label for s in at.slider] == ["Height (px)", "Spacing (px)"]
    assert at.slider[0].value == 400
    assert at.slider[1].value == 10
    assert at.color_picker[0].value == "#FFFFFF"
