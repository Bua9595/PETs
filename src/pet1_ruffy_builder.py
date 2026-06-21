from __future__ import annotations

import json
import math
import shutil
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
SOURCE_DIR = ASSETS_DIR / "source"
PET_DIR = ASSETS_DIR / "pets" / "ruffy"
CODEX_DIR = ASSETS_DIR / "codex" / "ruffy"

SOURCE_SHEETS = {
    "base": {
        "path": SOURCE_DIR / "pet1_ruffy_base_source.png",
        "cols": 5,
        "rows": 5,
        "notes": "Base/core Ruffy poses.",
    },
    "gear2": {
        "path": SOURCE_DIR / "pet1_ruffy_gear2_source.png",
        "cols": 5,
        "rows": 5,
        "notes": "Gear 2 steam and fast action poses.",
    },
    "gear3": {
        "path": SOURCE_DIR / "pet1_ruffy_gear3_source.png",
        "cols": 5,
        "rows": 4,
        "notes": "Rubber / Gear 3 giant-limb poses.",
    },
    "gear4": {
        "path": SOURCE_DIR / "pet1_ruffy_gear4_source.png",
        "cols": 5,
        "rows": 4,
        "notes": "Gear 4 Haki power-form poses.",
    },
    "gear5": {
        "path": SOURCE_DIR / "pet1_ruffy_gear5_source.png",
        "cols": 5,
        "rows": 4,
        "notes": "Gear 5 Joy Boy poses.",
    },
}

CELL_WIDTH = 320
CELL_HEIGHT = 320
ATLAS_COLUMNS = 10
TARGET_PADDING = 30
MIN_PADDING = 18

CODEX_COLUMNS = 8
CODEX_ROWS = 9
CODEX_CELL_WIDTH = 192
CODEX_CELL_HEIGHT = 208


@dataclass(frozen=True)
class StatePlan:
    name: str
    refs: list[tuple[str, int]]
    timing_ms: int
    loop: bool
    category: str
    notes: str
    weight: int = 1


STATE_PLANS = [
    StatePlan("idle", [("base", 1), ("base", 2), ("base", 1), ("base", 3)], 380, True, "core", "Neutral/friendly idle.", 16),
    StatePlan("blink", [("base", 1), ("base", 9), ("base", 1)], 430, True, "core", "Blink/rest settle.", 7),
    StatePlan("wave", [("base", 1), ("base", 4), ("base", 21), ("base", 4)], 360, True, "social", "Wave and greeting poses.", 8),
    StatePlan("happy", [("base", 2), ("base", 11), ("base", 24), ("base", 2)], 340, True, "core", "Happy Ruffy loop.", 8),
    StatePlan("surprised", [("base", 5), ("base", 23), ("base", 5)], 360, True, "core", "Surprised/confused reaction.", 5),
    StatePlan("thinking", [("base", 6), ("base", 8), ("base", 6)], 380, True, "core", "Thinking / tactical look.", 5),
    StatePlan("curious", [("base", 12), ("base", 23), ("base", 3)], 360, True, "core", "Curious pointing / shrug.", 5),
    StatePlan("walk", [("base", 14), ("base", 15), ("base", 14), ("base", 15)], 320, True, "movement", "Best available base movement cycle.", 8),
    StatePlan("run", [("base", 14), ("base", 15), ("base", 14), ("base", 15)], 280, True, "movement", "Normal run loop from clean base frames.", 12),
    StatePlan("jump", [("base", 13), ("base", 15), ("base", 18), ("base", 19)], 340, False, "movement", "Jump start, air, kick, land.", 6),
    StatePlan("sit", [("base", 9), ("base", 20), ("base", 22)], 460, True, "rest", "Seated loop.", 4),
    StatePlan("rest", [("base", 22), ("base", 10), ("base", 20)], 520, True, "rest", "Rest / sleepy loop.", 4),
    StatePlan("failed", [("base", 25), ("gear3", 16), ("base", 20)], 480, True, "rest", "Failed / tired gag.", 3),
    StatePlan("celebrate", [("base", 11), ("base", 24), ("base", 2), ("base", 11)], 330, True, "social", "Cheer and victory poses.", 6),
    StatePlan("drag_react", [("base", 23), ("base", 20), ("base", 23)], 360, True, "desktop", "Dragged / dropped reaction.", 3),
    StatePlan("cursor_follow", [("base", 12), ("base", 3), ("base", 12)], 360, True, "desktop", "Pointer-following pose.", 3),
    StatePlan("rubber_stretch", [("gear3", 2), ("gear3", 3), ("gear3", 17), ("gear3", 10)], 300, False, "rubber", "Elastic wind-up and stretch.", 4),
    StatePlan("rubber_punch", [("gear3", 4), ("gear3", 5), ("gear3", 7), ("gear3", 19)], 260, False, "rubber", "Giant/rubber punch with visible fist.", 5),
    StatePlan("rubber_reach", [("gear3", 6), ("gear3", 9), ("gear3", 10)], 280, False, "rubber", "Long-arm reach / grab.", 3),
    StatePlan("rubber_kick", [("gear3", 11), ("gear3", 13), ("gear3", 14)], 280, False, "rubber", "Giant-foot and kick frames.", 3),
    StatePlan("gear2", [("gear2", 1), ("gear2", 2), ("gear2", 3), ("gear2", 4), ("gear2", 12), ("gear2", 15)], 240, True, "gear", "Gear 2: normal body, steam, speed stance.", 4),
    StatePlan("gear3", [("gear3", 4), ("gear3", 5), ("gear3", 8), ("gear3", 12), ("gear3", 13), ("gear3", 20)], 260, False, "gear", "Gear 3 giant-fist / giant-foot sequence.", 3),
    StatePlan("gear4", [("gear4", 1), ("gear4", 2), ("gear4", 3), ("gear4", 12), ("gear4", 18), ("gear4", 13)], 260, True, "gear", "Gear 4 Haki power-form.", 2),
    StatePlan("gear5", [("gear5", 1), ("gear5", 2), ("gear5", 3), ("gear5", 5), ("gear5", 7), ("gear5", 8), ("gear5", 18), ("gear5", 19), ("gear5", 20)], 260, True, "gear", "Gear 5 Joy Boy loop.", 2),
]


