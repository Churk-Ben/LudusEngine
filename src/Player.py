from abc import ABC, abstractmethod
from typing import Dict, List, Any


class Player(ABC):
    def __init__(
        self,
        name: str,
        role: str,
        config_data: Dict[str, Any],
        prompts: Dict[str, str],
        game_logger=None,
        input_handler=None,
        event_emitter=None,
    ):
        self.name = name
        self.role = role
        self.config = config_data
        self.prompts = prompts
        self.game_logger = game_logger
        self.input_handler = input_handler
        self.event_emitter = event_emitter

        self.is_human = self.config.get("human", False)
        self.is_alive = True
        self.is_guarded = False
        self.is_first_night = True

        # 将 self 注入主提示词
        self.prompt = self.prompts.get("PROMPT", "").format(self=self)

    def set_logger(self, logger):
        self.game_logger = logger

    @abstractmethod
    def speak(self, prompt_text: str) -> str:
        pass

    @abstractmethod
    def choose(
        self, prompt_text: str, valid_choices: List[str], allow_skip: bool = False
    ) -> str:
        pass
