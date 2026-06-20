from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from statistics import mean
from typing import Any

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
MANIFEST_PATH = ASSETS_DIR / "ruffy_sprite_manifest.json"
QA_DIR = ASSETS_DIR / "sprites" / "qa"
VISUAL_REVIEW_PATH = QA_DIR / "visual_review.json"
PREVIEW_DIR = ASSETS_DIR / "sprites" / "previews"
QA_ROWS_DIR = ASSETS_DIR / "sprites" / "qa_rows"
CONTACT_SHEET_PATH = ASSETS_DIR / "sprites" / "ruffy_v2_contact_sheet.png"

ALPHA_THRESHOLD = 24
MIN_ACCEPTED_MARGIN = 14
TARGET_MARGIN = 20
UPRIGHT_STATES = {"idle", "run", "wave", "rubber_punch", "gear2", "power_up", "review", "carry_run"}
NORMAL_STATES = {"idle", "run", "wave", "review"}
INTENTIONAL_EFFECT_STATES = {"gear2", "power_up"}
ALIAS_STATES = {"review", "carry_run", "power_up"}
ACTIVE_REVIEW_ANIMATIONS = ["hatch", "idle", "run", "jump", "wave", "failed", "rubber_punch", "gear2"]


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    atlas = Image.open(ASSETS_DIR / manifest["image"]).convert("RGBA")

    QA_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    QA_ROWS_DIR.mkdir(parents=True, exist_ok=True)

    visual_review = load_visual_review()
    report = build_report(atlas, manifest, visual_review)
    (QA_DIR / "qa_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_contact_sheet(atlas, manifest, report, CONTACT_SHEET_PATH)
    write_row_images(atlas, manifest)
    write_gifs(atlas, manifest)
    write_full_review_gif(atlas, manifest, QA_DIR / "ruffy_full_review.gif")

    print(json.dumps(report, indent=2))
    print(f"wrote {CONTACT_SHEET_PATH}")
    print(f"wrote previews in {PREVIEW_DIR}")


def load_visual_review() -> dict[str, Any]:
    if not VISUAL_REVIEW_PATH.exists():
        raise FileNotFoundError(
            f"Visual review file missing: {VISUAL_REVIEW_PATH}. "
            "Create it after inspecting the contact sheet; do not accept assets on metrics alone."
        )
    return json.loads(VISUAL_REVIEW_PATH.read_text(encoding="utf-8"))


def build_report(atlas: Image.Image, manifest: dict[str, Any], visual_review: dict[str, Any]) -> list[dict[str, Any]]:
    report: list[dict[str, Any]] = []
    cell_w = int(manifest["cell_width"])
    cell_h = int(manifest["cell_height"])

    for name, spec in manifest["animations"].items():
        row = int(spec["row"])
        frame_count = int(spec["frames"])
        frame_results = []

        for col in range(frame_count):
            frame = atlas.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
            frame_results.append(frame_metrics(frame, name))

        non_empty = [item for item in frame_results if item["min_margin_px"] is not None]
        margins = [int(item["min_margin_px"]) for item in non_empty]
        heights = [int(item["bbox_height"]) for item in non_empty]
        groundlines = [int(item["bbox_bottom"]) for item in non_empty]

        min_margin = min(margins) if margins else None
        edge_touch_count = sum(int(item["edge_touch_count"]) for item in frame_results)
        green_edge_pixels = sum(int(item["green_edge_pixels"]) for item in frame_results)
        pink_edge_pixels = sum(int(item["pink_edge_pixels"]) for item in frame_results)
        max_visible_clusters = max((int(item["visible_cluster_count"]) for item in frame_results), default=0)
        timing_ms = int(spec.get("frame_duration_ms", manifest.get("frame_duration_ms", 250)))
        height_variance_pct = round(((max(heights) - min(heights)) / mean(heights)) * 100, 1) if heights else 0.0
        groundline_variance_px = max(groundlines) - min(groundlines) if groundlines else 0
        heuristic_full_body = all(bool(item["full_body_visible"]) for item in frame_results)
        visual = visual_review.get(name, {})
        head_visible = bool(visual.get("head_visible", False))
        hands_visible = bool(visual.get("hands_visible", False))
        legs_visible = bool(visual.get("legs_visible", False))
        feet_visible = bool(visual.get("feet_visible", False))
        visual_full_body = bool(visual.get("full_body_visible", False))
        visual_notes = str(visual.get("notes", "missing visual review"))
        full_body_visible = heuristic_full_body and visual_full_body

        notes = build_notes(
            name=name,
            min_margin=min_margin,
            edge_touch_count=edge_touch_count,
            green_edge_pixels=green_edge_pixels,
            pink_edge_pixels=pink_edge_pixels,
            visible_cluster_count=max_visible_clusters,
            height_variance_pct=height_variance_pct,
            groundline_variance_px=groundline_variance_px,
            full_body_visible=full_body_visible,
            head_visible=head_visible,
            hands_visible=hands_visible,
            legs_visible=legs_visible,
            feet_visible=feet_visible,
            visual_notes=visual_notes,
        )

        accepted = (
            min_margin is not None
            and min_margin >= MIN_ACCEPTED_MARGIN
            and edge_touch_count == 0
            and green_edge_pixels == 0
            and pink_edge_pixels == 0
            and head_visible
            and hands_visible
            and legs_visible
            and feet_visible
            and full_body_visible
        )
        if name not in {"hatch", *INTENTIONAL_EFFECT_STATES} and max_visible_clusters > 1:
            accepted = False
        if name in UPRIGHT_STATES and name not in INTENTIONAL_EFFECT_STATES and groundline_variance_px > 10:
            accepted = False
        if name in NORMAL_STATES and height_variance_pct > 8:
            accepted = False

        report.append(
            {
                "animation": name,
                "frames": frame_count,
                "timing_ms": timing_ms,
                "min_margin_px": min_margin,
                "edge_touch_count": edge_touch_count,
                "green_edge_pixels": green_edge_pixels,
                "pink_edge_pixels": pink_edge_pixels,
                "height_variance_pct": height_variance_pct,
                "groundline_variance_px": groundline_variance_px,
                "visible_cluster_count": max_visible_clusters,
                "head_visible": head_visible,
                "hands_visible": hands_visible,
                "legs_visible": legs_visible,
                "feet_visible": feet_visible,
                "full_body_visible": full_body_visible,
                "accepted": accepted,
                "notes": notes,
                "frames_detail": frame_results,
            }
        )

    return report


def build_notes(
    name: str,
    min_margin: int | None,
    edge_touch_count: int,
    green_edge_pixels: int,
    pink_edge_pixels: int,
    visible_cluster_count: int,
    height_variance_pct: float,
    groundline_variance_px: int,
    full_body_visible: bool,
    head_visible: bool,
    hands_visible: bool,
    legs_visible: bool,
    feet_visible: bool,
    visual_notes: str,
) -> str:
    notes: list[str] = []
    if min_margin is None:
        notes.append("empty animation")
    elif min_margin < MIN_ACCEPTED_MARGIN:
        notes.append(f"margin below hard minimum {MIN_ACCEPTED_MARGIN}px")
    elif min_margin < TARGET_MARGIN:
        notes.append(f"margin accepted but below target {TARGET_MARGIN}px")
    else:
        notes.append("whole figure padded inside cell")

    if edge_touch_count:
        notes.append("visible pixels touch cell edge")
    if green_edge_pixels:
        notes.append("green edge pixels detected")
    if pink_edge_pixels:
        notes.append("pink edge pixels detected")
    if not full_body_visible:
        notes.append("full-body heuristic failed")
    if not head_visible:
        notes.append("visual review: head not visible")
    if not hands_visible:
        notes.append("visual review: hands not visible")
    if not legs_visible:
        notes.append("visual review: legs not visible")
    if not feet_visible:
        notes.append("visual review: feet not visible")
    if name not in {"hatch", *INTENTIONAL_EFFECT_STATES} and visible_cluster_count > 1:
        notes.append("unexpected detached visible clusters")
    if name in UPRIGHT_STATES and name not in INTENTIONAL_EFFECT_STATES and groundline_variance_px > 10:
        notes.append(f"groundline variance high at {groundline_variance_px}px")
    if name == "run" and height_variance_pct > 8 and groundline_variance_px <= 8:
        notes.append(
            f"height variance {height_variance_pct}% exceeds normal-state limit and must be corrected before acceptance"
        )
    elif name in NORMAL_STATES and height_variance_pct > 8:
        notes.append(f"height variance {height_variance_pct}% exceeds normal-state limit")
    if height_variance_pct > 55 and name not in {"jump", "failed", "hatch"}:
        notes.append(f"height variance high at {height_variance_pct}%")
    if name in ALIAS_STATES:
        notes.append("alias/runtime-compatible row")
    notes.append(f"visual: {visual_notes}")
    return "; ".join(notes)


def frame_metrics(frame: Image.Image, animation: str) -> dict[str, Any]:
    width, height = frame.size
    mask = frame.getchannel("A").point(lambda a: 255 if a > ALPHA_THRESHOLD else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return {
            "min_margin_px": None,
            "edge_touch_count": 0,
            "green_edge_pixels": 0,
            "pink_edge_pixels": 0,
            "visible_cluster_count": 0,
            "bbox_height": 0,
            "bbox_bottom": 0,
            "full_body_visible": False,
        }

    left, top, right, bottom = bbox
    min_margin = min(left, top, width - right, height - bottom)
    edge_touch = int(left <= 0 or top <= 0 or right >= width or bottom >= height)
    clusters = connected_components(frame)
    visible_clusters = [component for component in clusters if component["area"] >= 45]
    green = count_edge_pixels(frame, mode="green")
    pink = count_edge_pixels(frame, mode="pink")

    bbox_width = right - left
    bbox_height = bottom - top
    full_body_visible = is_full_body_visible(animation, bbox_width, bbox_height, min_margin)

    return {
        "min_margin_px": int(min_margin),
        "edge_touch_count": edge_touch,
        "green_edge_pixels": green,
        "pink_edge_pixels": pink,
        "visible_cluster_count": len(visible_clusters),
        "bbox_height": int(bbox_height),
        "bbox_bottom": int(bottom),
        "full_body_visible": bool(full_body_visible),
    }


def is_full_body_visible(animation: str, bbox_width: int, bbox_height: int, min_margin: int) -> bool:
    if min_margin < MIN_ACCEPTED_MARGIN:
        return False
    if animation == "hatch":
        return bbox_height >= 72 and bbox_width >= 42
    if animation == "failed":
        upright_body = bbox_height >= 78 and bbox_width >= 40
        fallen_body = bbox_height >= 36 and bbox_width >= 90
        return upright_body or fallen_body
    return bbox_height >= 76 and bbox_width >= 38


def connected_components(frame: Image.Image) -> list[dict[str, Any]]:
    alpha = frame.getchannel("A")
    pixels = alpha.load()
    width, height = frame.size
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []

    for y in range(height):
        for x in range(width):
            if (x, y) in seen or pixels[x, y] <= ALPHA_THRESHOLD:
                continue
            queue = deque([(x, y)])
            seen.add((x, y))
            area = 0
            left = top = 10**9
            right = bottom = -1
            while queue:
                cx, cy = queue.popleft()
                area += 1
                left = min(left, cx)
                top = min(top, cy)
                right = max(right, cx + 1)
                bottom = max(bottom, cy + 1)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if (
                        0 <= nx < width
                        and 0 <= ny < height
                        and (nx, ny) not in seen
                        and pixels[nx, ny] > ALPHA_THRESHOLD
                    ):
                        seen.add((nx, ny))
                        queue.append((nx, ny))
            components.append({"area": area, "bbox": [left, top, right, bottom]})

    return sorted(components, key=lambda item: item["area"], reverse=True)


def count_edge_pixels(frame: Image.Image, mode: str) -> int:
    width, height = frame.size
    pixels = frame.load()
    count = 0
    for y in range(height):
        for x in range(width):
            on_edge_band = x < 4 or y < 4 or x >= width - 4 or y >= height - 4
            if not on_edge_band:
                continue
            r, g, b, a = pixels[x, y]
            if not a:
                continue
            if mode == "green" and g > 90 and g > r * 1.25 and g > b * 1.15:
                count += 1
            if mode == "pink" and r > 150 and b > 130 and g < 90:
                count += 1
    return count


def write_contact_sheet(atlas: Image.Image, manifest: dict[str, Any], report: list[dict[str, Any]], output: Path) -> None:
    cell_w = int(manifest["cell_width"])
    cell_h = int(manifest["cell_height"])
    rows = int(manifest["rows"])
    cols = int(manifest["columns"])
    label_h = 26
    header_h = 44
    font = ImageFont.load_default()
    sheet = Image.new("RGB", (cols * cell_w, header_h + rows * (cell_h + label_h)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 6), "PET 1 Ruffy QA Contact Sheet", fill=(245, 245, 245), font=font)
    draw.text(
        (8, 23),
        "source: assets/sprites/ruffy_spritesheet.png | manifest: assets/ruffy_sprite_manifest.json",
        fill=(190, 190, 190),
        font=font,
    )
    report_by_row = {
        int(manifest["animations"][item["animation"]]["row"]): item
        for item in report
        if item["animation"] not in ALIAS_STATES
    }

    for row in range(rows):
        row_report = report_by_row.get(row)
        label = row_report["animation"] if row_report else f"row_{row}"
        accepted = bool(row_report["accepted"]) if row_report else False
        outline = (38, 150, 82) if accepted else (210, 60, 60)
        for col in range(cols):
            x = col * cell_w
            y = header_h + row * (cell_h + label_h) + label_h
            frame = atlas.crop((x, row * cell_h, x + cell_w, (row + 1) * cell_h))
            backing = Image.new("RGBA", frame.size, (24, 24, 24, 255))
            backing.alpha_composite(frame)
            sheet.paste(backing.convert("RGB"), (x, y))
            draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline=outline)
            draw.text((x + 4, y - label_h + 7), f"{label} {col + 1}", fill=(235, 235, 235), font=font)

    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def write_row_images(atlas: Image.Image, manifest: dict[str, Any]) -> None:
    cell_w = int(manifest["cell_width"])
    cell_h = int(manifest["cell_height"])
    for name, spec in manifest["animations"].items():
        if name in ALIAS_STATES:
            continue
        row = int(spec["row"])
        frames = int(spec["frames"])
        row_img = atlas.crop((0, row * cell_h, frames * cell_w, (row + 1) * cell_h))
        backing = Image.new("RGBA", row_img.size, (24, 24, 24, 255))
        backing.alpha_composite(row_img)
        backing.convert("RGB").save(QA_ROWS_DIR / f"{name}.png")


def write_gifs(atlas: Image.Image, manifest: dict[str, Any]) -> None:
    cell_w = int(manifest["cell_width"])
    cell_h = int(manifest["cell_height"])
    default_duration = int(manifest.get("frame_duration_ms", 250))
    for name, spec in manifest["animations"].items():
        row = int(spec["row"])
        frame_count = int(spec["frames"])
        duration = int(spec.get("frame_duration_ms", default_duration))
        frames = []
        for col in range(frame_count):
            frame = atlas.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
            backing = Image.new("RGBA", frame.size, (24, 24, 24, 255))
            backing.alpha_composite(frame)
            preview = backing.resize((cell_w * 2, cell_h * 2), Image.Resampling.LANCZOS)
            frames.append(preview.convert("P", palette=Image.Palette.ADAPTIVE))
        loop = 0 if bool(spec.get("loop", True)) else 1
        frames[0].save(
            PREVIEW_DIR / f"{name}.gif",
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=loop,
            disposal=2,
        )


def write_full_review_gif(atlas: Image.Image, manifest: dict[str, Any], output: Path) -> None:
    cell_w = int(manifest["cell_width"])
    cell_h = int(manifest["cell_height"])
    default_duration = int(manifest.get("frame_duration_ms", 250))
    review_frames = []
    durations = []
    font = ImageFont.load_default()
    canvas_size = (cell_w * 2, cell_h * 2)

    for name in ACTIVE_REVIEW_ANIMATIONS:
        spec = manifest["animations"][name]
        duration = int(spec.get("frame_duration_ms", default_duration))
        title = Image.new("RGB", canvas_size, (18, 18, 18))
        draw = ImageDraw.Draw(title)
        draw.text((18, 18), f"PET 1 / Ruffy: {name}", fill=(245, 245, 245), font=font)
        draw.text((18, 38), f"{spec['frames']} frames @ {duration}ms", fill=(190, 190, 190), font=font)
        review_frames.append(title.convert("P", palette=Image.Palette.ADAPTIVE))
        durations.append(900)

        frames = []
        row = int(spec["row"])
        for col in range(int(spec["frames"])):
            frame = atlas.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
            backing = Image.new("RGBA", frame.size, (24, 24, 24, 255))
            backing.alpha_composite(frame)
            preview = backing.resize(canvas_size, Image.Resampling.LANCZOS)
            frames.append(preview.convert("P", palette=Image.Palette.ADAPTIVE))

        min_loops = max(1, (3000 + duration * len(frames) - 1) // (duration * len(frames)))
        for _ in range(min_loops):
            for frame in frames:
                review_frames.append(frame)
                durations.append(duration)

    output.parent.mkdir(parents=True, exist_ok=True)
    review_frames[0].save(
        output,
        save_all=True,
        append_images=review_frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
    )


if __name__ == "__main__":
    main()