def main() -> None:
    missing = [str(item["path"].relative_to(PROJECT_ROOT)) for item in SOURCE_SHEETS.values() if not item["path"].exists()]
    if missing:
        raise FileNotFoundError(f"Missing PET1/Ruffy source sheets: {missing}")

    clean_output_dirs()
    make_output_dirs()

    source_frames = extract_all_source_frames()
    states = build_runtime_atlas(source_frames)
    qa_report = write_qa(source_frames, states)
    write_contact_sheets(states)
    write_previews(states)
    write_runtime_test_note()
    build_codex_export(states)
    write_asset_inventory(source_frames, states, qa_report)

    print(
        json.dumps(
            {
                "sources": {name: str(data["path"].relative_to(PROJECT_ROOT)) for name, data in SOURCE_SHEETS.items()},
                "spritesheet": str((PET_DIR / "spritesheet.png").relative_to(PROJECT_ROOT)),
                "manifest": str((PET_DIR / "manifest.json").relative_to(PROJECT_ROOT)),
                "codex_package": str(CODEX_DIR.relative_to(PROJECT_ROOT)),
                "states": [state["name"] for state in states],
                "qa_accepted": qa_report["accepted"],
            },
            indent=2,
        )
    )


def clean_output_dirs() -> None:
    for path in (PET_DIR, CODEX_DIR):
        if path.exists():
            shutil.rmtree(path)


