"""Immutable, read-only desktop geometry captured from the runtime."""

from __future__ import annotations

from dataclasses import dataclass


LEFT = "left"
RIGHT = "right"
TOP = "top"
BOTTOM = "bottom"


@dataclass(frozen=True)
class SensorSnapshot:
    """A point-in-time view using top-left origins and exclusive right/bottom edges."""

    cursor_x: int
    cursor_y: int
    pet_x: int
    pet_y: int
    pet_width: int
    pet_height: int
    screen_x: int
    screen_y: int
    screen_width: int
    screen_height: int

    @property
    def pet_left(self) -> int:
        return self.pet_x

    @property
    def pet_right(self) -> int:
        return self.pet_x + self.pet_width

    @property
    def pet_top(self) -> int:
        return self.pet_y

    @property
    def pet_bottom(self) -> int:
        return self.pet_y + self.pet_height

    @property
    def screen_left(self) -> int:
        return self.screen_x

    @property
    def screen_right(self) -> int:
        return self.screen_x + self.screen_width

    @property
    def screen_top(self) -> int:
        return self.screen_y

    @property
    def screen_bottom(self) -> int:
        return self.screen_y + self.screen_height

    def active_screen_edges(self, margin: float = 0) -> frozenset[str]:
        """Return the screen edges reached by the complete pet rectangle."""

        if margin < 0:
            raise ValueError("margin must be non-negative")
        edges: set[str] = set()
        if self.pet_left <= self.screen_left + margin:
            edges.add(LEFT)
        if self.pet_right >= self.screen_right - margin:
            edges.add(RIGHT)
        if self.pet_top <= self.screen_top + margin:
            edges.add(TOP)
        if self.pet_bottom >= self.screen_bottom - margin:
            edges.add(BOTTOM)
        return frozenset(edges)
