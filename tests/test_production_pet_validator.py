from __future__ import annotations

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from production_pet_validator import validate_pet_manifest, validate_pet_template_structure


class ProductionPetValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pack_dir = Path(self.temp_dir.name) / "production_template"
        self.metadata_dir = self.pack_dir / "metadata"
        self.parts_dir = self.pack_dir / "parts"
        self.metadata_dir.mkdir(parents=True)
        self.parts_dir.mkdir()
        self.data = json.loads(
            (PROJECT_ROOT / "assets/pets/production_template/metadata/pet_manifest.json").read_text(encoding="utf-8")
        )
        self._write_assets(self.data)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_assets(self, data: dict) -> None:
        for part in data["parts"]:
            path = self.metadata_dir / part["asset_path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><path d="M 0 0 H 1 V 1 H 0 Z"/></svg>',
                encoding="utf-8",
            )

    def _validate(self, data: dict) -> list[str]:
        manifest_path = self.metadata_dir / "pet_manifest.json"
        manifest_path.write_text(json.dumps(data), encoding="utf-8")
        return validate_pet_manifest(manifest_path)

    def test_valid_template_contract(self) -> None:
        self.assertEqual(self._validate(deepcopy(self.data)), [])

    def test_draft_template_structure_is_valid_without_art_files(self) -> None:
        template_manifest = PROJECT_ROOT / "assets/pets/production_template/metadata/pet_manifest.json"
        self.assertEqual(validate_pet_template_structure(template_manifest), [])

    def test_rejects_missing_required_part(self) -> None:
        data = deepcopy(self.data)
        data["parts"] = [part for part in data["parts"] if part["part_id"] != "left_hand"]
        self.assertIn("missing required part_id values: left_hand", "\n".join(self._validate(data)))

    def test_rejects_invalid_asset_path(self) -> None:
        data = deepcopy(self.data)
        data["parts"][0]["asset_path"] = "parts/missing.svg"
        self.assertIn("does not exist: parts/missing.svg", "\n".join(self._validate(data)))

    def test_rejects_duplicate_part_id(self) -> None:
        data = deepcopy(self.data)
        data["parts"][1]["part_id"] = data["parts"][0]["part_id"]
        self.assertIn("duplicate 'hair_back'", "\n".join(self._validate(data)))

    def test_rejects_unknown_parent_bone(self) -> None:
        data = deepcopy(self.data)
        data["parts"][0]["parent_bone"] = "MissingBone"
        self.assertIn("unknown bone 'MissingBone'", "\n".join(self._validate(data)))

    def test_rejects_implausible_pivot(self) -> None:
        data = deepcopy(self.data)
        data["parts"][0]["pivot"] = [999, -999]
        self.assertIn("pivot: lies outside plausible image bounds", "\n".join(self._validate(data)))

    def test_rejects_missing_action_bounds(self) -> None:
        data = deepcopy(self.data)
        del data["action_bounds"]
        self.assertIn("action_bounds: is required", "\n".join(self._validate(data)))

    def test_rejects_unsupported_schema_version(self) -> None:
        data = deepcopy(self.data)
        data["schema_version"] = 2
        self.assertIn("unsupported version 2; supported version is 1", "\n".join(self._validate(data)))


if __name__ == "__main__":
    unittest.main()