def make_output_dirs() -> None:
    for path in (
        PET_DIR / "source_cells",
        PET_DIR / "row_sources",
        PET_DIR / "previews",
        PET_DIR / "qa",
        CODEX_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def extract_all_source_frames() -> dict[str, dict]:
    frames: dict[str, dict] = {}
    for source_name, config in SOURCE_SHEETS.items():
        image = Image.open(config["path"]).convert("RGBA")
        cols = int(config["cols"])
        rows = int(config["rows"])
        x_lines = [round(i * image.width / cols) for i in range(cols + 1)]
        y_lines = [round(i * image.height / rows) for i in range(rows + 1)]
        index = 1
        for row in range(rows):
            for col in range(cols):
                cell = image.crop((x_lines[col], y_lines[row], x_lines[col + 1], y_lines[row + 1]))
                transparent = chroma_to_alpha(cell)
                cleaned = remove_stray_components(transparent)
                fitted = remove_edge_fringe(fit_to_cell(cleaned, CELL_WIDTH, CELL_HEIGHT, TARGET_PADDING))
                key = frame_key(source_name, index)
                source_path = PET_DIR / "source_cells" / f"{key}.png"
                fitted.save(source_path)
                frames[key] = {
                    "key": key,
                    "source": source_name,
                    "index": index,
                    "source_path": source_path,
                    "image": fitted,
                    "metrics": frame_metrics(fitted),
                }
                index += 1
    return frames


def frame_key(source: str, index: int) -> str:
    return f"{source}_{index:02d}"


def chroma_to_alpha(image: Image.Image) -> Image.Image:
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
        if not is_chroma_like(pixels[x, y]):
            continue
        pixels[x, y] = (0, 0, 0, 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    pixels = rgba.load()
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a and is_bright_chroma_fringe((r, g, b, a)):
                pixels[x, y] = (0, 0, 0, 0)

    return rgba


def remove_stray_components(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    components = alpha_components(alpha)
    if not components:
        return rgba

    largest = max(components, key=lambda item: item["size"])
    keep: set[int] = {largest["id"]}
    for component in components:
        if component["id"] == largest["id"]:
            continue
        if component["size"] < 80:
            continue
        if component_touches_cell_edge(component["bbox"], rgba.width, rgba.height):
            continue
        keep.add(component["id"])

    if len(keep) == len(components):
        return rgba

    mask = Image.new("L", rgba.size, 0)
    mask_pixels = mask.load()
    label_map = [[0 for _ in range(rgba.width)] for _ in range(rgba.height)]
    for component in components:
        if component["id"] not in keep:
            continue
        for x, y in component["pixels"]:
            label_map[y][x] = component["id"]
            mask_pixels[x, y] = 255

    output = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    output.alpha_composite(rgba)
    output.putalpha(mask)
    return output


def alpha_components(alpha: Image.Image) -> list[dict]:
    width, height = alpha.size
    pixels = alpha.load()
    visited = [[False for _ in range(width)] for _ in range(height)]
    components: list[dict] = []
    component_id = 1
    for y in range(height):
        for x in range(width):
            if visited[y][x] or pixels[x, y] == 0:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            visited[y][x] = True
            points: list[tuple[int, int]] = []
            min_x = max_x = x
            min_y = max_y = y
            while queue:
                cx, cy = queue.popleft()
                points.append((cx, cy))
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                        visited[ny][nx] = True
                        if pixels[nx, ny] > 0:
                            queue.append((nx, ny))
            components.append(
                {
                    "id": component_id,
                    "size": len(points),
                    "bbox": (min_x, min_y, max_x + 1, max_y + 1),
                    "pixels": points,
                }
            )
            component_id += 1
    return components


def component_touches_cell_edge(bbox: tuple[int, int, int, int], width: int, height: int) -> bool:
    left, top, right, bottom = bbox
    return left <= 1 or top <= 1 or right >= width - 1 or bottom >= height - 1


def is_chroma_like(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, a = pixel
    if a <= 12:
        return True
    if r >= 110 and b >= 110 and g <= 145 and min(r, b) - g >= 28 and abs(r - b) <= 130:
        return True
    return r >= 175 and b >= 140 and g <= 155 and r - g >= 45 and b - g >= 20


def is_bright_chroma_fringe(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, a = pixel
    return a > 0 and r >= 120 and b >= 120 and g <= 125 and min(r, b) - g >= 35 and abs(r - b) <= 125


def remove_edge_fringe(image: Image.Image, passes: int = 2) -> Image.Image:
    output = image.convert("RGBA")
    for _ in range(passes):
        source = output.copy()
        src = source.load()
        dst = output.load()
        width, height = output.size
        for y in range(height):
            for x in range(width):
                if is_bright_chroma_fringe(src[x, y]) and touches_transparency(src, width, height, x, y):
                    dst[x, y] = (0, 0, 0, 0)
    return output


def fit_to_cell(image: Image.Image, cell_width: int, cell_height: int, padding: int) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = rgba.getbbox()
    canvas = Image.new("RGBA", (cell_width, cell_height), (0, 0, 0, 0))
    if bbox is None:
        return canvas

    trimmed = rgba.crop(bbox)
    max_width = cell_width - 2 * padding
    max_height = cell_height - 2 * padding
    scale = min(max_width / trimmed.width, max_height / trimmed.height)
    width = max(1, round(trimmed.width * scale))
    height = max(1, round(trimmed.height * scale))
    resized = trimmed.resize((width, height), Image.Resampling.LANCZOS)

    x = (cell_width - width) // 2
    y = cell_height - padding - height
    if y < padding:
        y = (cell_height - height) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas


def build_runtime_atlas(source_frames: dict[str, dict]) -> list[dict]:
    states: list[dict] = []
    rows = len(STATE_PLANS)
    atlas = Image.new("RGBA", (ATLAS_COLUMNS * CELL_WIDTH, rows * CELL_HEIGHT), (0, 0, 0, 0))

    for row, plan in enumerate(STATE_PLANS):
        frame_keys = [frame_key(source, index) for source, index in plan.refs]
        if len(frame_keys) > ATLAS_COLUMNS:
            raise ValueError(f"State {plan.name} has {len(frame_keys)} frames but atlas has only {ATLAS_COLUMNS} columns.")
        metrics = []
        for column, key in enumerate(frame_keys):
            frame = source_frames[key]["image"]
            atlas.alpha_composite(frame, (column * CELL_WIDTH, row * CELL_HEIGHT))
            row_path = PET_DIR / "row_sources" / f"{plan.name}_{column + 1:02d}_{key}.png"
            frame.save(row_path)
            metrics.append(source_frames[key]["metrics"])
        states.append(
            {
                "name": plan.name,
                "row": row,
                "frames": len(frame_keys),
                "loop": plan.loop,
                "frame_duration_ms": plan.timing_ms,
                "source_refs": frame_keys,
                "category": plan.category,
                "notes": plan.notes,
                "weight": plan.weight,
                "metrics": aggregate_metrics(metrics),
            }
        )

    atlas_path = PET_DIR / "spritesheet.png"
    atlas.save(atlas_path)
    manifest = build_manifest(states)
    (PET_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return states


def build_manifest(states: list[dict]) -> dict:
    animations = {}
    for state in states:
        animations[state["name"]] = {
            "row": state["row"],
            "frames": state["frames"],
            "loop": state["loop"],
            "frame_duration_ms": state["frame_duration_ms"],
            "source_refs": state["source_refs"],
            "category": state["category"],
            "notes": state["notes"],
            "semantic_correct": True,
            "qa_accepted": state["metrics"]["accepted"],
        }

    categories = []
    category_labels = {
        "core": "Core",
        "movement": "Movement",
        "rest": "Rest",
        "social": "Social",
        "desktop": "Desktop",
        "rubber": "Rubber",
        "gear": "Gear",
    }
    category_weights = {"core": 12, "movement": 10, "rest": 7, "social": 6, "desktop": 5, "rubber": 4, "gear": 3}
    for category_id in category_labels:
        names = [state["name"] for state in states if state["category"] == category_id]
        if names:
            categories.append(
                {
                    "id": category_id,
                    "label": category_labels[category_id],
                    "weight": category_weights[category_id],
                    "animations": names,
                }
            )

    return {
        "id": "ruffy",
        "display_name": "Ruffy",
        "image": "spritesheet.png",
        "source_images": {name: f"../../source/{data['path'].name}" for name, data in SOURCE_SHEETS.items()},
        "columns": ATLAS_COLUMNS,
        "rows": len(states),
        "cell_width": CELL_WIDTH,
        "cell_height": CELL_HEIGHT,
        "frame_duration_ms": 340,
        "animations": animations,
        "desktop_behavior": {
            "initial_animation": "idle",
            "drag_animation": "drag_react",
            "double_click_animation": "rubber_punch",
            "animation_cooldown_seconds": 60,
            "choices": [{"animation": state["name"], "weight": state["weight"]} for state in states],
            "category_behavior": {
                "initial_category": "core",
                "attempts_before_switch_min": 2,
                "attempts_before_switch_max": 5,
                "switch_probability": 0.45,
                "categories": categories,
            },
            "menu_states": [{"label": menu_label(state["name"]), "animation": state["name"]} for state in states],
        },
        "personality_tags": ["energetic", "playful", "rubber", "pirate", "gear_forms"],
        "build_notes": "Rebuilt only from the five 2026-06-21 magenta PET1 source sheets.",
    }


def menu_label(name: str) -> str:
    return name.replace("_", " ").title()


def frame_metrics(image: Image.Image) -> dict:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return {
            "min_margin_px": 0,
            "edge_touch_count": 0,
            "chroma_edge_pixels": 0,
            "visible_cluster_count": 0,
            "accepted": False,
        }

    left, top, right, bottom = bbox
    margins = [left, top, rgba.width - right, rgba.height - bottom]
    edge_touch_count = count_edge_alpha(alpha)
    chroma_edge_pixels = count_chroma_pixels(rgba)
    cluster_count = count_visible_clusters(alpha)
    accepted = min(margins) >= MIN_PADDING and edge_touch_count == 0 and chroma_edge_pixels == 0
    return {
        "bbox": bbox,
        "min_margin_px": min(margins),
        "edge_touch_count": edge_touch_count,
        "chroma_edge_pixels": chroma_edge_pixels,
        "visible_cluster_count": cluster_count,
        "accepted": accepted,
    }


def aggregate_metrics(metrics: list[dict]) -> dict:
    min_margin = min(item["min_margin_px"] for item in metrics)
    edge_touch = sum(item["edge_touch_count"] for item in metrics)
    chroma = sum(item["chroma_edge_pixels"] for item in metrics)
    max_clusters = max(item["visible_cluster_count"] for item in metrics)
    accepted = all(item["accepted"] for item in metrics)
    return {
        "min_margin_px": min_margin,
        "edge_touch_count": edge_touch,
        "chroma_edge_pixels": chroma,
        "visible_cluster_count": max_clusters,
        "accepted": accepted,
    }


def count_edge_alpha(alpha: Image.Image) -> int:
    width, height = alpha.size
    pixels = alpha.load()
    count = 0
    for x in range(width):
        if pixels[x, 0] > 0:
            count += 1
        if pixels[x, height - 1] > 0:
            count += 1
    for y in range(height):
        if pixels[0, y] > 0:
            count += 1
        if pixels[width - 1, y] > 0:
            count += 1
    return count


def count_chroma_pixels(image: Image.Image) -> int:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    count = 0
    for y in range(rgba.height):
        for x in range(rgba.width):
            if is_qa_magenta_fringe(pixels[x, y]) and touches_transparency(pixels, rgba.width, rgba.height, x, y):
                count += 1
    return count


def is_qa_magenta_fringe(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, a = pixel
    return a > 0 and r >= 220 and b >= 210 and g <= 105 and min(r, b) - g >= 115 and abs(r - b) <= 70


def touches_transparency(pixels, width: int, height: int, x: int, y: int) -> bool:
    for ny in range(max(0, y - 1), min(height, y + 2)):
        for nx in range(max(0, x - 1), min(width, x + 2)):
            if pixels[nx, ny][3] == 0:
                return True
    return False


def count_visible_clusters(alpha: Image.Image) -> int:
    width, height = alpha.size
    pixels = alpha.load()
    visited = [[False for _ in range(width)] for _ in range(height)]
    clusters = 0
    for y in range(height):
        for x in range(width):
            if visited[y][x] or pixels[x, y] == 0:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            visited[y][x] = True
            size = 0
            while queue:
                cx, cy = queue.popleft()
                size += 1
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                        visited[ny][nx] = True
                        if pixels[nx, ny] > 0:
                            queue.append((nx, ny))
            if size >= 80:
                clusters += 1
    return clusters


def write_qa(source_frames: dict[str, dict], states: list[dict]) -> dict:
    state_rows = []
    accepted = True
    for state in states:
        metrics = state["metrics"]
        row = {
            "animation": state["name"],
            "frames": state["frames"],
            "min_margin_px": metrics["min_margin_px"],
            "edge_touch_count": metrics["edge_touch_count"],
            "chroma_edge_pixels": metrics["chroma_edge_pixels"],
            "visible_cluster_count": metrics["visible_cluster_count"],
            "accepted": metrics["accepted"],
            "source_refs": state["source_refs"],
        }
        if not row["accepted"]:
            accepted = False
        state_rows.append(row)

    report = {
        "accepted": accepted,
        "cell": {"width": CELL_WIDTH, "height": CELL_HEIGHT, "target_padding": TARGET_PADDING, "min_padding": MIN_PADDING},
        "sources": {name: {"path": str(data["path"].relative_to(PROJECT_ROOT)), "cols": data["cols"], "rows": data["rows"]} for name, data in SOURCE_SHEETS.items()},
        "states": state_rows,
        "source_frames": {
            key: {
                "source": frame["source"],
                "index": frame["index"],
                "path": str(frame["source_path"].relative_to(PROJECT_ROOT)),
                "metrics": frame["metrics"],
            }
            for key, frame in source_frames.items()
        },
        "known_source_limits": [
            "The supplied base sheet has only two clean normal locomotion poses, so walk/run are solid but not truly fluid yet.",
            "The new supplied Ruffy sheets do not contain gaming, phone, laptop, folder, or multi-pet social props; those states are intentionally omitted instead of faked.",
        ],
    }
    (PET_DIR / "qa_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (PET_DIR / "qa" / "qa_table.md").write_text(format_qa_table(state_rows), encoding="utf-8")
    return report


def format_qa_table(rows: list[dict]) -> str:
    lines = [
        "| animation | frames | min_margin_px | edge_touch_count | chroma_edge_pixels | visible_cluster_count | accepted |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['animation']} | {row['frames']} | {row['min_margin_px']} | "
            f"{row['edge_touch_count']} | {row['chroma_edge_pixels']} | {row['visible_cluster_count']} | {row['accepted']} |"
        )
    return "\n".join(lines) + "\n"


def write_contact_sheets(states: list[dict]) -> None:
    write_contact_sheet(states, PET_DIR / "contact_sheet.png", background=(28, 28, 30, 255))
    write_contact_sheet(states, PET_DIR / "qa" / "contact_sheet_dark.png", background=(20, 20, 22, 255))
    write_contact_sheet(states, PET_DIR / "qa" / "contact_sheet_magenta.png", background=(255, 0, 255, 255))


def write_contact_sheet(states: list[dict], output_path: Path, background: tuple[int, int, int, int]) -> None:
    label_width = 180
    row_height = CELL_HEIGHT + 44
    width = label_width + ATLAS_COLUMNS * CELL_WIDTH
    height = len(states) * row_height
    sheet = Image.new("RGBA", (width, height), background)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    atlas = Image.open(PET_DIR / "spritesheet.png").convert("RGBA")

    for state in states:
        y = state["row"] * row_height
        draw.text((10, y + 16), state["name"], fill=(255, 255, 255, 255), font=font)
        draw.text((10, y + 34), f"{state['frames']}f {state['frame_duration_ms']}ms", fill=(190, 190, 190, 255), font=font)
        for col in range(ATLAS_COLUMNS):
            x = label_width + col * CELL_WIDTH
            draw.rectangle((x, y, x + CELL_WIDTH - 1, y + CELL_HEIGHT - 1), outline=(82, 82, 88, 255))
            if col < state["frames"]:
                frame = atlas.crop((col * CELL_WIDTH, state["row"] * CELL_HEIGHT, (col + 1) * CELL_WIDTH, (state["row"] + 1) * CELL_HEIGHT))
                sheet.alpha_composite(frame, (x, y))
                draw.text((x + 8, y + CELL_HEIGHT + 8), state["source_refs"][col], fill=(220, 220, 220, 255), font=font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def write_previews(states: list[dict]) -> None:
    atlas = Image.open(PET_DIR / "spritesheet.png").convert("RGBA")
    for state in states:
        frames = [
            atlas.crop((col * CELL_WIDTH, state["row"] * CELL_HEIGHT, (col + 1) * CELL_WIDTH, (state["row"] + 1) * CELL_HEIGHT))
            for col in range(state["frames"])
        ]
        path = PET_DIR / "previews" / f"{state['name']}.gif"
        frames[0].save(
            path,
            save_all=True,
            append_images=frames[1:],
            duration=state["frame_duration_ms"],
            loop=0 if state["loop"] else 1,
            disposal=2,
        )


def build_codex_export(states: list[dict]) -> None:
    manifest = json.loads((PET_DIR / "manifest.json").read_text(encoding="utf-8"))
    runtime_atlas = Image.open(PET_DIR / manifest["image"]).convert("RGBA")
    codex_atlas = Image.new("RGBA", (CODEX_COLUMNS * CODEX_CELL_WIDTH, CODEX_ROWS * CODEX_CELL_HEIGHT), (0, 0, 0, 0))

    row_map = [
        ("idle", False, 6),
        ("run", False, 8),
        ("run", True, 8),
        ("wave", False, 4),
        ("jump", False, 5),
        ("failed", False, 8),
        ("curious", False, 6),
        ("gear2", False, 6),
        ("gear5", False, 6),
    ]
    for target_row, (animation, mirror, used_columns) in enumerate(row_map):
        state = manifest["animations"][animation]
        source_row = int(state["row"])
        source_frames = int(state["frames"])
        for target_col in range(used_columns):
            source_col = target_col % source_frames
            cell = runtime_atlas.crop(
                (
                    source_col * CELL_WIDTH,
                    source_row * CELL_HEIGHT,
                    (source_col + 1) * CELL_WIDTH,
                    (source_row + 1) * CELL_HEIGHT,
                )
            )
            if mirror:
                cell = ImageOps.mirror(cell)
            fitted = fit_to_cell(cell, CODEX_CELL_WIDTH, CODEX_CELL_HEIGHT, 14)
            codex_atlas.alpha_composite(fitted, (target_col * CODEX_CELL_WIDTH, target_row * CODEX_CELL_HEIGHT))

    png_path = CODEX_DIR / "spritesheet.png"
    webp_path = CODEX_DIR / "spritesheet.webp"
    codex_atlas.save(png_path)
    codex_atlas.save(webp_path, lossless=True, quality=100, method=6)
    pet_json = {
        "id": "ruffy",
        "displayName": "Ruffy",
        "description": "A local fan-inspired rubber-pirate desktop pet rebuilt from the 2026-06-21 PET1 source sheets.",
        "spritesheetPath": "spritesheet.webp",
    }
    (CODEX_DIR / "pet.json").write_text(json.dumps(pet_json, indent=2), encoding="utf-8")


def write_runtime_test_note() -> None:
    (PET_DIR / "runtime_test.txt").write_text(
        "Run with: python src/desktop_pet.py --pet ruffy --scale 0.5\n"
        "Controls: drag with left mouse, double-click rubber_punch, right-click menu, Esc closes.\n",
        encoding="utf-8",
    )


def write_asset_inventory(source_frames: dict[str, dict], states: list[dict], qa_report: dict) -> None:
    lines = [
        "# PET1 / Ruffy Asset Inventory",
        "",
        "## Runtime",
        "",
        "- spritesheet: `assets/pets/ruffy/spritesheet.png`",
        "- manifest: `assets/pets/ruffy/manifest.json`",
        "- QA: `assets/pets/ruffy/qa_report.json`",
        "- Codex package: `assets/codex/ruffy/`",
        "",
        "## Sources Kept",
        "",
    ]
    for name, data in SOURCE_SHEETS.items():
        lines.append(f"- `{data['path'].relative_to(PROJECT_ROOT)}` - {data['notes']}")
    lines.extend(["", "## Animations", ""])
    for state in states:
        lines.append(f"- `{state['name']}`: {state['frames']} frames, {state['frame_duration_ms']}ms, refs {', '.join(state['source_refs'])}")
    lines.extend(["", "## QA", "", f"- accepted: `{qa_report['accepted']}`", ""])
    (PET_DIR / "ASSET_INVENTORY.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
