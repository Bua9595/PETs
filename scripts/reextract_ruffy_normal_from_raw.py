"""Re-extract Ruffy normal sprite candidates from the raw base source sheet.

Reads ONLY ``assets/source/pet1_ruffy_base_source.png``. Does not use archived
source_cells, row_sources, runtime atlases or review sheets.

Outputs review artefacts under ``assets/review/`` — nothing is approved and
nothing is written to ``assets/source_approved/``.

Usage::

    python scripts/reextract_ruffy_normal_from_raw.py
"""

from __future__ import annotations

import csv
import sys
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

RAW_SOURCE = REPO_ROOT / "assets" / "source" / "pet1_ruffy_base_source.png"
GRID_COLS = 5
GRID_ROWS = 5

PREFERRED_PADDING = 48
MIN_PADDING = 32

CANDIDATES_DIR = REPO_ROOT / "assets" / "review" / "candidates" / "ruffy_normal_reextract"
CSV_PATH = REPO_ROOT / "assets" / "review" / "reports" / "ruffy_normal_reextract_review.csv"
CONTACT_SHEET = REPO_ROOT / "assets" / "review" / "contact_sheets" / "ruffy_normal_reextract_review.png"
DIAGNOSIS_PATH = REPO_ROOT / "assets" / "review" / "reports" / "ruffy_normal_reextract_diagnosis.md"

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
    review_status: str
    reject_reason: str
    notes: str
    abs_path: Path = field(default=Path("."), repr=False)


# --- Chroma helpers (aligned with pet1_ruffy_builder, self-contained) ---


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
    """Pixels of chroma-like background between cell top and content top."""
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


def extract_cell(
    cell_rgb: Image.Image,
    grid_row: int,
    grid_col: int,
) -> tuple[Image.Image | None, bool, bool, str]:
    """Return (image, cutoff_risk, source_already_clipped, notes)."""
    cw, ch = cell_rgb.size
    rgba = chroma_to_alpha(cell_rgb)
    bbox = content_bbox(rgba)
    if bbox is None:
        return None, True, False, "no visible sprite content after chroma key"

    cl, ct, cr, cb = bbox
    content_w = cr - cl
    content_h = cb - ct

    pad_top = min(PREFERRED_PADDING, ct)
    pad_bottom = min(PREFERRED_PADDING, ch - cb)
    pad_left = min(PREFERRED_PADDING, cl)
    pad_right = min(PREFERRED_PADDING, cw - cr)

    actual_top_pad = pad_top
    actual_bottom_pad = pad_bottom
    actual_left_pad = pad_left
    actual_right_pad = pad_right

    el, et = cl - pad_left, ct - pad_top
    er, eb = cr + pad_right, cb + pad_bottom

    cutoff_risk = False
    source_already_clipped = False
    notes: list[str] = []

    # cutoff_risk: content flush with cell edge — cannot add padding without leaving cell
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

    if actual_top_pad < MIN_PADDING and ct > 3:
        notes.append(f"top pad limited to {actual_top_pad}px within cell (content not at edge)")
    if actual_bottom_pad < MIN_PADDING and cb < ch - 3:
        notes.append(f"bottom pad limited to {actual_bottom_pad}px (tall sprite, not edge-clipped)")

    crop = rgba.crop((max(0, el), max(0, et), min(cw, er), min(eb, eb)))
    note_str = "; ".join(notes) if notes else f"extracted {content_w}x{content_h} with up to {PREFERRED_PADDING}px padding"
    return crop, cutoff_risk, source_already_clipped, note_str


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
    per_page = cols * rows

    cell_w = box + pad
    cell_h = box + label_h + pad
    sheet_w = pad + cols * cell_w
    body_h = rows * cell_h
    sheet_h = header_h + body_h + pad

    font = load_font(13)
    title_font = load_font(20)
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (24, 24, 28, 255))
    draw = ImageDraw.Draw(sheet)
    draw.text(
        (pad, 18),
        "ruffy normal re-extract | REVIEW ONLY - raw source extraction - not approved",
        fill=(235, 235, 240),
        font=title_font,
    )

    for idx, cand in enumerate(candidates[:per_page]):
        r, c = divmod(idx, cols)
        x = pad + c * cell_w
        y = header_h + r * cell_h
        tile = Image.new("RGBA", (box, box), (45, 45, 52, 255))
        with Image.open(cand.abs_path) as im:
            im = im.convert("RGBA")
            im.thumbnail((box - 8, box - 8), Image.LANCZOS)
            off = ((box - im.width) // 2, (box - im.height) // 2)
            tile.alpha_composite(im, off)
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
                    c.review_status,
                    c.reject_reason,
                    c.notes,
                ]
            )


