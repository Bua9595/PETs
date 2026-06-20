from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PetState:
    name: str
    look: str
    hatched: bool = False
    level: int = 1
    experience: int = 0
    hunger: int = 5
    energy: int = 5
    attributes: Dict[str, int] = field(default_factory=lambda: {
        "strength": 1,
        "stamina": 1,
        "charisma": 1,
        "agility": 1,
    })
    gear: str | None = None
    active_skills: List[str] = field(default_factory=list)
    history: List[str] = field(default_factory=list)
    state: str = "egg"

    def record(self, event: str):
        self.history.append(event)

    def stats(self) -> str:
        return ", ".join(f"{k}={v}" for k, v in self.attributes.items())

    def gain_experience(self, amount: int):
        self.experience += amount
        self.record(f"exp+{amount}")
        while self.experience >= self.level * 10:
            self.experience -= self.level * 10
            self.level += 1
            self.record(f"levelup:{self.level}")
            print(f"{self.name} erreicht Level {self.level}!")

    def change_hunger(self, amount: int):
        self.hunger = max(0, min(10, self.hunger + amount))
        self.record(f"hunger{amount:+d}")

    def change_energy(self, amount: int):
        self.energy = max(0, min(10, self.energy + amount))
        self.record(f"energy{amount:+d}")
