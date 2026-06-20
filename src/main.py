import argparse
import os

from asset_loader import load_look_definition, list_available_looks
from hatch_flow import HatchFlow
from pet import Pet
from sprite_animator import SpriteAnimator


def main():
    parser = argparse.ArgumentParser(description="PET Hatch CLI")
    parser.add_argument("--name", "-n", default="Ruffy", help="Name des Pets")
    parser.add_argument("--look", "-l", default="Ruffy", help="Look/Design des Pets")
    parser.add_argument("--skill", "-s", help="Skill anwenden (Name)")
    parser.add_argument("--gear", "-g", help="Gear ausruesten (z.B. Gear1, Gear2, Gear3)")
    parser.add_argument("--action", "-a", choices=["rest", "train", "play", "status"], help="Pet-Aktion ausfuehren")
    parser.add_argument("--list-skills", action="store_true", help="Verfuegbare Skills anzeigen")
    parser.add_argument("--list-looks", action="store_true", help="Verfuegbare Looks anzeigen")
    parser.add_argument("--list-animations", action="store_true", help="Verfuegbare Sprite-Animationen anzeigen")
    parser.add_argument("--export-animation", help="Sprite-Animation als GIF exportieren")
    parser.add_argument("--animation-out", help="Ausgabepfad fuer --export-animation")
    args = parser.parse_args()

    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
    if args.list_looks:
        looks = list_available_looks(assets_dir)
        print("Verfuegbare Looks:", looks)
        return

    look_def = load_look_definition(args.look, assets_dir)
    attributes = look_def.get("attributes") if look_def else None
    if look_def:
        print(f"Look '{args.look}' geladen: {look_def.get('description', 'Keine Beschreibung')}")
    else:
        print(f"Look '{args.look}' nicht gefunden. Verwende Standardattribute.")

    animator = load_animator(assets_dir, look_def)
    if args.list_animations:
        if not animator:
            print("Keine Sprite-Animationen fuer diesen Look gefunden.")
            return
        print("Verfuegbare Animationen:", animator.available_animations)
        return

    if args.export_animation:
        if not animator:
            print("Keine Sprite-Animationen fuer diesen Look gefunden.")
            return
        output_path = args.animation_out or os.path.join(
            assets_dir,
            "sprites",
            "previews",
            f"{args.export_animation}.gif",
        )
        exported = animator.export_gif(args.export_animation, output_path)
        print(f"Animation exportiert: {exported}")
        return

    pet = Pet(name=args.name, look=args.look, attributes=attributes)
    hatch_flow = HatchFlow(pet, assets_dir)

    if args.list_skills:
        print("Verfuegbare Skills:", hatch_flow.list_skills())
        return

    available_skills = hatch_flow.list_skills()
    if available_skills:
        print(f"Geladene Skills: {available_skills}")

    if args.skill:
        try:
            hatch_flow.choose_skill(args.skill)
            print(f"Skill '{args.skill}' auf {pet.state.name} angewendet.")
        except Exception as e:
            print(f"Fehler: {e}")

    if args.gear:
        hatch_flow.equip_gear(args.gear)

    if args.action:
        from actions import PetAction

        action_handler = PetAction(pet)
        action_handler.perform(args.action)

    hatch_flow.hatch()


def load_animator(assets_dir: str, look_def: dict | None) -> SpriteAnimator | None:
    sprite_manifest = look_def.get("sprite_manifest") if look_def else None
    if not sprite_manifest:
        return None

    manifest_path = os.path.join(assets_dir, sprite_manifest)
    if not os.path.isfile(manifest_path):
        print(f"Sprite-Manifest nicht gefunden: {manifest_path}")
        return None

    animator = SpriteAnimator(assets_dir, manifest_path)
    print(f"Sprites geladen: {animator.sheet_path}")
    return animator


if __name__ == "__main__":
    main()