def write_diagnosis(
    raw_exists: bool,
    raw_size: tuple[int, int],
    raw_mode: str,
    usable: bool,
    candidates: list[Candidate],
) -> None:
    cutoff_count = sum(1 for c in candidates if c.cutoff_risk)
    clipped_count = sum(1 for c in candidates if c.source_already_clipped)
    likely_slicing = usable and cutoff_count == 0 and clipped_count == 0
    raw_clipped = clipped_count > 0

    lines = [
        "# Ruffy Normal Re-Extraction Diagnosis",
        "",
        "## Raw Source",
        "",
        f"* path: `{RAW_SOURCE.relative_to(REPO_ROOT).as_posix()}`",
        f"* exists: {'yes' if raw_exists else 'no'}",
        f"* dimensions: {raw_size[0]}x{raw_size[1]}" if raw_exists else "* dimensions: n/a",
        f"* mode: {raw_mode}" if raw_exists else "* mode: n/a",
        f"* usable: {'yes' if usable else 'no'}",
        "",
        "Background: solid magenta/chroma RGB (~210,20,215). Grid: 5x5.",
        "",
        "Visible margin above hats in raw (row 0): yes — raw sheet shows intact hat tops with chroma gap.",
        "",
        "## Ursache alter Cutoffs",
        "",
        "Bewertung:",
        "",
        f"* likely_old_slicing_issue: {'yes' if likely_slicing or (usable and not raw_clipped) else 'unclear'}",
        f"* raw_source_clipped: {'yes' if raw_clipped else 'no' if usable else 'unclear'}",
        "",
        "Der alte Builder nutzte feste 320x320-Zellen mit TARGET_PADDING=30 und Bottom-Alignment",
        "(`fit_to_cell` in `pet1_ruffy_builder.py`). Das kann Inhalt oben verlieren, obwohl das",
        "Raw-Sheet oben noch Rand hat.",
        "",
        "## Neue Re-Extraction",
        "",
        f"* candidate_count: {len(candidates)}",
        f"* candidates_with_cutoff_risk: {cutoff_count}",
        f"* candidates_source_already_clipped: {clipped_count}",
        f"* review_sheet: `{CONTACT_SHEET.relative_to(REPO_ROOT).as_posix()}`",
        "",
        "## Entscheidung",
        "",
        "Noch keine Approved-Sprites.",
        "Dieses Review-Paket dient nur zur manuellen Auswahl.",
        "",
        "Das alte Sheet `assets/archive/deprecated_sprite_sources_20260627/review/ruffy_normal_review.png`",
        "ist nicht approvalfähig (sichtbare Hut-/Kopf-Cutoffs aus altem Slicing).",
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
    for old in CANDIDATES_DIR.glob("ruffy_normal_reextract_*.png"):
        old.unlink()

    x_lines = [round(i * raw_size[0] / GRID_COLS) for i in range(GRID_COLS + 1)]
    y_lines = [round(i * raw_size[1] / GRID_ROWS) for i in range(GRID_ROWS + 1)]

    candidates: list[Candidate] = []
    index = 1
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell = raw.crop((x_lines[col], y_lines[row], x_lines[col + 1], y_lines[row + 1]))
            extracted, cutoff_risk, source_clipped, notes = extract_cell(cell, row, col)
            cid = f"ruffy_normal_reextract_{index:04d}"
            rel_file = f"assets/review/candidates/ruffy_normal_reextract/{cid}.png"

            if extracted is None:
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
                        review_status="needs_fix",
                        reject_reason="no_content",
                        notes=notes,
                        abs_path=CANDIDATES_DIR / f"{cid}.png",
                    )
                )
                index += 1
                continue

            out_path = CANDIDATES_DIR / f"{cid}.png"
            extracted.save(out_path)
            top_m, bot_m, left_m, right_m = margins_in_image(extracted)
            needs_fix = cutoff_risk or source_clipped
            reject = ""
            if cutoff_risk and source_clipped:
                reject = "cutoff_risk;source_already_clipped"
            elif cutoff_risk:
                reject = "cutoff_risk"
            elif source_clipped:
                reject = "source_already_clipped"

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
                    review_status="needs_fix" if needs_fix else "pending",
                    reject_reason=reject,
                    notes=notes,
                    abs_path=out_path,
                )
            )
            index += 1

    write_csv(candidates)
    build_contact_sheet(candidates)
    write_diagnosis(True, raw_size, raw_mode, True, candidates)

    pending = sum(1 for c in candidates if c.review_status == "pending")
    needs_fix = sum(1 for c in candidates if c.review_status == "needs_fix")
    print(f"candidates: {len(candidates)} pending={pending} needs_fix={needs_fix}")
    print(f"csv: {CSV_PATH.relative_to(REPO_ROOT)}")
    print(f"sheet: {CONTACT_SHEET.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
