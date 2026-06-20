from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
MANIFEST_PATH = ASSETS_DIR / "ruffy_sprite_manifest.json"
ARCHIVE_DIR = ASSETS_DIR / "sprites" / "archive"

CELL_WIDTH = 192
CELL_HEIGHT = 208
ALPHA_THRESHOLD = 24


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    atlas_path = ASSETS_DIR / manifest["image"]
    source_atlas = Image.open(atlas_path).convert("RGBA")

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = ARCHIVE_DIR / "ruffy_spritesheet_pre_strict_rebuild.png"
    if not archive_path.exists():
        source_atlas.save(archive_path)

    rebuilt = Image.new("RGBA", source_atlas.size, (0, 0, 0, 0))

    row_sources = {
        int(spec["row"]): name
        for name, spec in manifest["animations"].items()
        if name not in {"review", "carry_run", "power_up"}
    }

    for row in range(manifest["rows"]):
        animation = row_sources.get(row)
        if animation is None:
            continue
        spec = manifest["animations"][animation]
        frame_count = int(spec["frames"])
        for col in range(frame_count):
            frame = source_atlas.crop(
                (
                    col * CELL_WIDTH,
                    row * CELL_HEIGHT,
                    (col + 1) * CELL_WIDTH,
                    (row + 1) * CELL_HEIGHT,
                )
            )
            rebuilt_frame = rebuild_frame(frame, animation)
            rebuilt.alpha_composite(rebuilt_frame, (col * CELL_WIDTH, row * CELL_HEIGHT))

    rebuilt.save(atlas_path)
    print(f"rebuilt {atlas_path}")
    print(f"archived previous atlas at {archive_path}")


def rebuild_frame(frame: Image.Image, animation: str) -> Image.Image:
    frame = frame.convert("RGBA")
    frame = strip_key_color(frame)

    if animation == "hatch":
        frame = keep_components(frame, min_area=180, keep_largest_only=True)
        return fit_to_cell(frame, padding=24, bottom_padding=24, allow_upscale=False)

    if animation in {"gear2"}:
        frame = keep_components(frame, min_area=36, keep_largest_only=False)
        return fit_to_cell(frame, padding=22, bottom_padding=22, allow_upscale=False)

    if animation == "rubber_punch":
        frame = keep_components(frame, min_area=70, keep_largest_only=False)
        return fit_to_cell(frame, padding=22, bottom_padding=22, allow_upscale=False)

    if animation == "run":
        frame = keep_components(frame, min_area=90, keep_largest_only=False)
        return fit_to_cell(frame, padding=24, bottom_padding=24, allow_upscale=False, target_height=112)

    frame = keep_components(frame, min_area=90, keep_largest_only=False)
    return fit_to_cell(frame, padding=24, bottom_padding=24, allow_upscale=False)


def strip_key_color(frame: Image.Image) -> Image.Image:
    output = frame.copy()
    pixels = output.load()
    for y in range(output.height):
        for x in range(output.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            green_key = g > 150 and g > r * 1.35 and g > b * 1.2
            magenta_key = r > 180 and b > 180 and g < 80
            if green_key or magenta_key:
                pixels[x, y] = (0, 0, 0, 0)
    return output


def keep_components(frame: Image.Image, min_area: int, keep_largest_only: bool) -> Image.Image:
    alpha = frame.getchannel("A")
    alpha_pixels = alpha.load()
    width, height = frame.size
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []

    for y in range(height):
        for x in range(width):
            if (x, y) in seen or alpha_pixels[x, y] <= ALPHA_THRESHOLD:
                continue
            queue = deque([(x, y)])
            seen.add((x, y))
            component: list[tuple[int, int]] = []
            while queue:
                cx, cy = queue.popleft()
                component.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if (
                        0 <= nx < width
                        and 0 <= ny < height
                        and (nx, ny) not in seen
                        and alpha_pixels[nx, ny] > ALPHA_THRESHOLD
                    ):
                        seen.add((nx, ny))
                        queue.append((nx, ny))
            components.append(component)

    if not components:
        return Image.new("RGBA", frame.size, (0, 0, 0, 0))

    components.sort(key=len, reverse=True)
    if keep_largest_only:
        kept = {point for point in components[0]}
    else:
        kept = {point for component in components if len(component) >= min_area for point in component}

    output = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    src = frame.load()
    dst = output.load()
    for x, y in kept:
        dst[x, y] = src[x, y]
    return output


def fit_to_cell(
    frame: Image.Image,
    padding: int,
    bottom_padding: int,
    allow_upscale: bool,
    target_height: int | None = None,
) -> Image.Image:
    bbox = frame.getchannel("A").point(lambda a: 255 if a > ALPHA_THRESHOLD else 0).getbbox()
    if bbox is None:
        return Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))

    subject = frame.crop(bbox)
    max_width = CELL_WIDTH - padding * 2
    max_height = CELL_HEIGHT - padding - bottom_padding
    scale = min(max_width / subject.width, max_height / subject.height)
    if target_height is not None:
        scale = min(scale, target_height / subject.height)
    if not allow_upscale:
        scale = min(scale, 1.0)

    new_size = (
        max(1, round(subject.width * scale)),
        max(1, round(subject.height * scale)),
    )
    if new_size != subject.size:
        subject = subject.resize(new_size, Image.Resampling.LANCZOS)

    cell = Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
    x = (CELL_WIDTH - subject.width) // 2
    y = CELL_HEIGHT - bottom_padding - subject.height
    y = max(padding, min(y, CELL_HEIGHT - bottom_padding - subject.height))
    cell.alpha_composite(subject, (x, y))
    return cell


if __name__ == "__main__":
    main()
