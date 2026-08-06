"""Pure movement calculation for moving one abstract position toward another."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class PositionBounds:
    """Inclusive valid bounds for the same position anchor used by chase_target."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        min_x = _finite("bounds.min_x", self.min_x)
        min_y = _finite("bounds.min_y", self.min_y)
        max_x = _finite("bounds.max_x", self.max_x)
        max_y = _finite("bounds.max_y", self.max_y)
        if min_x > max_x:
            raise ValueError("bounds.min_x must be less than or equal to bounds.max_x")
        if min_y > max_y:
            raise ValueError("bounds.min_y must be less than or equal to bounds.max_y")


def chase_target(
    current_x: float,
    current_y: float,
    target_x: float,
    target_y: float,
    speed: float,
    delta_time: float,
    *,
    bounds: PositionBounds | None = None,
) -> tuple[float, float]:
    """Move toward a target by at most ``speed * delta_time`` pixels.

    Current and target coordinates use the same caller-defined anchor.  Bounds,
    when supplied, constrain that anchor's target position only; a current
    position outside the bounds is never teleported back into them.
    """

    current_x = _finite("current_x", current_x)
    current_y = _finite("current_y", current_y)
    target_x = _finite("target_x", target_x)
    target_y = _finite("target_y", target_y)
    speed = _finite("speed", speed)
    delta_time = _finite("delta_time", delta_time)
    if speed < 0:
        raise ValueError("speed must be non-negative")
    if bounds is not None and not isinstance(bounds, PositionBounds):
        raise ValueError("bounds must be a PositionBounds instance or None")

    if bounds is not None:
        target_x = min(max(target_x, bounds.min_x), bounds.max_x)
        target_y = min(max(target_y, bounds.min_y), bounds.max_y)

    if speed == 0 or delta_time <= 0:
        return current_x, current_y

    dx = target_x - current_x
    dy = target_y - current_y
    distance = math.hypot(dx, dy)
    max_distance = speed * delta_time
    if distance == 0 or max_distance >= distance:
        return target_x, target_y

    ratio = max_distance / distance
    return current_x + dx * ratio, current_y + dy * ratio


def _finite(name: str, value: Any) -> float:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a finite number") from error
    if not math.isfinite(numeric_value):
        raise ValueError(f"{name} must be a finite number")
    return numeric_value
