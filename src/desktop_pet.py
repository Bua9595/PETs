from __future__ import annotations

import argparse
import os
import random
import tkinter as tk
from pathlib import Path
from tkinter import Menu

from PIL import Image, ImageOps, ImageTk

from sprite_animator import SpriteAnimator


TRANSPARENT_COLOR = "#ff00ff"
DEFAULT_SCALE = 0.5
DEFAULT_PET_ID = "ruffy"


class DesktopPet:
    def __init__(self, assets_dir: Path, manifest_path: Path, scale: float = DEFAULT_SCALE):
        self.assets_dir = assets_dir
        self.animator = SpriteAnimator(assets_dir, manifest_path)
        self.desktop_behavior = self.animator.manifest.get("desktop_behavior", {})
        self.scale = max(0.5, min(scale, 2.5))
        self.default_frame_ms = int(self.animator.manifest.get("frame_duration_ms", 250))
        self.cell_width = int(self.animator.manifest["cell_width"])
        self.cell_height = int(self.animator.manifest["cell_height"])
        self.window_width = int(self.cell_width * self.scale)
        self.window_height = int(self.cell_height * self.scale)

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=TRANSPARENT_COLOR)
        self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.root.title("Hatch Pet")

        self.label = tk.Label(self.root, bd=0, highlightthickness=0, bg=TRANSPARENT_COLOR)
        self.label.pack()

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.x = max(0, (self.screen_width - self.window_width) // 2)
        self.y = max(0, self.screen_height - self.window_height - 100)
        self.base_y = self.y
        self.direction = 1
        self.dragging = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        self.initial_animation = str(self.desktop_behavior.get("initial_animation", "hatch"))
        self.drag_animation = str(self.desktop_behavior.get("drag_animation", "idle"))
        self.double_click_animation = str(self.desktop_behavior.get("double_click_animation", "rubber_punch"))
        self.current_animation = self.initial_animation
        self.frame_index = 0
        self.frame_cache: dict[tuple[str, int], list[ImageTk.PhotoImage]] = {}
        self.next_decision_frames = 0

        self._build_menu()
        self._bind_events()
        self._move_window()
        self.play(self.initial_animation)

    def _build_menu(self):
        self.menu = Menu(self.root, tearoff=False)
        default_menu_states = [
            ("Idle", "idle"),
            ("Blink", "blink"),
            ("Walk", "walk"),
            ("Run", "run"),
            ("Jump", "jump"),
            ("Wave", "wave"),
            ("Happy", "happy"),
            ("Sit", "sit"),
            ("Rest", "rest"),
            ("Nap", "nap"),
            ("Failed", "failed"),
            ("Curious", "curious"),
            ("Celebrate", "celebrate"),
            ("Rubber Stretch", "rubber_stretch"),
            ("Rubber Punch", "rubber_punch"),
            ("Rubber Reach", "rubber_reach"),
            ("Gear 2", "gear2"),
            ("Gear 3", "gear3"),
            ("Gear 4", "gear4"),
            ("Gear 5", "gear5"),
        ]
        manifest_menu_states = self.desktop_behavior.get("menu_states", default_menu_states)
        menu_states = []
        for item in manifest_menu_states:
            if isinstance(item, dict):
                menu_states.append((str(item.get("label", item.get("animation", "State"))), str(item.get("animation", "idle"))))
            else:
                label, animation = item
                menu_states.append((str(label), str(animation)))
        for label, animation in menu_states:
            if animation in self.animator.available_animations:
                self.menu.add_command(label=label, command=lambda name=animation: self.play(name))
        self.menu.add_separator()
        self.menu.add_command(label="Close", command=self.root.destroy)

    def _bind_events(self):
        self.label.bind("<ButtonPress-1>", self._start_drag)
        self.label.bind("<B1-Motion>", self._drag)
        self.label.bind("<ButtonRelease-1>", self._stop_drag)
        self.label.bind("<Double-Button-1>", lambda _event: self.play(self.double_click_animation))
        self.label.bind("<Button-3>", self._open_menu)
        self.root.bind("<Escape>", lambda _event: self.root.destroy())

    def _start_drag(self, event):
        self.dragging = True
        self.drag_offset_x = event.x
        self.drag_offset_y = event.y
        self.play(self.drag_animation)

    def _drag(self, event):
        self.x = self.root.winfo_pointerx() - self.drag_offset_x
        self.y = self.root.winfo_pointery() - self.drag_offset_y
        self._clamp_to_screen()
        self._move_window()

    def _stop_drag(self, _event):
        self.dragging = False
        self.base_y = self.y
        self.next_decision_frames = 8

    def _open_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def _clamp_to_screen(self):
        self.x = max(0, min(self.x, self.screen_width - self.window_width))
        self.y = max(0, min(self.y, self.screen_height - self.window_height))

    def _move_window(self):
        self.root.geometry(f"{self.window_width}x{self.window_height}+{int(self.x)}+{int(self.y)}")

    def _load_frames(self, animation: str, direction: int) -> list[ImageTk.PhotoImage]:
        key = (animation, direction)
        if key in self.frame_cache:
            return self.frame_cache[key]

        frames = []
        for frame in self.animator.frames(animation):
            image = frame
            if direction < 0 and animation not in {"hatch"}:
                image = ImageOps.mirror(image)
            if self.scale != 1.0:
                image = image.resize((self.window_width, self.window_height), Image.Resampling.LANCZOS)
            else:
                image = image.copy()

            frames.append(ImageTk.PhotoImage(self._to_color_key_frame(image)))

        self.frame_cache[key] = frames
        return frames

    def _to_color_key_frame(self, image: Image.Image) -> Image.Image:
        """Tk color-key transparency must be binary or it creates magenta fringes."""
        image = image.convert("RGBA")
        output = Image.new("RGB", image.size, TRANSPARENT_COLOR)
        src = image.load()
        dst = output.load()

        for y in range(image.height):
            for x in range(image.width):
                r, g, b, a = src[x, y]
                if a > 24:
                    dst[x, y] = (r, g, b)

        return output

    def play(self, animation: str):
        if animation not in self.animator.available_animations:
            animation = "idle"
        self.current_animation = animation
        self.frame_index = 0

    def run(self):
        self._tick()
        self.root.mainloop()

    def _tick(self):
        frames = self._load_frames(self.current_animation, self.direction)
        self.label.configure(image=frames[self.frame_index])

        if not self.dragging:
            self._apply_behavior()

        self.frame_index += 1
        spec = self.animator.spec(self.current_animation)
        if self.frame_index >= len(frames):
            if spec.loop:
                self.frame_index = 0
            else:
                self.frame_index = 0
                self._choose_next_action(force=True)

        self.root.after(self._current_frame_ms(), self._tick)

    def _current_frame_ms(self) -> int:
        animation = self.animator.manifest["animations"].get(self.current_animation, {})
        return int(animation.get("frame_duration_ms", self.default_frame_ms))

    def _apply_behavior(self):
        if self.current_animation == "run":
            self.x += self.direction * 8
            if self.x <= 0 or self.x >= self.screen_width - self.window_width:
                self.direction *= -1
                self.x = max(0, min(self.x, self.screen_width - self.window_width))
            self._move_window()
        elif self.current_animation == "jump":
            phase = self.frame_index % 8
            lift = [0, -12, -28, -42, -36, -18, -4, 0][phase]
            self.y = max(0, self.base_y + lift)
            self._move_window()

        self.next_decision_frames -= 1
        if self.next_decision_frames <= 0:
            self._choose_next_action()

    def _choose_next_action(self, force: bool = False):
        if self.current_animation == "hatch" and not force:
            return

        default_choices = [
            ("idle", 24),
            ("blink", 8),
            ("walk", 12),
            ("run", 18),
            ("wave", 9),
            ("happy", 7),
            ("jump", 7),
            ("sit", 5),
            ("rest", 4),
            ("curious", 4),
            ("rubber_stretch", 3),
            ("rubber_punch", 3),
            ("rubber_reach", 2),
            ("gear2", 2),
            ("gear3", 1),
            ("gear4", 1),
            ("gear5", 1),
            ("failed", 2),
        ]
        configured_choices = self.desktop_behavior.get("choices", default_choices)
        choices = []
        for item in configured_choices:
            if isinstance(item, dict):
                choices.append((str(item.get("animation", "idle")), int(item.get("weight", 1))))
            else:
                name, weight = item
                choices.append((str(name), int(weight)))
        choices = [(name, weight) for name, weight in choices if name in self.animator.available_animations]
        animation = random.choices([name for name, _weight in choices], [weight for _name, weight in choices])[0]
        if animation == "run" and random.random() < 0.35:
            self.direction *= -1
        self.play(animation)
        self.next_decision_frames = random.randint(14, 32)


def parse_args():
    parser = argparse.ArgumentParser(description="Run the animated desktop pet.")
    parser.add_argument("--look", default="Ruffy", help="Legacy look name. Defaults to the Ruffy manifest.")
    parser.add_argument("--pet", default=DEFAULT_PET_ID, help="Pet id to load. Default: ruffy.")
    parser.add_argument("--list-pets", action="store_true", help="List available pet ids and exit.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Optional manifest path for another pet. Defaults to assets/pets/ruffy/manifest.json.",
    )
    parser.add_argument("--scale", type=float, default=DEFAULT_SCALE, help="Window scale, e.g. 0.8, 1.0, 1.5")
    return parser.parse_args()


def available_pet_manifests(project_root: Path) -> dict[str, Path]:
    pets: dict[str, Path] = {}
    pets_root = project_root / "assets" / "pets"
    if pets_root.exists():
        for manifest in sorted(pets_root.glob("*/manifest.json")):
            pets[manifest.parent.name] = manifest
    ruffy_manifest = project_root / "assets" / "ruffy_sprite_manifest.json"
    if ruffy_manifest.exists() and DEFAULT_PET_ID not in pets:
        pets[DEFAULT_PET_ID] = ruffy_manifest
    return pets


def main():
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent
    pets = available_pet_manifests(project_root)

    if args.list_pets:
        for pet_id, manifest in sorted(pets.items()):
            print(f"{pet_id}: {manifest.relative_to(project_root)}")
        return

    manifest_path = args.manifest or pets.get(args.pet)
    if manifest_path is None:
        available = ", ".join(sorted(pets)) or "none"
        raise ValueError(f"Pet '{args.pet}' not found. Available pets: {available}")
    if not manifest_path.is_absolute():
        manifest_path = project_root / manifest_path
    assets_dir = manifest_path.parent
    if not manifest_path.exists():
        raise FileNotFoundError(f"Sprite manifest not found: {manifest_path}")

    os.chdir(project_root)
    DesktopPet(assets_dir=assets_dir, manifest_path=manifest_path, scale=args.scale).run()


if __name__ == "__main__":
    main()
