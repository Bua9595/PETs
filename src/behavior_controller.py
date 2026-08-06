"""Headless selection logic for the existing desktop-pet behaviour."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Sequence


@dataclass(frozen=True)
class CategoryDefinition:
    """Read-only category data for non-selection consumers such as menus."""

    id: str
    label: str
    weight: int
    animations: tuple[str, ...]


class BehaviorController:
    """Choose animations using the existing ``desktop_behavior`` schema.

    This class deliberately owns selection state only.  Rendering, playback,
    movement, Tk bindings and decision scheduling remain the responsibility of
    ``DesktopPet``.
    """

    def __init__(
        self,
        desktop_behavior: dict[str, Any],
        available_animations: Sequence[str],
        *,
        rng: Any = random,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.desktop_behavior = desktop_behavior
        self.available_animations = list(available_animations)
        self.rng = rng
        self.clock = clock
        self.current_category: str | None = None
        self.category_attempts = 0
        self.category_switch_goal = self._random_category_switch_goal()
        self.animation_cooldown_seconds = float(self.desktop_behavior.get("animation_cooldown_seconds", 60))
        self.animation_cooldowns: dict[str, float] = {}

    def record_animation_played(self, animation: str) -> None:
        """Record the same category and cooldown side effects as old ``play``."""

        self.current_category = self._category_for_animation(animation)
        self.animation_cooldowns[animation] = self.clock() + max(0.0, self.animation_cooldown_seconds)

    def choose_next_action(self, force: bool = False) -> str:
        """Return the next animation using the original candidate/fallback order."""

        default_choices = [
            ("idle", 24), ("blink", 8), ("walk", 12), ("run", 18), ("wave", 9),
            ("happy", 7), ("jump", 7), ("sit", 5), ("rest", 4), ("curious", 4),
            ("rubber_stretch", 3), ("rubber_punch", 3), ("rubber_reach", 2),
            ("gear2", 2), ("gear3", 1), ("gear4", 1), ("gear5", 1), ("failed", 2),
        ]
        configured_choices = self.desktop_behavior.get("choices", default_choices)
        choices = self._normalized_choices(configured_choices)
        category_defs = self._available_category_definitions()
        active_category = self._pick_active_category(category_defs, force=force)
        if active_category:
            scoped_choices = [(name, weight) for name, weight in choices if name in active_category["animations"]]
            if not scoped_choices:
                scoped_choices = choices
        else:
            scoped_choices = choices
        available_choices = self._available_non_cooldown_choices(scoped_choices)
        if not available_choices:
            available_choices = self._available_non_cooldown_choices(choices)
        if not available_choices:
            available_choices = scoped_choices or choices
        return self.rng.choices(
            [name for name, _weight in available_choices],
            [weight for _name, weight in available_choices],
        )[0]

    def record_choice_made(self) -> None:
        """Record the old post-selection category attempt increment."""

        self.category_attempts += 1

    def available_category_definitions(self) -> tuple[CategoryDefinition, ...]:
        """Expose the existing normalized categories without exposing mutable state."""

        return tuple(
            CategoryDefinition(
                id=category["id"],
                label=category["label"],
                weight=category["weight"],
                animations=tuple(category["animations"]),
            )
            for category in self._available_category_definitions()
        )

    def _available_non_cooldown_choices(self, choices):
        now = self.clock()
        return [(name, weight) for name, weight in choices if self.animation_cooldowns.get(name, 0.0) <= now]

    def _normalized_choices(self, configured_choices):
        choices = []
        for item in configured_choices:
            if isinstance(item, dict):
                choices.append((str(item.get("animation", "idle")), int(item.get("weight", 1))))
            else:
                name, weight = item
                choices.append((str(name), int(weight)))
        return [(name, weight) for name, weight in choices if name in self.available_animations]

    def _random_category_switch_goal(self) -> int:
        behavior = self.desktop_behavior.get("category_behavior", {})
        minimum = int(behavior.get("attempts_before_switch_min", 2))
        maximum = int(behavior.get("attempts_before_switch_max", max(minimum, 4)))
        if maximum < minimum:
            maximum = minimum
        return self.rng.randint(minimum, maximum)

    def _available_category_definitions(self):
        raw_behavior = self.desktop_behavior.get("category_behavior", {})
        raw_categories = raw_behavior.get("categories")
        if raw_categories:
            category_defs = self._normalize_category_definitions(raw_categories)
            if category_defs:
                return category_defs
        return self._default_category_definitions()

    def _normalize_category_definitions(self, raw_categories):
        categories = []
        for index, raw in enumerate(raw_categories):
            animations = [str(name) for name in raw.get("animations", []) if str(name) in self.available_animations]
            if not animations:
                continue
            categories.append(
                {
                    "id": str(raw.get("id", f"category_{index}")),
                    "label": str(raw.get("label", raw.get("id", f"Category {index + 1}"))),
                    "weight": max(1, int(raw.get("weight", 1))),
                    "animations": animations,
                }
            )
        return categories

    def _default_category_definitions(self):
        buckets = {
            "core": {"label": "Core", "weight": 12, "animations": []},
            "movement": {"label": "Movement", "weight": 10, "animations": []},
            "rest": {"label": "Rest", "weight": 6, "animations": []},
            "desktop": {"label": "Desktop", "weight": 6, "animations": []},
            "social": {"label": "Social", "weight": 8, "animations": []},
            "power": {"label": "Power", "weight": 6, "animations": []},
            "special": {"label": "Special", "weight": 4, "animations": []},
        }
        for animation in self.available_animations:
            bucket_id = self._heuristic_category_id(animation)
            buckets[bucket_id]["animations"].append(animation)
        return [
            {"id": key, "label": value["label"], "weight": value["weight"], "animations": value["animations"]}
            for key, value in buckets.items()
            if value["animations"]
        ]

    def _heuristic_category_id(self, animation: str) -> str:
        name = animation.lower()
        if name.startswith("gear") or name.startswith("rubber") or name in {"failed", "ko", "ko_ghost", "eat"}:
            return "power"
        if any(token in name for token in ("walk", "run", "jump", "drag", "cursor", "follow")):
            return "movement"
        if any(token in name for token in ("rest", "nap", "sleep", "sit", "drink")):
            return "rest"
        if any(token in name for token in ("peek", "hang", "folder")):
            return "desktop"
        if any(token in name for token in ("phone", "chat", "gaming", "laptop", "celebrate", "pet_play", "greet_pet")):
            return "social"
        if any(token in name for token in ("idle", "blink", "wave", "wink", "happy", "shy", "surprised", "confused", "thinking", "curious", "heart", "peace", "facepalm", "mischief")):
            return "core"
        return "special"

    def _category_for_animation(self, animation: str) -> str | None:
        for category in self._available_category_definitions():
            if animation in category["animations"]:
                return category["id"]
        return None

    def _pick_active_category(self, category_defs, force: bool = False):
        if not category_defs:
            return None
        by_id = {category["id"]: category for category in category_defs}
        behavior = self.desktop_behavior.get("category_behavior", {})
        switch_probability = float(behavior.get("switch_probability", 0.4))
        if self.current_category not in by_id:
            preferred = str(behavior.get("initial_category", category_defs[0]["id"]))
            self.current_category = preferred if preferred in by_id else self._weighted_category_choice(category_defs)
            self.category_attempts = 0
            self.category_switch_goal = self._random_category_switch_goal()
        elif self.category_attempts >= self.category_switch_goal and (force or self.rng.random() < switch_probability):
            next_category = self._weighted_category_choice(category_defs, exclude=self.current_category)
            if next_category:
                self.current_category = next_category
            self.category_attempts = 0
            self.category_switch_goal = self._random_category_switch_goal()
        return by_id.get(self.current_category)

    def _weighted_category_choice(self, category_defs, exclude: str | None = None) -> str | None:
        options = [category for category in category_defs if category["id"] != exclude]
        if not options:
            options = category_defs
        if not options:
            return None
        return self.rng.choices([category["id"] for category in options], [category["weight"] for category in options])[0]
