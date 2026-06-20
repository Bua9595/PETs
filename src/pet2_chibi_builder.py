from __future__ import annotations

import json
import math
import shutil
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
REFERENCE_PATH = ASSETS_DIR / "source" / "pet2_chibi_reference_sheet.png"
PET_DIR = ASSETS_DIR / "pets" / "pet2_chibi"

CELL_WIDTH = 192
CELL_HEIGHT = 208
ATLAS_COLUMNS = 12
TARGET_PADDING = 20
MIN_PADDING = 14


@dataclass(frozen=True)
class StatePlan:
    name: str
    refs: list[tuple[str, int]]
    timing_ms: int
    loop: bool
    notes: str
    head_visible: bool = True
    hands_visible: bool = True
    legs_visible: bool = True
    feet_visible: bool = True


SECTIONS = {
    "idle": (13, 34, 491, 154),
    "walk": (503, 34, 944, 154),
    "run": (950, 34, 1432, 154),
    "jump": (13, 159, 491, 290),
    "emotions": (503, 159, 944, 290),
    "social": (950, 159, 1432, 290),
    "gaming": (13, 301, 491, 426),
    "laptop": (503, 301, 944, 426),
    "chat": (950, 301, 1432, 426),
    "rest": (13, 713, 491, 845),
    "sleep": (503, 713, 944, 845),
    "extra": (950, 713, 1432, 845),
}

STATE_PLANS = [
    StatePlan("idle", [("idle", 1), ("idle", 4), ("idle", 5), ("idle", 6)], 300, True, "Neutral idle and look-around loop."),
    StatePlan("blink", [("idle", 1), ("idle", 2), ("idle", 3), ("idle", 1)], 260, True, "Closed-eye blink loop."),
    StatePlan("wave", [("social", 1), ("social", 1), ("social", 1)], 230, True, "Single clean wave pose held as a pet loop."),
    StatePlan("happy", [("emotions", 1), ("emotions", 2), ("emotions", 3), ("emotions", 1)], 230, True, "Happy / laugh / excited reaction loop."),
    StatePlan("walk", [("walk", 1), ("walk", 2), ("walk", 3), ("walk", 4), ("walk", 5), ("walk", 6), ("walk", 7)], 220, True, "Short soft walk cycle."),
    StatePlan("run", [("run", 1), ("run", 2), ("run", 3), ("run", 4), ("run", 5), ("run", 6), ("run", 7), ("run", 8)], 180, True, "Full directional run cycle."),
    StatePlan("jump", [("jump", 1), ("jump", 2), ("jump", 3), ("jump", 4), ("jump", 5), ("jump", 6), ("jump", 7)], 220, False, "Jump, airtime, and landing sequence."),
    StatePlan("rest", [("rest", 1), ("rest", 2), ("rest", 6), ("rest", 7)], 320, True, "Sit and calm desk-rest loop."),
    StatePlan("wink", [("social", 2), ("social", 2), ("social", 2)], 260, True, "Held wink pose."),
    StatePlan("shy", [("social", 6), ("social", 6), ("social", 6)], 280, True, "Held shy pose."),
    StatePlan("gaming", [("gaming", 1), ("gaming", 2), ("gaming", 3), ("gaming", 4)], 300, True, "Cute gaming/controller poses; seated lower body intentionally compact."),
    StatePlan("chat", [("chat", 1), ("chat", 3), ("chat", 4), ("chat", 6)], 280, True, "Chat / Discord / voice-chat variations; body remains readable at pet scale."),
    StatePlan("phone", [("chat", 5), ("chat", 6), ("chat", 5)], 280, True, "Phone check and texting hold loop."),
    StatePlan("celebrate", [("extra", 5), ("extra", 6), ("extra", 6)], 220, True, "Short cheer / hype celebration sequence."),
]


