from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from chase_target_adapter import calculate_chase_window_position
from desktop_pet import DesktopPet
from sensor_snapshot import SensorSnapshot


class ChaseTargetAdapterTests(unittest.TestCase):
    def _snapshot(self, **overrides) -> SensorSnapshot:
        values = {
            "cursor_x": 0,
            "cursor_y": 0,
            "pet_x": 10,
            "pet_y": 20,
            "pet_width": 20,
            "pet_height": 10,
            "screen_x": 0,
            "screen_y": 0,
            "screen_width": 100,
            "screen_height": 80,
        }
        values.update(overrides)
        return SensorSnapshot(**values)

    def assertPositionAlmostEqual(self, actual, expected) -> None:
        self.assertAlmostEqual(actual[0], expected[0])
        self.assertAlmostEqual(actual[1], expected[1])

    def test_current_window_centre_and_reached_target_return_same_top_left_position(self) -> None:
        snapshot = self._snapshot()
        self.assertPositionAlmostEqual(calculate_chase_window_position(snapshot, 20, 25, 10, 1), (10, 20))

    def test_target_coordinates_are_interpreted_as_window_centre(self) -> None:
        snapshot = self._snapshot()
        self.assertPositionAlmostEqual(calculate_chase_window_position(snapshot, 40, 25, 5, 1), (15, 20))

    def test_moves_horizontally_and_vertically(self) -> None:
        snapshot = self._snapshot()
        self.assertPositionAlmostEqual(calculate_chase_window_position(snapshot, 40, 25, 5, 1), (15, 20))
        self.assertPositionAlmostEqual(calculate_chase_window_position(snapshot, 20, 45, 5, 1), (10, 25))

    def test_moves_diagonally_without_overshooting(self) -> None:
        snapshot = self._snapshot()
        self.assertPositionAlmostEqual(
            calculate_chase_window_position(snapshot, 40, 45, 5, 1),
            (10 + 5 / (2**0.5), 20 + 5 / (2**0.5)),
        )
        self.assertPositionAlmostEqual(calculate_chase_window_position(snapshot, 23, 29, 100, 1), (13, 24))

    def test_zero_and_negative_delta_time_and_zero_speed_keep_top_left_position(self) -> None:
        snapshot = self._snapshot()
        for speed, delta_time in ((0, 1), (5, 0), (5, -1)):
            with self.subTest(speed=speed, delta_time=delta_time):
                self.assertPositionAlmostEqual(
                    calculate_chase_window_position(snapshot, 90, 70, speed, delta_time), (10, 20)
                )

    def test_clamps_left_right_top_and_bottom_targets_using_pet_size(self) -> None:
        snapshot = self._snapshot()
        self.assertPositionAlmostEqual(calculate_chase_window_position(snapshot, -50, 25, 100, 1), (0, 20))
        self.assertPositionAlmostEqual(calculate_chase_window_position(snapshot, 500, 25, 100, 1), (80, 20))
        self.assertPositionAlmostEqual(calculate_chase_window_position(snapshot, 20, -50, 100, 1), (10, 0))
        self.assertPositionAlmostEqual(calculate_chase_window_position(snapshot, 20, 500, 100, 1), (10, 70))

    def test_clamps_diagonal_target_at_screen_corner(self) -> None:
        self.assertPositionAlmostEqual(calculate_chase_window_position(self._snapshot(), -50, -50, 100, 1), (0, 0))

    def test_respects_nonzero_screen_origin(self) -> None:
        snapshot = self._snapshot(pet_x=-50, pet_y=70, screen_x=-100, screen_y=50)
        self.assertPositionAlmostEqual(calculate_chase_window_position(snapshot, -500, -500, 100, 1), (-100, 50))

    def test_outside_start_is_not_teleported(self) -> None:
        snapshot = self._snapshot(pet_x=-10)
        self.assertPositionAlmostEqual(calculate_chase_window_position(snapshot, 50, 25, 5, 1), (-5, 20))

    def test_fractional_values_are_not_rounded(self) -> None:
        snapshot = self._snapshot(pet_x=0.25, pet_y=1.5, pet_width=1.0, pet_height=1.0)
        self.assertPositionAlmostEqual(calculate_chase_window_position(snapshot, 1.75, 2.0, 0.2, 1), (0.45, 1.5))

    def test_rejects_pet_wider_or_taller_than_screen(self) -> None:
        with self.assertRaisesRegex(ValueError, "width"):
            calculate_chase_window_position(self._snapshot(pet_width=101), 0, 0, 1, 1)
        with self.assertRaisesRegex(ValueError, "height"):
            calculate_chase_window_position(self._snapshot(pet_height=81), 0, 0, 1, 1)

    def test_does_not_mutate_snapshot(self) -> None:
        snapshot = self._snapshot()
        self.assertEqual(snapshot, self._snapshot())
        calculate_chase_window_position(snapshot, 90, 70, 10, 1)
        self.assertEqual(snapshot, self._snapshot())

    def test_desktop_pet_method_only_delegates_without_a_tk_instance(self) -> None:
        snapshot = self._snapshot()
        with patch("desktop_pet.calculate_chase_window_position_from_snapshot", return_value=(1.25, 2.5)) as adapter:
            result = DesktopPet.calculate_chase_window_position(object(), snapshot, 30, 40, 5, 0.5)
        self.assertEqual(result, (1.25, 2.5))
        adapter.assert_called_once_with(snapshot, 30, 40, 5, 0.5)

    def test_manual_move_applies_exact_result_after_one_calculation(self) -> None:
        snapshot = self._snapshot()
        pet = DesktopPet.__new__(DesktopPet)
        pet.x = -1
        pet.y = -2
        pet.direction = 1
        pet.next_decision_frames = 12
        calculation_calls = []
        move_calls = []

        def calculate(received_snapshot, target_x, target_y, speed, delta_time):
            calculation_calls.append((received_snapshot, target_x, target_y, speed, delta_time))
            return 1.25, 2.5

        def move_window():
            move_calls.append((pet.x, pet.y))

        def capture_snapshot():
            raise AssertionError("capture_sensor_snapshot must not be called")

        pet.calculate_chase_window_position = calculate
        pet._move_window = move_window
        pet.capture_sensor_snapshot = capture_snapshot

        result = pet.move_chase_window_once(snapshot, 30.5, 40.25, 5.75, 0.5)

        self.assertEqual(result, (1.25, 2.5))
        self.assertEqual((pet.x, pet.y), (1.25, 2.5))
        self.assertEqual(calculation_calls, [(snapshot, 30.5, 40.25, 5.75, 0.5)])
        self.assertEqual(move_calls, [(1.25, 2.5)])
        self.assertEqual((pet.direction, pet.next_decision_frames), (1, 12))
        self.assertEqual(snapshot, self._snapshot())

    def test_manual_move_keeps_state_and_window_untouched_on_calculation_error(self) -> None:
        snapshot = self._snapshot()
        pet = DesktopPet.__new__(DesktopPet)
        pet.x = 11.5
        pet.y = 12.5
        move_calls = []

        def fail_calculation(*_args):
            raise ValueError("invalid chase input")

        pet.calculate_chase_window_position = fail_calculation
        pet._move_window = lambda: move_calls.append(True)

        with self.assertRaisesRegex(ValueError, "invalid chase input"):
            pet.move_chase_window_once(snapshot, 30, 40, 5, 1)

        self.assertEqual((pet.x, pet.y), (11.5, 12.5))
        self.assertEqual(move_calls, [])
        self.assertEqual(snapshot, self._snapshot())


if __name__ == "__main__":
    unittest.main()
