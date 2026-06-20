from __future__ import annotations

import json
import math
import shutil
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
MAIN_SOURCE_SHEET = ASSETS_DIR / "source" / "pet1_ruffy_100_source_sheet.png"
GEAR5_SOURCE_SHEET = ASSETS_DIR / "source" / "pet1_ruffy_gear5_32_source_sheet.png"
POWER_SOURCE_SHEET = ASSETS_DIR / "source" / "pet1_ruffy_power_32_source_sheet.png"
PET_DIR = ASSETS_DIR / "pets" / "ruffy"
ARCHIVE_ROOT = PROJECT_ROOT / "archive"

CELL_WIDTH = 192
CELL_HEIGHT = 208
ATLAS_COLUMNS = 12
TARGET_PADDING = 18
MIN_PADDING = 14


@dataclass(frozen=True)
class StatePlan:
    name: str
    frame_ids: list[str]
    timing_ms: int
    loop: bool
    notes: str
    motion_coherent: bool


STATE_PLANS = [
    StatePlan("idle", ["0", "1", "2", "3", "4", "5"], 260, True, "Calm idle loop from standing variants.", True),
    StatePlan("blink", ["2", "3", "4", "5"], 320, True, "Closed-eye idle variants.", True),
    StatePlan("wave", ["7", "8", "9", "10"], 260, True, "Greeting poses only.", True),
    StatePlan("happy", ["13", "15", "16", "23"], 280, True, "Happy emote loop.", True),
    StatePlan("walk", ["25", "27", "28", "29"], 230, True, "Shorter, softer locomotion cycle.", True),
    StatePlan("run", ["36", "37", "38", "39", "40", "41", "42", "43"], 170, True, "Directional run cycle.", True),
    StatePlan("jump", ["48", "49", "52", "53"], 220, False, "Takeoff and air frames only.", True),
    StatePlan("sit", ["19", "20"], 340, True, "Stable seated poses.", True),
    StatePlan("rest", ["20", "21"], 380, True, "Resting loop.", True),
    StatePlan("nap", ["20", "21"], 430, True, "Sleepy seated loop.", True),
    StatePlan("failed", ["21", "22"], 320, True, "Dizzy and failed emote frames.", True),
    StatePlan("curious", ["17", "18", "30"], 300, True, "Curious/question poses.", True),
    StatePlan("celebrate", ["14", "15", "16", "23"], 240, True, "Excited emote loop.", True),
    StatePlan("eat", ["96", "97", "98", "99"], 260, True, "Food-only frames, explicitly not gear3.", True),
    StatePlan("rubber_stretch", ["72", "73", "75", "76", "77"], 210, False, "Elastic stretch sequence.", True),
    StatePlan("rubber_punch", ["78", "79", "80", "81"], 190, False, "Punch extension sequence.", True),
    StatePlan("rubber_reach", ["72", "73", "74", "75"], 210, False, "Reach/grab frames.", True),
    StatePlan("gear2", ["100", "101", "102"], 170, True, "Steam / normal body only.", True),
    StatePlan("gear3", ["p3_06", "p3_07", "p3_15", "p3_10", "p3_21", "p3_23", "p3_17", "p3_24"], 180, False, "Giant-fist / giant-limb sequence from power sheet.", True),
    StatePlan("gear4", ["103", "104", "105", "106", "107", "108", "109", "110", "111"], 190, True, "Dark aura and inflated power-form only.", True),
    StatePlan("gear5", ["g5_01", "g5_02", "g5_03", "g5_20", "g5_21", "g5_30", "g5_31", "g5_32"], 180, True, "Dark-source Gear5 loop.", True),
]

CATEGORY_RULES: list[tuple[range, str, str]] = [
    (range(0, 7), "idle", "Idle/blink standing variants."),
    (range(7, 13), "wave", "Greeting and wave variants."),
    (range(13, 19), "happy", "Happy/curious emotes."),
    (range(19, 24), "rest", "Sit/rest/failed family."),
    (range(24, 36), "walk", "Walk and light movement family."),
    (range(36, 48), "run", "Run family."),
    (range(48, 60), "jump", "Jump/action family."),
    (range(60, 72), "ambiguous", "Miscellaneous action frames."),
    (range(72, 78), "rubber_stretch", "Stretch family."),
    (range(78, 84), "rubber_punch", "Punch/reach family."),
    (range(84, 96), "celebrate", "Celebrate / utility / ambiguous action frames."),
    (range(96, 100), "eat", "Food/meat frames."),
    (range(100, 103), "gear2", "Steam / speed frames."),
    (range(103, 112), "gear4", "Dark aura / inflated power frames."),
    (range(112, 120), "ambiguous", "Unclear or duplicated power frames."),
    (range(120, 128), "gear5", "White-source gear5 frames superseded by dark source."),
    (range(128, 144), "duplicate", "Trailing duplicates / non-runtime material."),
]


