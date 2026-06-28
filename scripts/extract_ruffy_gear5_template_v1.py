"""Extract Gear5 template candidate v1 from manually cleaned source.

Reads ONLY the gear5 template candidate under assets/source_candidates/.
Does not modify the source file. Outputs review artefacts only.

Usage::

    python scripts/extract_ruffy_gear5_template_v1.py
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[1]

SOURCE_DIR = REPO_ROOT / "assets" / "source_candidates" / "ruffy" / "gear5_template"
SOURCE_PRIMARY = SOURCE_DIR / "gear5_template.png"
SOURCE_FALLBACK = SOURCE_DIR / "ruffy_gear5_template.png"

CANDIDATES_DIR = REPO_ROOT / "assets" / "review" / "candidates" / "ruffy_gear5_template_v1"
CANDIDATE_PATH = CANDIDATES_DIR / "ruffy_gear5_template_candidate_v1.png"
CONTACT_SHEET = REPO_ROOT / "assets" / "review" / "contact_sheets" / "ruffy_gear5_template_v1_review.png"
REPORT_PATH = REPO_ROOT / "assets" / "review" / "reports" / "ruffy_gear5_template_v1_review.md"

PREFERRED_PADDING = 48
MIN_PADDING = 32


@dataclass
class ExtractionReport:
    source_path: Path
    source_exists: bool
    source_dimensions: str
    source_mode: str
    visible_watermark: str
    character_full: str
    chroma_background: str
    candidate_path: Path
    candidate_size: tuple[int, int]
    transparent_bg: bool
    margins: tuple[int, int, int, int]
    cutoff_risk: bool
    detached_fragments: bool
    detached_notes: list[str]
    recommendation: str
    notes: list[str]


def is_chroma_like(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, a = pixel
    if a <= 12:
        return True
    if r >= 110 and b >= 130 and g <= 90 and b - g >= 60 and r - g >= 40:
        return True
    return r >= 150 and b >= 150 and g <= 110 and min(r, b) - g >= 55


def is_bright_chroma_fringe(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, a = pixel
    return a > 0 and r >= 120 and b >= 140 and g <= 100 and min(r, b) - g >= 50


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


def margins_in_image(rgba: Image.Image) -> tuple[int, int, int, int]:
    bbox = content_bbox(rgba)
    if bbox is None:
        return 0, 0, 0, 0
    left, top, right, bottom = bbox
    w, h = rgba.size
    return top, h - bottom, left, w - right


def find_detached_fragments(rgba: Image.Image) -> tuple[bool, list[str]]:
    w, h = rgba.size
    alpha = rgba.split()[3]
    px = alpha.load()
    visited = [[False] * w for _ in range(h)]
    components: list[tuple[int, int, int, int, int]] = []

    for sy in range(h):
        for sx in range(w):
            if visited[sy][sx] or px[sx, sy] <= 12:
                continue
            stack = [(sx, sy)]
            visited[sy][sx] = True
            area = 0
            minx = maxx = sx
            miny = maxy = sy
            while stack:
                x, y = stack.pop()
                area += 1
                minx, miny = min(minx, x), min(miny, y)
                maxx, maxy = max(maxx, x), max(maxy, y)
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and px[nx, ny] > 12:
                        visited[ny][nx] = True
                        stack.append((nx, ny))
            components.append((area, minx, miny, maxx, maxy))

    if len(components) <= 1:
        return False, []

    components.sort(reverse=True)
    main = components[0]
    main_bottom_y = main[4]
    notes: list[str] = []
    for area, minx, miny, maxx, maxy in components[1:]:
        if area < 35:
            continue
        if miny >= main_bottom_y - 8:
            notes.append(f"detached fragment blob area={area} below main mass")
        else:
            notes.append(f"secondary blob area={area} (possible aura/sash)")
    return bool(notes), notes


def detect_watermark_heuristic(rgba: Image.Image) -> str:
    """Rough check for corner text/watermark overlays."""
    w, h = rgba.size
    px = rgba.load()
    corner_h = max(24, h // 10)
    corner_w = max(24, w // 10)
    regions = [
        (0, h - corner_h, corner_w, h),
        (w - corner_w, h - corner_h, w, h),
        (0, 0, corner_w, corner_h),
        (w - corner_w, 0, w, corner_h),
    ]
    for left, top, right, bottom in regions:
        dark_textish = 0
        total = 0
        for y in range(top, bottom):
            for x in range(left, right):
                r, g, b, a = px[x, y]
                if a <= 12:
                    continue
                total += 1
                if r < 80 and g < 80 and b < 80:
                    dark_textish += 1
        if total > 40 and dark_textish / total > 0.18:
            return "yes"
    return "no"


def chroma_ratio(image: Image.Image) -> float:
    px = image.convert("RGBA").load()
    w, h = image.size
    total = w * h
    chroma = sum(1 for y in range(h) for x in range(w) if is_chroma_like(px[x, y]))
    return chroma / total


def extract_character(source: Image.Image) -> tuple[Image.Image | None, list[str]]:
    notes: list[str] = []
    rgba = chroma_to_alpha(source)
    bbox = content_bbox(rgba)
    if bbox is None:
        notes.append("no visible content after chroma key")
        return None, notes

    left, top, right, bottom = bbox
    sw, sh = rgba.size
    pad_top = max(MIN_PADDING, min(PREFERRED_PADDING, top))
    pad_bottom = max(MIN_PADDING, min(PREFERRED_PADDING, sh - bottom))
    pad_left = max(MIN_PADDING, min(PREFERRED_PADDING, left))
    pad_right = max(MIN_PADDING, min(PREFERRED_PADDING, sw - right))

    el = max(0, left - pad_left)
    et = max(0, top - pad_top)
    er = min(sw, right + pad_right)
    eb = min(sh, bottom + pad_bottom)
    crop = rgba.crop((el, et, er, eb))
    notes.append(
        f"bbox=({left},{top},{right},{bottom}) padding=({pad_top},{pad_bottom},{pad_left},{pad_right})"
    )
    return crop, notes


def assess_recommendation(
    cutoff_risk: bool,
    detached: bool,
    detached_notes: list[str],
    margins: tuple[int, int, int, int],
    watermark: str,
) -> str:
    top, bottom, left, right = margins
    min_margin = min(top, bottom, left, right)
    if watermark == "yes":
        return "reject"
    if cutoff_risk or min_margin < 8:
        return "needs_aseprite_fix"
    if detached and any("detached fragment" in n for n in detached_notes):
        return "needs_aseprite_fix"
    if min_margin < MIN_PADDING:
        return "needs_aseprite_fix"
    return "approve_candidate_for_aseprite_check"


def load_font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_contact_sheet(candidate: Image.Image, filename: str) -> None:
    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    pad = 32
    header_h = 72
    label_h = 36
    preview_max = 720
    im = candidate.convert("RGBA")
    scale = min(1.0, preview_max / max(im.width, im.height))
    if scale < 1.0:
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    box_w = im.width + pad * 2
    box_h = im.height + pad * 2
    sheet_w = max(860, box_w + pad * 2)
    sheet_h = header_h + box_h + label_h + pad
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (24, 24, 28, 255))
    draw = ImageDraw.Draw(sheet)
    title_font = load_font(18)
    label_font = load_font(13)
    draw.text(
        (pad, 22),
        "ruffy gear5 template candidate v1 | REVIEW ONLY - not approved",
        fill=(235, 235, 240),
        font=title_font,
    )
    tile = Image.new("RGBA", (box_w, box_h), (45, 45, 52, 255))
    tile.alpha_composite(im, (pad, pad))
    x = (sheet_w - box_w) // 2
    y = header_h
    sheet.alpha_composite(tile, (x, y))
    tw = draw.textlength(filename, font=label_font)
    draw.text(
        (x + max(0, (box_w - tw) / 2), y + box_h + 8),
        filename,
        fill=(210, 210, 220),
        font=label_font,
    )
    sheet.convert("RGB").save(CONTACT_SHEET)


def resolve_source() -> Path | None:
    if SOURCE_PRIMARY.is_file():
        return SOURCE_PRIMARY
    if SOURCE_FALLBACK.is_file():
        return SOURCE_FALLBACK
    return None


def write_report(report: ExtractionReport) -> None:
    rel_source = report.source_path.relative_to(REPO_ROOT).as_posix()
    rel_candidate = report.candidate_path.relative_to(REPO_ROOT).as_posix()
    top, bottom, left, right = report.margins
    lines = [
        "# Ruffy Gear5 Template Candidate v1 Review",
        "",
        "## Source",
        "",
        f"- path: `{rel_source}`",
        f"- exists: {'yes' if report.source_exists else 'no'}",
        f"- dimensions: {report.source_dimensions}",
        f"- mode: {report.source_mode}",
        f"- visible_watermark_present: {report.visible_watermark}",
        "",
        "## Extracted Candidate",
        "",
        f"- path: `{rel_candidate}`",
        f"- dimensions: {report.candidate_size[0]}x{report.candidate_size[1]}",
        f"- full_body_visible: {report.character_full}",
        f"- watermark_removed: {'yes' if report.visible_watermark == 'no' else 'no/unclear'}",
        f"- both_arms_visible: unclear (manual visual review required)",
        f"- both_hands_visible: unclear (manual visual review required)",
        f"- both_legs_visible: unclear (manual visual review required)",
        f"- both_feet_visible: unclear (manual visual review required)",
        f"- both_sandals_visible: unclear (manual visual review required)",
        f"- waist_sash_complete: unclear (manual visual review required)",
        f"- floating_sash_tail_complete_or_absent: unclear (manual visual review required)",
        f"- jacket_or_vest_complete: unclear (manual visual review required)",
        f"- aura_clouds_clean: unclear (manual visual review required)",
        f"- detached_fragments: {'yes' if report.detached_fragments else 'no/unclear'}",
        f"- cutoffs: {'yes' if report.cutoff_risk else 'no/unclear'}",
        f"- style_matches_pet1: unclear (manual visual review required)",
        f"- transparent_background: {'yes' if report.transparent_bg else 'no'}",
        f"- margins_px: top={top}, bottom={bottom}, left={left}, right={right}",
        f"- recommendation: **{report.recommendation}**",
        "",
        "## Notes",
        "",
    ]
    lines.extend(f"- {note}" for note in report.notes)
    if not SOURCE_PRIMARY.is_file() and SOURCE_FALLBACK.is_file():
        lines.append(
            f"- Prompt path `{SOURCE_PRIMARY.relative_to(REPO_ROOT).as_posix()}` not found; "
            f"used `{SOURCE_FALLBACK.relative_to(REPO_ROOT).as_posix()}` as manually cleaned source."
        )
    lines.append("")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    for directory in (SOURCE_DIR, CANDIDATES_DIR, CONTACT_SHEET.parent, REPORT_PATH.parent):
        directory.mkdir(parents=True, exist_ok=True)

    source_path = resolve_source()
    if source_path is None:
        print("STOP: source missing")
        print(f"  expected: {SOURCE_PRIMARY}")
        print(f"  fallback: {SOURCE_FALLBACK}")
        return 1

    with Image.open(source_path) as raw:
        raw_mode = raw.mode
        raw_size = raw.size
        watermark = detect_watermark_heuristic(raw.convert("RGBA"))
        chroma_bg = "yes" if chroma_ratio(raw) > 0.45 else "unclear"

        extracted, extract_notes = extract_character(raw)
        if extracted is None:
            print("STOP: extraction failed — no visible character content")
            return 1

        extracted.save(CANDIDATE_PATH)
        top_m, bot_m, left_m, right_m = margins_in_image(extracted)
        detached, detached_notes = find_detached_fragments(extracted)
        cutoff = min(top_m, bot_m, left_m, right_m) < 12
        alpha = extracted.split()[3]
        transparent_bg = alpha.getextrema()[0] == 0

        notes = list(extract_notes)
        notes.extend(detached_notes)
        notes.append(f"source chroma background ratio={chroma_ratio(raw):.2f}")
        notes.append("Automated body-part checks deferred to manual visual review on contact sheet.")

        recommendation = assess_recommendation(
            cutoff_risk=cutoff,
            detached=detached,
            detached_notes=detached_notes,
            margins=(top_m, bot_m, left_m, right_m),
            watermark=watermark,
        )

        report = ExtractionReport(
            source_path=source_path,
            source_exists=True,
            source_dimensions=f"{raw_size[0]}x{raw_size[1]}",
            source_mode=raw_mode,
            visible_watermark=watermark,
            character_full="yes" if not cutoff and top_m >= 12 and bot_m >= 12 else "unclear",
            chroma_background=chroma_bg,
            candidate_path=CANDIDATE_PATH,
            candidate_size=extracted.size,
            transparent_bg=transparent_bg,
            margins=(top_m, bot_m, left_m, right_m),
            cutoff_risk=cutoff,
            detached_fragments=detached,
            detached_notes=detached_notes,
            recommendation=recommendation,
            notes=notes,
        )

        build_contact_sheet(extracted, CANDIDATE_PATH.name)
        write_report(report)

    print(f"source: {source_path.relative_to(REPO_ROOT)} {raw_size} {raw_mode}")
    print(f"candidate: {CANDIDATE_PATH.relative_to(REPO_ROOT)} {report.candidate_size}")
    print(f"watermark: {watermark} transparent: {transparent_bg}")
    print(f"recommendation: {recommendation}")
    print(f"sheet: {CONTACT_SHEET.relative_to(REPO_ROOT)}")
    print(f"report: {REPORT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
