from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional

BASE = Path(__file__).resolve().parent.parent


class Game(ABC):
    @abstractmethod
    def set(self):
        pass

    @abstractmethod
    def run(self):
        pass


class Player(ABC):
    def __init__(self, name: str, info: Dict[str, str], status: Dict[str, str]):
        self.name = name
        self.role = info.get("role") or ""

    @abstractmethod
    def choose(self):
        pass

    @abstractmethod
    def speak(self):
        pass
