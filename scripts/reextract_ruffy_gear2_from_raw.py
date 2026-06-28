"""Re-extract Ruffy Gear2 sprite candidates from the raw gear2 source sheet.

Reads ONLY ``assets/source/pet1_ruffy_gear2_source.png``. Does not use archived
source_cells, row_sources, runtime atlases, review sheets, or normal approved sprites.

Outputs review artefacts under ``assets/review/`` — nothing is approved.

Usage::

    python scripts/reextract_ruffy_gear2_from_raw.py
"""

from __future__ import annotations

import csv
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_SOURCE = REPO_ROOT / "assets" / "source" / "pet1_ruffy_gear2_source.png"
GRID_COLS = 5
GRID_ROWS = 5

PREFERRED_PADDING = 48
MIN_PADDING = 32

CANDIDATES_DIR = REPO_ROOT / "assets" / "review" / "candidates" / "ruffy_gear2_reextract"
CSV_PATH = REPO_ROOT / "assets" / "review" / "reports" / "ruffy_gear2_reextract_review.csv"
CONTACT_SHEET = REPO_ROOT / "assets" / "review" / "contact_sheets" / "ruffy_gear2_reextract_review.png"
DIAGNOSIS_PATH = REPO_ROOT / "assets" / "review" / "reports" / "ruffy_gear2_reextract_diagnosis.md"

CSV_COLUMNS = [
    "candidate_id",
    "file_path",
    "raw_source_path",
    "width",
    "height",
    "top_margin",
    "bottom_margin",
    "left_margin",
    "right_margin",
    "cutoff_risk",
    "source_already_clipped",
    "looks_like_gear2",
    "wrong_form_reason",
    "review_status",
    "reject_reason",
    "notes",
]


@dataclass
class Candidate:
    candidate_id: str
    file_path: str
    raw_source_path: str
    width: int
    height: int
    top_margin: int
    bottom_margin: int
    left_margin: int
    right_margin: int
    cutoff_risk: bool
    source_already_clipped: bool
    looks_like_gear2: str
    wrong_form_reason: str
    review_status: str
    reject_reason: str
    notes: str
    abs_path: Path = field(default=Path("."), repr=False)


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