def main() -> None:
    if not REFERENCE_PATH.exists():
        raise FileNotFoundError(f"PET2 reference sheet not found: {REFERENCE_PATH}")

    if PET_DIR.exists():
        shutil.rmtree(PET_DIR)
    (PET_DIR / "row_sources").mkdir(parents=True, exist_ok=True)
    (PET_DIR / "previews").mkdir(parents=True, exist_ok=True)
    (PET_DIR / "qa").mkdir(parents=True, exist_ok=True)

    source = Image.open(REFERENCE_PATH).convert("RGBA")
    section_components = extract_sections(source)
    source_frames = write_source_frames(section_components)
    atlas_path, manifest_path, state_rows = build_pet_outputs(source_frames)
    qa_report = write_qa(source_frames, state_rows)
    write_contact_sheets(source_frames, state_rows)
    write_previews_and_review(manifest_path)
    write_runtime_test_note()

    print(
        json.dumps(
            {
                "reference": str(REFERENCE_PATH.relative_to(PROJECT_ROOT)),
                "spritesheet": str(atlas_path.relative_to(PROJECT_ROOT)),
                "manifest": str(manifest_path.relative_to(PROJECT_ROOT)),
                "states": [state["name"] for state in state_rows],
                "qa_states": len(qa_report["states"]),
            },
            indent=2,
        )
    )


def extract_sections(source: Image.Image) -> dict[str, list[dict]]:
    extracted: dict[str, list[dict]] = {}
    for name, box in SECTIONS.items():
        crop = source.crop(box)
        components = connected_components(crop)
        components.sort(key=lambda item: item["bbox"][0])
        section_frames: list[dict] = []
        for index, comp in enumerate(components, start=1):
            raw = crop.crop(comp["bbox"])
            cleaned = crop_to_transparency(raw)
            fitted = fit_to_cell(cleaned)
            section_frames.append(
                {
                    "section": name,
                    "index": index,
                    "image": fitted,
                    "raw_image": cleaned,
                    "bbox": comp["bbox"],
                    "metrics": frame_metrics(fitted),
                }
            )
        extracted[name] = section_frames
    return extracted


def connected_components(image: Image.Image) -> list[dict]:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    visited = [[False for _ in range(width)] for _ in range(height)]
    output: list[dict] = []

    def is_foreground(x: int, y: int) -> bool:
        r, g, b, a = pixels[x, y]
        return a > 0 and not (r > 245 and g > 245 and b > 245)

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
            box = (min_x, min_y, max_x + 1, max_y + 1)
            bw = box[2] - box[0]
            bh = box[3] - box[1]
            if count >= 1500 and bw >= 35 and bh >= 45:
                output.append({"pixels": count, "bbox": box})
    return output


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

    def is_background(x: int, y: int) -> bool:
        r, g, b, a = pixels[x, y]
        if a == 0:
            return True
        return r > 242 and g > 242 and b > 242

    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= width or y >= height or visited[y][x]:
            continue
        visited[y][x] = True
        if not is_background(x, y):
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
    bbox = components[0][1]
    return rgba.crop(bbox)


