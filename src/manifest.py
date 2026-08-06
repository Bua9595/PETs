"""Loading and static validation for desktop-pet character manifests.

The module deliberately only validates data that the existing runtime already
uses.  It does not execute pack code or change pack assets.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


@dataclass(frozen=True)
class ManifestIssue:
    """One validation failure, including the affected pack and field path."""

    pack: Path
    field: str
    cause: str

    def __str__(self) -> str:
        return f"{self.pack}: {self.field}: {self.cause}"


class ManifestValidationError(ValueError):
    """Raised when a manifest cannot safely be used by the desktop runtime."""

    def __init__(self, issues: list[ManifestIssue]):
        self.issues = issues
        super().__init__("Manifest validation failed:\n" + "\n".join(f"- {issue}" for issue in issues))


@dataclass(frozen=True)
class LoadedManifest:
    path: Path
    pack_dir: Path
    data: dict[str, Any]
    schema_version: int
    warnings: tuple[str, ...] = ()

    @property
    def atlas_path(self) -> Path:
        return self.pack_dir / self.data["image"]


def load_manifest(manifest_path: str | Path) -> LoadedManifest:
    """Load a v1 manifest and validate its static runtime contract.

    Manifests without ``schema_version`` are intentionally treated as v1 so
    existing character packs remain valid without a migration.
    """

    path = Path(manifest_path).resolve()
    pack_dir = path.parent
    issues: list[ManifestIssue] = []

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ManifestValidationError([ManifestIssue(path, "$", f"cannot read manifest ({error})")]) from error

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ManifestValidationError(
            [ManifestIssue(path, "$", f"invalid JSON at line {error.lineno}, column {error.colno}: {error.msg}")]
        ) from error

    if not isinstance(data, dict):
        raise ManifestValidationError([ManifestIssue(path, "$", "expected a JSON object")])

    schema_version = data.get("schema_version", 1)
    if not _is_positive_int(schema_version):
        issues.append(ManifestIssue(path, "schema_version", "must be a positive integer"))
    elif schema_version != 1:
        issues.append(ManifestIssue(path, "schema_version", f"unsupported version {schema_version}"))

    for key in ("id", "display_name", "image"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            issues.append(ManifestIssue(path, key, "must be a non-empty string"))

    for key in ("columns", "rows", "cell_width", "cell_height", "frame_duration_ms"):
        if not _is_positive_int(data.get(key)):
            issues.append(ManifestIssue(path, key, "must be a positive integer"))

    animations = data.get("animations")
    if not isinstance(animations, dict) or not animations:
        issues.append(ManifestIssue(path, "animations", "must be a non-empty object"))
        animations = {}

    _validate_atlas(path, pack_dir, data, issues)
    _validate_animations(path, data, animations, issues)
    _validate_desktop_behavior(path, data.get("desktop_behavior"), animations, issues)

    if issues:
        raise ManifestValidationError(issues)
    return LoadedManifest(path=path, pack_dir=pack_dir, data=data, schema_version=int(schema_version))


def _validate_atlas(path: Path, pack_dir: Path, data: dict[str, Any], issues: list[ManifestIssue]) -> None:
    image_name = data.get("image")
    if not isinstance(image_name, str) or not image_name.strip():
        return
    image_relative_path = Path(image_name)
    if image_relative_path.is_absolute() or ".." in image_relative_path.parts:
        issues.append(ManifestIssue(path, "image", "must be a path relative to the character pack"))
        return
    image_path = pack_dir / image_relative_path
    if not image_path.is_file():
        issues.append(ManifestIssue(path, "image", f"atlas image does not exist: {image_path}"))
        return
    try:
        with Image.open(image_path) as image:
            width, height = image.size
    except (OSError, UnidentifiedImageError) as error:
        issues.append(ManifestIssue(path, "image", f"atlas image is unreadable ({error})"))
        return

    if all(_is_positive_int(data.get(key)) for key in ("columns", "rows", "cell_width", "cell_height")):
        expected = (data["columns"] * data["cell_width"], data["rows"] * data["cell_height"])
        if (width, height) != expected:
            issues.append(ManifestIssue(path, "image", f"atlas dimensions {width}x{height} do not match declared {expected[0]}x{expected[1]}"))


def _validate_animations(path: Path, data: dict[str, Any], animations: dict[str, Any], issues: list[ManifestIssue]) -> None:
    rows = data.get("rows")
    columns = data.get("columns")
    default_duration = data.get("frame_duration_ms")
    for name, spec in animations.items():
        prefix = f"animations.{name}"
        if not isinstance(name, str) or not name:
            issues.append(ManifestIssue(path, prefix, "animation name must be a non-empty string"))
        if not isinstance(spec, dict):
            issues.append(ManifestIssue(path, prefix, "must be an object"))
            continue
        row = spec.get("row")
        frames = spec.get("frames")
        if not _is_nonnegative_int(row):
            issues.append(ManifestIssue(path, f"{prefix}.row", "must be a non-negative integer"))
        elif _is_positive_int(rows) and row >= rows:
            issues.append(ManifestIssue(path, f"{prefix}.row", f"row {row} is outside declared rows {rows}"))
        if not _is_positive_int(frames):
            issues.append(ManifestIssue(path, f"{prefix}.frames", "must be a positive integer"))
        elif _is_positive_int(columns) and frames > columns:
            issues.append(ManifestIssue(path, f"{prefix}.frames", f"frame count {frames} exceeds declared columns {columns}"))
        duration = spec.get("frame_duration_ms", default_duration)
        if not _is_positive_int(duration):
            issues.append(ManifestIssue(path, f"{prefix}.frame_duration_ms", "must be a positive integer"))
        if "loop" in spec and not isinstance(spec["loop"], bool):
            issues.append(ManifestIssue(path, f"{prefix}.loop", "must be a boolean"))


def _validate_desktop_behavior(
    path: Path, behavior: Any, animations: dict[str, Any], issues: list[ManifestIssue]
) -> None:
    if behavior is None:
        return
    if not isinstance(behavior, dict):
        issues.append(ManifestIssue(path, "desktop_behavior", "must be an object"))
        return

    for key in ("initial_animation", "drag_animation", "double_click_animation"):
        if key in behavior:
            _validate_animation_reference(path, f"desktop_behavior.{key}", behavior[key], animations, issues)

    menu_states = behavior.get("menu_states")
    if menu_states is not None:
        if not isinstance(menu_states, list):
            issues.append(ManifestIssue(path, "desktop_behavior.menu_states", "must be a list"))
        else:
            for index, item in enumerate(menu_states):
                field = f"desktop_behavior.menu_states[{index}]"
                if isinstance(item, dict):
                    _validate_animation_reference(path, f"{field}.animation", item.get("animation"), animations, issues)
                elif isinstance(item, list) and len(item) == 2:
                    _validate_animation_reference(path, f"{field}[1]", item[1], animations, issues)
                else:
                    issues.append(ManifestIssue(path, field, "must be an object with animation or a two-item list"))

    choices = behavior.get("choices")
    if choices is not None:
        if not isinstance(choices, list):
            issues.append(ManifestIssue(path, "desktop_behavior.choices", "must be a list"))
        else:
            for index, item in enumerate(choices):
                field = f"desktop_behavior.choices[{index}]"
                reference = item.get("animation") if isinstance(item, dict) else item[0] if isinstance(item, list) and len(item) == 2 else None
                _validate_animation_reference(path, f"{field}.animation", reference, animations, issues)

    category_behavior = behavior.get("category_behavior")
    if category_behavior is not None:
        if not isinstance(category_behavior, dict):
            issues.append(ManifestIssue(path, "desktop_behavior.category_behavior", "must be an object"))
        else:
            categories = category_behavior.get("categories")
            if categories is not None:
                if not isinstance(categories, list):
                    issues.append(ManifestIssue(path, "desktop_behavior.category_behavior.categories", "must be a list"))
                else:
                    for index, category in enumerate(categories):
                        field = f"desktop_behavior.category_behavior.categories[{index}]"
                        if not isinstance(category, dict):
                            issues.append(ManifestIssue(path, field, "must be an object"))
                            continue
                        names = category.get("animations", [])
                        if not isinstance(names, list):
                            issues.append(ManifestIssue(path, f"{field}.animations", "must be a list"))
                            continue
                        for animation_index, name in enumerate(names):
                            _validate_animation_reference(path, f"{field}.animations[{animation_index}]", name, animations, issues)


def _validate_animation_reference(
    path: Path, field: str, value: Any, animations: dict[str, Any], issues: list[ManifestIssue]
) -> None:
    if not isinstance(value, str) or not value:
        issues.append(ManifestIssue(path, field, "must reference an animation name"))
    elif value not in animations:
        issues.append(ManifestIssue(path, field, f"references unknown animation '{value}'"))


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
