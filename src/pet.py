import os
import sys
import time

from pet_state import PetState


class Pet:
    ANIMATIONS = {
        'hatch': [
            (r"""
             _____
            /     \
           /  .-.  \
          /  (o o)  \
         /   | - |   \
        /_________\
            """, "Das Ei beginnt zu vibrieren..."),
            (r"""
             _____
            /  .-. \
           /  (x x) \
          /   | - | \
         /    \_/  \
        /_________\
            """, "Die Schale reißt, kleine Risse erscheinen..."),
            (r"""
             _____
            /  .-. \
           /  (o o) \
          /   | v | \
         /  \_____/
        /__________\
            """, "Ein Schimmer dringt durch die Spalte..."),
            (r"""
             _____
            /  .-. \
           /  (o o) \
          /   /|\  \
         /   / | \  \
        /___/  |  \__\
            """, "Ein Schatten schiebt sich nach vorne..."),
            (r"""
              .-""-.
             / .--. \
             | |  | |
             |o \/ o|
             |  /\  |
              \____/
             /|    |\
            /_|____|_\
            """, "Der Hatch wird vollzogen. Der Charakter erstrahlt."),
        ],
        'idle': [
            (r"""
              .-""-.
             / .--. \
             | |  | |
             |o \/ o|
             |  /\  |
              \____/
             /|    |\
            /_|____|_\
            """, "Ruffy steht bereit."),
            (r"""
              .-""-.
             / .--. \
             | |  | |
             |o \/ o|
             |  /\  |
              \____/
             /|  / |\
            /_|_/  |_\
            """, "Ruffy bewegt sich leicht in der Pose."),
        ],
        'run': [
            (r"""
              .-""-.
             / .--. \
             | |  | |
             |o \/ o|
             |  /\  |
              \____/
             /|  /|\
            /_|_/ |_\
            """, "Ruffy sprintet vorwärts."),
            (r"""
              .-""-.
             / .--. \
             | |  | |
             |o \/ o|
             |  /\  |
              \____/
             /| / |\
            /_|/  |_\
            """, "Der Schritt wird schneller."),
        ],
        'attack': [
            (r"""
              .-""-.
             / .--. \
             | |  | |
             |o \/ o|
             |  /\  |
              \____/
             /|  /|\
            /_|_/ |_\
            """, "Ruffy spannt einen Angriff an."),
            (r"""
              .-""-.
             / .--. \
             | |  | |
             |o \/ o|
             |  /\  |
              \____/
             /| / |\
            /_|/  |_\
            """, "Der Schlag trifft mit voller Wucht."),
        ],
        'skill': [
            (r"""
              .-""-.
             / .--. \
             | |  | |
             |^ \/ ^|
             |  /\  |
              \____/
             /| ** |\
            /_|_**_|_\
            """, "Mystische Energie lädt sich auf."),
            (r"""
              .-""-.
             / .--. \
             | |  | |
             |^ \/ ^|
             |  /\  |
              \____/
             /| ** |\
            /_|_**_|_\
            """, "Der Skill entfaltet seine Wirkung."),
        ],
    }

    def __init__(self, name: str, look: str = "default", attributes: dict | None = None):
        self.state = PetState(name=name, look=look, attributes=attributes or {
            "strength": 1,
            "stamina": 1,
            "charisma": 1,
            "agility": 1,
        })

    def hatch(self):
        if self.state.hatched:
            print(f"{self.state.name} ist bereits geschlüpft.")
            return

        self.state.state = "hatching"
        self.state.record("hatching")
        self._play_animation('hatch')

        self.state.state = "hatched"
        self.state.hatched = True
        self.state.gain_experience(4)
        self.state.change_energy(1)
        self.state.record("hatched")

        print(f"{self.state.name} ist jetzt geschlüpft und bereit für Abenteuer!")
        self.describe()

    def _clear_screen(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def _print_frame(self, frame: str, caption: str = ""):
        self._clear_screen()
        print(frame)
        if caption:
            print(caption)
        sys.stdout.flush()

    def _play_animation(self, animation_name: str, delay: float = 0.6, extra_caption: str | None = None):
        frames = self.ANIMATIONS.get(animation_name, self.ANIMATIONS['idle'])
        for frame, caption in frames:
            caption_text = caption
            if extra_caption:
                caption_text = f"{caption} {extra_caption}"
            self._print_frame(frame, caption_text)
            time.sleep(delay)

    def _animate_hatch_sequence(self):
        self._play_animation('hatch')
        if self.state.gear:
            self._print_frame(self.ANIMATIONS['hatch'][-1][0], f"{self.state.name} trägt {self.state.gear} und wirkt jetzt noch stärker.")
        if self.state.active_skills:
            skill_line = ', '.join(self.state.active_skills)
            self._print_frame(self.ANIMATIONS['skill'][-1][0], f"Skills ({skill_line}) laden jetzt sofort nach dem Hatch.")

    def equip_gear(self, gear_name: str):
        self.state.gear = gear_name
        self.state.record(f"gear:{gear_name}")
        gear_boosts = {
            "Gear1": {"strength": 2, "agility": 1},
            "Gear2": {"stamina": 3, "charisma": 1},
            "Gear3": {"strength": 4, "stamina": 1, "agility": 2},
        }
        boosts = gear_boosts.get(gear_name)
        if boosts:
            for key, value in boosts.items():
                self.state.attributes[key] = self.state.attributes.get(key, 0) + value
            print(f"{self.state.name} rüstet {gear_name} aus und erhält einen Balancing-Boost.")
        else:
            print(f"{self.state.name} rüstet {gear_name} aus.")

    def apply_skill(self, skill_name: str, effect: dict):
        self.state.active_skills.append(skill_name)
        self.state.record(f"skill:{skill_name}")
        for key, value in effect.items():
            self.state.attributes[key] = self.state.attributes.get(key, 0) + value
        print(f"Skill {skill_name} angewendet: {effect}")

    def rest(self):
        self.state.change_energy(3)
        self.state.change_hunger(-1)
        self.state.gain_experience(2)
        self.state.record('rest')
        print(f"{self.state.name} ruht sich aus. Energie +3, Hunger -1.")
        self._play_animation('idle', delay=0.5)

    def train(self):
        self.state.change_energy(-2)
        self.state.change_hunger(-1)
        self.state.gain_experience(5)
        self.state.attributes['strength'] += 1
        self.state.attributes['agility'] += 1
        self.state.record('train')
        print(f"{self.state.name} trainiert. Stärke +1, Agilität +1.")
        self._play_animation('run', delay=0.35)

    def play(self):
        self.state.change_energy(-1)
        self.state.change_hunger(-2)
        self.state.gain_experience(3)
        self.state.attributes['charisma'] += 1
        self.state.attributes['agility'] += 1
        self.state.record('play')
        print(f"{self.state.name} spielt fröhlich. Charisma +1, Agilität +1.")
        self._play_animation('idle', delay=0.5)

    def describe(self):
        print("--- PET STATUS ---")
        print(f"Name: {self.state.name}")
        print(f"Look: {self.state.look}")
        print(f"Zustand: {self.state.state}")
        print(f"Level: {self.state.level} (Exp: {self.state.experience}/{self.state.level * 10})")
        print(f"Hunger: {self.state.hunger}/10")
        print(f"Energie: {self.state.energy}/10")
        if self.state.gear:
            print(f"Gear: {self.state.gear}")
        if self.state.active_skills:
            print(f"Aktive Skills: {', '.join(self.state.active_skills)}")
        print("Attribute:")
        for key, value in self.state.attributes.items():
            print(f"  - {key}: {value}")
        print("History:")
        for event in self.state.history[-10:]:
            print(f"  - {event}")
        self._play_animation('idle', delay=0.6)

    def render(self) -> str:
        if self.state.state == "egg":
            art = r"""
             ___
            /___\
           /     \
          /  o o  \
         /   ---   \
        /_________\
            """
        else:
            art = r"""
              .-""-.
             / .===. \
             \/ 6 6 \
             (  \_/  )
              )=====(
             /      \
            /        \
            """
        return f"{self.state.name} ({self.state.look})\n{art}"
