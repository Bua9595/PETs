"""Focused review package for Ruffy single-sprite candidates.

This builds a per-form review CSV and contact sheets using ONLY the
``assets/pets/ruffy/source_cells/`` directory, which contains individual
sprite cells suitable for manual approval.

Explicitly excluded as approval candidates (raw sheets, row sources, runtime
atlases, GIFs, QA/contact sheets, codex atlases) are never mixed into these
form sheets.

It is read-only for the runtime:

* No runtime atlas, manifest or sprite is modified.
* Nothing is copied into ``assets/source_approved/``.
* Nothing is deleted or moved.

Usage::

    python scripts/build_ruffy_cell_review.py
"""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw

# Reuse helpers from the general review builder (same scripts/ folder).
from build_candidate_review import REPO_ROOT, _load_font, _make_thumb

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}

SOURCE_DIR = REPO_ROOT / "assets" / "pets" / "ruffy" / "source_cells"
REVIEW_DIR = REPO_ROOT / "assets" / "review"
CONTACT_DIR = REVIEW_DIR / "contact_sheets"
REPORT_DIR = REVIEW_DIR / "reports"
CSV_PATH = REPORT_DIR / "ruffy_source_cell_review.csv"

CSV_COLUMNS = [
    "candidate_id",
    "form",
    "state_guess",
    "source_path",
    "width",
    "height",
    "review_status",
    "reject_reason",
    "notes",
]

# Form order controls both CSV order and sheet generation order.
FORM_ORDER = ["normal", "gear2", "gear3", "gear4", "gear5", "unknown"]


def cell_form(name: str) -> str:
    """Map a source_cell filename to a Ruffy form, only from explicit tokens."""
    lower = name.lower()
    for gear in ("gear2", "gear3", "gear4", "gear5"):
        if lower.startswith(gear):
            return gear
    if lower.startswith("base"):
        return "normal"
    # Fall back to substring match before giving up.
    for gear in ("gear2", "gear3", "gear4", "gear5"):
        if gear in lower:
            return gear
    if "base" in lower:
        return "normal"
    return "unknown"


def collect_cells() -> list[dict]:
    if not SOURCE_DIR.is_dir():
        return []
    rows: list[dict] = []
    files = sorted(
        p
        for p in SOURCE_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS and p.name != ".gitkeep"
    )
    for path in files:
        form = cell_form(path.name)
        try:
            with Image.open(path) as im:
                width, height = im.size
        except Exception:  # noqa: BLE001
            width, height = 0, 0
        rows.append(
            {
                "form": form,
                # source_cells carry no explicit state token -> never guessed.
                "state_guess": "unknown",
                "source_path": path.relative_to(REPO_ROOT).as_posix(),
                "abs_path": path,
                "width": width,
                "height": height,
                "review_status": "pending",
                "reject_reason": "",
                "notes": "",
            }
        )
    return rows


def order_and_id(rows: list[dict]) -> list[dict]:
    def sort_key(r: dict) -> tuple[int, str]:
        idx = FORM_ORDER.index(r["form"]) if r["form"] in FORM_ORDER else len(FORM_ORDER)
        return (idx, r["source_path"])

    rows.sort(key=sort_key)
    counters: dict[str, int] = {}
    for r in rows:
        form = r["form"]
        counters[form] = counters.get(form, 0) + 1
        r["candidate_id"] = f"ruffy_{form}_{counters[form]:04d}"
    return rows


def write_csv(rows: list[dict]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        for r in rows:
            writer.writerow([r[col] for col in CSV_COLUMNS])


def build_form_sheets(rows: list[dict]) -> dict[str, list[str]]:
    CONTACT_DIR.mkdir(parents=True, exist_ok=True)
    cols, page_rows = 5, 6
    box = 200
    label_h = 26
    pad = 14
    header_h = 60
    per_page = cols * page_rows

    cell_w = box + pad
    cell_h = box + label_h + pad
    sheet_w = pad + cols * cell_w

    font = _load_font(14)
    title_font = _load_font(22)

    written: dict[str, list[str]] = {}
    for form in FORM_ORDER:
        subset = [r for r in rows if r["form"] == form]
        if not subset:
            continue
        pages = [subset[i : i + per_page] for i in range(0, len(subset), per_page)]
        multi = len(pages) > 1
        written[form] = []
        for page_idx, page in enumerate(pages, start=1):
            body_h = page_rows * cell_h
            sheet = Image.new("RGBA", (sheet_w, header_h + body_h + pad), (24, 24, 28, 255))
            draw = ImageDraw.Draw(sheet)
            title = f"ruffy {form} | REVIEW ONLY - source_cells only - not approved"
            if multi:
                title += f" | page {page_idx:03d}/{len(pages):03d}"
            draw.text((pad, 20), title, fill=(235, 235, 240), font=title_font)
            for idx, r in enumerate(page):
                rr, cc = divmod(idx, cols)
                x = pad + cc * cell_w
                y = header_h + rr * cell_h
                sheet.alpha_composite(_make_thumb(r["abs_path"], box), (x, y))
                label = r["candidate_id"]
                tw = draw.textlength(label, font=font)
                draw.text(
                    (x + (box - tw) / 2, y + box + 4),
                    label,
                    fill=(210, 210, 220),
                    font=font,
                )
            if multi:
                out = CONTACT_DIR / f"ruffy_{form}_review_{page_idx:03d}.png"
            else:
                out = CONTACT_DIR / f"ruffy_{form}_review.png"
            sheet.convert("RGB").save(out)
            written[form].append(out.relative_to(REPO_ROOT).as_posix())
    return written


def main() -> None:
    rows = collect_cells()
    rows = order_and_id(rows)
    write_csv(rows)
    sheets = build_form_sheets(rows)

    by_form: dict[str, int] = {}
    for r in rows:
        by_form[r["form"]] = by_form.get(r["form"], 0) + 1

    print(f"ruffy source_cell candidates: {len(rows)}")
    for form in FORM_ORDER:
        print(f"  {form}: {by_form.get(form, 0)}")
    print(f"csv: {CSV_PATH.relative_to(REPO_ROOT).as_posix()}")
    for form, paths in sheets.items():
        print(f"sheets[{form}]: {paths}")


if __name__ == "__main__":
    main()
