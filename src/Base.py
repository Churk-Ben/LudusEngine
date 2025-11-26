from abc import ABC, abstractmethod


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
