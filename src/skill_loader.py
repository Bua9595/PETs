import os
import json
from typing import List
from skills import Skill, SkillManager


def load_skills_from_assets(manager: SkillManager, assets_dir: str) -> List[Skill]:
    """Lädt alle JSON-Skill-Dateien aus `assets/hatch-skill/` rekursiv und registriert sie im Manager."""
    root_folder = os.path.join(assets_dir, 'hatch-skill')
    loaded: List[Skill] = []
    if not os.path.isdir(root_folder):
        return loaded

    for dirpath, _, filenames in os.walk(root_folder):
        for file_name in filenames:
            if not file_name.lower().endswith('.json'):
                continue
            path = os.path.join(dirpath, file_name)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                name = data.get('name') or os.path.splitext(file_name)[0]
                desc = data.get('description', '')
                effects = data.get('effects', {})
                if not isinstance(effects, dict):
                    print(f"Skill-Effekte in {path} sind ungültig, überspringe.")
                    continue
                skill = Skill(name, desc, effects)
                manager.register_skill(skill)
                loaded.append(skill)
            except Exception as e:
                print(f"Fehler beim Laden von Skill {path}: {e}")
    return loaded
