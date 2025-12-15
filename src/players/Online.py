import os
import json
import random
import time
from typing import List, Dict, Any
from litellm import completion
from ..Player import Player


class Online(Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 注入 self 到 prompt
        self.prompt = self.prompts.get("PROMPT", "").format(self=self)

    def _get_memory(self) -> str:
        if self.game_logger:
            log_file = self.game_logger.get_events(self.name)
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    return f.read()
        return ""

    def _build_history(
        self, prompt_text: str, is_speak: bool = False
    ) -> List[Dict[str, str]]:
        history = []

        # 1. Memory / Context
        if self.game_logger:
            log_content = self._get_memory()
            # 总是带上 memory 以保持上下文连贯
            if log_content or is_speak:
                context_reminder = self.prompts.get("REMINDER", "").format(
                    self.name, self.role
                )

                # Werewolf specific reminder logic
                if (
                    "请发言或输入 '0' 准备投票" in prompt_text
                    and self.role == "Werewolf"
                ):
                    context_reminder += self.prompts.get("REMINDER_WEREWOLF", "")
                    if self.is_first_night:
                        self.is_first_night = False
                        context_reminder += self.prompts.get("REMINDER_FIRST_NIGHT", "")

                history.append(
                    {
                        "role": "system",
                        "content": f"本场全部游戏记录：\n{log_content}\n\n{context_reminder}",
                    }
                )

        # 2. System Prompt (Identity)
        system_prompt = self.prompt
        # 强制 JSON 输出提示
        if "JSON" not in system_prompt:
            system_prompt += "\n\n[System Requirement]\nYou MUST reply in JSON format."

        history.append({"role": "system", "content": system_prompt})

        print(history)
        return history

    def _call_llm(self, history: List[Dict[str, str]]) -> str:
        try:
            model = self.config.get("model", "gpt-3.5-turbo")
            provider = self.config.get("providerId")
            api_base = self.config.get("apiBase")

            completion_kwargs = {
                "model": model,
                "messages": history,
                "stream": False,
                "response_format": {"type": "json_object"},  # 尝试启用 JSON 模式
            }

            if provider and provider != "default":
                if "/" not in model:
                    completion_kwargs["model"] = f"{provider}/{model}"

            if api_base:
                completion_kwargs["api_base"] = api_base

            response = completion(**completion_kwargs)
            return response.choices[0].message.content
        except Exception as e:
            if self.game_logger:
                self.game_logger.system_logger.error(f"AI Error: {e}")
            else:
                print(f"AI Error: {e}")
            return ""

    def speak(self, prompt_text: str) -> str:
        delay = random.uniform(2.0, 4.0)
        if self.event_emitter:
            self.event_emitter(f"{self.name} 正在组织语言...", None)
        else:
            print(f"{self.name} 正在思考...")
        time.sleep(delay)

        if os.getenv("DEBUG_GAME", "0") == "1":
            return "ai_response (debug)"

        history = self._build_history(prompt_text, is_speak=True)

        user_content = f"""
{prompt_text}

Please output in JSON format with the following keys:
- "thought": your internal thought process (reflection on the situation, strategy)
- "speech": your public statement (what other players hear)
"""
        history.append({"role": "user", "content": user_content})

        response_content = self._call_llm(history)

        try:
            # Clean potential markdown code blocks
            clean_content = (
                response_content.replace("```json", "").replace("```", "").strip()
            )
            data = json.loads(clean_content)
            speech = data.get("speech", response_content)

            if self.game_logger and "thought" in data:
                self.game_logger.system_logger.info(
                    f"Player {self.name} thought: {data['thought']}"
                )

            if self.game_logger:
                self.game_logger.system_logger.info(
                    f"Player {self.name} (AI) generated speech"
                )

            return speech
        except json.JSONDecodeError:
            # Fallback: just return the raw content if parsing fails
            return response_content

    def choose(
        self, prompt_text: str, valid_choices: List[str], allow_skip: bool = False
    ) -> str:
        delay = random.uniform(1.5, 3.0)
        if self.event_emitter:
            self.event_emitter(f"{self.name} 正在思考...", None)
        time.sleep(delay)

        if os.getenv("DEBUG_GAME", "0") == "1":
            return random.choice(valid_choices)

        history = self._build_history(prompt_text, is_speak=False)

        user_content = f"""
{prompt_text}
Valid choices: {', '.join(valid_choices)}

Please output in JSON format with the following keys:
- "thought": your internal thought process
- "choice": your final choice (must be one of the valid choices exactly)
"""
        history.append({"role": "user", "content": user_content})

        response_content = self._call_llm(history)

        try:
            clean_content = (
                response_content.replace("```json", "").replace("```", "").strip()
            )
            data = json.loads(clean_content)
            ai_choice = data.get("choice", "")

            # Exact match check
            if ai_choice in valid_choices:
                if self.game_logger:
                    self.game_logger.system_logger.info(
                        f"Player {self.name} (AI) chose: {ai_choice}"
                    )
                return ai_choice

            # Fuzzy match check
            for choice in valid_choices:
                if choice in ai_choice:
                    if self.game_logger:
                        self.game_logger.system_logger.info(
                            f"Player {self.name} (AI) chose: {choice}"
                        )
                    return choice
        except:
            pass

        # Fallback to string matching on raw response
        for choice in valid_choices:
            if choice in response_content:
                if self.game_logger:
                    self.game_logger.system_logger.info(
                        f"Player {self.name} (AI) chose: {choice}"
                    )
                return choice

        return random.choice(valid_choices)
