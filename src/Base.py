from abc import ABC, abstractmethod
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


class Game(ABC):
    @abstractmethod
    def set(self):
        pass

    @abstractmethod
    def run(self):
        pass


class Player(ABC):
    @abstractmethod
    def get_choice(self):
        pass

    @abstractmethod
    def call_speak(self):
        pass
