from typing import List
import random
from ..Player import Player


class Local(Player):
    def speak(self, prompt_text: str) -> str:
        return f"Local Player ({self.name}) says: This is a test speech."

    def choose(
        self, prompt_text: str, valid_choices: List[str], allow_skip: bool = False
    ) -> str:
        choice = random.choice(valid_choices)
        return choice