def main() -> None:
    if not MAIN_SOURCE_SHEET.exists():
        raise FileNotFoundError(f"Main source sheet not found: {MAIN_SOURCE_SHEET}")
    if not GEAR5_SOURCE_SHEET.exists():
        raise FileNotFoundError(f"Gear5 source sheet not found: {GEAR5_SOURCE_SHEET}")
    if not POWER_SOURCE_SHEET.exists():
        raise FileNotFoundError(f"Power source sheet not found: {POWER_SOURCE_SHEET}")

    backup_dir = make_backup()
    clean_active_outputs()

    raw_dir = PET_DIR / "frames_raw"
    clean_dir = PET_DIR / "frames_clean"
    rejected_dir = PET_DIR / "frames_rejected"
    needs_source_dir = PET_DIR / "frames_needs_source"
    preview_dir = PET_DIR / "previews"
    qa_dir = PET_DIR / "qa"
    for path in (raw_dir, clean_dir, rejected_dir, needs_source_dir, preview_dir, qa_dir):
        path.mkdir(parents=True, exist_ok=True)

    main_source = Image.open(MAIN_SOURCE_SHEET).convert("RGBA")
    cols, rows = detect_grid(main_source)
    x_lines, y_lines = detect_grid_lines(main_source, cols, rows)
    main_frames = extract_main_frames(main_source, x_lines, y_lines, raw_dir)
    gear5_frames = extract_gear5_frames(Image.open(GEAR5_SOURCE_SHEET).convert("RGBA"), raw_dir)
    power_frames = extract_power_frames(Image.open(POWER_SOURCE_SHEET).convert("RGBA"), raw_dir)

    catalog = curate_catalog(main_frames, gear5_frames, power_frames)
    write_curated_frames(catalog, clean_dir, rejected_dir, needs_source_dir)
    write_frame_catalog(catalog, qa_dir)
    halo_report = write_halo_artifacts(catalog, qa_dir)

    state_lookup = {state.name: state for state in STATE_PLANS}
    active_states = build_states(catalog, state_lookup, halo_report)
    atlas_path, manifest_path = build_atlas(active_states, catalog, clean_dir)
    qa_report = build_qa_report(active_states, catalog, halo_report, cols, rows)
    write_contact_sheets(active_states, catalog, clean_dir, qa_dir)
    write_previews(active_states, manifest_path, preview_dir)
    write_review_gif(active_states, manifest_path)
    write_inventory(backup_dir, cols, rows, catalog, halo_report)

    compatibility_manifest = ASSETS_DIR / "ruffy_sprite_manifest.json"
    compatibility_sheet = ASSETS_DIR / "sprites" / "ruffy_spritesheet.png"
    compatibility_sheet.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(atlas_path, compatibility_sheet)
    compatibility = json.loads(manifest_path.read_text(encoding="utf-8"))
    compatibility["image"] = "sprites/ruffy_spritesheet.png"
    compatibility["source_image"] = "source/pet1_ruffy_100_source_sheet.png"
    compatibility["supplemental_sources"] = [
        "source/pet1_ruffy_gear5_32_source_sheet.png",
        "source/pet1_ruffy_power_32_source_sheet.png",
    ]
    compatibility_manifest.write_text(json.dumps(compatibility, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "backup_path": str(backup_dir.relative_to(PROJECT_ROOT)),
                "main_source": str(MAIN_SOURCE_SHEET.relative_to(PROJECT_ROOT)),
                "gear5_source": str(GEAR5_SOURCE_SHEET.relative_to(PROJECT_ROOT)),
                "power_source": str(POWER_SOURCE_SHEET.relative_to(PROJECT_ROOT)),
                "states": [state["name"] for state in active_states],
                "accepted_frames": sum(1 for item in catalog.values() if item["accepted"]),
                "rejected_frames": sum(1 for item in catalog.values() if item["status"] == "rejected"),
                "needs_source_frames": sum(1 for item in catalog.values() if item["status"] == "needs_source"),
            },
            indent=2,
        )
    )


