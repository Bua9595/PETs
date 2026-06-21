from __future__ import annotations

import json
import shutil
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
PET_DIR = ASSETS_DIR / "pets" / "pet2_chibi"

SOURCE_SHEETS = {
    "main": ASSETS_DIR / "source" / "pet2_chibi_master_main.png",
    "support": ASSETS_DIR / "source" / "pet2_chibi_master_support.png",
    "extra": ASSETS_DIR / "source" / "pet2_chibi_master_extra.png",
}

CELL_WIDTH = 256
CELL_HEIGHT = 256
ATLAS_COLUMNS = 8
TARGET_PADDING = 24
MIN_PADDING = 18
MIN_COMPONENT_PIXELS = 800


@dataclass(frozen=True)
class StatePlan:
    name: str
    refs: list[tuple[str, int]]
    timing_ms: int
    loop: bool
    notes: str


STATE_PLANS = [
    StatePlan("idle", [("main", 1), ("main", 4), ("main", 6), ("main", 4)], 360, True, "Neutral/friendly idle loop."),
    StatePlan("blink", [("main", 1), ("main", 1), ("main", 5), ("main", 1)], 340, True, "Blink and settle."),
    StatePlan("wave", [("main", 6), ("main", 2), ("main", 6)], 320, True, "Friendly wave / open-hand greet."),
    StatePlan("wink", [("main", 8), ("support", 16), ("main", 8)], 320, True, "Playful wink loop."),
    StatePlan("happy", [("extra", 17), ("extra", 38), ("main", 16), ("extra", 9)], 300, True, "Big happy / streamer cheer."),
    StatePlan("shy", [("extra", 13), ("main", 19), ("extra", 13)], 340, True, "Shy held pose."),
    StatePlan("surprised", [("extra", 10), ("main", 18), ("extra", 10)], 320, True, "Surprised reaction."),
    StatePlan("confused", [("main", 20), ("main", 19), ("main", 20)], 340, True, "Confused / unsure look."),
    StatePlan("thinking", [("extra", 18), ("main", 17), ("extra", 18)], 340, True, "Thinking / tactical gamer look."),
    StatePlan("mischief", [("support", 2), ("support", 2), ("support", 2)], 420, True, "Emoji-inspired fishbowl drink pose."),
    StatePlan("heart", [("extra", 8), ("main", 45), ("extra", 8)], 320, True, "Heart / affectionate pose."),
    StatePlan("peace", [("extra", 14), ("main", 43), ("extra", 14)], 320, True, "Peace sign pose."),
    StatePlan("facepalm", [("support", 11), ("main", 11), ("support", 11)], 340, True, "Facepalm loop."),
    StatePlan("walk", [("main", 25), ("main", 22), ("main", 24), ("main", 22)], 300, True, "Short walk cycle."),
    StatePlan("run", [("main", 23), ("main", 26), ("support", 19), ("main", 33)], 240, True, "Run cycle with stronger motion."),
    StatePlan("jump", [("main", 22), ("extra", 15), ("main", 27), ("extra", 21)], 300, False, "Jump start, air, peak, land."),
    StatePlan("drag_react", [("support", 22), ("support", 22), ("extra", 21)], 340, True, "Dragged / dropped reaction."),
    StatePlan("cursor_follow", [("extra", 32), ("main", 29), ("extra", 32)], 320, True, "Pointer-following pose."),
    StatePlan("drink", [("extra", 39), ("extra", 39), ("extra", 39)], 420, True, "Emoji-inspired normal cup/glass drink pose."),
    StatePlan("gaming", [("main", 12), ("extra", 6), ("main", 12)], 380, True, "Controller gaming pose."),
    StatePlan("gaming_focus", [("main", 13), ("extra", 40), ("extra", 37)], 380, True, "Focused gamer vibe."),
    StatePlan("laptop", [("main", 9), ("extra", 5), ("main", 10)], 380, True, "Laptop / stream-work loop."),
    StatePlan("phone", [("main", 14), ("extra", 27), ("extra", 24)], 360, True, "Phone / texting poses."),
    StatePlan("celebrate", [("extra", 9), ("main", 16), ("extra", 38), ("extra", 36)], 300, True, "Celebrate / victory loop."),
    StatePlan("cheer_arms_up", [("support", 3), ("support", 3), ("support", 3)], 420, True, "Emoji-inspired mischievous grin pose."),
    StatePlan("rest", [("main", 34), ("support", 30), ("extra", 26)], 420, True, "Cozy sit / blanket rest."),
    StatePlan("sleepy", [("main", 21), ("main", 28), ("extra", 41)], 480, True, "Sleepy / nap sequence."),
    StatePlan("sit_edge", [("extra", 20), ("main", 38), ("support", 25)], 380, True, "Sit on edge / ledge."),
    StatePlan("hang_edge", [("extra", 28), ("main", 24), ("main", 23)], 340, True, "Hang from edge / peek over ledge."),
    StatePlan("peek_side", [("extra", 23), ("main", 39), ("extra", 23)], 340, True, "Peek from side / doorway."),
    StatePlan("folder_play", [("extra", 31), ("extra", 31), ("extra", 32)], 360, True, "Carry folder / inspect object."),
    StatePlan("pet_play", [("extra", 34), ("main", 41), ("extra", 34)], 380, True, "Play with pet / object."),
    StatePlan("greet_pet", [("extra", 35), ("main", 42), ("extra", 35)], 360, True, "Greeting / celebrating with other pet."),
    StatePlan("ko", [("extra", 43), ("main", 35), ("main", 6)], 500, True, "KO / game-over gag."),
    StatePlan("ko_ghost", [("support", 6), ("support", 6), ("support", 6)], 500, True, "Exact KO emoji pose with ghost cue."),
]


