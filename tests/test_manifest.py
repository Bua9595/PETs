from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from desktop_pet import available_pet_manifests
from manifest import ManifestValidationError, load_manifest


class ManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pack_dir = Path(self.temp_dir.name) / "sample"
        self.pack_dir.mkdir()
        Image.new("RGBA", (20, 10), (0, 0, 0, 0)).save(self.pack_dir / "sheet.png")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _valid_data(self) -> dict:
        return {
            "id": "sample",
            "display_name": "Sample",
            "image": "sheet.png",
            "columns": 2,
            "rows": 1,
            "cell_width": 10,
            "cell_height": 10,
            "frame_duration_ms": 100,
            "animations": {"idle": {"row": 0, "frames": 2, "loop": True}},
            "desktop_behavior": {
                "initial_animation": "idle",
                "drag_animation": "idle",
                "double_click_animation": "idle",
                "menu_states": [{"label": "Idle", "animation": "idle"}],
                "choices": [{"animation": "idle", "weight": 1}],
            },
        }

    def _write_manifest(self, data: dict | str) -> Path:
        path = self.pack_dir / "manifest.json"
        path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
        return path

    def _assert_invalid(self, data: dict | str, field: str, cause: str) -> None:
        with self.assertRaises(ManifestValidationError) as context:
            load_manifest(self._write_manifest(data))
        message = str(context.exception)
        self.assertIn("manifest.json", message)
        self.assertIn(field, message)
        self.assertIn(cause, message)

    def test_loads_existing_ruffy_manifest_as_v1(self) -> None:
        loaded = load_manifest(PROJECT_ROOT / "assets/pets/ruffy/manifest.json")
        self.assertEqual(loaded.schema_version, 1)
        self.assertEqual(loaded.data["id"], "ruffy")

    def test_loads_existing_pet2_manifest_as_v1(self) -> None:
        loaded = load_manifest(PROJECT_ROOT / "assets/pets/pet2_chibi/manifest.json")
        self.assertEqual(loaded.schema_version, 1)
        self.assertEqual(loaded.data["id"], "pet2_chibi")

    def test_missing_schema_version_is_v1_and_configuration_is_preserved(self) -> None:
        data = self._valid_data()
        loaded = load_manifest(self._write_manifest(data))
        self.assertEqual(loaded.schema_version, 1)
        self.assertEqual(loaded.data["desktop_behavior"], data["desktop_behavior"])

    def test_existing_runtime_configuration_is_preserved(self) -> None:
        for pet_id in ("ruffy", "pet2_chibi"):
            path = PROJECT_ROOT / "assets" / "pets" / pet_id / "manifest.json"
            raw = json.loads(path.read_text(encoding="utf-8"))
            loaded = load_manifest(path)
            self.assertEqual(loaded.data["desktop_behavior"], raw["desktop_behavior"])
            self.assertIn(loaded.data["desktop_behavior"]["initial_animation"], loaded.data["animations"])
            self.assertTrue(loaded.data["desktop_behavior"].get("menu_states"))

    def test_pack_discovery_finds_existing_packs(self) -> None:
        packs = available_pet_manifests(PROJECT_ROOT)
        self.assertEqual(set(packs), {"ruffy", "pet2_chibi"})

    def test_rejects_invalid_json(self) -> None:
        self._assert_invalid("{not-json", "$", "invalid JSON")

    def test_rejects_missing_atlas(self) -> None:
        data = self._valid_data()
        data["image"] = "missing.png"
        self._assert_invalid(data, "image", "does not exist")

    def test_rejects_non_positive_cell_size(self) -> None:
        data = self._valid_data()
        data["cell_width"] = 0
        self._assert_invalid(data, "cell_width", "positive integer")

    def test_rejects_atlas_dimension_mismatch(self) -> None:
        data = self._valid_data()
        data["columns"] = 3
        self._assert_invalid(data, "image", "dimensions")

    def test_rejects_animation_row_outside_grid(self) -> None:
        data = self._valid_data()
        data["animations"]["idle"]["row"] = 1
        self._assert_invalid(data, "animations.idle.row", "outside")

    def test_rejects_frame_count_outside_grid(self) -> None:
        data = self._valid_data()
        data["animations"]["idle"]["frames"] = 3
        self._assert_invalid(data, "animations.idle.frames", "exceeds")

    def test_rejects_unknown_behavior_animation(self) -> None:
        data = self._valid_data()
        data["desktop_behavior"]["drag_animation"] = "missing"
        self._assert_invalid(data, "desktop_behavior.drag_animation", "unknown animation")

    def test_rejects_unknown_context_menu_animation(self) -> None:
        data = self._valid_data()
        data["desktop_behavior"]["menu_states"][0]["animation"] = "missing"
        self._assert_invalid(data, "desktop_behavior.menu_states[0].animation", "unknown animation")

    def test_rejects_invalid_frame_duration(self) -> None:
        data = self._valid_data()
        data["animations"]["idle"]["frame_duration_ms"] = 0
        self._assert_invalid(data, "animations.idle.frame_duration_ms", "positive integer")

    def test_rejects_non_boolean_loop(self) -> None:
        data = self._valid_data()
        data["animations"]["idle"]["loop"] = "yes"
        self._assert_invalid(data, "animations.idle.loop", "boolean")


if __name__ == "__main__":
    unittest.main()
