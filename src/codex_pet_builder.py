from __future__ import annotations

import json
import argparse
from pathlib import Path

from PIL import Image, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
SOURCE_MANIFEST = ASSETS_DIR / "pets" / "ruffy" / "manifest.json"
DEFAULT_OUTPUT_DIR = ASSETS_DIR / "codex" / "ruffy"

CONTRACT_COLUMNS = 8
CONTRACT_ROWS = 9
CELL_WIDTH = 192
CELL_HEIGHT = 208


def main():
    args = parse_args()
    source_manifest = args.manifest
    if not source_manifest.is_absolute():
        source_manifest = PROJECT_ROOT / source_manifest
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
    source_atlas = Image.open(source_manifest.parent / manifest["image"]).convert("RGBA")

    atlas = Image.new(
        "RGBA",
        (CONTRACT_COLUMNS * CELL_WIDTH, CONTRACT_ROWS * CELL_HEIGHT),
        (0, 0, 0, 0),
    )

    copy_row(atlas, source_atlas, manifest, target_row=0, source_animation="idle", columns=6)
    copy_row(atlas, source_atlas, manifest, target_row=1, source_animation="run", columns=8)
    copy_row(atlas, source_atlas, manifest, target_row=2, source_animation="run", columns=8, mirror=True)
    copy_row(atlas, source_atlas, manifest, target_row=3, source_animation="wave", columns=4)
    copy_row(atlas, source_atlas, manifest, target_row=4, source_animation="jump", columns=5, cycle_to_columns=True)
    copy_row(atlas, source_atlas, manifest, target_row=5, source_animation="failed", columns=8, cycle_to_columns=True)
    copy_row(atlas, source_atlas, manifest, target_row=6, source_animation="idle", columns=6, source_columns=[0, 1, 2, 3, 4, 5])
    copy_row(atlas, source_atlas, manifest, target_row=7, source_animation="gear2", columns=6, cycle_to_columns=True)
    copy_row(
        atlas,
        source_atlas,
        manifest,
        target_row=8,
        source_animation="gear5",
        columns=6,
        cycle_to_columns=True,
    )

    png_path = output_dir / "spritesheet.png"
    webp_path = output_dir / "spritesheet.webp"
    atlas.save(png_path)
    atlas.save(webp_path, lossless=True, quality=100, method=6)

    pet_json = {
        "id": "ruffy",
        "displayName": "Ruffy",
        "description": "A small rubber-pirate desktop pet rebuilt from the 100-sprite PET-1 source sheet.",
        "spritesheetPath": "spritesheet.webp",
    }
    (output_dir / "pet.json").write_text(json.dumps(pet_json, indent=2), encoding="utf-8")

    print(f"wrote {png_path}")
    print(f"wrote {webp_path}")
    print(f"wrote {output_dir / 'pet.json'}")


def parse_args():
    parser = argparse.ArgumentParser(description="Build a Codex-compatible pet package from a desktop atlas.")
    parser.add_argument("--manifest", type=Path, default=SOURCE_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def copy_row(
    target_atlas: Image.Image,
    source_atlas: Image.Image,
    manifest: dict,
    target_row: int,
    source_animation: str,
    columns: int,
    mirror: bool = False,
    source_columns: list[int] | None = None,
    cycle_to_columns: bool = False,
):
    source = manifest["animations"][source_animation]
    source_row = int(source["row"])
    source_columns = source_columns or list(range(int(source["frames"])))
    if cycle_to_columns and source_columns:
        expanded = []
        while len(expanded) < columns:
            expanded.extend(source_columns)
        source_columns = expanded[:columns]
    else:
        source_columns = source_columns[:columns]

    for target_column, source_column in enumerate(source_columns):
        cell = source_atlas.crop(
            (
                source_column * CELL_WIDTH,
                source_row * CELL_HEIGHT,
                (source_column + 1) * CELL_WIDTH,
                (source_row + 1) * CELL_HEIGHT,
            )
        )
        if mirror:
            cell = ImageOps.mirror(cell)
        target_atlas.alpha_composite(cell, (target_column * CELL_WIDTH, target_row * CELL_HEIGHT))


if __name__ == "__main__":
    main()
