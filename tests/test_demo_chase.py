from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from desktop_pet import DesktopPet, main
from sensor_snapshot import SensorSnapshot


class DemoChaseTests(unittest.TestCase):
    def _snapshot(self) -> SensorSnapshot:
        return SensorSnapshot(
            cursor_x=123.5,
            cursor_y=456.25,
            pet_x=10,
            pet_y=20,
            pet_width=30,
            pet_height=40,
            screen_x=0,
            screen_y=0,
            screen_width=800,
            screen_height=600,
        )

    def test_demo_captures_once_then_moves_once_with_cursor_as_centre_target(self) -> None:
        snapshot = self._snapshot()
        pet = DesktopPet.__new__(DesktopPet)
        calls = []

        def capture():
            calls.append("capture")
            return snapshot

        def move(received_snapshot, target_x, target_y, speed, delta_time):
            calls.append(("move", received_snapshot, target_x, target_y, speed, delta_time))
            return 1.25, 2.5

        pet.capture_sensor_snapshot = capture
        pet.move_chase_window_once = move

        result = pet.demo_chase_cursor_once(300.75, 0.125)

        self.assertEqual(result, (1.25, 2.5))
        self.assertEqual(calls, ["capture", ("move", snapshot, 123.5, 456.25, 300.75, 0.125)])
        self.assertEqual(snapshot, self._snapshot())

    def test_snapshot_error_prevents_movement(self) -> None:
        pet = DesktopPet.__new__(DesktopPet)
        movement_calls = []

        def fail_capture():
            raise RuntimeError("snapshot failure")

        pet.capture_sensor_snapshot = fail_capture
        pet.move_chase_window_once = lambda *_args: movement_calls.append(True)

        with self.assertRaisesRegex(RuntimeError, "snapshot failure"):
            pet.demo_chase_cursor_once(300, 0.1)
        self.assertEqual(movement_calls, [])

    def test_move_error_is_propagated_without_retry(self) -> None:
        pet = DesktopPet.__new__(DesktopPet)
        snapshot = self._snapshot()
        capture_calls = []
        movement_calls = []

        def capture():
            capture_calls.append(True)
            return snapshot

        def fail_move(*_args):
            movement_calls.append(True)
            raise ValueError("movement failure")

        pet.capture_sensor_snapshot = capture
        pet.move_chase_window_once = fail_move

        with self.assertRaisesRegex(ValueError, "movement failure"):
            pet.demo_chase_cursor_once(300, 0.1)
        self.assertEqual(capture_calls, [True])
        self.assertEqual(movement_calls, [True])

    def test_cli_without_demo_option_does_not_call_demo(self) -> None:
        with patch("desktop_pet.DesktopPet") as pet_class, patch.object(sys, "argv", ["desktop_pet.py", "--pet", "ruffy"]):
            main()
        pet_class.return_value.demo_chase_cursor_once.assert_not_called()
        pet_class.return_value.run.assert_called_once_with()

    def test_cli_demo_option_calls_demo_once_with_both_explicit_values(self) -> None:
        arguments = ["desktop_pet.py", "--pet", "ruffy", "--demo-chase-cursor-once", "300.5", "0.125"]
        with patch("desktop_pet.DesktopPet") as pet_class, patch.object(sys, "argv", arguments):
            main()
        pet_class.return_value.demo_chase_cursor_once.assert_called_once_with(300.5, 0.125)
        pet_class.return_value.run.assert_called_once_with()

    def test_list_pets_exits_before_pet_creation_or_demo(self) -> None:
        arguments = ["desktop_pet.py", "--list-pets", "--demo-chase-cursor-once", "300", "0.1"]
        with patch("desktop_pet.DesktopPet") as pet_class, patch.object(sys, "argv", arguments):
            main()
        pet_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
