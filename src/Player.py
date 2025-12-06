import os
import random
from litellm import completion
from typing import List, Dict, Optional

from .Base import Player
from .Config import load_config


config = load_config()
DEBUG = os.getenv("debug", "0") == "1"


# 本地人类玩家 通过前端应用交互
class LocalHumanPlayer(Player):
    """本地人类玩家, 通过前端应用交互"""

    def __init__(self, name: str, info: Dict[str, str], status: Dict[str, str]):
        super().__init__(name, info, status)

    def choose(
        self, prompt_text: str, valid_choices: List[str], allow_skip: bool = False
    ) -> str:
        """本地玩家选择"""
        while True:
            print(prompt_text)
            display_choices = list(valid_choices)
            if allow_skip:
                display_choices.append("skip")

            for i, choice in enumerate(display_choices):
                print(f"[yellow]{i + 1}[/yellow]. [cyan]{choice}[/cyan]")

            player_input = input("> ").strip()
            player_input_lower = player_input.lower()

            if player_input.isdigit():
                choice_index = int(player_input) - 1
                if 0 <= choice_index < len(display_choices):
                    return display_choices[choice_index]

            if allow_skip and player_input_lower == "skip":
                return "skip"

            for choice in valid_choices:
                if choice.lower() == player_input_lower:
                    return choice

            print("[bold red]无效的选择, 请重新输入.[/bold red]")

    def speak(self, prompt_text: str) -> str:
        """本地玩家发言"""
        return input(prompt_text)


# 在线人类玩家 通过网络交互
class OnlineHumanPlayer(Player):
    """在线人类玩家, 通过网络交互"""

    def __init__(self, name: str, info: Dict[str, str], status: Dict[str, str]):
        super().__init__(name, info, status)

    def choose(
        self, prompt_text: str, valid_choices: List[str], allow_skip: bool = False
    ) -> str:
        pass

    def speak(self, prompt_text: str) -> str:
        pass


# 在线LLM玩家 通过Litellm API交互
class OnlineLLMPlayer(Player):
    """在线LLM玩家, 通过Litellm API交互"""

    def __init__(self, name: str, info: Dict[str, str], status: Dict[str, str]):
        super().__init__(name, info, status)
        self.model = info.get("model")
        self.provider = info.get("provider")
        # TODO: Consider how to manage prompts and history more flexibly.
        self.prompt = "Default LLM prompt"
        self.is_first_night = True  # Specific to some game logic

    def choose(self, prompt_text: str, valid_choices: List[str]) -> str:
        """Generates a choice using an online LLM."""
        if DEBUG:
            return random.choice(valid_choices)

        history = self._build_history(prompt_text)
        prompt = f"{prompt_text}\n请从以下选项中选择: {', '.join(valid_choices)}"
        history.append({"role": "user", "content": prompt})

        response = completion(
            model=self.model,
            messages=history,
            stream=False,
        )
        ai_choice = response.choices[0].message.content

        # Simple matching logic
        for choice in valid_choices:
            if choice in ai_choice:
                return choice

        # Fallback if no match is found
        return random.choice(valid_choices)

    def speak(self, prompt_text: str) -> str:
        """Generates speech using an online LLM."""
        if DEBUG:
            return "AI generated speech with <strong>formatting</strong>."

        history = self._build_history(prompt_text)
        history.append({"role": "user", "content": prompt_text})

        print(f"{self.name} 正在思考...")
        response = completion(
            model=self.model,
            messages=history,
            stream=False,
        )
        speech = response.choices[0].message.content
        return speech

    def _build_history(self, prompt_text: str) -> List[Dict[str, str]]:
        """Builds the message history for the LLM call."""
        history = []
        if self.game_logger:
            log_file = self.game_logger._get_player_log_file(self.name)
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    log_content = f.read()
                    if log_content.strip():
                        # Simplified context reminder
                        context_reminder = (
                            f"You are {self.name}, your role is {self.role}."
                        )
                        context_prompt = (
                            f"Game History:\n{log_content}\n\n{context_reminder}"
                        )
                        history.append({"role": "system", "content": context_prompt})

        history.append({"role": "system", "content": self.prompt})
        return history


# 本地LLM玩家 通过Ollama API交互(暂定)
class LocalLLMPlayer(Player):
    """本地LLM玩家, 通过Ollama API交互"""

    def __init__(self, name: str, info: Dict[str, str], status: Dict[str, str]):
        super().__init__(name, info, status)
        self.model_path = info.get("model_path")

    def choose(self, prompt_text: str, valid_choices: List[str]) -> str:
        pass

    def speak(self, prompt_text: str) -> str:
        pass