def chroma_to_alpha(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    visited = [[False] * width for _ in range(height)]
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
            if is_bright_chroma_fringe(pixels[x, y]):
                pixels[x, y] = (0, 0, 0, 0)
    return rgba


def content_bbox(rgba: Image.Image, alpha_threshold: int = 12) -> tuple[int, int, int, int] | None:
    alpha = rgba.split()[3]
    return alpha.point(lambda v: 255 if v > alpha_threshold else 0).getbbox()


def chroma_gap_above_content(cell_rgb: Image.Image, content_top: int) -> int:
    if content_top <= 0:
        return 0
    px = cell_rgb.load()
    gap = 0
    width = cell_rgb.width
    for y in range(content_top):
        row_chroma = sum(1 for x in range(width) if is_chroma_like((*px[x, y], 255)))
        if row_chroma >= width * 0.85:
            gap += 1
        else:
            break
    return gap


def margins_in_image(rgba: Image.Image) -> tuple[int, int, int, int]:
    bbox = content_bbox(rgba)
    if bbox is None:
        return 0, 0, 0, 0
    left, top, right, bottom = bbox
    w, h = rgba.size
    return top, h - bottom, left, w - right


def assess_gear2_form(rgba: Image.Image) -> tuple[str, str, list[str]]:
    """Heuristic Gear2 vs wrong-form check. Conservative — prefer unclear over false reject."""
    bbox = content_bbox(rgba)
    if bbox is None:
        return "false", "no_visible_content", ["empty after chroma key"]

    left, top, right, bottom = bbox
    w, h = rgba.size
    pixels = rgba.load()
    notes: list[str] = []
    opaque = [(x, y) for y in range(h) for x in range(w) if pixels[x, y][3] > 12]
    if not opaque:
        return "false", "no_visible_content", ["no opaque pixels"]

    # Gear5 signal: bright white clusters in upper head band (not steam pink)
    head_y_max = top + int((bottom - top) * 0.35)
    white_head = 0
    head_opaque = 0
    for x, y in opaque:
        if y <= head_y_max:
            head_opaque += 1
            r, g, b, _ = pixels[x, y]
            # Neutral white only — exclude pink/steam vapor (high R+B, lower G).
            if r > 235 and g > 235 and b > 235 and abs(r - g) < 22 and abs(r - b) < 22:
                white_head += 1
    if head_opaque > 40 and white_head / head_opaque > 0.12:
        notes.append(f"high white ratio in head band ({white_head}/{head_opaque})")
        return "false", "gear5_white_hair_or_clothing", notes

    # Gear4 signal: large dark red/black arm regions
    dark_haki = 0
    for x, y in opaque:
        r, g, b, _ = pixels[x, y]
        if r < 55 and g < 45 and b < 45:
            dark_haki += 1
        elif r > 90 and g < 55 and b < 55 and r - g > 35:
            dark_haki += 1
    if dark_haki / len(opaque) > 0.28:
        notes.append(f"dark haki-like pixels {dark_haki}/{len(opaque)}")
        return "false", "gear4_haki_arms", notes

    # Gear3 signal: extremely wide content vs height (giant limb dominates)
    content_w = right - left
    content_h = bottom - top
    if content_w > content_h * 1.55 and content_w > w * 0.72:
        notes.append(f"very wide content bbox {content_w}x{content_h}")
        return "false", "gear3_oversized_limb", notes

    # Positive Gear2 steam signal (soft pink/white vapor)
    steam_like = 0
    for x, y in opaque:
        r, g, b, _ = pixels[x, y]
        if r > 200 and b > 200 and 120 <= g <= 220:
            steam_like += 1
    if steam_like > 80:
        notes.append(f"steam-like pixels detected ({steam_like})")

    # Default: likely gear2 sheet cell
    if steam_like > 40:
        return "true", "", notes
    return "unclear", "", notes + ["limited steam signal; manual review recommended"]


def extract_cell(cell_rgb: Image.Image, grid_row: int) -> tuple[Image.Image | None, bool, bool, str]:
    cw, ch = cell_rgb.size
    rgba = chroma_to_alpha(cell_rgb)
    bbox = content_bbox(rgba)
    if bbox is None:
        return None, True, False, "no visible sprite content after chroma key"

    cl, ct, cr, cb = bbox
    pad_top = min(PREFERRED_PADDING, ct)
    pad_bottom = min(PREFERRED_PADDING, ch - cb)
    pad_left = min(PREFERRED_PADDING, cl)
    pad_right = min(PREFERRED_PADDING, cw - cr)
    el, et = cl - pad_left, ct - pad_top
    er, eb = cr + pad_right, cb + pad_bottom

    cutoff_risk = False
    source_already_clipped = False
    notes: list[str] = []

    if ct <= 3:
        cutoff_risk = True
        notes.append(f"content at cell top (ct={ct})")
    if cl <= 3:
        cutoff_risk = True
        notes.append(f"content at cell left (cl={cl})")
    if cr >= cw - 3:
        cutoff_risk = True
        notes.append(f"content at cell right (cr={cr})")
    if cb >= ch - 3:
        notes.append(f"content at cell bottom (cb={cb})")

    chroma_gap = chroma_gap_above_content(cell_rgb, ct)
    if ct <= 3 and chroma_gap < 8:
        source_already_clipped = True
        notes.append(f"no chroma gap above content (gap={chroma_gap}px)")
    elif grid_row == 0 and chroma_gap >= 8:
        notes.append(f"raw row0 chroma gap above content={chroma_gap}px (raw intact)")

    crop = rgba.crop((max(0, el), max(0, et), min(cw, er), min(eb, eb)))
    note_str = "; ".join(notes) if notes else f"extracted with up to {PREFERRED_PADDING}px padding"
    return crop, cutoff_risk, source_already_clipped, note_str


def decide_status(
    cutoff_risk: bool,
    source_clipped: bool,
    looks_like: str,
    wrong_reason: str,
) -> tuple[str, str]:
    if looks_like == "false" and wrong_reason in {
        "gear4_haki_arms",
        "gear3_oversized_limb",
        "no_visible_content",
    }:
        return "rejected", wrong_reason
    if looks_like == "false" and wrong_reason == "gear5_white_hair_or_clothing":
        # Steam vapor can mimic white pixels — flag for manual review, do not auto-reject.
        return "needs_fix", wrong_reason
    if cutoff_risk and source_clipped:
        return "needs_fix", "cutoff_risk;source_already_clipped"
    if cutoff_risk:
        return "needs_fix", "cutoff_risk"
    if source_clipped:
        return "needs_fix", "source_already_clipped"
    if looks_like == "unclear":
        return "needs_fix", "gear2_form_unclear"
    return "pending", ""


def load_font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_contact_sheet(candidates: list[Candidate]) -> None:
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    cols, rows = 5, 5
    box = 220
    label_h = 28
    pad = 16
    header_h = 64
    cell_w = box + pad
    cell_h = box + label_h + pad
    sheet_w = pad + cols * cell_w
    sheet_h = header_h + rows * cell_h + pad
    font = load_font(12)
    title_font = load_font(18)
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (24, 24, 28, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (pad, 18),
        "ruffy gear2 re-extract | REVIEW ONLY - raw source extraction - not approved",
        fill=(235, 235, 240),
        font=title_font,
    )
    for idx, cand in enumerate(candidates[: cols * rows]):
        r, c = divmod(idx, cols)
        x = pad + c * cell_w
        y = header_h + r * cell_h
        tile = Image.new("RGBA", (box, box), (45, 45, 52, 255))
        with Image.open(cand.abs_path) as im:
            im = im.convert("RGBA")
            im.thumbnail((box - 8, box - 8), Image.LANCZOS)
            tile.alpha_composite(im, ((box - im.width) // 2, (box - im.height) // 2))
        sheet.alpha_composite(tile, (x, y))
        label = cand.candidate_id
        tw = draw.textlength(label, font=font)
        draw.text((x + (box - tw) / 2, y + box + 4), label, fill=(210, 210, 220), font=font)
    sheet.convert("RGB").save(CONTACT_SHEET)


def write_csv(candidates: list[Candidate]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        for c in candidates:
            writer.writerow(
                [
                    c.candidate_id,
                    c.file_path,
                    c.raw_source_path,
                    c.width,
                    c.height,
                    c.top_margin,
                    c.bottom_margin,
                    c.left_margin,
                    c.right_margin,
                    str(c.cutoff_risk).lower(),
                    str(c.source_already_clipped).lower(),
                    c.looks_like_gear2,
                    c.wrong_form_reason,
                    c.review_status,
                    c.reject_reason,
                    c.notes,
                ]
            )


def write_diagnosis(raw_size: tuple[int, int], raw_mode: str, candidates: list[Candidate]) -> None:
    pending = sum(1 for c in candidates if c.review_status == "pending")
    needs_fix = sum(1 for c in candidates if c.review_status == "needs_fix")
    rejected = sum(1 for c in candidates if c.review_status == "rejected")
    cutoff = sum(1 for c in candidates if c.cutoff_risk)
    clipped = sum(1 for c in candidates if c.source_already_clipped)
    wrong = sum(1 for c in candidates if c.looks_like_gear2 == "false")

    lines = [
        "# Ruffy Gear2 Re-Extraction Diagnosis",
        "",
        "## Raw Source",
        "",
        f"* path: `{RAW_SOURCE.relative_to(REPO_ROOT).as_posix()}`",
        "* exists: yes",
        f"* dimensions: {raw_size[0]}x{raw_size[1]}",
        f"* mode: {raw_mode}",
        "* usable: yes",
        "",
        "Background: solid magenta/chroma RGB. Grid: 5x5 (25 cells).",
        "",
        "## Gear2-Erwartung",
        "",
        "* normale Körperform",
        "* Steam/Dampf",
        "* schneller/angespannter Ausdruck",
        "* keine Gear3/Gear4/Gear5-Elemente",
        "",
        "## Neue Re-Extraction",
        "",
        f"* candidate_count: {len(candidates)}",
        f"* candidates_pending: {pending}",
        f"* candidates_needs_fix: {needs_fix}",
        f"* candidates_rejected: {rejected}",
        f"* candidates_with_cutoff_risk: {cutoff}",
        f"* candidates_source_already_clipped: {clipped}",
        f"* candidates_wrong_form: {wrong}",
        f"* review_sheet: `{CONTACT_SHEET.relative_to(REPO_ROOT).as_posix()}`",
        "",
        "## Entscheidung",
        "",
        "Noch keine Approved-Sprites.",
        "Dieses Review-Paket dient nur zur manuellen Auswahl.",
        "",
    ]
    DIAGNOSIS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DIAGNOSIS_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if not RAW_SOURCE.is_file():
        print(f"STOP: raw source missing: {RAW_SOURCE}")
        return 1

    raw = Image.open(RAW_SOURCE)
    raw_mode = raw.mode
    raw_size = raw.size
    print(f"raw: {RAW_SOURCE.relative_to(REPO_ROOT)} mode={raw_mode} size={raw_size}")

    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    for old in CANDIDATES_DIR.glob("ruffy_gear2_reextract_*.png"):
        old.unlink()

    x_lines = [round(i * raw_size[0] / GRID_COLS) for i in range(GRID_COLS + 1)]
    y_lines = [round(i * raw_size[1] / GRID_ROWS) for i in range(GRID_ROWS + 1)]

    candidates: list[Candidate] = []
    index = 1
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell = raw.crop((x_lines[col], y_lines[row], x_lines[col + 1], y_lines[row + 1]))
            extracted, cutoff_risk, source_clipped, extract_notes = extract_cell(cell, row)
            cid = f"ruffy_gear2_reextract_{index:04d}"
            rel_file = f"assets/review/candidates/ruffy_gear2_reextract/{cid}.png"
            out_path = CANDIDATES_DIR / f"{cid}.png"

            if extracted is None:
                status, reject = "rejected", "no_content"
                candidates.append(
                    Candidate(
                        candidate_id=cid,
                        file_path=rel_file,
                        raw_source_path=RAW_SOURCE.relative_to(REPO_ROOT).as_posix(),
                        width=0,
                        height=0,
                        top_margin=0,
                        bottom_margin=0,
                        left_margin=0,
                        right_margin=0,
                        cutoff_risk=True,
                        source_already_clipped=False,
                        looks_like_gear2="false",
                        wrong_form_reason="no_visible_content",
                        review_status=status,
                        reject_reason=reject,
                        notes=extract_notes,
                        abs_path=out_path,
                    )
                )
                index += 1
                continue

            extracted.save(out_path)
            top_m, bot_m, left_m, right_m = margins_in_image(extracted)
            looks, wrong, form_notes = assess_gear2_form(extracted)
            all_notes = "; ".join(filter(None, [extract_notes, *form_notes]))
            status, reject = decide_status(cutoff_risk, source_clipped, looks, wrong)

            candidates.append(
                Candidate(
                    candidate_id=cid,
                    file_path=rel_file,
                    raw_source_path=RAW_SOURCE.relative_to(REPO_ROOT).as_posix(),
                    width=extracted.width,
                    height=extracted.height,
                    top_margin=top_m,
                    bottom_margin=bot_m,
                    left_margin=left_m,
                    right_margin=right_m,
                    cutoff_risk=cutoff_risk,
                    source_already_clipped=source_clipped,
                    looks_like_gear2=looks,
                    wrong_form_reason=wrong,
                    review_status=status,
                    reject_reason=reject,
                    notes=all_notes,
                    abs_path=out_path,
                )
            )
            index += 1

    write_csv(candidates)
    build_contact_sheet(candidates)
    write_diagnosis(raw_size, raw_mode, candidates)

    pending = sum(1 for c in candidates if c.review_status == "pending")
    needs_fix = sum(1 for c in candidates if c.review_status == "needs_fix")
    rejected = sum(1 for c in candidates if c.review_status == "rejected")
    print(f"candidates: {len(candidates)} pending={pending} needs_fix={needs_fix} rejected={rejected}")
    print(f"csv: {CSV_PATH.relative_to(REPO_ROOT)}")
    print(f"sheet: {CONTACT_SHEET.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
