import json
import os
from typing import Dict, Any, List, Optional


def load_look_definition(look_name: str, assets_dir: str) -> Optional[Dict[str, Any]]:
    candidate = os.path.join(assets_dir, f"{look_name.lower()}.json")
    if not os.path.isfile(candidate):
        return None
    with open(candidate, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_available_looks(assets_dir: str) -> List[str]:
    definitions: List[str] = []
    if not os.path.isdir(assets_dir):
        return definitions
    for file_name in os.listdir(assets_dir):
        if file_name.lower().endswith('.json'):
            definitions.append(os.path.splitext(file_name)[0])
    return sorted(definitions)
