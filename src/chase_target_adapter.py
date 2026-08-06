"""Pure DesktopPet window-position adapter for the anchor-neutral chase function."""

from __future__ import annotations

from chase_target import PositionBounds, chase_target
from sensor_snapshot import SensorSnapshot


def calculate_chase_window_position(
    snapshot: SensorSnapshot,
    target_x: float,
    target_y: float,
    speed: float,
    delta_time: float,
) -> tuple[float, float]:
    """Return the next top-left window position while chasing with its centre.

    ``target_x`` and ``target_y`` denote the desired window centre.  The
    returned coordinates are suitable for the existing top-left Tk geometry.
    """

    if snapshot.pet_width > snapshot.screen_width:
        raise ValueError("pet width must not exceed screen width")
    if snapshot.pet_height > snapshot.screen_height:
        raise ValueError("pet height must not exceed screen height")

    half_width = snapshot.pet_width / 2
    half_height = snapshot.pet_height / 2
    current_center_x = snapshot.pet_x + half_width
    current_center_y = snapshot.pet_y + half_height
    bounds = PositionBounds(
        min_x=snapshot.screen_left + half_width,
        min_y=snapshot.screen_top + half_height,
        max_x=snapshot.screen_right - half_width,
        max_y=snapshot.screen_bottom - half_height,
    )
    next_center_x, next_center_y = chase_target(
        current_center_x,
        current_center_y,
        target_x,
        target_y,
        speed,
        delta_time,
        bounds=bounds,
    )
    return next_center_x - half_width, next_center_y - half_height
