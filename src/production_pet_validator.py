"""Validation for manifest-driven production Godot pet packs.

This validator checks structural and technical readiness only.  It deliberately
does not judge anatomy, style, or any other visual-art quality.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import xml.etree.ElementTree as element_tree
from pathlib import Path
from typing import Any


REQUIRED_PART_IDS = frozenset(
    {
        "hair_back",
        "head",
        "face",
        "eye_whites",
        "left_pupil",
        "right_pupil",
        "mouth",
        "hair_front",
        "torso",
        "left_upper_arm",
        "left_lower_arm",
        "left_hand",
        "right_upper_arm",
        "right_lower_arm",
        "right_hand",
        "left_upper_leg",
        "left_lower_leg",
        "left_foot",
        "right_upper_leg",
        "right_lower_leg",
        "right_foot",
    }
)
SUPPORTED_SCHEMA_VERSION = 1


def validate_pet_manifest(manifest_path: Path) -> list[str]:
    """Return every structural or asset error found in a production pet manifest."""
    return _validate(manifest_path, check_assets=True)


def validate_pet_template_structure(manifest_path: Path) -> list[str]:
    """Validate a draft template contract without requiring its future art files."""
    return _validate(manifest_path, check_assets=False)


def _validate(manifest_path: Path, *, check_assets: bool) -> list[str]:
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as error:
        return [f"{manifest_path}: cannot read manifest: {error}"]
    except json.JSONDecodeError as error:
        return [f"{manifest_path}: invalid JSON: {error.msg}"]

    if not isinstance(data, dict):
        return [f"{manifest_path}: root must be an object"]

    errors: list[str] = []
    _validate_top_level(data, errors)
    _validate_schema_version(data.get("schema_version"), errors)
    canvas = _validate_canvas(data.get("canvas"), errors)
    _validate_ground_anchor(data.get("ground_anchor"), canvas, errors)
    bones = _validate_bones(data.get("bones"), errors)
    action_bounds = _validate_action_bounds(data.get("action_bounds"), canvas, errors)
    _validate_parts(data.get("parts"), manifest_path.parent, bones, canvas, action_bounds, check_assets, errors)
    return errors


def _validate_top_level(data: dict[str, Any], errors: list[str]) -> None:
    for field in (
        "schema_version",
        "pet_id",
        "name",
        "version",
        "status",
        "source_reference",
        "canvas",
        "ground_anchor",
        "parts",
        "bones",
        "animations",
        "action_bounds",
    ):
        if field not in data:
            errors.append(f"{field}: is required")


def _validate_schema_version(value: Any, errors: list[str]) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append("schema_version: must be an integer")
    elif value != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            f"schema_version: unsupported version {value}; supported version is {SUPPORTED_SCHEMA_VERSION}"
        )


def _validate_canvas(value: Any, errors: list[str]) -> tuple[float, float] | None:
    if not isinstance(value, dict):
        errors.append("canvas: must be an object with positive width and height")
        return None
    width = value.get("width")
    height = value.get("height")
    if not _is_positive_number(width) or not _is_positive_number(height):
        errors.append("canvas: width and height must be positive numbers")
        return None
    return float(width), float(height)


def _validate_ground_anchor(
    value: Any, canvas: tuple[float, float] | None, errors: list[str]
) -> None:
    anchor = _as_point(value)
    if anchor is None:
        errors.append("ground_anchor: must be a coordinate pair")
    elif canvas and not _point_in_canvas(anchor, canvas):
        errors.append("ground_anchor: must remain inside canvas")


def _validate_bones(value: Any, errors: list[str]) -> set[str]:
    if not isinstance(value, list) or not value:
        errors.append("bones: must be a non-empty array")
        return set()
    names: set[str] = set()
    for index, bone in enumerate(value):
        if not isinstance(bone, dict) or not isinstance(bone.get("bone_id"), str) or not bone["bone_id"]:
            errors.append(f"bones[{index}].bone_id: is required")
            continue
        bone_id = bone["bone_id"]
        if bone_id in names:
            errors.append(f"bones[{index}].bone_id: duplicate '{bone_id}'")
        names.add(bone_id)
    for index, bone in enumerate(value):
        if not isinstance(bone, dict):
            continue
        parent = bone.get("parent_bone")
        if parent is not None and parent not in names:
            errors.append(f"bones[{index}].parent_bone: unknown bone '{parent}'")
    return names


def _validate_action_bounds(
    value: Any, canvas: tuple[float, float] | None, errors: list[str]
) -> dict[str, list[tuple[float, float]]]:
    if not isinstance(value, dict):
        errors.append("action_bounds: must define idle_bounds and wave_bounds")
        return {}
    result: dict[str, list[tuple[float, float]]] = {}
    for name in ("idle_bounds", "wave_bounds"):
        polygon = _as_polygon(value.get(name))
        if polygon is None:
            errors.append(f"action_bounds.{name}: must contain at least three coordinate pairs")
            continue
        if canvas and any(not _point_in_canvas(point, canvas) for point in polygon):
            errors.append(f"action_bounds.{name}: points must remain inside canvas")
        result[name] = polygon
    return result


def _validate_parts(
    value: Any,
    manifest_dir: Path,
    bones: set[str],
    canvas: tuple[float, float] | None,
    action_bounds: dict[str, list[tuple[float, float]]],
    check_assets: bool,
    errors: list[str],
) -> None:
    if not isinstance(value, list):
        errors.append("parts: must be an array")
        return

    part_ids: set[str] = set()
    for index, part in enumerate(value):
        prefix = f"parts[{index}]"
        if not isinstance(part, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        for field in ("part_id", "asset_path", "parent_bone", "pivot", "local_position", "z_index", "visible", "required", "overlap_margin"):
            if field not in part:
                errors.append(f"{prefix}.{field}: is required")
        part_id = part.get("part_id")
        if not isinstance(part_id, str) or not part_id:
            errors.append(f"{prefix}.part_id: must be a non-empty string")
        elif part_id in part_ids:
            errors.append(f"{prefix}.part_id: duplicate '{part_id}'")
        else:
            part_ids.add(part_id)

        if isinstance(part_id, str) and part_id in REQUIRED_PART_IDS and part.get("required") is not True:
            errors.append(f"{prefix}.required: required production part '{part_id}' must be true")
        if "z_index" in part and (not isinstance(part["z_index"], int) or isinstance(part["z_index"], bool)):
            errors.append(f"{prefix}.z_index: must be an integer")
        if "visible" in part and not isinstance(part["visible"], bool):
            errors.append(f"{prefix}.visible: must be a boolean")

        parent_bone = part.get("parent_bone")
        if not isinstance(parent_bone, str) or parent_bone not in bones:
            errors.append(f"{prefix}.parent_bone: unknown bone '{parent_bone}'")

        asset_file = _validate_asset_reference(part.get("asset_path"), manifest_dir, prefix, errors)
        asset_dimensions = (
            _validate_asset_file(asset_file, part.get("asset_path"), prefix, errors)
            if check_assets and asset_file is not None
            else None
        )
        _validate_part_geometry(part, asset_dimensions, prefix, errors)
        _validate_idle_contribution(part, canvas, action_bounds.get("idle_bounds"), prefix, errors)

    missing = REQUIRED_PART_IDS - part_ids
    if missing:
        errors.append("parts: missing required part_id values: " + ", ".join(sorted(missing)))


def _validate_asset_reference(asset_path: Any, manifest_dir: Path, prefix: str, errors: list[str]) -> Path | None:
    if not isinstance(asset_path, str) or not asset_path:
        errors.append(f"{prefix}.asset_path: must be a non-empty relative path")
        return None
    path = Path(asset_path)
    if path.is_absolute():
        errors.append(f"{prefix}.asset_path: must stay within the pet pack")
        return None
    pack_root = manifest_dir.parent.resolve()
    resolved = (manifest_dir / path).resolve()
    if not resolved.is_relative_to(pack_root):
        errors.append(f"{prefix}.asset_path: must stay within the pet pack")
        return None
    return resolved


def _validate_asset_file(
    resolved: Path, asset_path: Any, prefix: str, errors: list[str]
) -> tuple[float, float] | None:
    if not resolved.is_file():
        errors.append(f"{prefix}.asset_path: does not exist: {asset_path}")
        return None
    if resolved.stat().st_size == 0:
        errors.append(f"{prefix}.asset_path: is empty: {asset_path}")
        return None
    return _read_image_dimensions(resolved, prefix, errors)


def _read_image_dimensions(path: Path, prefix: str, errors: list[str]) -> tuple[float, float] | None:
    if path.suffix.lower() == ".svg":
        try:
            root = element_tree.fromstring(path.read_bytes())
            view_box = root.attrib.get("viewBox", "").replace(",", " ").split()
            if len(view_box) == 4:
                width, height = float(view_box[2]), float(view_box[3])
                if _is_positive_number(width) and _is_positive_number(height):
                    return width, height
            raise ValueError("missing positive viewBox")
        except (element_tree.ParseError, ValueError) as error:
            errors.append(f"{prefix}.asset_path: SVG is not loadable: {error}")
            return None
    try:
        from PIL import Image

        with Image.open(path) as image:
            image.verify()
            width, height = image.size
        return float(width), float(height)
    except Exception as error:  # Pillow reports format-specific decode errors.
        errors.append(f"{prefix}.asset_path: image is not loadable: {error}")
        return None


def _validate_part_geometry(
    part: dict[str, Any], dimensions: tuple[float, float] | None, prefix: str, errors: list[str]
) -> None:
    pivot = _as_point(part.get("pivot"))
    local_position = _as_point(part.get("local_position"))
    overlap_margin = part.get("overlap_margin")
    if pivot is None:
        errors.append(f"{prefix}.pivot: must be a coordinate pair")
    if local_position is None:
        errors.append(f"{prefix}.local_position: must be a coordinate pair")
    if not _is_non_negative_number(overlap_margin):
        errors.append(f"{prefix}.overlap_margin: must be a non-negative number")
        return
    if pivot is not None and dimensions is not None:
        margin = float(overlap_margin)
        width, height = dimensions
        if not (-margin <= pivot[0] <= width + margin and -margin <= pivot[1] <= height + margin):
            errors.append(f"{prefix}.pivot: lies outside plausible image bounds")


def _validate_idle_contribution(
    part: dict[str, Any],
    canvas: tuple[float, float] | None,
    idle_polygon: list[tuple[float, float]] | None,
    prefix: str,
    errors: list[str],
) -> None:
    contribution = part.get("action_bounds_contribution")
    if not isinstance(contribution, dict) or "idle" not in contribution:
        errors.append(f"{prefix}.action_bounds_contribution.idle: is required")
        return
    rectangle = _as_rectangle(contribution["idle"])
    if rectangle is None:
        errors.append(f"{prefix}.action_bounds_contribution.idle: must be [min_x, min_y, max_x, max_y]")
        return
    corners = [(rectangle[0], rectangle[1]), (rectangle[2], rectangle[1]), (rectangle[2], rectangle[3]), (rectangle[0], rectangle[3])]
    if canvas and any(not _point_in_canvas(point, canvas) for point in corners):
        errors.append(f"{prefix}.action_bounds_contribution.idle: must remain inside canvas")
    if idle_polygon and any(not _point_in_or_on_polygon(point, idle_polygon) for point in corners):
        errors.append(f"{prefix}.action_bounds_contribution.idle: must fit inside action_bounds.idle_bounds")


def _as_point(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, list) or len(value) != 2 or not all(_is_finite_number(item) for item in value):
        return None
    return float(value[0]), float(value[1])


def _as_polygon(value: Any) -> list[tuple[float, float]] | None:
    if not isinstance(value, list) or len(value) < 3:
        return None
    points = [_as_point(point) for point in value]
    return points if all(point is not None for point in points) else None  # type: ignore[return-value]


def _as_rectangle(value: Any) -> tuple[float, float, float, float] | None:
    if not isinstance(value, list) or len(value) != 4 or not all(_is_finite_number(item) for item in value):
        return None
    min_x, min_y, max_x, max_y = (float(item) for item in value)
    return (min_x, min_y, max_x, max_y) if min_x <= max_x and min_y <= max_y else None


def _point_in_canvas(point: tuple[float, float], canvas: tuple[float, float]) -> bool:
    return 0 <= point[0] <= canvas[0] and 0 <= point[1] <= canvas[1]


def _point_in_or_on_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        if _point_on_segment(point, start, end):
            return True
    inside = False
    previous = polygon[-1]
    for current in polygon:
        if (current[1] > point[1]) != (previous[1] > point[1]):
            crossing = (previous[0] - current[0]) * (point[1] - current[1]) / (previous[1] - current[1]) + current[0]
            if point[0] < crossing:
                inside = not inside
        previous = current
    return inside


def _point_on_segment(point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]) -> bool:
    cross = (point[1] - start[1]) * (end[0] - start[0]) - (point[0] - start[0]) * (end[1] - start[1])
    if not math.isclose(cross, 0.0, abs_tol=1e-7):
        return False
    return min(start[0], end[0]) <= point[0] <= max(start[0], end[0]) and min(start[1], end[1]) <= point[1] <= max(start[1], end[1])


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _is_positive_number(value: Any) -> bool:
    return _is_finite_number(value) and float(value) > 0


def _is_non_negative_number(value: Any) -> bool:
    return _is_finite_number(value) and float(value) >= 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a production Godot pet manifest.")
    parser.add_argument("manifest", type=Path, help="Path to metadata/pet_manifest.json")
    args = parser.parse_args()
    errors = validate_pet_manifest(args.manifest)
    if errors:
        print("Production pet manifest validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"Production pet manifest is valid: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
