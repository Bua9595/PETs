from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from behavior_controller import BehaviorController


class FakeRandom:
    def __init__(self, *, choice_index: int = 0, random_value: float = 0.0, randint_value: int = 2) -> None:
        self.choice_index = choice_index
        self.random_value = random_value
        self.randint_value = randint_value
        self.choice_calls: list[tuple[list, list]] = []

    def choices(self, population, weights):
        self.choice_calls.append((list(population), list(weights)))
        return [population[self.choice_index]]

    def random(self) -> float:
        return self.random_value

    def randint(self, _minimum: int, _maximum: int) -> int:
        return self.randint_value


class MutableClock:
    def __init__(self, value: float = 100.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


class BehaviorControllerTests(unittest.TestCase):
    def _behavior(self, choices, categories) -> dict:
        return {
            "initial_animation": "idle",
            "animation_cooldown_seconds": 10,
            "choices": choices,
            "category_behavior": {
                "initial_category": "core",
                "switch_probability": 0.4,
                "attempts_before_switch_min": 2,
                "attempts_before_switch_max": 2,
                "categories": categories,
            },
        }

    def _controller(self, behavior, *, rng=None, clock=None) -> BehaviorController:
        return BehaviorController(
            behavior,
            ["idle", "blink", "run", "missing_from_pack"],
            rng=rng or FakeRandom(),
            clock=clock or MutableClock(),
        )

    def test_selects_only_candidates_in_active_category_and_forwards_weights(self) -> None:
        rng = FakeRandom(choice_index=1)
        behavior = self._behavior(
            [{"animation": "idle", "weight": 2}, {"animation": "blink", "weight": 7}, {"animation": "run", "weight": 99}],
            [{"id": "core", "animations": ["idle", "blink"]}, {"id": "movement", "animations": ["run"]}],
        )
        controller = self._controller(behavior, rng=rng)

        self.assertEqual(controller.choose_next_action(), "blink")
        self.assertEqual(rng.choice_calls[-1], (["idle", "blink"], [2, 7]))

    def test_empty_active_category_falls_back_to_all_configured_choices(self) -> None:
        rng = FakeRandom()
        behavior = self._behavior(
            [{"animation": "idle", "weight": 3}],
            [{"id": "core", "animations": ["run"]}, {"id": "movement", "animations": ["idle"]}],
        )
        controller = self._controller(behavior, rng=rng)
        controller.record_animation_played("run")
        controller.current_category = "core"

        self.assertEqual(controller.choose_next_action(), "idle")
        self.assertEqual(rng.choice_calls[-1], (["idle"], [3]))

    def test_cooldown_excludes_animation_when_another_candidate_is_available(self) -> None:
        clock = MutableClock()
        rng = FakeRandom()
        behavior = self._behavior(
            [{"animation": "idle", "weight": 2}, {"animation": "blink", "weight": 5}],
            [{"id": "core", "animations": ["idle", "blink"]}],
        )
        controller = self._controller(behavior, rng=rng, clock=clock)
        controller.record_animation_played("idle")

        self.assertEqual(controller.choose_next_action(), "blink")
        self.assertEqual(rng.choice_calls[-1], (["blink"], [5]))

    def test_cooldown_expires_with_injected_clock(self) -> None:
        clock = MutableClock()
        rng = FakeRandom()
        behavior = self._behavior(
            [{"animation": "idle", "weight": 2}, {"animation": "blink", "weight": 5}],
            [{"id": "core", "animations": ["idle", "blink"]}],
        )
        controller = self._controller(behavior, rng=rng, clock=clock)
        controller.record_animation_played("idle")
        clock.value = 110.0

        controller.choose_next_action()
        self.assertEqual(rng.choice_calls[-1], (["idle", "blink"], [2, 5]))

    def test_only_valid_candidate_is_selected(self) -> None:
        rng = FakeRandom()
        behavior = self._behavior(
            [{"animation": "missing", "weight": 99}, {"animation": "run", "weight": 4}],
            [{"id": "core", "animations": ["run"]}],
        )
        controller = self._controller(behavior, rng=rng)
        controller.record_animation_played("run")

        self.assertEqual(controller.choose_next_action(), "run")
        self.assertEqual(rng.choice_calls[-1], (["run"], [4]))

    def test_all_unavailable_configured_choices_keep_existing_index_error(self) -> None:
        behavior = self._behavior(
            [{"animation": "missing", "weight": 1}],
            [{"id": "core", "animations": ["idle"]}],
        )
        controller = self._controller(behavior)
        controller.record_animation_played("idle")

        with self.assertRaises(IndexError):
            controller.choose_next_action()

    def test_existing_ruffy_and_pet2_configurations_are_accepted_unchanged(self) -> None:
        for pet_id in ("ruffy", "pet2_chibi"):
            manifest = json.loads((PROJECT_ROOT / "assets" / "pets" / pet_id / "manifest.json").read_text(encoding="utf-8"))
            behavior = manifest["desktop_behavior"]
            controller = BehaviorController(behavior, manifest["animations"].keys(), rng=FakeRandom())
            self.assertEqual(controller.desktop_behavior, behavior)
            self.assertTrue(controller._available_category_definitions())


if __name__ == "__main__":
    unittest.main()
