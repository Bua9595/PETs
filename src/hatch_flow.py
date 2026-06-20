from __future__ import annotations

from typing import List

from pet import Pet
from skills import SkillManager, load_builtin_skills
from skill_loader import load_skills_from_assets


class HatchFlow:
    def __init__(self, pet: Pet, assets_dir: str):
        self.pet = pet
        self.skill_manager = SkillManager()
        for skill in load_builtin_skills():
            self.skill_manager.register_skill(skill)
        load_skills_from_assets(self.skill_manager, assets_dir)

    def list_skills(self) -> List[str]:
        return self.skill_manager.list_skills()

    def choose_skill(self, skill_name: str):
        skill = self.skill_manager.get_skill(skill_name)
        if not skill:
            raise ValueError(f"Skill '{skill_name}' nicht gefunden")
        self.pet.apply_skill(skill.name, skill.effects)

    def hatch(self):
        self.pet.hatch()

    def equip_gear(self, gear_name: str):
        self.pet.equip_gear(gear_name)

    def status(self):
        self.pet.describe()
