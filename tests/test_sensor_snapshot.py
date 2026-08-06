from __future__ import annotations

from dataclasses import FrozenInstanceError
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sensor_snapshot import BOTTOM, LEFT, RIGHT, TOP, SensorSnapshot


class SensorSnapshotTests(unittest.TestCase):
    def _snapshot(self, **overrides) -> SensorSnapshot:
        values = {
            "cursor_x": 150,
            "cursor_y": 160,
            "pet_x": 100,
            "pet_y": 100,
            "pet_width": 20,
            "pet_height": 30,
            "screen_x": 0,
            "screen_y": 0,
            "screen_width": 400,
            "screen_height": 300,
        }
        values.update(overrides)
        return SensorSnapshot(**values)

    def test_stores_coordinates_without_clamping(self) -> None:
        snapshot = self._snapshot(cursor_x=-25, cursor_y=999, pet_x=-10, pet_y=350)
        self.assertEqual((snapshot.cursor_x, snapshot.cursor_y), (-25, 999))
        self.assertEqual((snapshot.pet_x, snapshot.pet_y), (-10, 350))

    def test_calculates_pet_boundaries(self) -> None:
        snapshot = self._snapshot()
        self.assertEqual((snapshot.pet_left, snapshot.pet_right, snapshot.pet_top, snapshot.pet_bottom), (100, 120, 100, 130))

    def test_calculates_screen_boundaries_with_nonzero_origin(self) -> None:
        snapshot = self._snapshot(screen_x=-200, screen_y=50, screen_width=400, screen_height=300)
        self.assertEqual((snapshot.screen_left, snapshot.screen_right, snapshot.screen_top, snapshot.screen_bottom), (-200, 200, 50, 350))

    def test_middle_pet_has_no_active_edge(self) -> None:
        self.assertEqual(self._snapshot().active_screen_edges(), frozenset())

    def test_exact_hits_at_each_edge(self) -> None:
        cases = {
            LEFT: {"pet_x": 0},
            RIGHT: {"pet_x": 380},
            TOP: {"pet_y": 0},
            BOTTOM: {"pet_y": 270},
        }
        for edge, values in cases.items():
            with self.subTest(edge=edge):
                self.assertEqual(self._snapshot(**values).active_screen_edges(), frozenset({edge}))

    def test_margin_includes_close_edge_but_not_position_outside_margin(self) -> None:
        self.assertEqual(self._snapshot(pet_x=5).active_screen_edges(margin=5), frozenset({LEFT}))
        self.assertEqual(self._snapshot(pet_x=6).active_screen_edges(margin=5), frozenset())

    def test_partially_outside_pet_reaches_corresponding_edges(self) -> None:
        self.assertEqual(self._snapshot(pet_x=-1, pet_y=280).active_screen_edges(), frozenset({LEFT, BOTTOM}))

    def test_corner_can_reach_two_edges(self) -> None:
        self.assertEqual(self._snapshot(pet_x=380, pet_y=270).active_screen_edges(), frozenset({RIGHT, BOTTOM}))

    def test_oversized_pet_can_reach_opposite_edges(self) -> None:
        snapshot = self._snapshot(pet_x=-10, pet_y=-5, pet_width=420, pet_height=310)
        self.assertEqual(snapshot.active_screen_edges(), frozenset({LEFT, RIGHT, TOP, BOTTOM}))

    def test_nonzero_origin_partially_outside_is_not_clamped(self) -> None:
        snapshot = self._snapshot(pet_x=-210, pet_y=40, screen_x=-200, screen_y=50)
        self.assertEqual(snapshot.active_screen_edges(), frozenset({LEFT, TOP}))
        self.assertEqual(snapshot.pet_x, -210)

    def test_negative_margin_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "margin must be non-negative"):
            self._snapshot().active_screen_edges(margin=-0.1)

    def test_snapshot_and_edge_result_are_immutable(self) -> None:
        snapshot = self._snapshot()
        with self.assertRaises(FrozenInstanceError):
            snapshot.pet_x = 1
        with self.assertRaises(AttributeError):
            snapshot.active_screen_edges().add(LEFT)


if __name__ == "__main__":
    unittest.main()
