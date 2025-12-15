from typing import List
from ..Player import Player


class Human(Player):
    def speak(self, prompt_text: str) -> str:
        if self.input_handler:
            return self.input_handler(self.name, "speech", prompt_text, [], False)
        return input(f"{prompt_text}\n> ")

    def choose(
        self, prompt_text: str, valid_choices: List[str], allow_skip: bool = False
    ) -> str:
        if self.input_handler:
            while True:
                response = self.input_handler(
                    self.name, "choice", prompt_text, valid_choices, allow_skip
                )

                if allow_skip and response.lower() == "skip":
                    return "skip"

                if response in valid_choices:
                    return response

                if response.isdigit():
                    idx = int(response) - 1
                    if 0 <= idx < len(valid_choices):
                        return valid_choices[idx]

                # If input handler is used, we might need to loop or return error
                # Ideally input_handler handles the UI loop, but here we assume it returns a single input
                # and we might need to re-prompt.
                # However, the original code had a loop for input_handler too.
                prompt_text = f"[无效输入，请重试] {prompt_text}"

        while True:
            print(prompt_text)
            display_choices = list(valid_choices)
            if allow_skip:
                display_choices.append("skip")

            for i, choice in enumerate(display_choices):
                print(f"{i + 1}. {choice}")

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

            print("无效的选择, 请重新输入.")
