from pathlib import Path
from typing import Annotated

import typer
from rich import print

from collagify.collage import create_collage, find_images

app = typer.Typer(add_completion=False)


@app.command()
def main(
    input_dir: Annotated[
        Path, typer.Option("--input-dir", "-i", help="Folder containing source images")
    ] = Path("images"),
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Path to write the collage to")
    ] = Path("output/collage.png"),
    height: Annotated[
        int, typer.Option("--height", "-h", help="Height (px) each image is scaled to")
    ] = 400,
    spacing: Annotated[
        int, typer.Option("--spacing", "-s", help="Gap (px) between images")
    ] = 10,
    background: Annotated[
        str, typer.Option("--background", "-b", help="Background color (name or hex)")
    ] = "white",
) -> None:
    """Tile every image in INPUT_DIR into a single-row collage."""
    images = find_images(input_dir)
    if not images:
        print(f"[red]No images found in {input_dir}[/red]")
        raise typer.Exit(code=1)

    print(f"Found [bold]{len(images)}[/bold] images in {input_dir}")
    result_path = create_collage(
        images, output, target_height=height, spacing=spacing, background=background
    )
    print(f"[green]Collage saved to {result_path}[/green]")


if __name__ == "__main__":
    app()
