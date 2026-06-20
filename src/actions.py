from pet import Pet


class PetAction:
    def __init__(self, pet: Pet):
        self.pet = pet

    def status(self):
        self.pet.describe()

    def rest(self):
        self.pet.rest()

    def train(self):
        self.pet.train()

    def play(self):
        self.pet.play()

    def perform(self, action: str):
        if action == 'rest':
            self.rest()
        elif action == 'train':
            self.train()
        elif action == 'play':
            self.play()
        elif action == 'status':
            self.status()
        else:
            raise ValueError(f"Unbekannter Action-Befehl: {action}")

    @staticmethod
    def available_actions() -> list[str]:
        return ['rest', 'train', 'play', 'status']
