from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from manifest import load_manifest


@dataclass(frozen=True)
class AnimationSpec:
    name: str
    row: int
    frames: int
    loop: bool


class SpriteAnimator:
    def __init__(self, assets_dir: str | Path, manifest_path: str | Path):
        self.assets_dir = Path(assets_dir)
        self.manifest_path = Path(manifest_path)
        self.manifest = load_manifest(self.manifest_path).data
        self.sheet_path = self.assets_dir / self.manifest["image"]
        self.sheet = Image.open(self.sheet_path).convert("RGBA")

    @property
    def available_animations(self) -> list[str]:
        return sorted(self.manifest["animations"].keys())

    def spec(self, name: str) -> AnimationSpec:
        animations = self.manifest["animations"]
        if name not in animations:
            available = ", ".join(sorted(animations))
            raise ValueError(f"Animation '{name}' nicht gefunden. Verfuegbar: {available}")
        raw = animations[name]
        return AnimationSpec(
            name=name,
            row=int(raw["row"]),
            frames=int(raw["frames"]),
            loop=bool(raw.get("loop", True)),
        )

    def frames(self, name: str) -> list[Image.Image]:
        spec = self.spec(name)
        cell_width = int(self.manifest["cell_width"])
        cell_height = int(self.manifest["cell_height"])
        output: list[Image.Image] = []
        for column in range(spec.frames):
            box = (
                column * cell_width,
                spec.row * cell_height,
                (column + 1) * cell_width,
                (spec.row + 1) * cell_height,
            )
            output.append(self.sheet.crop(box))
        return output

    def export_gif(self, name: str, output_path: str | Path, scale: int = 2) -> Path:
        if scale < 1:
            raise ValueError("scale muss mindestens 1 sein")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        raw_spec = self.manifest["animations"].get(name, {})
        frame_duration = int(raw_spec.get("frame_duration_ms", self.manifest.get("frame_duration_ms", 120)))
        frames = [
            frame.resize((frame.width * scale, frame.height * scale), Image.Resampling.LANCZOS)
            for frame in self.frames(name)
        ]
        loop = 0 if self.spec(name).loop else 1
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration,
            loop=loop,
            disposal=2,
        )
        return output_path