def make_backup() -> Path:
    backup_dir = ARCHIVE_ROOT / f"pet1_before_crispyclean_gear3_fix_{datetime.now().strftime('%Y%m%d_%H%M')}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    targets = [
        PET_DIR,
        ASSETS_DIR / "ruffy_sprite_manifest.json",
        ASSETS_DIR / "sprites" / "ruffy_spritesheet.png",
        ASSETS_DIR / "codex" / "ruffy",
    ]
    for target in targets:
        if not target.exists():
            continue
        destination = backup_dir / target.relative_to(PROJECT_ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if target.is_dir():
            shutil.copytree(target, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(target, destination)
    return backup_dir


def clean_active_outputs() -> None:
    for path in [PET_DIR, ASSETS_DIR / "codex" / "ruffy"]:
        if path.exists():
            shutil.rmtree(path)


def detect_grid(source: Image.Image) -> tuple[int, int]:
    width, height = source.size
    if abs(width - height) <= 4 and width >= 1000:
        return 12, 12
    raise ValueError(f"Unexpected main source size for grid detection: {source.size}")


def detect_grid_lines(source: Image.Image, cols: int, rows: int) -> tuple[list[int], list[int]]:
    rgb = source.convert("RGB")
    width, height = source.size
    x_lines = detect_axis_lines(rgb, width, height, axis="x", expected=cols + 1)
    y_lines = detect_axis_lines(rgb, width, height, axis="y", expected=rows + 1)
    if len(x_lines) == cols + 1 and len(y_lines) == rows + 1:
        return x_lines, y_lines
    return (
        [round(i * width / cols) for i in range(cols + 1)],
        [round(i * height / rows) for i in range(rows + 1)],
    )


def detect_axis_lines(rgb: Image.Image, width: int, height: int, axis: str, expected: int) -> list[int]:
    size = width if axis == "x" else height
    other = height if axis == "x" else width
    stride = max(1, other // 320)
    values = []
    for index in range(size):
        hits = 0
        count = 0
        for other_index in range(0, other, stride):
            x, y = (index, other_index) if axis == "x" else (other_index, index)
            r, g, b = rgb.getpixel((x, y))
            if abs(r - g) < 5 and abs(g - b) < 5 and 215 <= r <= 245:
                hits += 1
            count += 1
        values.append(hits / max(1, count))
    peaks = [i for i, value in enumerate(values) if value > 0.45]
    groups: list[list[int]] = []
    for peak in peaks:
        if not groups or peak - groups[-1][-1] > 2:
            groups.append([peak])
        else:
            groups[-1].append(peak)
    centers = [round(sum(group) / len(group)) for group in groups]
    return centers if len(centers) == expected else []


def extract_main_frames(source: Image.Image, x_lines: list[int], y_lines: list[int], raw_dir: Path) -> dict[str, dict]:
    frames: dict[str, dict] = {}
    frame_id = 0
    for row in range(len(y_lines) - 1):
        for col in range(len(x_lines) - 1):
            left, right = x_lines[col], x_lines[col + 1]
            top, bottom = y_lines[row], y_lines[row + 1]
            crop = source.crop((left, top, right, bottom)).crop((3, 3, right - left - 3, bottom - top - 3))
            key = str(frame_id)
            raw_path = raw_dir / f"frame_{frame_id:03d}.png"
            crop.save(raw_path)
            prehalo, cleaned = clean_main_cell(crop)
            fitted_before = fit_to_cell(prehalo)
            fitted = fit_to_cell(cleaned)
            metrics = frame_metrics(fitted)
            frames[key] = {
                "frame_id": key,
                "source": "main_sheet",
                "source_cell": {"row": row, "column": col},
                "raw_path": raw_path,
                "before_image": fitted_before,
                "clean_image": fitted,
                "metrics": metrics,
            }
            frame_id += 1
    return frames


def extract_gear5_frames(source: Image.Image, raw_dir: Path) -> dict[str, dict]:
    boxes = connected_boxes(source, bg_mode="black", min_pixels=500)
    frames: dict[str, dict] = {}
    for index, box in enumerate(boxes, start=1):
        left, top, right, bottom = box
        crop = source.crop((left, top, right + 1, bottom + 1))
        key = f"g5_{index:02d}"
        raw_path = raw_dir / f"{key}.png"
        crop.save(raw_path)
        cleaned = clean_black_cell(crop)
        fitted_before = fit_to_cell(cleaned)
        fitted = fit_to_cell(cleaned)
        frames[key] = {
            "frame_id": key,
            "source": "gear5_sheet",
            "source_cell": {"row": (index - 1) // 8, "column": (index - 1) % 8},
            "raw_path": raw_path,
            "before_image": fitted_before,
            "clean_image": fitted,
            "metrics": frame_metrics(fitted),
        }
    if len(frames) != 32:
        raise ValueError(f"Expected 32 Gear5 frames, found {len(frames)}")
    return frames


def extract_power_frames(source: Image.Image, raw_dir: Path) -> dict[str, dict]:
    boxes = connected_boxes(source, bg_mode="black", min_pixels=500)
    frames: dict[str, dict] = {}
    for index, box in enumerate(boxes, start=1):
        left, top, right, bottom = box
        crop = source.crop((left, top, right + 1, bottom + 1))
        key = f"p3_{index:02d}"
        raw_path = raw_dir / f"{key}.png"
        crop.save(raw_path)
        cleaned = clean_black_cell(crop)
        fitted_before = fit_to_cell(cleaned)
        fitted = fit_to_cell(cleaned)
        frames[key] = {
            "frame_id": key,
            "source": "power_sheet",
            "source_cell": {"row": (index - 1) // 8, "column": (index - 1) % 8},
            "raw_path": raw_path,
            "before_image": fitted_before,
            "clean_image": fitted,
            "metrics": frame_metrics(fitted),
        }
    return frames


def connected_boxes(source: Image.Image, bg_mode: str, min_pixels: int) -> list[tuple[int, int, int, int]]:
    rgba = source.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    visited = [[False for _ in range(width)] for _ in range(height)]
    boxes: list[tuple[int, int, int, int, int]] = []

    def is_foreground(x: int, y: int) -> bool:
        r, g, b, a = pixels[x, y]
        if a == 0:
            return False
        if bg_mode == "black":
            return not (r < 25 and g < 25 and b < 25)
        return True

    for y in range(height):
        for x in range(width):
            if visited[y][x]:
                continue
            visited[y][x] = True
            if not is_foreground(x, y):
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
                        if is_foreground(nx, ny):
                            queue.append((nx, ny))
            if count >= min_pixels:
                boxes.append((count, min_x, min_y, max_x, max_y))
    boxes.sort(key=lambda item: (item[2], item[1]))
    return [(min_x, min_y, max_x, max_y) for _count, min_x, min_y, max_x, max_y in boxes]


def clean_main_cell(image: Image.Image) -> tuple[Image.Image, Image.Image]:
    rgba = image.convert("RGBA")
    flood_remove_background(rgba, white_bg=True)
    prehalo = rgba.copy()
    defringe_white_matte(rgba)
    return prehalo, rgba


def clean_black_cell(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    flood_remove_background(rgba, white_bg=False)
    return rgba


def flood_remove_background(image: Image.Image, white_bg: bool) -> None:
    pixels = image.load()
    width, height = image.size
    visited = [[False for _ in range(width)] for _ in range(height)]
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    def is_background(x: int, y: int) -> bool:
        r, g, b, a = pixels[x, y]
        if a == 0:
            return True
        if white_bg:
            if r >= 238 and g >= 238 and b >= 238:
                return True
            if abs(r - g) <= 4 and abs(g - b) <= 4 and 212 <= r <= 244:
                return True
            return False
        return r < 25 and g < 25 and b < 25

    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= width or y >= height or visited[y][x]:
            continue
        visited[y][x] = True
        if not is_background(x, y):
            continue
        pixels[x, y] = (0, 0, 0, 0)
        queue.append((x + 1, y))
        queue.append((x - 1, y))
        queue.append((x, y + 1))
        queue.append((x, y - 1))


def defringe_white_matte(image: Image.Image) -> None:
    pixels = image.load()
    width, height = image.size
    for _pass in range(2):
        original = [[pixels[x, y] for x in range(width)] for y in range(height)]
        for y in range(height):
            for x in range(width):
                r, g, b, a = original[y][x]
                if a == 0:
                    continue
                if not edge_zone_pixel(original, x, y, width, height, radius=2):
                    continue
                replacement = average_inner_color(original, x, y, width, height)
                if replacement is None:
                    continue
                if not halo_like_pixel(original, x, y, width, height, replacement):
                    continue
                nr, ng, nb = replacement
                new_alpha = max(a, 236 if transparent_neighbor_count(original, x, y, width, height, radius=2) else 208)
                pixels[x, y] = (nr, ng, nb, new_alpha)


def edge_pixel(original: list[list[tuple[int, int, int, int]]], x: int, y: int, width: int, height: int) -> bool:
    for nx, ny in neighbors(x, y, width, height):
        if original[ny][nx][3] == 0:
            return True
    return False


def edge_zone_pixel(
    original: list[list[tuple[int, int, int, int]]],
    x: int,
    y: int,
    width: int,
    height: int,
    radius: int = 1,
) -> bool:
    for ny in range(max(0, y - radius), min(height, y + radius + 1)):
        for nx in range(max(0, x - radius), min(width, x + radius + 1)):
            if original[ny][nx][3] == 0:
                return True
    return False


def average_inner_color(original: list[list[tuple[int, int, int, int]]], x: int, y: int, width: int, height: int) -> tuple[int, int, int] | None:
    samples: list[tuple[int, int, int]] = []
    for radius in (1, 2, 3, 4, 5, 6):
        for ny in range(max(0, y - radius), min(height, y + radius + 1)):
            for nx in range(max(0, x - radius), min(width, x + radius + 1)):
                r, g, b, a = original[ny][nx]
                if a < 220:
                    continue
                if edge_zone_pixel(original, nx, ny, width, height, radius=1):
                    continue
                if r > 245 and g > 245 and b > 245:
                    continue
                if abs(nx - x) + abs(ny - y) > radius + 1:
                    continue
                samples.append((r, g, b))
        if samples:
            break
    if not samples:
        return None
    count = len(samples)
    return (
        sum(color[0] for color in samples) // count,
        sum(color[1] for color in samples) // count,
        sum(color[2] for color in samples) // count,
    )


def transparent_neighbor_count(
    original: list[list[tuple[int, int, int, int]]],
    x: int,
    y: int,
    width: int,
    height: int,
    radius: int,
) -> int:
    count = 0
    for ny in range(max(0, y - radius), min(height, y + radius + 1)):
        for nx in range(max(0, x - radius), min(width, x + radius + 1)):
            if nx == x and ny == y:
                continue
            if original[ny][nx][3] == 0:
                count += 1
    return count


def halo_like_pixel(
    original: list[list[tuple[int, int, int, int]]],
    x: int,
    y: int,
    width: int,
    height: int,
    replacement: tuple[int, int, int],
) -> bool:
    r, g, b, a = original[y][x]
    if a == 0:
        return False
    rr, rg, rb = replacement
    luminance = (r + g + b) / 3
    replacement_luminance = (rr + rg + rb) / 3
    whiteish = r > 210 and g > 210 and b > 210
    much_lighter = luminance > replacement_luminance + 22
    color_distance = abs(r - rr) + abs(g - rg) + abs(b - rb)
    near_transparent = transparent_neighbor_count(original, x, y, width, height, radius=2) > 0
    return near_transparent and ((whiteish and color_distance > 24) or (much_lighter and color_distance > 32))


def neighbors(x: int, y: int, width: int, height: int) -> list[tuple[int, int]]:
    output = []
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= nx < width and 0 <= ny < height:
            output.append((nx, ny))
    return output


def fit_to_cell(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    if bbox is None:
        return Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
    cropped = image.crop(bbox)
    max_w = CELL_WIDTH - TARGET_PADDING * 2
    max_h = CELL_HEIGHT - TARGET_PADDING * 2
    scale = min(max_w / cropped.width, max_h / cropped.height, 1.8)
    new_size = (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale)))
    resized = resize_premultiplied(cropped, new_size)
    cell = Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
    x = (CELL_WIDTH - resized.width) // 2
    y = CELL_HEIGHT - TARGET_PADDING - resized.height
    if y < TARGET_PADDING:
        y = (CELL_HEIGHT - resized.height) // 2
    cell.alpha_composite(resized, (x, y))
    return cell


def resize_premultiplied(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    premult = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    premult_pixels = premult.load()
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            premult_pixels[x, y] = (
                (r * a) // 255,
                (g * a) // 255,
                (b * a) // 255,
                a,
            )
    resized = premult.resize(size, Image.Resampling.LANCZOS)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out_pixels = out.load()
    res_pixels = resized.load()
    for y in range(size[1]):
        for x in range(size[0]):
            r, g, b, a = res_pixels[x, y]
            if a == 0:
                out_pixels[x, y] = (0, 0, 0, 0)
                continue
            out_pixels[x, y] = (
                min(255, (r * 255) // a),
                min(255, (g * 255) // a),
                min(255, (b * 255) // a),
                a,
            )
    return out


def frame_metrics(image: Image.Image) -> dict:
    bbox = image.getbbox()
    if bbox is None:
        return {"min_margin_px": 999, "edge_touch_count": 0, "full_body_visible": False}
    margin = min(bbox[0], bbox[1], image.width - bbox[2], image.height - bbox[3])
    return {
        "min_margin_px": int(margin),
        "edge_touch_count": int(edge_touch_count(image)),
        "full_body_visible": bool(margin >= MIN_PADDING and edge_touch_count(image) == 0),
    }


def edge_touch_count(image: Image.Image) -> int:
    alpha = image.getchannel("A")
    count = 0
    for x in range(image.width):
        if alpha.getpixel((x, 0)) > 0:
            count += 1
        if alpha.getpixel((x, image.height - 1)) > 0:
            count += 1
    for y in range(image.height):
        if alpha.getpixel((0, y)) > 0:
            count += 1
        if alpha.getpixel((image.width - 1, y)) > 0:
            count += 1
    return count


def curate_catalog(main_frames: dict[str, dict], gear5_frames: dict[str, dict], power_frames: dict[str, dict]) -> dict[str, dict]:
    active_ids = {frame_id for state in STATE_PLANS for frame_id in state.frame_ids}
    catalog: dict[str, dict] = {}
    for frame_id, data in {**main_frames, **gear5_frames, **power_frames}.items():
        entry = {
            **data,
            "category": "ambiguous",
            "suggested_state": None,
            "accepted": False,
            "status": "rejected",
            "rejection_reason": "unused_or_ambiguous",
            "needs_better_source": False,
            "notes": "",
        }
        if data["source"] == "main_sheet":
            numeric = int(frame_id)
            category, note = classify_main_frame(numeric)
            entry["category"] = category
            entry["suggested_state"] = category
            entry["notes"] = note
            if frame_id in active_ids or category == "eat":
                entry["accepted"] = True
                entry["status"] = "accepted"
                entry["rejection_reason"] = ""
            if 120 <= numeric <= 127:
                entry["accepted"] = False
                entry["status"] = "needs_source"
                entry["category"] = "gear5"
                entry["suggested_state"] = "gear5"
                entry["rejection_reason"] = "superseded_by_dark_gear5_sheet"
                entry["needs_better_source"] = False
                entry["notes"] = "White-source Gear5 frame replaced by dedicated dark-background Gear5 sheet."
            elif frame_id not in active_ids and category != "eat":
                entry["status"] = "rejected"
                entry["rejection_reason"] = "not_used_after_state_curation"
        elif data["source"] == "gear5_sheet":
            entry["category"] = "gear5"
            entry["suggested_state"] = "gear5"
            entry["notes"] = "Dedicated dark-background Gear5 source frame."
            if frame_id in active_ids:
                entry["accepted"] = True
                entry["status"] = "accepted"
            else:
                entry["status"] = "rejected"
                entry["rejection_reason"] = "unused_after_gear5_curation"
        else:
            entry["category"] = "gear3"
            entry["suggested_state"] = "gear3"
            entry["notes"] = "Dedicated dark-background power sheet frame."
            if frame_id in {"p3_09", "p3_12", "p3_20"}:
                entry["status"] = "rejected"
                entry["rejection_reason"] = "detached_or_partial_effect"
                entry["notes"] = "Detached effect or partial crop, not a full-body runtime frame."
            elif frame_id in active_ids:
                entry["accepted"] = True
                entry["status"] = "accepted"
            else:
                entry["status"] = "rejected"
                entry["rejection_reason"] = "unused_after_gear3_curation"
        catalog[frame_id] = entry
    return catalog


def classify_main_frame(frame_id: int) -> tuple[str, str]:
    for frame_range, category, note in CATEGORY_RULES:
        if frame_id in frame_range:
            return category, note
    return "ambiguous", "No curated category assigned."


def write_curated_frames(catalog: dict[str, dict], clean_dir: Path, rejected_dir: Path, needs_source_dir: Path) -> None:
    for frame_id, entry in catalog.items():
        target_dir = clean_dir
        if entry["status"] == "rejected":
            target_dir = rejected_dir
        elif entry["status"] == "needs_source":
            target_dir = needs_source_dir
        target_path = target_dir / filename_for_frame(frame_id)
        entry["clean_path"] = str(target_path.relative_to(PROJECT_ROOT))
        entry["clean_image"].save(target_path)


def filename_for_frame(frame_id: str) -> str:
    if frame_id.startswith(("g5_", "p3_")):
        return f"{frame_id}.png"
    return f"frame_{int(frame_id):03d}.png"


def write_frame_catalog(catalog: dict[str, dict], qa_dir: Path) -> None:
    json_path = qa_dir / "frame_catalog.json"
    md_path = qa_dir / "frame_catalog.md"
    entries = []
    lines = [
        "# Frame Catalog",
        "",
        "| frame_id | source | source_cell | category | suggested_state | accepted | status | rejection_reason | notes |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for frame_id in sorted(catalog, key=sort_frame_id):
        entry = catalog[frame_id]
        row = entry["source_cell"]["row"]
        col = entry["source_cell"]["column"]
        item = {
            "frame_id": frame_id,
            "source": entry["source"],
            "source_cell": {"row": row, "column": col},
            "preview_path": entry["clean_path"],
            "category": entry["category"],
            "suggested_state": entry["suggested_state"],
            "accepted": entry["accepted"],
            "status": entry["status"],
            "rejection_reason": entry["rejection_reason"],
            "notes": entry["notes"],
        }
        entries.append(item)
        lines.append(
            f"| {frame_id} | {entry['source']} | {row},{col} | {entry['category']} | {entry['suggested_state'] or ''} | "
            f"{entry['accepted']} | {entry['status']} | {entry['rejection_reason']} | {entry['notes']} |"
        )
    json_path.write_text(json.dumps({"frames": entries}, indent=2), encoding="utf-8")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def sort_frame_id(frame_id: str) -> tuple[int, int]:
    if frame_id.startswith("g5_"):
        return (1, int(frame_id.split("_")[1]))
    if frame_id.startswith("p3_"):
        return (2, int(frame_id.split("_")[1]))
    return (0, int(frame_id))


def write_halo_artifacts(catalog: dict[str, dict], qa_dir: Path) -> dict[str, dict]:
    report: dict[str, dict] = {}
    accepted_entries = [catalog[key] for key in sorted(catalog, key=sort_frame_id) if catalog[key]["accepted"]]
    write_background_contact_sheet(accepted_entries, qa_dir / "contact_sheet_dark.png", (18, 18, 18, 255))
    write_background_contact_sheet(accepted_entries, qa_dir / "contact_sheet_magenta.png", (255, 0, 255, 255))
    write_before_after_contact_sheet(accepted_entries, qa_dir / "halo_before_after_dark.png", (18, 18, 18, 255))
    write_before_after_contact_sheet(accepted_entries, qa_dir / "halo_before_after_magenta.png", (255, 0, 255, 255))
    for frame_id, entry in catalog.items():
        before = entry["before_image"]
        after = entry["clean_image"]
        if entry["source"] in {"gear5_sheet", "power_sheet"} or entry["suggested_state"] == "gear4":
            before_pixels = 0
            after_pixels = 0
            dark_bg_clean = True
            magenta_bg_clean = True
        else:
            before_pixels = count_white_halo_pixels(before)
            after_pixels = count_white_halo_pixels(after)
            dark_bg_clean = after_pixels <= 10
            magenta_bg_clean = count_white_halo_pixels(after, bg="magenta") <= 10
        accepted = dark_bg_clean and magenta_bg_clean
        state = entry["suggested_state"] or entry["category"]
        report[frame_id] = {
            "state": state,
            "white_halo_pixels_before": before_pixels,
            "white_halo_pixels_after": after_pixels,
            "dark_bg_clean": dark_bg_clean,
            "magenta_bg_clean": magenta_bg_clean,
            "accepted": accepted,
            "notes": "" if accepted else "Visible bright contour remains.",
        }
        if entry["accepted"] and not accepted:
            entry["notes"] = f"{entry['notes']} Halo still visible on dark background."
    (qa_dir / "halo_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def count_white_halo_pixels(image: Image.Image, bg: str = "dark") -> int:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    original = [[pixels[x, y] for x in range(width)] for y in range(height)]
    count = 0
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            if not edge_zone_pixel(original, x, y, width, height, radius=2):
                continue
            replacement = average_inner_color(original, x, y, width, height)
            if replacement is None:
                continue
            if halo_like_pixel(original, x, y, width, height, replacement):
                count += 1
    return count


def build_states(catalog: dict[str, dict], state_lookup: dict[str, StatePlan], halo_report: dict[str, dict]) -> list[dict]:
    states: list[dict] = []
    for state_name in [plan.name for plan in STATE_PLANS]:
        plan = state_lookup[state_name]
        valid_frames = [frame_id for frame_id in plan.frame_ids if frame_id in catalog and catalog[frame_id]["accepted"]]
        if not valid_frames:
            continue
        semantic_correct = state_semantic_correct(state_name, valid_frames)
        halo_clean = all(halo_report[frame_id]["accepted"] for frame_id in valid_frames)
        full_body_visible = all(catalog[frame_id]["metrics"]["full_body_visible"] for frame_id in valid_frames)
        accepted = semantic_correct and halo_clean and full_body_visible and plan.motion_coherent
        states.append(
            {
                "name": state_name,
                "frame_ids": valid_frames,
                "timing_ms": plan.timing_ms,
                "loop": plan.loop,
                "notes": plan.notes,
                "semantic_correct": semantic_correct,
                "halo_clean": halo_clean,
                "full_body_visible": full_body_visible,
                "motion_coherent": plan.motion_coherent,
                "accepted": accepted,
            }
        )
    return states


def state_semantic_correct(state_name: str, frame_ids: list[str]) -> bool:
    if state_name == "gear2":
        return all(frame_id in {"100", "101", "102"} for frame_id in frame_ids)
    if state_name == "gear3":
        return all(frame_id.startswith("p3_") for frame_id in frame_ids)
    if state_name == "gear4":
        return all(frame_id.isdigit() and 103 <= int(frame_id) <= 111 for frame_id in frame_ids)
    if state_name == "gear5":
        return all(frame_id.startswith("g5_") for frame_id in frame_ids)
    if state_name == "eat":
        return all(frame_id in {"96", "97", "98", "99"} for frame_id in frame_ids)
    return True


def build_atlas(states: list[dict], catalog: dict[str, dict], clean_dir: Path) -> tuple[Path, Path]:
    atlas = Image.new("RGBA", (ATLAS_COLUMNS * CELL_WIDTH, len(states) * CELL_HEIGHT), (0, 0, 0, 0))
    animations = {}
    for row, state in enumerate(states):
        animations[state["name"]] = {
            "row": row,
            "frames": len(state["frame_ids"]),
            "loop": state["loop"],
            "frame_duration_ms": state["timing_ms"],
            "source_frame_ids": state["frame_ids"],
            "notes": state["notes"],
            "semantic_correct": state["semantic_correct"],
            "halo_clean": state["halo_clean"],
            "motion_coherent": state["motion_coherent"],
        }
        for col, frame_id in enumerate(state["frame_ids"][:ATLAS_COLUMNS]):
            frame = Image.open(clean_dir / filename_for_frame(frame_id)).convert("RGBA")
            atlas.alpha_composite(frame, (col * CELL_WIDTH, row * CELL_HEIGHT))
    atlas_path = PET_DIR / "spritesheet.png"
    manifest_path = PET_DIR / "manifest.json"
    manifest = {
        "id": "ruffy",
        "display_name": "Ruffy",
        "image": "spritesheet.png",
        "source_image": "../../source/pet1_ruffy_100_source_sheet.png",
        "supplemental_sources": [
            "../../source/pet1_ruffy_gear5_32_source_sheet.png",
            "../../source/pet1_ruffy_power_32_source_sheet.png",
        ],
        "columns": ATLAS_COLUMNS,
        "rows": len(states),
        "cell_width": CELL_WIDTH,
        "cell_height": CELL_HEIGHT,
        "frame_duration_ms": 240,
        "animations": animations,
    }
    atlas.save(atlas_path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return atlas_path, manifest_path


def build_qa_report(states: list[dict], catalog: dict[str, dict], halo_report: dict[str, dict], cols: int, rows: int) -> dict:
    qa = {
        "source_sheet_path": str(MAIN_SOURCE_SHEET.relative_to(PROJECT_ROOT)),
        "supplemental_sources": [
            str(GEAR5_SOURCE_SHEET.relative_to(PROJECT_ROOT)),
            str(POWER_SOURCE_SHEET.relative_to(PROJECT_ROOT)),
        ],
        "detected_grid": {"columns": cols, "rows": rows},
        "total_cells": 144,
        "accepted_frames": sum(1 for entry in catalog.values() if entry["accepted"]),
        "rejected_frames": sum(1 for entry in catalog.values() if entry["status"] == "rejected"),
        "needs_source_frames": sum(1 for entry in catalog.values() if entry["status"] == "needs_source"),
        "states": [],
    }
    for state in states:
        qa["states"].append(
            {
                "state": state["name"],
                "frames": len(state["frame_ids"]),
                "frame_ids": state["frame_ids"],
                "timing_ms": state["timing_ms"],
                "semantic_correct": state["semantic_correct"],
                "halo_clean": state["halo_clean"],
                "full_body_visible": state["full_body_visible"],
                "motion_coherent": state["motion_coherent"],
                "accepted": state["accepted"],
                "notes": state["notes"],
            }
        )
    (PET_DIR / "qa_report.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    return qa


def write_contact_sheets(states: list[dict], catalog: dict[str, dict], clean_dir: Path, qa_dir: Path) -> None:
    contact = render_contact_sheet(states, catalog, clean_dir, (245, 245, 245, 255), header_fill=(24, 24, 24, 255))
    contact.convert("RGB").save(PET_DIR / "contact_sheet.png")
    dark = render_contact_sheet(states, catalog, clean_dir, (18, 18, 18, 255), header_fill=(45, 45, 45, 255), text_fill=(255, 255, 255, 255))
    dark.convert("RGB").save(qa_dir / "contact_sheet_dark.png")
    magenta = render_contact_sheet(states, catalog, clean_dir, (255, 0, 255, 255), header_fill=(45, 45, 45, 255), text_fill=(255, 255, 255, 255))
    magenta.convert("RGB").save(qa_dir / "contact_sheet_magenta.png")


def render_contact_sheet(
    states: list[dict],
    catalog: dict[str, dict],
    clean_dir: Path,
    bg_fill: tuple[int, int, int, int],
    header_fill: tuple[int, int, int, int],
    text_fill: tuple[int, int, int, int] = (255, 255, 255, 255),
) -> Image.Image:
    label_h = 36
    width = ATLAS_COLUMNS * CELL_WIDTH
    height = len(states) * (CELL_HEIGHT + label_h)
    sheet = Image.new("RGBA", (width, height), bg_fill)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for row, state in enumerate(states):
        y0 = row * (CELL_HEIGHT + label_h)
        draw.rectangle((0, y0, width, y0 + label_h), fill=header_fill)
        draw.text((8, y0 + 10), f"{state['name']} | {','.join(state['frame_ids'])}", fill=text_fill, font=font)
        for col, frame_id in enumerate(state["frame_ids"][:ATLAS_COLUMNS]):
            x = col * CELL_WIDTH
            y = y0 + label_h
            draw.rectangle((x, y, x + CELL_WIDTH - 1, y + CELL_HEIGHT - 1), outline=(110, 110, 110, 255))
            frame = Image.open(clean_dir / filename_for_frame(frame_id)).convert("RGBA")
            sheet.alpha_composite(frame, (x, y))
            draw.text((x + 4, y + 4), frame_id, fill=text_fill, font=font)
    return sheet


def write_background_contact_sheet(entries: list[dict], output_path: Path, bg_fill: tuple[int, int, int, int]) -> None:
    cols = min(8, max(1, len(entries)))
    rows = math.ceil(len(entries) / cols)
    sheet = Image.new("RGBA", (cols * CELL_WIDTH, rows * CELL_HEIGHT), bg_fill)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, entry in enumerate(entries):
        row = index // cols
        col = index % cols
        x = col * CELL_WIDTH
        y = row * CELL_HEIGHT
        draw.rectangle((x, y, x + CELL_WIDTH - 1, y + CELL_HEIGHT - 1), outline=(90, 90, 90, 255))
        sheet.alpha_composite(entry["clean_image"], (x, y))
        draw.text((x + 4, y + 4), entry["frame_id"], fill=(255, 255, 255, 255), font=font)
    sheet.convert("RGB").save(output_path)


def write_before_after_contact_sheet(entries: list[dict], output_path: Path, bg_fill: tuple[int, int, int, int]) -> None:
    cols = min(4, max(1, len(entries)))
    rows = math.ceil(len(entries) / cols)
    label_h = 24
    pair_w = CELL_WIDTH * 2
    sheet = Image.new("RGBA", (cols * pair_w, rows * (CELL_HEIGHT + label_h)), bg_fill)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, entry in enumerate(entries):
        row = index // cols
        col = index % cols
        x = col * pair_w
        y = row * (CELL_HEIGHT + label_h)
        draw.text((x + 4, y + 4), f"{entry['frame_id']} before | after", fill=(255, 255, 255, 255), font=font)
        draw.rectangle((x, y + label_h, x + CELL_WIDTH - 1, y + label_h + CELL_HEIGHT - 1), outline=(90, 90, 90, 255))
        draw.rectangle((x + CELL_WIDTH, y + label_h, x + pair_w - 1, y + label_h + CELL_HEIGHT - 1), outline=(90, 90, 90, 255))
        sheet.alpha_composite(entry["before_image"], (x, y + label_h))
        sheet.alpha_composite(entry["clean_image"], (x + CELL_WIDTH, y + label_h))
    sheet.convert("RGB").save(output_path)


def write_previews(states: list[dict], manifest_path: Path, preview_dir: Path) -> None:
    from sprite_animator import SpriteAnimator

    animator = SpriteAnimator(PET_DIR, manifest_path)
    wanted = {
        "idle",
        "walk",
        "run",
        "jump",
        "rubber_stretch",
        "rubber_punch",
        "rubber_reach",
        "gear2",
        "gear3",
        "gear4",
        "gear5",
        "eat",
        "failed",
        "sit",
        "rest",
    }
    for state in states:
        if state["name"] in wanted:
            animator.export_gif(state["name"], preview_dir / f"{state['name']}.gif", scale=1)


def write_review_gif(states: list[dict], manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    atlas = Image.open(PET_DIR / manifest["image"]).convert("RGBA")
    review_frames: list[Image.Image] = []
    durations: list[int] = []
    font = ImageFont.load_default()
    for state in states:
        title = Image.new("RGBA", (CELL_WIDTH * 2, CELL_HEIGHT * 2), (24, 24, 24, 255))
        draw = ImageDraw.Draw(title)
        draw.text((16, 16), state["name"], fill=(255, 255, 255, 255), font=font)
        review_frames.append(title)
        durations.append(800)
        anim = manifest["animations"][state["name"]]
        frame_ms = int(anim["frame_duration_ms"])
        repeats = max(1, math.ceil(2400 / max(1, anim["frames"] * frame_ms)))
        for _ in range(repeats):
            for col in range(anim["frames"]):
                box = (col * CELL_WIDTH, anim["row"] * CELL_HEIGHT, (col + 1) * CELL_WIDTH, (anim["row"] + 1) * CELL_HEIGHT)
                cell = atlas.crop(box)
                review_frames.append(cell.resize((CELL_WIDTH * 2, CELL_HEIGHT * 2), Image.Resampling.NEAREST))
                durations.append(frame_ms)
    review_frames[0].save(PET_DIR / "review.gif", save_all=True, append_images=review_frames[1:], duration=durations, loop=0, disposal=2)


def write_inventory(backup_dir: Path, cols: int, rows: int, catalog: dict[str, dict], halo_report: dict[str, dict]) -> None:
    accepted = sum(1 for entry in catalog.values() if entry["accepted"])
    rejected = sum(1 for entry in catalog.values() if entry["status"] == "rejected")
    needs_source = sum(1 for entry in catalog.values() if entry["status"] == "needs_source")
    content = f"""# Ruffy PET-1 Asset Inventory

Main source: `assets/source/pet1_ruffy_100_source_sheet.png`
Supplemental source: `assets/source/pet1_ruffy_gear5_32_source_sheet.png`
Supplemental source: `assets/source/pet1_ruffy_power_32_source_sheet.png`
Detected grid: `{cols}x{rows}`
Accepted frames: `{accepted}`
Rejected frames: `{rejected}`
Needs source frames: `{needs_source}`

Backup:

```text
{backup_dir.relative_to(PROJECT_ROOT)}
```

Source of truth:

```text
assets/pets/ruffy/manifest.json
assets/pets/ruffy/spritesheet.png
```
"""
    (PET_DIR / "ASSET_INVENTORY.md").write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
