"""Build a sprite-candidate review index and contact sheets.

This script is part of the PET review/approval pipeline. It scans the real
candidate sources, writes ``assets/review/reports/candidates.csv`` and renders
dark-background review contact sheets with candidate IDs.

It is intentionally read-only with respect to the runtime:

* It does NOT modify any runtime atlas, manifest or sprite.
* It does NOT copy anything into ``assets/source_approved/``.
* It does NOT delete or move any file.

Only review artefacts under ``assets/review/`` are (re)written.

Usage::

    python scripts/build_candidate_review.py
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

# (relative source dir, pet, source_type). Only real, non-runtime candidate
# sources are listed here. Runtime atlases, GIFs, QA sheets and previews are
# deliberately excluded so they can never become a sprite source.
SOURCES: list[tuple[str, str, str]] = [
    ("assets/source_raw/ruffy", "ruffy", "raw_sheet"),
    ("assets/source_raw/pet2_chibi", "pet2_chibi", "raw_sheet"),
    ("assets/pets/ruffy/source_cells", "ruffy", "source_cell"),
    ("assets/pets/ruffy/row_sources", "ruffy", "row_source"),
    ("assets/pets/pet2_chibi/source_cells", "pet2_chibi", "source_cell"),
    ("assets/pets/pet2_chibi/row_sources", "pet2_chibi", "row_source"),
]

REVIEW_DIR = REPO_ROOT / "assets" / "review"
CONTACT_DIR = REVIEW_DIR / "contact_sheets"
REPORT_DIR = REVIEW_DIR / "reports"
CSV_PATH = REPORT_DIR / "candidates.csv"

PET_SHORT = {"ruffy": "ruffy", "pet2_chibi": "pet2", "unknown": "unknown"}
FORM_SHORT = {
    "normal": "normal",
    "gear2": "gear2",
    "gear3": "gear3",
    "gear4": "gear4",
    "gear5": "gear5",
    "core": "core",
    "gaming": "gaming",
    "social": "social",
    "desktop_interaction": "desktop",
    "unknown": "unknown",
}

CSV_COLUMNS = [
    "candidate_id",
    "pet",
    "form",
    "state_guess",
    "source_path",
    "source_type",
    "width",
    "height",
    "review_status",
    "reject_reason",
    "notes",
]


@dataclass
class Candidate:
    pet: str
    form: str
    state_guess: str
    source_path: str
    source_type: str
    width: int
    height: int
    candidate_id: str = ""
    review_status: str = "pending"
    reject_reason: str = ""
    notes: str = ""
    abs_path: Path = field(default=Path("."), repr=False)


def guess_ruffy_form(name: str) -> str:
    lower = name.lower()
    for gear in ("gear2", "gear3", "gear4", "gear5"):
        if gear in lower:
            return gear
    if "base" in lower:
        return "normal"
    return "unknown"


def guess_ruffy_state(name: str, source_type: str) -> str:
    """Derive a state only from explicit row_source filenames."""
    if source_type != "row_source":
        return "unknown"
    stem = Path(name).stem
    tokens = stem.split("_")
    state_tokens: list[str] = []
    for tok in tokens:
        if tok.isdigit() or tok.lower() in {"base", "gear2", "gear3", "gear4", "gear5"}:
            break
        state_tokens.append(tok)
    state = "_".join(state_tokens)
    return state if state else "unknown"


def classify(pet: str, source_type: str, name: str) -> tuple[str, str]:
    """Return (form, state_guess) derived only from name/folder."""
    if pet == "ruffy":
        return guess_ruffy_form(name), guess_ruffy_state(name, source_type)
    # pet2_chibi sources do not encode a single form/state in the filename.
    return "unknown", "unknown"


def collect_candidates() -> list[Candidate]:
    candidates: list[Candidate] = []
    for rel_dir, pet, source_type in SOURCES:
        directory = REPO_ROOT / rel_dir
        if not directory.is_dir():
            continue
        files = sorted(
            p
            for p in directory.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTS and p.name != ".gitkeep"
        )
        for path in files:
            form, state_guess = classify(pet, source_type, path.name)
            try:
                with Image.open(path) as im:
                    width, height = im.size
            except Exception:  # noqa: BLE001 - record unreadable images too
                width, height = 0, 0
            rel = path.relative_to(REPO_ROOT).as_posix()
            candidates.append(
                Candidate(
                    pet=pet,
                    form=form,
                    state_guess=state_guess,
                    source_path=rel,
                    source_type=source_type,
                    width=width,
                    height=height,
                    abs_path=path,
                )
            )
    return candidates


def assign_ids(candidates: list[Candidate]) -> None:
    counters: dict[tuple[str, str], int] = {}
    for cand in candidates:
        pet_short = PET_SHORT.get(cand.pet, "unknown")
        form_short = FORM_SHORT.get(cand.form, "unknown")
        key = (pet_short, form_short)
        counters[key] = counters.get(key, 0) + 1
        cand.candidate_id = f"{pet_short}_{form_short}_{counters[key]:04d}"


def write_csv(candidates: list[Candidate]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        for cand in candidates:
            writer.writerow(
                [
                    cand.candidate_id,
                    cand.pet,
                    cand.form,
                    cand.state_guess,
                    cand.source_path,
                    cand.source_type,
                    cand.width,
                    cand.height,
                    cand.review_status,
                    cand.reject_reason,
                    cand.notes,
                ]
            )


def _load_font(size: int) -> ImageFont.ImageFont:
    for candidate in ("arial.ttf", "DejaVuSans.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _make_thumb(path: Path, box: int) -> Image.Image:
    tile = Image.new("RGBA", (box, box), (45, 45, 52, 255))
    try:
        with Image.open(path) as im:
            im = im.convert("RGBA")
            im.thumbnail((box - 12, box - 12), Image.LANCZOS)
            off = ((box - im.width) // 2, (box - im.height) // 2)
            tile.alpha_composite(im, off)
    except Exception:  # noqa: BLE001
        draw = ImageDraw.Draw(tile)
        draw.text((10, box // 2), "unreadable", fill=(220, 80, 80))
    return tile


def build_contact_sheets(
    candidates: list[Candidate], pet: str, base_name: str
) -> list[str]:
    subset = [c for c in candidates if c.pet == pet]
    if not subset:
        return []

    CONTACT_DIR.mkdir(parents=True, exist_ok=True)

    cols, rows = 5, 6
    box = 200
    label_h = 26
    pad = 14
    header_h = 60
    per_page = cols * rows

    cell_w = box + pad
    cell_h = box + label_h + pad
    sheet_w = pad + cols * cell_w
    body_h = rows * cell_h

    font = _load_font(14)
    title_font = _load_font(22)

    pages = [subset[i : i + per_page] for i in range(0, len(subset), per_page)]
    multi = len(pages) > 1
    written: list[str] = []

    for page_idx, page in enumerate(pages, start=1):
        sheet_h = header_h + body_h + pad
        sheet = Image.new("RGBA", (sheet_w, sheet_h), (24, 24, 28, 255))
        draw = ImageDraw.Draw(sheet)
        title = f"{pet} candidates"
        if multi:
            title += f" - page {page_idx:03d}/{len(pages):03d}"
        title += "  (REVIEW ONLY - not a sprite source)"
        draw.text((pad, 20), title, fill=(235, 235, 240), font=title_font)

        for idx, cand in enumerate(page):
            r, c = divmod(idx, cols)
            x = pad + c * cell_w
            y = header_h + r * cell_h
            sheet.alpha_composite(_make_thumb(cand.abs_path, box), (x, y))
            label = cand.candidate_id
            tw = draw.textlength(label, font=font)
            draw.text(
                (x + (box - tw) / 2, y + box + 4),
                label,
                fill=(210, 210, 220),
                font=font,
            )

        if multi:
            out = CONTACT_DIR / f"{base_name}_{page_idx:03d}.png"
        else:
            out = CONTACT_DIR / f"{base_name}.png"
        sheet.convert("RGB").save(out)
        written.append(out.relative_to(REPO_ROOT).as_posix())

    return written


def main() -> None:
    candidates = collect_candidates()
    assign_ids(candidates)
    write_csv(candidates)

    ruffy_sheets = build_contact_sheets(candidates, "ruffy", "ruffy_candidates")
    pet2_sheets = build_contact_sheets(candidates, "pet2_chibi", "pet2_chibi_candidates")

    by_pet: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for cand in candidates:
        by_pet[cand.pet] = by_pet.get(cand.pet, 0) + 1
        by_type[cand.source_type] = by_type.get(cand.source_type, 0) + 1

    print(f"candidates total: {len(candidates)}")
    print("by pet:", dict(sorted(by_pet.items())))
    print("by source_type:", dict(sorted(by_type.items())))
    print(f"csv: {CSV_PATH.relative_to(REPO_ROOT).as_posix()}")
    print("ruffy sheets:", ruffy_sheets)
    print("pet2 sheets:", pet2_sheets)


if __name__ == "__main__":
    main()
