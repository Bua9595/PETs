from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chase_target import PositionBounds, chase_target


class ChaseTargetTests(unittest.TestCase):
    def assertPositionAlmostEqual(self, actual, expected) -> None:
        self.assertAlmostEqual(actual[0], expected[0])
        self.assertAlmostEqual(actual[1], expected[1])

    def test_returns_current_position_when_target_is_reached(self) -> None:
        self.assertPositionAlmostEqual(chase_target(3, 4, 3, 4, 10, 1), (3, 4))

    def test_moves_horizontally_left_and_right(self) -> None:
        self.assertPositionAlmostEqual(chase_target(10, 2, 0, 2, 3, 1), (7, 2))
        self.assertPositionAlmostEqual(chase_target(0, 2, 10, 2, 3, 1), (3, 2))

    def test_moves_vertically_up_and_down(self) -> None:
        self.assertPositionAlmostEqual(chase_target(2, 10, 2, 0, 3, 1), (2, 7))
        self.assertPositionAlmostEqual(chase_target(2, 0, 2, 10, 3, 1), (2, 3))

    def test_diagonal_movement_uses_euclidean_speed(self) -> None:
        position = chase_target(0, 0, 3, 4, 2, 1)
        self.assertPositionAlmostEqual(position, (1.2, 1.6))
        self.assertAlmostEqual(math.hypot(*position), 2)

    def test_does_not_overshoot_and_reaches_exact_target_at_equal_distance(self) -> None:
        self.assertPositionAlmostEqual(chase_target(0, 0, 3, 4, 10, 1), (3, 4))
        self.assertPositionAlmostEqual(chase_target(0, 0, 3, 4, 5, 1), (3, 4))

    def test_zero_or_negative_delta_time_and_zero_speed_do_not_move(self) -> None:
        expected = (1, 2)
        self.assertPositionAlmostEqual(chase_target(1, 2, 8, 9, 0, 1), expected)
        self.assertPositionAlmostEqual(chase_target(1, 2, 8, 9, 3, 0), expected)
        self.assertPositionAlmostEqual(chase_target(1, 2, 8, 9, 3, -1), expected)

    def test_rejects_negative_speed(self) -> None:
        with self.assertRaisesRegex(ValueError, "speed must be non-negative"):
            chase_target(0, 0, 1, 1, -1, 1)

    def test_movement_is_unbounded_without_bounds(self) -> None:
        self.assertPositionAlmostEqual(chase_target(0, 0, 20, 30, 100, 1), (20, 30))

    def test_reaches_target_inside_explicit_bounds(self) -> None:
        bounds = PositionBounds(0, 0, 10, 10)
        self.assertPositionAlmostEqual(chase_target(0, 0, 8, 6, 20, 1, bounds=bounds), (8, 6))

    def test_clamps_outside_target_on_both_axes(self) -> None:
        bounds = PositionBounds(0, 0, 10, 10)
        self.assertPositionAlmostEqual(chase_target(5, 5, -3, 30, 100, 1, bounds=bounds), (0, 10))

    def test_moves_diagonally_to_clamped_target(self) -> None:
        bounds = PositionBounds(0, 0, 10, 5)
        position = chase_target(0, 0, 30, 30, 5, 1, bounds=bounds)
        self.assertPositionAlmostEqual(position, (math.sqrt(20), math.sqrt(5)))

    def test_outside_current_position_is_not_teleported(self) -> None:
        bounds = PositionBounds(0, 0, 10, 10)
        self.assertPositionAlmostEqual(chase_target(-5, 5, 5, 5, 1, 1, bounds=bounds), (-4, 5))

    def test_nonpositive_delta_time_keeps_outside_current_position_with_bounds(self) -> None:
        bounds = PositionBounds(0, 0, 10, 10)
        self.assertPositionAlmostEqual(chase_target(-5, 12, 100, -100, 3, 0, bounds=bounds), (-5, 12))
        self.assertPositionAlmostEqual(chase_target(-5, 12, 100, -100, 3, -1, bounds=bounds), (-5, 12))

    def test_rejects_inverted_bounds(self) -> None:
        with self.assertRaisesRegex(ValueError, "min_x"):
            PositionBounds(2, 0, 1, 1)
        with self.assertRaisesRegex(ValueError, "min_y"):
            PositionBounds(0, 2, 1, 1)

    def test_preserves_fractional_inputs_without_integer_rounding(self) -> None:
        self.assertPositionAlmostEqual(chase_target(0.25, 1.5, 1.25, 1.5, 0.2, 1), (0.45, 1.5))

    def test_rejects_non_finite_inputs_and_bounds(self) -> None:
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(position=value):
                with self.assertRaisesRegex(ValueError, "current_x"):
                    chase_target(value, 0, 1, 1, 1, 1)
            with self.subTest(speed=value):
                with self.assertRaisesRegex(ValueError, "speed"):
                    chase_target(0, 0, 1, 1, value, 1)
            with self.subTest(delta_time=value):
                with self.assertRaisesRegex(ValueError, "delta_time"):
                    chase_target(0, 0, 1, 1, 1, value)
            with self.subTest(bounds=value):
                with self.assertRaisesRegex(ValueError, "bounds.min_x"):
                    PositionBounds(value, 0, 1, 1)


if __name__ == "__main__":
    unittest.main()