def fit_to_cell(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    if bbox is None:
        return Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
    cropped = image.crop(bbox)
    max_w = CELL_WIDTH - TARGET_PADDING * 2
    max_h = CELL_HEIGHT - TARGET_PADDING * 2
    scale = min(max_w / cropped.width, max_h / cropped.height, 2.2)
    new_size = (max(1, round(cropped.width * scale)), max(1, round(cropped.height * scale)))
    resized = cropped.resize(new_size, Image.Resampling.LANCZOS)
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
            "green_edge_pixels": 0,
            "pink_edge_pixels": 0,
            "groundline_px": 0,
            "height_px": 0,
        }
    alpha = image.getchannel("A")
    margin = min(bbox[0], bbox[1], image.width - bbox[2], image.height - bbox[3])
    edge_touches = 0
    for x in range(image.width):
        edge_touches += int(alpha.getpixel((x, 0)) > 0)
        edge_touches += int(alpha.getpixel((x, image.height - 1)) > 0)
    for y in range(image.height):
        edge_touches += int(alpha.getpixel((0, y)) > 0)
        edge_touches += int(alpha.getpixel((image.width - 1, y)) > 0)
    green = pink = 0
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            if not edge_zone(alpha, x, y):
                continue
            if a > 110:
                continue
            if g > 240 and r < 100 and b < 100:
                green += 1
            if r > 245 and b > 245 and g < 90:
                pink += 1
    return {
        "min_margin_px": int(margin),
        "edge_touch_count": int(edge_touches),
        "green_edge_pixels": int(green),
        "pink_edge_pixels": int(pink),
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


def write_source_frames(section_components: dict[str, list[dict]]) -> dict[str, dict]:
    output: dict[str, dict] = {}
    for section, frames in section_components.items():
        for frame in frames:
            key = f"{section}_{frame['index']:02d}"
            path = PET_DIR / "row_sources" / f"{key}.png"
            frame["image"].save(path)
            output[key] = {
                **frame,
                "key": key,
                "path": path,
            }
    return output


def build_pet_outputs(source_frames: dict[str, dict]) -> tuple[Path, Path, list[dict]]:
    states: list[dict] = []
    atlas = Image.new("RGBA", (ATLAS_COLUMNS * CELL_WIDTH, len(STATE_PLANS) * CELL_HEIGHT), (0, 0, 0, 0))
    animations: dict[str, dict] = {}
    for row, plan in enumerate(STATE_PLANS):
        frame_keys = [f"{section}_{index:02d}" for section, index in plan.refs]
        metrics = [source_frames[key]["metrics"] for key in frame_keys]
        min_margin = min(item["min_margin_px"] for item in metrics)
        edge_touch = max(item["edge_touch_count"] for item in metrics)
        green = sum(item["green_edge_pixels"] for item in metrics)
        pink = sum(item["pink_edge_pixels"] for item in metrics)
        heights = [item["height_px"] for item in metrics]
        groundlines = [item["groundline_px"] for item in metrics]
        state_info = {
            "name": plan.name,
            "frame_keys": frame_keys,
            "timing_ms": plan.timing_ms,
            "loop": plan.loop,
            "notes": plan.notes,
            "min_margin_px": min_margin,
            "edge_touch_count": edge_touch,
            "green_edge_pixels": green,
            "pink_edge_pixels": pink,
            "height_var_pct": variation_pct(heights),
            "groundline_var_px": max(groundlines) - min(groundlines),
            "head_visible": plan.head_visible,
            "hands_visible": plan.hands_visible,
            "legs_visible": plan.legs_visible,
            "feet_visible": plan.feet_visible,
        }
        state_info["full_body_visible"] = (
            state_info["head_visible"]
            and state_info["hands_visible"]
            and state_info["legs_visible"]
            and state_info["feet_visible"]
            and min_margin >= MIN_PADDING
            and edge_touch == 0
        )
        state_info["accepted"] = (
            state_info["full_body_visible"]
            and green <= 3
            and pink <= 12
            and state_info["height_var_pct"] <= (30 if plan.name == "jump" else 18)
            and state_info["groundline_var_px"] <= 20
        )
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
    manifest_path = PET_DIR / "manifest.json"
    atlas.save(atlas_path)
    manifest = {
        "id": "pet2_chibi",
        "display_name": "Pet 2 Chibi Girl",
        "image": "spritesheet.png",
        "source_image": "../../source/pet2_chibi_reference_sheet.png",
        "columns": ATLAS_COLUMNS,
        "rows": len(STATE_PLANS),
        "cell_width": CELL_WIDTH,
        "cell_height": CELL_HEIGHT,
        "frame_duration_ms": 280,
        "personality_tags": ["cute", "social", "gamer", "cheerful", "playful", "streamer", "competitive"],
        "interaction_tags": ["greet", "wave_to_other_pet", "sit_together", "play_together", "follow", "celebrate_together"],
        "compatible_group_actions": ["greet", "wave_to_other_pet", "sit_together", "play_together", "follow", "celebrate_together", "inspect_folder_together"],
        "desktop_behavior": {
            "initial_animation": "idle",
            "drag_animation": "idle",
            "double_click_animation": "happy",
            "menu_states": [
                {"label": "Idle", "animation": "idle"},
                {"label": "Blink", "animation": "blink"},
                {"label": "Wave", "animation": "wave"},
                {"label": "Happy", "animation": "happy"},
                {"label": "Walk", "animation": "walk"},
                {"label": "Run", "animation": "run"},
                {"label": "Jump", "animation": "jump"},
                {"label": "Rest", "animation": "rest"},
                {"label": "Wink", "animation": "wink"},
                {"label": "Shy", "animation": "shy"},
                {"label": "Gaming", "animation": "gaming"},
                {"label": "Chat", "animation": "chat"},
                {"label": "Phone", "animation": "phone"},
                {"label": "Celebrate", "animation": "celebrate"},
            ],
            "choices": [
                {"animation": "idle", "weight": 22},
                {"animation": "blink", "weight": 7},
                {"animation": "wave", "weight": 5},
                {"animation": "happy", "weight": 5},
                {"animation": "walk", "weight": 8},
                {"animation": "run", "weight": 10},
                {"animation": "jump", "weight": 7},
                {"animation": "rest", "weight": 5},
                {"animation": "wink", "weight": 4},
                {"animation": "shy", "weight": 4},
                {"animation": "gaming", "weight": 4},
                {"animation": "chat", "weight": 4},
                {"animation": "phone", "weight": 4},
                {"animation": "celebrate", "weight": 3},
            ],
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
        "reference_file": str(REFERENCE_PATH.relative_to(PROJECT_ROOT)),
        "states": [],
        "planned_backlog": [
            {"group": "core_idle_movement", "proposed_states": ["idle_variations", "blink_variants", "walk_cycle", "jump_land", "sit_rest"], "estimated_frames": 24, "priority": "high", "generate_now_or_later": "generate_now+later"},
            {"group": "social_cute_reactions", "proposed_states": ["wave", "wink", "shy", "heart", "happy_sparkle", "laugh", "surprise"], "estimated_frames": 18, "priority": "high", "generate_now_or_later": "generate_now+later"},
            {"group": "gamer_streamer", "proposed_states": ["gaming", "laptop", "phone", "chat", "celebrate", "focus_mode", "headset_adjust"], "estimated_frames": 20, "priority": "high", "generate_now_or_later": "generate_now+later"},
            {"group": "counter_strike_inspired", "proposed_states": ["queue_wait", "tactical_think", "clutch_celebrate", "peek_pose", "rank_pride", "desk_competitive_mode"], "estimated_frames": 16, "priority": "medium", "generate_now_or_later": "later"},
            {"group": "desktop_interaction", "proposed_states": ["drag_react", "cursor_follow", "sit_on_edge", "hang", "folder_peek", "window_peek", "object_inspect"], "estimated_frames": 14, "priority": "medium", "generate_now_or_later": "later"},
            {"group": "multi_pet_interaction", "proposed_states": ["greet_other_pet", "wave_to_other_pet", "play_together", "sit_together", "celebrate_together", "follow_other_pet"], "estimated_frames": 14, "priority": "medium", "generate_now_or_later": "later"},
        ],
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
                "green_edge_pixels": state["green_edge_pixels"],
                "pink_edge_pixels": state["pink_edge_pixels"],
                "height_var_pct": state["height_var_pct"],
                "groundline_var_px": state["groundline_var_px"],
                "head_visible": state["head_visible"],
                "hands_visible": state["hands_visible"],
                "legs_visible": state["legs_visible"],
                "feet_visible": state["feet_visible"],
                "full_body_visible": state["full_body_visible"],
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
    sheet = Image.new("RGBA", (width, height), (245, 245, 245, 255))
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
            draw.rectangle(box, outline=(180, 180, 180, 255))
            dark_draw.rectangle(box, outline=(90, 90, 90, 255))
            image = source_frames[key]["image"]
            sheet.alpha_composite(image, (x, y + label_h))
            dark.alpha_composite(image, (x, y + label_h))
            draw.text((x + 4, y + label_h + 4), key, fill=(60, 60, 60, 255), font=font)
            dark_draw.text((x + 4, y + label_h + 4), key, fill=(255, 255, 255, 255), font=font)
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
            box = (col * CELL_WIDTH, anim["row"] * CELL_HEIGHT, (col + 1) * CELL_WIDTH, (anim["row"] + 1) * CELL_HEIGHT)
            cell = atlas.crop(box).resize((CELL_WIDTH * 2, CELL_HEIGHT * 2), Image.Resampling.LANCZOS)
            review_frames.append(cell)
            durations.append(frame_ms)
    review_frames[0].save(PET_DIR / "review.gif", save_all=True, append_images=review_frames[1:], duration=durations, loop=0, disposal=2)


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
