"""Streamlit dashboard for collagify."""

from __future__ import annotations

import io

import streamlit as st

from collagify.collage import IMAGE_EXTENSIONS, build_collage, load_image


def main() -> None:
    st.set_page_config(page_title="Collagify", page_icon="🖼️", layout="wide")

    st.title("🖼️ Collagify")
    st.caption(
        "Tile your images into a single side-by-side collage so small "
        "differences jump out at a glance."
    )

    controls, preview = st.columns([1, 2], gap="large")

    with controls:
        uploaded_files = st.file_uploader(
            "Upload images",
            type=sorted(ext.lstrip(".") for ext in IMAGE_EXTENSIONS),
            accept_multiple_files=True,
            help="Images are tiled in filename order, left to right.",
        )
        height = st.slider("Height (px)", min_value=50, max_value=1200, value=400, step=10)
        spacing = st.slider("Spacing (px)", min_value=0, max_value=100, value=10, step=1)
        background = st.color_picker("Background color", "#FFFFFF")

    with preview:
        if not uploaded_files:
            st.info("Upload two or more images to build a collage.")
            return

        files = sorted(uploaded_files, key=lambda f: f.name)
        images = [load_image(f) for f in files]
        collage = build_collage(
            images, target_height=height, spacing=spacing, background=background
        )

        st.image(
            collage,
            caption=f"{len(images)} images · {collage.width}×{collage.height}px",
            width="stretch",
        )

        buffer = io.BytesIO()
        collage.save(buffer, format="PNG")
        st.download_button(
            "Download collage",
            data=buffer.getvalue(),
            file_name="collage.png",
            mime="image/png",
        )


if __name__ == "__main__":
    main()
