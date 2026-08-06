from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from behavior_controller import BehaviorController
from desktop_pet import DesktopPet


class RecordingMenu:
    def __init__(self, _root, tearoff=False) -> None:
        self.tearoff = tearoff
        self.entries: list[tuple] = []

    def add_command(self, **kwargs) -> None:
        self.entries.append(("command", kwargs["label"]))

    def add_cascade(self, **kwargs) -> None:
        self.entries.append(("cascade", kwargs["label"], kwargs["menu"]))

    def add_separator(self) -> None:
        self.entries.append(("separator",))

    def index(self, _index) -> int | None:
        return len(self.entries) - 1 if self.entries else None


class AnimatorDouble:
    available_animations = ["idle", "run"]


class RootDouble:
    def destroy(self) -> None:
        pass


class DesktopMenuTests(unittest.TestCase):
    def test_build_menu_uses_read_only_controller_categories(self) -> None:
        behavior = {
            "menu_states": [
                {"label": "Idle", "animation": "idle"},
                {"label": "Run", "animation": "run"},
            ],
            "category_behavior": {
                "categories": [
                    {"id": "core", "label": "Core", "weight": 1, "animations": ["idle"]},
                ]
            },
        }
        controller = BehaviorController(behavior, AnimatorDouble.available_animations)
        definitions = controller.available_category_definitions()
        self.assertEqual(definitions[0].id, "core")
        self.assertEqual(definitions[0].label, "Core")
        self.assertEqual(definitions[0].animations, ("idle",))

        pet = DesktopPet.__new__(DesktopPet)
        pet.root = RootDouble()
        pet.desktop_behavior = behavior
        pet.animator = AnimatorDouble()
        pet.behavior_controller = controller
        pet.play = lambda _animation: None

        with patch("desktop_pet.Menu", RecordingMenu):
            pet._build_menu()

        cascades = [entry for entry in pet.menu.entries if entry[0] == "cascade"]
        self.assertEqual([(entry[0], entry[1]) for entry in cascades], [("cascade", "Core")])
        self.assertIn(("command", "Idle"), cascades[0][2].entries)
        self.assertIn(("command", "Run"), pet.menu.entries)


if __name__ == "__main__":
    unittest.main()
