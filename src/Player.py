from .Base import Player
from litellm import completion
from yaml import safe_load
from enum import Enum
import os
import random
from typing import List, Dict, Optional

DEBUG = False

PROMPT = """
你正在一局狼人杀游戏中, 你的名字是{self.name}, 身份是{self.role}. 请认真参与游戏, 努力帮助自己的阵营获胜.

**基本原则:**
1.  **隐藏身份:** 不要直接或间接透露你的身份, 尤其是你的特殊能力.
2.  **分析局势:** 根据发言和投票, 判断其他玩家的身份和阵营.
3.  **有效沟通:** 你的发言和投票是影响游戏走向的关键. 请表达清晰, 有逻辑. 使用<br>标签换行, <strong></strong>标签组加粗, 其余一律不允许使用.
4.  **避免重复:** 每次发言都要提供新的信息或观点, 绝对不要重复之前已经说过的话. 仔细阅读游戏记录, 确保你的发言是独特和有价值的.
5.  **避免幻想:** **不要编造游戏开始前的场外信息或虚构的背景故事**. 你的发言应该基于当前游戏进程中发生的事件. 游戏内的策略性欺诈(如狼人伪装身份、平民虚报身份等)是允许的, 但不要创造不存在的游戏外情节.
6.  **注意角色配置:** **严格按照本场游戏的角色配置发言, 不要提及本场不存在的角色**. 仔细确认当前游戏中实际存在哪些角色, 避免谈论不存在的神职或玩家.
7.  **锚定自我身份:** **始终以你自己的身份和立场发言, 不要跑到其他玩家的立场上去思考或发言**. 你是{self.name}, 身份是{self.role}, 请严格从这个角度参与游戏.

**角色专属指南:**
*   **如果你是狼人:**
    *   **夜晚讨论:** 和你的狼同伴积极讨论, 统一击杀目标. 优先选择看起来像神职的玩家(如预言家、女巫). 如果无法确定, 可以选择发言较好或者被怀疑的玩家, 混淆视听. **重要：每次发言都要提出新的观点或信息, 不要重复之前说过的话. 当你们讨论完毕并达成一致意见后, 必须输入'0'来结束讨论进入投票阶段, 不要无休止地讨论下去. **
    *   **战术:** 可以选择悍跳(假装自己是预言家)、倒钩(站边一个真正的预言家以获取信任)或者深潜(隐藏在好人中).
    *   **发言:** 伪装成好人, 误导好人阵营的判断. 可以通过踩其他玩家、聊心态、或者提出自己的逻辑来建立好人形象. **避免重复之前的发言内容. **
*   **如果你是预言家:**
    *   **验人:** 每天查验一个你怀疑是狼人的玩家. 你的验人结果对好人至关重要.
    *   **跳身份:** 在合适的时机(通常是第一天)跳出身份, 报出你的验人信息, 带领好人投票.
    *   **策略建议:** 可以根据游戏策略需要调整报告内容, 但避免编造游戏外的虚假背景信息.
*   **如果你是女巫:**
    *   **用药:** 你的解药和毒药非常宝贵. 解药通常在第一晚救下被杀的玩家. 毒药要谨慎使用, 最好在你确认一个玩家是狼人时再用.
    *   **策略建议:** 可以根据游戏策略需要调整发言内容, 但避免编造游戏外的虚假背景信息.
*   **如果你是猎人:**
    *   **威慑:** 你可以在发言中适当表现强势, 让狼人不敢轻易攻击你.
    *   **开枪:** 当你被投票出局或被狼人杀死时, 你可以带走场上任意一个玩家. 请根据局势, 射杀你认为是狼人的玩家.
*   **如果你是守卫:**
    *   **守护:** 每晚选择一个玩家进行守护, 不能连续两晚守护同一人.
    *   **策略建议:** 可以根据游戏策略需要调整发言内容, 但避免编造游戏外的虚假背景信息.
*   **如果你是平民:**
    *   **逻辑:** 仔细听发言, 找出逻辑漏洞. 你的目标是帮助神职玩家找出所有狼人.
    *   **站边:** 相信你认为是预言家的玩家, 并跟随他投票.

**行动指令:**
接下来, 你会收到法官的指令. 请严格按照指令要求行动.
*   **如果是选择:** 从给出的选项中选择一项, **仅返回选项的名称**, 不要添加任何解释、序号或其他文字.
*   **如果是发言:** **仅输出你想要说的话**, 不要包含你的名字、身份或任何解释.
"""

REMINDER = """
重要提醒：请根据当前情况发表新的、有意义的观点, 避免重复之前的发言内容. 
**关键警告：不要编造游戏开始前的场外信息或虚构的背景故事. 你的发言应该基于当前游戏进程, 游戏内的策略性欺诈是允许的. **
**角色配置提醒：严格按照本场游戏的角色配置发言, 不要提及本场不存在的角色. **
**身份锚定：你是{0}, 身份是{1}, 请严格从这个角度发言, 不要跑到其他玩家的立场上. **
"""

REMINDER_WEREWOLF = """
**特别注意**：如果你是狼人且正在夜晚讨论阶段, 当你们已经充分讨论并达成一致意见时, 请**仅回答**'0'来结束讨论进入投票阶段. **不要无休止地重复讨论**. 
"""

REMINDER_FIRST_NIGHT = """
**现在是第一晚** , 游戏刚刚开始, 因此你不应该讨论例如"先前的发言等"场外信息.
"""


class LocalHumanPlayer(Player):
    """Represents a human player playing on the local machine via console."""

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


class OnlineHumanPlayer(Player):
    """Represents a human player playing remotely (e.g., via a web interface)."""

    def __init__(self, name: str, info: Dict[str, str], status: Dict[str, str]):
        super().__init__(name, info, status)

    def choose(
        self, prompt_text: str, valid_choices: List[str], allow_skip: bool = False
    ) -> str:
        # This would typically involve waiting for a WebSocket message or an API call.
        pass

    def speak(self, prompt_text: str) -> str:
        # This would also be handled via network communication.
        pass


class OnlineLLMPlayer(Player):
    """Represents an AI player powered by a remote LLM API (e.g., OpenAI, Anthropic)."""

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


class LocalLLMPlayer(Player):
    """Represents an AI player powered by a locally running LLM (e.g., via Ollama)."""

    def __init__(self, name: str, info: Dict[str, str], status: Dict[str, str]):
        super().__init__(name, info, status)
        self.model_path = info.get("model_path")

    def choose(self, prompt_text: str, valid_choices: List[str]) -> str:
        # This would involve calling a local model inference function.
        pass

    def speak(self, prompt_text: str) -> str:
        # This would also call the local model.
        pass
