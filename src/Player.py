import os
from typing import Dict, List, Any
from litellm import completion


class Player:
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

    def call_ai_response(self, prompt_text: str, valid_choices: List[str]):
        # 增加思考延迟，提升游戏节奏感
        import time
        import random

        delay = random.uniform(1.5, 3.0)
        if self.event_emitter:
            self.event_emitter(f"{self.name} 正在思考...", None)
        time.sleep(delay)

        # 检查环境或配置中的调试标志，这里我们假设通过配置或 os 传递
        if os.getenv("DEBUG_GAME", "0") == "1":
            return random.choice(valid_choices)

        history = []
        if self.game_logger:
            log_file = self.game_logger.get_events(self.name)
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    log_content = f.read()

                    # 使用注入的模板构建上下文提醒
                    context_reminder = self.prompts.get("REMINDER", "").format(
                        self.name, self.role
                    )

                    # 狼人夜间讨论提醒的逻辑
                    # 注意：此逻辑略微特定于游戏，但依赖于提示词的存在
                    if (
                        "请发言或输入 '0' 准备投票" in prompt_text
                        and self.role == "Werewolf"
                    ):
                        context_reminder += self.prompts.get("REMINDER_WEREWOLF", "")
                        if self.is_first_night:
                            self.is_first_night = False
                            context_reminder += self.prompts.get(
                                "REMINDER_FIRST_NIGHT", ""
                            )

                    history.append(
                        {
                            "role": "system",
                            "content": f"本场全部游戏记录：\n{log_content}\n\n{context_reminder}",
                        }
                    )

        history.append({"role": "system", "content": self.prompt})
        prompt = f"{prompt_text}\n请从以下选项中选择: {', '.join(valid_choices)}"
        history.append({"role": "user", "content": prompt})

        try:
            model = self.config.get("model", "gpt-3.5-turbo")
            provider = self.config.get("providerId")
            api_base = self.config.get("apiBase")

            # 构建 completion 参数
            completion_kwargs = {
                "model": model,
                "messages": history,
                "stream": False,
            }

            # 如果指定了 provider，且 model 中没有包含 /，则尝试组合
            # 或者直接作为参数传递（取决于 litellm 版本，通常 model="provider/model_name" 是推荐方式）
            if provider and provider != "default":
                # 对于某些 provider，可能需要显式传递 custom_llm_provider 或者修改 model 字符串
                # 如果 model 已经包含了 provider（例如 "openai/gpt-4"），则不重复添加
                if "/" not in model:
                    completion_kwargs["model"] = f"{provider}/{model}"

            if api_base:
                completion_kwargs["api_base"] = api_base

            response = completion(**completion_kwargs)

            ai_choice = response.choices[0].message.content
            for choice in valid_choices:
                if choice in ai_choice:
                    if self.game_logger:
                        self.game_logger.system_logger.info(
                            f"Player {self.name} (AI) chose: {choice}"
                        )
                    return choice
            # 兜底
            import random

            return random.choice(valid_choices)
        except Exception as e:
            if self.game_logger:
                self.game_logger.system_logger.error(
                    f"AI Error in call_ai_response: {e}"
                )
            else:
                print(f"AI Error: {e}")
            import random

            return random.choice(valid_choices)

    def call_human_response(
        self, prompt_text: str, valid_choices: List[str], allow_skip: bool = False
    ):
        if self.input_handler:
            while True:
                response = self.input_handler(
                    self.name, "choice", prompt_text, valid_choices, allow_skip
                )

                # 验证输入
                if allow_skip and response.lower() == "skip":
                    return "skip"

                if response in valid_choices:
                    return response

                # 如果输入是索引（数字），尝试转换
                if response.isdigit():
                    idx = int(response) - 1
                    if 0 <= idx < len(valid_choices):
                        return valid_choices[idx]

                # 如果都不匹配，发送错误提示并重试
                # 注意：我们需要一种方式通知玩家输入无效。
                # 简单起见，我们可以再次调用 input_handler，并在 prompt 中加入错误提示
                prompt_text = f"[无效输入，请重试] {prompt_text}"

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

            print("[bold red]无效的选择, 请重新输入. [/bold red]")

    def call_ai_speak(self, prompt_text: str):
        import time
        import random

        delay = random.uniform(2.0, 4.0)
        if self.event_emitter:
            self.event_emitter(f"{self.name} 正在组织语言...", None)
        else:
            print(f"{self.name} 正在思考...")
        time.sleep(delay)

        if os.getenv("DEBUG_GAME", "0") == "1":
            return "ai_response (debug)"

        history = []
        if self.game_logger:
            log_file = self.game_logger.get_events(self.name)
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    log_content = f.read()
                    if log_content.strip():
                        context_reminder = self.prompts.get("REMINDER", "").format(
                            self.name, self.role
                        )
                        if (
                            "请发言或输入 '0' 准备投票" in prompt_text
                            and self.role == "Werewolf"
                        ):
                            context_reminder += self.prompts.get(
                                "REMINDER_WEREWOLF", ""
                            )

                        context_prompt = (
                            f"游戏记录:\n{log_content}\n\n{context_reminder}"
                        )
                        history.append({"role": "system", "content": context_prompt})

        history.append({"role": "system", "content": self.prompt})
        history.append({"role": "user", "content": prompt_text})

        try:
            model = self.config.get("model", "gpt-3.5-turbo")
            provider = self.config.get("providerId")
            api_base = self.config.get("apiBase")

            # 构建 completion 参数
            completion_kwargs = {
                "model": model,
                "messages": history,
                "stream": False,
            }

            if provider and provider != "default":
                if "/" not in model:
                    completion_kwargs["model"] = f"{provider}/{model}"

            if api_base:
                completion_kwargs["api_base"] = api_base

            response = completion(**completion_kwargs)

            speech = response.choices[0].message.content
            if self.game_logger:
                self.game_logger.system_logger.info(
                    f"Player {self.name} (AI) generated speech"
                )
            return speech
        except Exception as e:
            if self.game_logger:
                self.game_logger.system_logger.error(f"AI Error in call_ai_speak: {e}")
            return f"(生成演讲时出错: {e})"

    def call_human_speak(self, prompt_text: str):
        if self.input_handler:
            return self.input_handler(self.name, "speech", prompt_text, [], False)
        return input(prompt_text)

    def speak(self, prompt_text: str):
        if self.is_human:
            return self.call_human_speak(prompt_text)
        else:
            return self.call_ai_speak(prompt_text)

    def choose(
        self, prompt_text: str, valid_choices: List[str], allow_skip: bool = False
    ) -> str:
        if self.is_human:
            return self.call_human_response(prompt_text, valid_choices, allow_skip)
        else:
            return self.call_ai_response(prompt_text, valid_choices)