def main() -> None:
    missing = [path for path in SOURCE_SHEETS.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing PET2 source sheets: {missing}")

    if PET_DIR.exists():
        shutil.rmtree(PET_DIR)
    (PET_DIR / "row_sources").mkdir(parents=True, exist_ok=True)
    (PET_DIR / "previews").mkdir(parents=True, exist_ok=True)
    (PET_DIR / "qa").mkdir(parents=True, exist_ok=True)

    source_frames = extract_all_sources()
    atlas_path, manifest_path, states = build_pet_outputs(source_frames)
    qa_report = write_qa(source_frames, states)
    write_contact_sheets(source_frames, states)
    write_previews_and_review(manifest_path)
    write_runtime_test_note()

    print(
        json.dumps(
            {
                "sources": {name: str(path.relative_to(PROJECT_ROOT)) for name, path in SOURCE_SHEETS.items()},
                "spritesheet": str(atlas_path.relative_to(PROJECT_ROOT)),
                "manifest": str(manifest_path.relative_to(PROJECT_ROOT)),
                "states": [state["name"] for state in states],
                "qa_states": len(qa_report["states"]),
            },
            indent=2,
        )
    )


def extract_all_sources() -> dict[str, dict]:
    output: dict[str, dict] = {}
    for source_name, path in SOURCE_SHEETS.items():
        image = Image.open(path).convert("RGBA")
        components = extract_components(image)
        for index, component in enumerate(components, start=1):
            raw = image.crop(component["bbox"])
            cleaned = crop_to_transparency(raw)
            refined = reduce_edge_halo(cleaned)
            fitted = fit_to_cell(refined)
            key = f"{source_name}_{index:02d}"
            save_path = PET_DIR / "row_sources" / f"{key}.png"
            fitted.save(save_path)
            output[key] = {
                "key": key,
                "source_name": source_name,
                "source_index": index,
                "bbox": component["bbox"],
                "raw_image": refined,
                "image": fitted,
                "path": save_path,
                "metrics": frame_metrics(fitted),
            }
    return output


def extract_components(image: Image.Image) -> list[dict]:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    visited = [[False for _ in range(width)] for _ in range(height)]
    components: list[dict] = []

    for y in range(height):
        for x in range(width):
            if visited[y][x]:
                continue
            visited[y][x] = True
            if is_chroma_pixel(pixels[x, y]):
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            min_x = max_x = x
            min_y = max_y = y
            count = 0
            while queue:
                cx, cy = queue.popleft()
                count += 1
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                        visited[ny][nx] = True
                        if not is_chroma_pixel(pixels[nx, ny]):
                            queue.append((nx, ny))
            bbox = (min_x, min_y, max_x + 1, max_y + 1)
            bw = bbox[2] - bbox[0]
            bh = bbox[3] - bbox[1]
            if count >= MIN_COMPONENT_PIXELS and bw >= 40 and bh >= 40:
                components.append({"pixels": count, "bbox": bbox})
    components.sort(key=lambda item: (item["bbox"][1], item["bbox"][0]))
    return components


def is_chroma_pixel(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, a = pixel
    if a == 0:
        return True
    return r > 170 and b > 170 and g < 120 and abs(r - b) < 90 and min(r, b) - g > 60


def crop_to_transparency(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    visited = [[False for _ in range(width)] for _ in range(height)]
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= width or y >= height or visited[y][x]:
            continue
        visited[y][x] = True
        if not is_chroma_pixel(pixels[x, y]):
            continue
        pixels[x, y] = (0, 0, 0, 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    bbox = rgba.getbbox()
    if bbox is None:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    return keep_largest_component(rgba.crop(bbox))


def keep_largest_component(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    visited = [[False for _ in range(width)] for _ in range(height)]
    components: list[tuple[int, tuple[int, int, int, int]]] = []

    for y in range(height):
        for x in range(width):
            if visited[y][x]:
                continue
            visited[y][x] = True
            if pixels[x, y][3] == 0:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            min_x = max_x = x
            min_y = max_y = y
            count = 0
            while queue:
                cx, cy = queue.popleft()
                count += 1
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                        visited[ny][nx] = True
                        if pixels[nx, ny][3] > 0:
                            queue.append((nx, ny))
            components.append((count, (min_x, min_y, max_x + 1, max_y + 1)))

    if not components:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    components.sort(key=lambda item: item[0], reverse=True)
    return rgba.crop(components[0][1])


def reduce_edge_halo(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    contracted = alpha.filter(ImageFilter.MinFilter(3))
    deeply_contracted = alpha.filter(ImageFilter.MinFilter(5))
    softened = alpha.point(lambda a: max(0, a - 36))
    new_alpha = ImageChops.lighter(contracted, softened)

    output = rgba.copy()
    out_pixels = output.load()
    src_pixels = rgba.load()
    alpha_pixels = alpha.load()
    contracted_pixels = contracted.load()
    deep_pixels = deeply_contracted.load()
    width, height = rgba.size

    for y in range(height):
        for x in range(width):
            current_alpha = new_alpha.getpixel((x, y))
            if current_alpha == 0:
                out_pixels[x, y] = (0, 0, 0, 0)
                continue
            r, g, b, _ = src_pixels[x, y]
            if not edge_zone(alpha, x, y):
                out_pixels[x, y] = (r, g, b, current_alpha)
                continue
            chroma_like = is_chroma_pixel((r, g, b, 255)) or is_outline_tint(r, g, b)
            white_like = is_white_halo(r, g, b)
            if chroma_like or white_like:
                samples = []
                for radius in (1, 2, 3):
                    for ny in range(max(0, y - radius), min(height, y + radius + 1)):
                        for nx in range(max(0, x - radius), min(width, x + radius + 1)):
                            if nx == x and ny == y:
                                continue
                            if contracted_pixels[nx, ny] <= 0:
                                continue
                            nr, ng, nb, na = src_pixels[nx, ny]
                            if na > 0 and not is_chroma_pixel((nr, ng, nb, 255)):
                                samples.append((nr, ng, nb))
                    if samples:
                        break
                if samples:
                    r = round(sum(item[0] for item in samples) / len(samples))
                    g = round(sum(item[1] for item in samples) / len(samples))
                    b = round(sum(item[2] for item in samples) / len(samples))
                    if chroma_like:
                        current_alpha = min(current_alpha, 120)
                    elif white_like:
                        current_alpha = min(current_alpha, 170)
                elif deep_pixels[x, y] == 0:
                    out_pixels[x, y] = (0, 0, 0, 0)
                    continue
            elif contracted_pixels[x, y] == 0:
                current_alpha = max(0, current_alpha - 40)
            out_pixels[x, y] = (r, g, b, current_alpha)

    bbox = output.getbbox()
    if bbox is None:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    return output.crop(bbox)


def is_white_halo(r: int, g: int, b: int) -> bool:
    return r > 205 and g > 205 and b > 205


def is_outline_tint(r: int, g: int, b: int) -> bool:
    return max(r, b) > 90 and r > g + 25 and b > g + 25


def fit_to_cell(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    if bbox is None:
        return Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
    cropped = image.crop(bbox)
    max_w = CELL_WIDTH - TARGET_PADDING * 2
    max_h = CELL_HEIGHT - TARGET_PADDING * 2
    scale = min(max_w / cropped.width, max_h / cropped.height, 3.0)
    resized = cropped.resize(
        (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale))),
        Image.Resampling.LANCZOS,
    )
    cell = Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
    x = (CELL_WIDTH - resized.width) // 2
    y = CELL_HEIGHT - TARGET_PADDING - resized.height
    if y < TARGET_PADDING:
        y = (CELL_HEIGHT - resized.height) // 2
    cell.alpha_composite(resized, (x, y))
    return cell


def frame_metrics(image: Image.Image) -> dict:
    bbox = image.getbbox()
    if bbox is None:
        return {
            "min_margin_px": 999,
            "edge_touch_count": 0,
            "white_edge_pixels": 0,
            "magenta_edge_pixels": 0,
            "groundline_px": 0,
            "height_px": 0,
        }
    alpha = image.getchannel("A")
    pixels = image.load()
    margin = min(bbox[0], bbox[1], image.width - bbox[2], image.height - bbox[3])
    edge_touches = 0
    white_edges = 0
    magenta_edges = 0

    for x in range(image.width):
        edge_touches += int(alpha.getpixel((x, 0)) > 0)
        edge_touches += int(alpha.getpixel((x, image.height - 1)) > 0)
    for y in range(image.height):
        edge_touches += int(alpha.getpixel((0, y)) > 0)
        edge_touches += int(alpha.getpixel((image.width - 1, y)) > 0)

    for y in range(image.height):
        for x in range(image.width):
            if alpha.getpixel((x, y)) == 0 or not edge_zone(alpha, x, y):
                continue
            r, g, b, _ = pixels[x, y]
            if is_white_halo(r, g, b):
                white_edges += 1
            if is_chroma_pixel((r, g, b, 255)) or is_outline_tint(r, g, b):
                magenta_edges += 1

    return {
        "min_margin_px": int(margin),
        "edge_touch_count": int(edge_touches),
        "white_edge_pixels": int(white_edges),
        "magenta_edge_pixels": int(magenta_edges),
        "groundline_px": int(bbox[3]),
        "height_px": int(bbox[3] - bbox[1]),
    }


def edge_zone(alpha: Image.Image, x: int, y: int) -> bool:
    width, height = alpha.size
    if alpha.getpixel((x, y)) == 0:
        return False
    for ny in range(max(0, y - 1), min(height, y + 2)):
        for nx in range(max(0, x - 1), min(width, x + 2)):
            if alpha.getpixel((nx, ny)) == 0:
                return True
    return False


def build_pet_outputs(source_frames: dict[str, dict]) -> tuple[Path, Path, list[dict]]:
    states: list[dict] = []
    atlas = Image.new("RGBA", (ATLAS_COLUMNS * CELL_WIDTH, len(STATE_PLANS) * CELL_HEIGHT), (0, 0, 0, 0))
    animations: dict[str, dict] = {}

    for row, plan in enumerate(STATE_PLANS):
        frame_keys = [f"{source}_{index:02d}" for source, index in plan.refs]
        metrics = [source_frames[key]["metrics"] for key in frame_keys]
        min_margin = min(item["min_margin_px"] for item in metrics)
        edge_touch = max(item["edge_touch_count"] for item in metrics)
        white_edges = sum(item["white_edge_pixels"] for item in metrics)
        magenta_edges = sum(item["magenta_edge_pixels"] for item in metrics)
        heights = [item["height_px"] for item in metrics]
        groundlines = [item["groundline_px"] for item in metrics]
        accepted = (
            min_margin >= MIN_PADDING
            and edge_touch == 0
            and white_edges <= 120
            and magenta_edges <= 6
            and variation_pct(heights) <= (34 if plan.name in {"jump", "hang_edge", "sit_edge"} else 24)
            and max(groundlines) - min(groundlines) <= 28
        )
        state_info = {
            "name": plan.name,
            "frame_keys": frame_keys,
            "timing_ms": plan.timing_ms,
            "loop": plan.loop,
            "notes": plan.notes,
            "min_margin_px": min_margin,
            "edge_touch_count": edge_touch,
            "white_edge_pixels": white_edges,
            "magenta_edge_pixels": magenta_edges,
            "height_var_pct": variation_pct(heights),
            "groundline_var_px": max(groundlines) - min(groundlines),
            "accepted": accepted,
        }
        for col, key in enumerate(frame_keys):
            atlas.alpha_composite(source_frames[key]["image"], (col * CELL_WIDTH, row * CELL_HEIGHT))
        animations[plan.name] = {
            "row": row,
            "frames": len(frame_keys),
            "loop": plan.loop,
            "frame_duration_ms": plan.timing_ms,
            "source_frame_keys": frame_keys,
            "notes": plan.notes,
        }
        states.append(state_info)

    atlas_path = PET_DIR / "spritesheet.png"
    atlas.save(atlas_path)

    menu_states = [
        {"label": "Idle", "animation": "idle"},
        {"label": "Blink", "animation": "blink"},
        {"label": "Wave", "animation": "wave"},
        {"label": "Wink", "animation": "wink"},
        {"label": "Happy", "animation": "happy"},
        {"label": "Shy", "animation": "shy"},
        {"label": "Surprised", "animation": "surprised"},
        {"label": "Confused", "animation": "confused"},
        {"label": "Thinking", "animation": "thinking"},
        {"label": "Mischief", "animation": "mischief"},
        {"label": "Heart", "animation": "heart"},
        {"label": "Peace", "animation": "peace"},
        {"label": "Facepalm", "animation": "facepalm"},
        {"label": "Walk", "animation": "walk"},
        {"label": "Run", "animation": "run"},
        {"label": "Jump", "animation": "jump"},
        {"label": "Drag React", "animation": "drag_react"},
        {"label": "Cursor Follow", "animation": "cursor_follow"},
        {"label": "Drink", "animation": "drink"},
        {"label": "Gaming", "animation": "gaming"},
        {"label": "Gaming Focus", "animation": "gaming_focus"},
        {"label": "Laptop", "animation": "laptop"},
        {"label": "Phone", "animation": "phone"},
        {"label": "Celebrate", "animation": "celebrate"},
        {"label": "Arms Up Cheer", "animation": "cheer_arms_up"},
        {"label": "Rest", "animation": "rest"},
        {"label": "Sleepy", "animation": "sleepy"},
        {"label": "Sit Edge", "animation": "sit_edge"},
        {"label": "Hang", "animation": "hang_edge"},
        {"label": "Peek", "animation": "peek_side"},
        {"label": "Folder Play", "animation": "folder_play"},
        {"label": "Pet Play", "animation": "pet_play"},
        {"label": "Greet Pet", "animation": "greet_pet"},
        {"label": "KO", "animation": "ko"},
        {"label": "KO Ghost", "animation": "ko_ghost"},
    ]
    category_behavior = {
        "initial_category": "core",
        "switch_probability": 0.42,
        "attempts_before_switch_min": 2,
        "attempts_before_switch_max": 4,
        "categories": [
            {
                "id": "core",
                "label": "Core",
                "weight": 24,
                "animations": ["idle", "blink", "wave", "wink", "happy", "shy", "surprised", "confused", "thinking", "mischief", "heart", "peace", "facepalm"],
            },
            {
                "id": "movement",
                "label": "Movement",
                "weight": 18,
                "animations": ["walk", "run", "jump", "drag_react", "cursor_follow"],
            },
            {
                "id": "gamer_social",
                "label": "Gaming / Social",
                "weight": 18,
                "animations": ["drink", "gaming", "gaming_focus", "laptop", "phone", "celebrate", "cheer_arms_up"],
            },
            {
                "id": "rest",
                "label": "Rest / Cozy",
                "weight": 14,
                "animations": ["rest", "sleepy"],
            },
            {
                "id": "desktop",
                "label": "Desktop / Pet",
                "weight": 14,
                "animations": ["sit_edge", "hang_edge", "peek_side", "folder_play"],
            },
            {
                "id": "multi_pet",
                "label": "Multi-Pet",
                "weight": 8,
                "animations": ["pet_play", "greet_pet"],
            },
            {
                "id": "special",
                "label": "Special",
                "weight": 4,
                "animations": ["ko", "ko_ghost"],
            },
        ],
    }
    choices = [
        {"animation": "idle", "weight": 18},
        {"animation": "blink", "weight": 6},
        {"animation": "wave", "weight": 5},
        {"animation": "wink", "weight": 4},
        {"animation": "happy", "weight": 5},
        {"animation": "shy", "weight": 4},
        {"animation": "surprised", "weight": 3},
        {"animation": "confused", "weight": 3},
        {"animation": "thinking", "weight": 4},
        {"animation": "mischief", "weight": 3},
        {"animation": "walk", "weight": 8},
        {"animation": "run", "weight": 8},
        {"animation": "jump", "weight": 5},
        {"animation": "drag_react", "weight": 2},
        {"animation": "cursor_follow", "weight": 3},
        {"animation": "drink", "weight": 3},
        {"animation": "gaming", "weight": 4},
        {"animation": "gaming_focus", "weight": 3},
        {"animation": "laptop", "weight": 4},
        {"animation": "phone", "weight": 4},
        {"animation": "celebrate", "weight": 3},
        {"animation": "cheer_arms_up", "weight": 2},
        {"animation": "rest", "weight": 4},
        {"animation": "sleepy", "weight": 4},
        {"animation": "sit_edge", "weight": 3},
        {"animation": "hang_edge", "weight": 2},
        {"animation": "peek_side", "weight": 3},
        {"animation": "folder_play", "weight": 2},
        {"animation": "pet_play", "weight": 2},
        {"animation": "greet_pet", "weight": 2},
        {"animation": "heart", "weight": 2},
        {"animation": "peace", "weight": 2},
        {"animation": "facepalm", "weight": 2},
        {"animation": "ko", "weight": 1},
        {"animation": "ko_ghost", "weight": 1},
    ]

    manifest_path = PET_DIR / "manifest.json"
    manifest = {
        "id": "pet2_chibi",
        "display_name": "Pet 2 Chibi Girl",
        "image": "spritesheet.png",
        "source_images": {name: str(path.relative_to(PROJECT_ROOT)) for name, path in SOURCE_SHEETS.items()},
        "columns": ATLAS_COLUMNS,
        "rows": len(STATE_PLANS),
        "cell_width": CELL_WIDTH,
        "cell_height": CELL_HEIGHT,
        "frame_duration_ms": 360,
        "personality_tags": ["cute", "social", "gamer", "cheerful", "playful", "streamer", "competitive"],
        "interaction_tags": ["greet", "wave_to_other_pet", "sit_together", "play_together", "follow", "celebrate_together"],
        "compatible_group_actions": ["greet", "wave_to_other_pet", "sit_together", "play_together", "follow", "celebrate_together", "inspect_folder_together"],
        "desktop_behavior": {
            "initial_animation": "idle",
            "drag_animation": "drag_react",
            "double_click_animation": "happy",
            "animation_cooldown_seconds": 60,
            "menu_states": menu_states,
            "choices": choices,
            "category_behavior": category_behavior,
        },
        "animations": animations,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return atlas_path, manifest_path, states


def variation_pct(values: list[int]) -> float:
    if not values:
        return 0.0
    avg = sum(values) / len(values)
    if avg == 0:
        return 0.0
    return round(((max(values) - min(values)) / avg) * 100, 2)


def write_qa(source_frames: dict[str, dict], states: list[dict]) -> dict:
    report = {
        "pet": "pet2_chibi",
        "source_images": {name: str(path.relative_to(PROJECT_ROOT)) for name, path in SOURCE_SHEETS.items()},
        "states": [],
    }
    for state in states:
        report["states"].append(
            {
                "pet": "pet2_chibi",
                "state": state["name"],
                "frames": len(state["frame_keys"]),
                "timing_ms": state["timing_ms"],
                "min_margin_px": state["min_margin_px"],
                "edge_touch_count": state["edge_touch_count"],
                "white_edge_pixels": state["white_edge_pixels"],
                "magenta_edge_pixels": state["magenta_edge_pixels"],
                "height_var_pct": state["height_var_pct"],
                "groundline_var_px": state["groundline_var_px"],
                "accepted": state["accepted"],
                "notes": state["notes"],
                "source_keys": state["frame_keys"],
            }
        )
    path = PET_DIR / "qa_report.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def write_contact_sheets(source_frames: dict[str, dict], states: list[dict]) -> None:
    font = ImageFont.load_default()
    label_h = 34
    width = ATLAS_COLUMNS * CELL_WIDTH
    height = len(states) * (CELL_HEIGHT + label_h)
    sheet = Image.new("RGBA", (width, height), (248, 248, 248, 255))
    dark = Image.new("RGBA", (width, height), (18, 18, 18, 255))
    draw = ImageDraw.Draw(sheet)
    dark_draw = ImageDraw.Draw(dark)

    for row, state in enumerate(states):
        y = row * (CELL_HEIGHT + label_h)
        draw.rectangle((0, y, width, y + label_h), fill=(235, 235, 235, 255))
        dark_draw.rectangle((0, y, width, y + label_h), fill=(45, 45, 45, 255))
        title = f"{state['name']} | {', '.join(state['frame_keys'])}"
        draw.text((8, y + 10), title, fill=(30, 30, 30, 255), font=font)
        dark_draw.text((8, y + 10), title, fill=(255, 255, 255, 255), font=font)
        for col, key in enumerate(state["frame_keys"]):
            x = col * CELL_WIDTH
            box = (x, y + label_h, x + CELL_WIDTH - 1, y + label_h + CELL_HEIGHT - 1)
            draw.rectangle(box, outline=(190, 190, 190, 255))
            dark_draw.rectangle(box, outline=(90, 90, 90, 255))
            image = source_frames[key]["image"]
            sheet.alpha_composite(image, (x, y + label_h))
            dark.alpha_composite(image, (x, y + label_h))
            draw.text((x + 5, y + label_h + 5), key, fill=(60, 60, 60, 255), font=font)
            dark_draw.text((x + 5, y + label_h + 5), key, fill=(255, 255, 255, 255), font=font)

    sheet.convert("RGB").save(PET_DIR / "contact_sheet.png")
    dark.convert("RGB").save(PET_DIR / "qa" / "contact_sheet_dark.png")


def write_previews_and_review(manifest_path: Path) -> None:
    from sprite_animator import SpriteAnimator

    animator = SpriteAnimator(PET_DIR, manifest_path)
    previews_dir = PET_DIR / "previews"
    review_frames: list[Image.Image] = []
    durations: list[int] = []
    font = ImageFont.load_default()
    atlas = Image.open(PET_DIR / "spritesheet.png").convert("RGBA")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for name in animator.available_animations:
        animator.export_gif(name, previews_dir / f"{name}.gif", scale=1)
        title = Image.new("RGBA", (CELL_WIDTH * 2, CELL_HEIGHT * 2), (24, 24, 24, 255))
        ImageDraw.Draw(title).text((16, 16), name, fill=(255, 255, 255, 255), font=font)
        review_frames.append(title)
        durations.append(600)
        anim = manifest["animations"][name]
        frame_ms = int(anim["frame_duration_ms"])
        for col in range(anim["frames"]):
            box = (
                col * CELL_WIDTH,
                anim["row"] * CELL_HEIGHT,
                (col + 1) * CELL_WIDTH,
                (anim["row"] + 1) * CELL_HEIGHT,
            )
            cell = atlas.crop(box).resize((CELL_WIDTH * 2, CELL_HEIGHT * 2), Image.Resampling.LANCZOS)
            review_frames.append(cell)
            durations.append(frame_ms)
    review_frames[0].save(
        PET_DIR / "review.gif",
        save_all=True,
        append_images=review_frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
    )


def write_runtime_test_note() -> None:
    note = """PET2 runtime integration note

Expected runtime command:
python src/desktop_pet.py --pet pet2_chibi --scale 0.5

The visible Tk window cannot be proven inside this Codex environment when Tcl/Tk is missing.
Use --list-pets and manifest/atlas load checks as the non-GUI runtime proof here.
"""
    (PET_DIR / "runtime_test.txt").write_text(note, encoding="utf-8")


if __name__ == "__main__":
    main()
