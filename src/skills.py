from typing import Dict, Any, List


class Skill:
    def __init__(self, name: str, description: str, effects: Dict[str, Any]):
        self.name = name
        self.description = description
        self.effects = effects

    def apply(self, pet: "Pet"):
        for k, v in self.effects.items():
            if k in pet.state.attributes:
                pet.state.attributes[k] = pet.state.attributes.get(k, 0) + v
            else:
                setattr(pet.state, k, getattr(pet.state, k, 0) + v)


class SkillManager:
    def __init__(self):
        self._skills: Dict[str, Skill] = {}

    def register_skill(self, skill: Skill):
        self._skills[skill.name] = skill

    def get_skill(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list_skills(self) -> List[str]:
        return sorted(self._skills.keys())

    def apply_skill_to_pet(self, pet: "Pet", name: str):
        skill = self.get_skill(name)
        if not skill:
            raise ValueError(f"Skill '{name}' nicht gefunden")
        skill.apply(pet)


def load_builtin_skills() -> List[Skill]:
    return [
        Skill("Gear1", "Gear 1: Kraftverstärkung und Geschwindigkeit.", {"strength": 4, "agility": 2}),
        Skill("Gear2", "Gear 2: Ausdauer und Charisma-Bonus.", {"stamina": 5, "charisma": 1}),
        Skill("Gear3", "Gear 3: Agilitätssprung und starke Präsenz.", {"agility": 3, "charisma": 2}),
    ]
