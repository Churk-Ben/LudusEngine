import random
import yaml
import time
from typing import List, Dict, Optional
from pathlib import Path
from enum import Enum
import os
from datetime import datetime
from litellm import completion
from yaml import safe_load


# models.py
class Role(Enum):
    WEREWOLF = "werewolf"
    VILLAGER = "villager"
    SEER = "seer"
    WITCH = "witch"
    HUNTER = "hunter"
    GUARD = "guard"


class DeathReason(Enum):
    KILLED_BY_WEREWOLF = "在夜晚被杀害"
    POISONED_BY_WITCH = "被女巫毒杀"
    VOTED_OUT = "被投票出局"
    SHOT_BY_HUNTER = "被猎人带走"


# logger.py
class GameLogger:
    def __init__(self, base_log_dir="logs"):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = os.path.join(base_log_dir, self.timestamp)
        self.player_log_files: Dict[str, str] = {}
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _log(self, file_path, message):
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
            f.flush()

    def _get_player_log_file(self, player_name: str) -> str:
        if player_name not in self.player_log_files:
            self.player_log_files[player_name] = os.path.join(
                self.log_dir, f"{player_name}.txt"
            )
        return self.player_log_files[player_name]

    def log_event(self, message: str, visible_to: List[str]):
        for player_name in visible_to:
            log_file = self._get_player_log_file(player_name)
            self._log(log_file, message)

    def log_public_event(self, message: str, all_players: List[str]):
        self.log_event(message, all_players)

    def close(self):
        for log_file in self.player_log_files.values():
            try:
                os.close(log_file)
            except OSError:
                pass


# player.py
DEBUG = False
with open("config.yaml", "r", encoding="utf-8") as f:
    config = safe_load(f)
    DEBUG = config["debug"]

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


class Player:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.prompt = PROMPT.format(self=self)
        self.is_alive = True
        self.is_guarded = False
        self.config = None
        self.bind_config()
        self.is_human = self.config["human"]
        self.game_logger = None
        self.is_first_night = True

    def bind_config(self):
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = safe_load(f)
            for player in config["players"]:
                if player["name"] == self.name:
                    self.config = player
                    break

    def set_logger(self, logger):
        self.game_logger = logger

    def call_ai_response(self, prompt_text: str, valid_choices: List[str]):
        if DEBUG:
            return random.choice(valid_choices)

        history = []
        if self.game_logger:
            log_file = self.game_logger._get_player_log_file(self.name)
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    log_content = f.read()
                    context_reminder = REMINDER.format(self.name, self.role)
                    if (
                        "请发言或输入 '0' 准备投票" in prompt_text
                        and self.role == "Werewolf"
                    ):
                        context_reminder += REMINDER_WEREWOLF
                        if self.is_first_night:
                            self.is_first_night = False
                            context_reminder += REMINDER_FIRST_NIGHT
                    history.append(
                        {
                            "role": "system",
                            "content": f"本场全部游戏记录：\n{log_content}\n\n{context_reminder}",
                        }
                    )

        history.append({"role": "system", "content": self.prompt})
        prompt = f"{prompt_text}\n请从以下选项中选择: {', '.join(valid_choices)}"
        history.append({"role": "user", "content": prompt})

        response = completion(
            model=self.config["model"],
            messages=history,
            stream=False,
        )
        ai_choice = response.choices[0].message.content
        for choice in valid_choices:
            if choice in ai_choice:
                return choice
        return random.choice(valid_choices)

    def call_human_response(
        self, prompt_text: str, valid_choices: List[str], allow_skip: bool = False
    ):
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
                    selected_choice = display_choices[choice_index]
                    return selected_choice

            if allow_skip and player_input_lower == "skip":
                return "skip"

            for choice in valid_choices:
                if choice.lower() == player_input_lower:
                    return choice

            print("[bold red]无效的选择, 请重新输入. [/bold red]")

    def call_ai_speak(self, prompt_text: str):
        if DEBUG:
            return "ai_response<br>, and <strong>ai_response</strong>"
        history = []
        if self.game_logger:
            log_file = self.game_logger._get_player_log_file(self.name)
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    log_content = f.read()
                    if log_content.strip():
                        context_reminder = REMINDER.format(self.name, self.role)
                        if (
                            "请发言或输入 '0' 准备投票" in prompt_text
                            and self.role == "Werewolf"
                        ):
                            context_reminder += REMINDER_WEREWOLF
                        context_prompt = (
                            f"游戏记录:\n{log_content}\n\n{context_reminder}"
                        )
                        history.append({"role": "system", "content": context_prompt})

        history.append({"role": "system", "content": self.prompt})
        prompt = f"{prompt_text}"
        history.append({"role": "user", "content": prompt})

        print(f"{self.name} 正在思考...")
        response = completion(
            model=self.config["model"],
            messages=history,
            stream=False,
        )
        speech = response.choices[0].message.content
        return speech

    def call_human_speak(self, prompt_text: str):
        return input(prompt_text)

    def speak(self, prompt_text: str):
        if self.is_human:
            return self.call_human_speak(prompt_text)
        else:
            return self.call_ai_speak(prompt_text)


# ui.py
def prompt_for_choice(
    player: "Player",
    prompt_text: str,
    valid_choices: List[str],
    allow_skip: bool = False,
) -> str:
    if player.is_human:
        return player.call_human_response(prompt_text, valid_choices, allow_skip)
    else:
        return player.call_ai_response(prompt_text, valid_choices)


# Game.py
class WerewolfGame:
    def __init__(self):
        self.players: Dict[str, Player] = {}
        self.roles: Dict[str, int] = {}
        self.all_player_names: List[str] = []
        self.killed_player: Optional[str] = None
        self.last_guarded: Optional[str] = None
        self.witch_save_used = False
        self.witch_poison_used = False
        self.day_number = 0
        self.logger = GameLogger()

    def _get_alive_players(self, roles: Optional[List[Role]] = None) -> List[str]:
        alive_players = []
        role_values = []
        if roles:
            for r in roles:
                role_values.append(r.value)

        for name, p in self.players.items():
            if p.is_alive:
                if roles is None or p.role in role_values:
                    alive_players.append(name)
        return alive_players

    def _get_player_by_role(self, role: Role) -> Optional[Player]:
        for p in self.players.values():
            if p.role == role.value and p.is_alive:
                return p
        return None

    def _cancel(self):
        self.logger.log_public_event(
            f"游戏已取消.",
            self.all_player_names,
        )
        self.logger.close()
        self.players.clear()
        self.roles.clear()
        self.all_player_names.clear()
        self.killed_player = None
        self.last_guarded = None
        self.witch_save_used = False
        self.witch_poison_used = False
        self.day_number = 0

    def setup_game(self):
        try:
            with open("config.yaml", "r", encoding="utf-8") as file:
                config = yaml.safe_load(file)
                player_count = len(config["players"])
                player_names = [player["name"] for player in config["players"]]
                self.all_player_names = player_names

        except (FileNotFoundError, KeyError, ValueError):
            print("#! 配置文件有错, 请检查配置文件.")

        except Exception as e:
            print(f"#! 未知错误: {str(e)}")

        if player_count == 6:
            self.roles = {
                Role.WEREWOLF.value: 2,
                Role.VILLAGER.value: 2,
                Role.SEER.value: 1,
                Role.WITCH.value: 1,
            }

        else:
            self.roles = {
                Role.WEREWOLF.value: max(1, player_count // 4),
                Role.SEER.value: 1,
                Role.WITCH.value: 1,
                Role.HUNTER.value: 1,
                Role.GUARD.value: 1,
            }
            self.roles[Role.VILLAGER.value] = player_count - sum(self.roles.values())

        print("#@ 本局游戏角色配置")
        role_config = []
        for role, count in self.roles.items():
            if count > 0:
                role_config.append(f"{role.capitalize()} {count}人")
        print("#@ " + ", ".join(role_config))

        self.logger.log_public_event(
            f"本局玩家人数: {player_count}",
            self.all_player_names,
        )
        self.logger.log_public_event(
            f"角色卡配置: {role_config}",
            self.all_player_names,
        )
        self.logger.log_public_event(
            f"玩家 {player_names} 已加入游戏.",
            self.all_player_names,
        )

        role_list = []
        for role, count in self.roles.items():
            for _ in range(count):
                role_list.append(role)
        random.shuffle(role_list)

        for name, role in zip(player_names, role_list):
            player = Player(name, role)
            player.set_logger(self.logger)
            self.players[name] = player

        werewolves = self._get_alive_players([Role.WEREWOLF])

        print("#@ 角色分配完成, 正在分发身份牌...")
        for name, player in self.players.items():
            time.sleep(0.3)
            print(f"\n{name}, 你的身份是: {player.role.capitalize()}")
            if player.role == Role.WEREWOLF.value:
                teammates = []
                for w in werewolves:
                    if w != name:
                        teammates.append(w)
                if teammates:
                    print(f"你的狼人同伴是: {', '.join(teammates)}")
                else:
                    print("你是唯一的狼人")

        self.logger.log_public_event(
            "角色分配完成, 正在分发身份牌...",
            self.all_player_names,
        )

        for name, player in self.players.items():
            self.logger.log_event(
                f"你的身份是: {player.role.capitalize()}",
                [player.name],
            )

            if player.role == Role.WEREWOLF.value:
                teammates = []
                for w in werewolves:
                    if w != name:
                        teammates.append(w)
                if teammates:
                    self.logger.log_event(
                        f"你的狼人同伴是: {', '.join(teammates)}",
                        [player.name],
                    )
                else:
                    self.logger.log_event(
                        "你是唯一的狼人",
                        [player.name],
                    )

        print("#: 游戏开始. 天黑, 请闭眼.")
        self.logger.log_public_event(
            "游戏开始. 天黑, 请闭眼.",
            self.all_player_names,
        )

    def night_phase(self):
        self.day_number += 1
        print(f"#@ 第 {self.day_number} 天夜晚降临")
        self.logger.log_public_event(
            f"第 {self.day_number} 天夜晚降临",
            self.all_player_names,
        )
        self.killed_player = None
        for p in self.players.values():
            p.is_guarded = False
        alive_players = self._get_alive_players()

        guard = self._get_player_by_role(Role.GUARD)
        if guard:
            print("#@ 守卫请睁眼")
            prompt = f"守卫, 请选择你要守护的玩家 (不能连续两晚守护同一个人): "
            self.logger.log_event(
                "守卫请睁眼" + prompt,
                [guard.name],
            )

            valid_targets = []
            for p in alive_players:
                if p != self.last_guarded:
                    valid_targets.append(p)
            target = prompt_for_choice(guard, prompt, valid_targets)

            self.players[target].is_guarded = True
            self.last_guarded = target

            print("#@ 守卫请闭眼")
            self.logger.log_event(
                f"你守护了 {target}",
                [guard.name],
            )
            self.logger.log_public_event(
                f"守卫行动了",
                self.all_player_names,
            )

        werewolves = self._get_alive_players([Role.WEREWOLF])
        if werewolves:
            print("#@ 狼人请睁眼")
            print(f"#@ 现在的狼人有: {', '.join(werewolves)}")
            self.logger.log_event(
                "狼人请睁眼" + f"现在的狼人有: {', '.join(werewolves)}",
                werewolves,
            )

            if len(werewolves) == 1:
                print("#@ 独狼无需讨论，直接进入投票阶段")
                self.logger.log_event(
                    "独狼无需讨论，直接进入投票阶段",
                    werewolves,
                )
            else:
                print("#@ 狼人请开始讨论")
                print("#@ 请轮流发言, 输入 '0' 表示准备好投票")
                self.logger.log_event(
                    "狼人请开始讨论, 输入 '0' 表示发言结束, 准备投票",
                    werewolves,
                )
                ready_to_vote = set()
                discussion_rounds = 0
                max_discussion_rounds = 5

                while (
                    len(ready_to_vote) < len(werewolves)
                    and discussion_rounds < max_discussion_rounds
                ):
                    discussion_rounds += 1
                    for wolf in werewolves:
                        if wolf in ready_to_vote:
                            continue
                        wolf_player = self.players[wolf]
                        action = wolf_player.speak(
                            f"{wolf}, 请发言或输入 '0' 准备投票: "
                        )
                        if action == "0":
                            ready_to_vote.add(wolf)
                            print(
                                f"#@ ({wolf} 已准备好投票 {len(ready_to_vote)}/{len(werewolves)})"
                            )
                            self.logger.log_event(
                                f"({wolf} 已准备好投票 {len(ready_to_vote)}/{len(werewolves)})",
                                werewolves,
                            )
                        elif action:
                            print(f"#: [狼人频道] {wolf} 发言: {action}")
                            self.logger.log_event(
                                f"[狼人频道] {wolf} 发言: {action}",
                                werewolves,
                            )

                if discussion_rounds >= max_discussion_rounds and len(
                    ready_to_vote
                ) < len(werewolves):
                    print(
                        f"#@ 讨论已达到最大轮次({max_discussion_rounds}轮)，强制进入投票阶段"
                    )
                    self.logger.log_event(
                        f"讨论已达到最大轮次({max_discussion_rounds}轮)，强制进入投票阶段",
                        werewolves,
                    )
                    ready_to_vote = set(werewolves)

            print("#@ 狼人请投票")
            self.logger.log_event(
                "狼人请投票",
                werewolves,
            )
            while True:
                votes = {name: 0 for name in alive_players}
                for wolf_name in werewolves:
                    wolf_player = self.players[wolf_name]
                    prompt = f"{wolf_name}, 请投票选择要击杀的目标: "
                    target = prompt_for_choice(wolf_player, prompt, alive_players)
                    votes[target] += 1

                max_votes = 0
                kill_targets = []
                if votes:
                    max_votes = max(votes.values())
                    if max_votes > 0:
                        kill_targets = []
                        for name, count in votes.items():
                            if count == max_votes:
                                kill_targets.append(name)

                if len(kill_targets) == 1:
                    self.killed_player = kill_targets[0]
                    print(f"#@ 狼人达成一致, 选择了击杀 {self.killed_player}")
                    self.logger.log_event(
                        f"狼人投票决定击杀 {self.killed_player}",
                        werewolves,
                    )
                    break
                else:
                    print("#@ 狼人投票出现平票, 请重新商议并投票")
                    self.logger.log_event(
                        "狼人投票出现平票, 请重新商议并投票",
                        werewolves,
                    )

            print(f"#@ 狼人请闭眼")
            self.logger.log_event(
                f"你击杀了 {self.killed_player}",
                werewolves,
            )
            self.logger.log_public_event(
                f"狼人行动了",
                self.all_player_names,
            )

        seer_player = self._get_player_by_role(Role.SEER)
        if seer_player:
            print("#@ 预言家请睁眼")
            prompt = "预言家, 请选择要查验的玩家: "
            self.logger.log_event(
                "预言家请睁眼. 请选择要你要查验的玩家: ",
                [seer_player.name],
            )
            target = prompt_for_choice(seer_player, prompt, alive_players)

            role = self.players[target].role
            identity = "狼人" if role == Role.WEREWOLF.value else "好人"
            print(f"#@ 查验结果: {target} 的身份是 {identity}")

            print("#@ 预言家请闭眼")
            self.logger.log_event(
                f"你查验了 {target} 的身份, 结果为 {identity}",
                [seer_player.name],
            )
            self.logger.log_public_event(
                f"预言家行动了",
                self.all_player_names,
            )

        witch_player = self._get_player_by_role(Role.WITCH)
        if witch_player:
            print("#@ 女巫请睁眼")
            self.logger.log_event(
                "女巫请睁眼",
                [witch_player.name],
            )

            if self.killed_player and self.players[self.killed_player].is_guarded:
                print(f"#@ 今晚是个平安夜, {self.killed_player} 被守护了")
                self.logger.log_public_event(
                    f"今晚是个平安夜, {self.killed_player} 被守护了",
                    self.all_player_names,
                )
                actual_killed = None
            else:
                if self.killed_player:
                    print(f"#@ 今晚 {self.killed_player} 被杀害了")
                    self.logger.log_event(
                        f"今晚 {self.killed_player} 被杀害了",
                        [witch_player.name],
                    )
                actual_killed = self.killed_player

            if not self.witch_save_used and actual_killed:
                prompt = f"女巫, 你要使用解药吗? "
                if prompt_for_choice(witch_player, prompt, ["y", "n"]) == "y":
                    actual_killed = None
                    self.witch_save_used = True
                    print(f"#@ 你使用解药救了 {self.killed_player}")
                    self.logger.log_event(
                        f"你使用解药救了 {self.killed_player}",
                        [witch_player.name],
                    )
                    self.logger.log_public_event(
                        f"女巫使用了解药",
                        self.all_player_names,
                    )

            if not self.witch_poison_used:
                prompt = "女巫, 你要使用毒药吗? "
                if prompt_for_choice(witch_player, prompt, ["y", "n"]) == "y":
                    poison_prompt = "请选择要毒杀的玩家: "
                    target = prompt_for_choice(
                        witch_player, poison_prompt, alive_players
                    )
                    if actual_killed is None:
                        actual_killed = target
                    else:
                        self.handle_death(target, DeathReason.POISONED_BY_WITCH)
                    self.witch_poison_used = True
                    print(f"#@ 你使用毒药毒了 {target} ")
                    self.logger.log_event(
                        f"你使用毒药毒了 {target}",
                        [witch_player.name],
                    )
                    self.logger.log_public_event(
                        f"女巫使用了毒药",
                        self.all_player_names,
                    )
            self.killed_player = actual_killed

            print("#@ 女巫请闭眼")
            self.logger.log_public_event(
                f"女巫行动了",
                self.all_player_names,
            )

    def handle_death(self, player_name: str, reason: DeathReason):
        if player_name and self.players[player_name].is_alive:
            self.players[player_name].is_alive = False
            print(f"#! {player_name} 死了, 原因是{reason.value}")
            self.logger.log_public_event(
                f"{player_name} 死了, 原因是 {reason.value}",
                self.all_player_names,
            )

            is_first_night_death = self.day_number == 1 and reason in [
                DeathReason.KILLED_BY_WEREWOLF,
                DeathReason.POISONED_BY_WITCH,
            ]
            can_have_last_words = (
                reason in [DeathReason.VOTED_OUT, DeathReason.SHOT_BY_HUNTER]
                or is_first_night_death
            )

            if can_have_last_words:
                player = self.players[player_name]
                last_words = player.speak(f"{player_name}, 请发表你的遗言: ")
                if last_words:
                    print(f"#: [遗言] {player_name} 发言: {last_words}")
                    self.logger.log_public_event(
                        f"[遗言] {player_name} 发言: {last_words}",
                        self.all_player_names,
                    )
                else:
                    print(f"#@ {player_name} 选择保持沉默, 没有留下遗言")
                    self.logger.log_public_event(
                        f"{player_name} 选择保持沉默, 没有留下遗言",
                        self.all_player_names,
                    )

            if self.players[player_name].role == Role.HUNTER.value:
                self.handle_hunter_shot(player_name)

    def handle_hunter_shot(self, hunter_name: str):
        print(f"#@ {hunter_name} 是猎人, 可以在临死前开枪带走一人")
        self.logger.log_public_event(
            f"{hunter_name} 是猎人, 可以在临死前开枪带走一人",
            self.all_player_names,
        )
        alive_players_for_shot = []
        for p in self._get_alive_players():
            if p != hunter_name:
                alive_players_for_shot.append(p)
        hunter_player = self.players[hunter_name]
        prompt = f"{hunter_name}, 请选择你要带走的玩家: "
        target = prompt_for_choice(
            hunter_player, prompt, alive_players_for_shot, allow_skip=True
        )

        if target == "skip":
            print("#@ 猎人放弃了开枪")
            self.logger.log_public_event(
                "猎人放弃了开枪",
                self.all_player_names,
            )
        else:
            self.logger.log_public_event(
                f"猎人 {hunter_name} 开枪带走了 {target}",
                self.all_player_names,
            )
            self.handle_death(target, DeathReason.SHOT_BY_HUNTER)

    def day_phase(self):
        print("#: 天亮了.")
        print(f"#@ 现在是第 {self.day_number} 天白天")
        self.logger.log_public_event(
            f"天亮了. 现在是第 {self.day_number} 天白天",
            self.all_player_names,
        )

        if self.killed_player:
            self.handle_death(self.killed_player, DeathReason.KILLED_BY_WEREWOLF)
        else:
            print("#@ 今晚是平安夜")
            self.logger.log_public_event(
                "今晚是平安夜",
                self.all_player_names,
            )

        if self.check_game_over():
            return

        alive_players = self._get_alive_players()
        print(f"#@ 场上存活的玩家: {', '.join(alive_players)}")
        self.logger.log_public_event(
            f"场上存活的玩家: {', '.join(alive_players)}",
            self.all_player_names,
        )

        for player_name in alive_players:
            player = self.players[player_name]
            speech = player.speak(f"{player_name}, 请发言: ")
            print(f"#: {player_name} 发言: {speech}")
            self.logger.log_public_event(
                f"{player_name} 发言: {speech}",
                self.all_player_names,
            )

        self.vote_phase()

    def vote_phase(self):
        alive_players = self._get_alive_players()
        print("#@ 请开始投票")
        self.logger.log_public_event(
            "请开始投票",
            self.all_player_names,
        )

        votes = {name: 0 for name in alive_players}
        for voter_name in alive_players:
            voter = self.players[voter_name]
            prompt = f"{voter_name}, 请投票: "
            target = prompt_for_choice(voter, prompt, alive_players)
            votes[target] += 1
            print(f"#: {voter_name} 投票给 {target}")
            self.logger.log_public_event(
                f"{voter_name} 投票给 {target}",
                self.all_player_names,
            )

        max_votes = max(votes.values())
        voted_out_players = [
            name for name, count in votes.items() if count == max_votes
        ]

        if len(voted_out_players) == 1:
            voted_out_player = voted_out_players[0]
            print(f"#! 投票结果: {voted_out_player} 被投票出局")
            self.logger.log_public_event(
                f"投票结果: {voted_out_player} 被投票出局",
                self.all_player_names,
            )
            self.handle_death(voted_out_player, DeathReason.VOTED_OUT)
        else:
            print("#@ 投票平票, 无人出局")
            self.logger.log_public_event(
                "投票平票, 无人出局",
                self.all_player_names,
            )

    def check_game_over(self):
        alive_werewolves = self._get_alive_players([Role.WEREWOLF])
        alive_villagers = self._get_alive_players(
            [Role.VILLAGER, Role.SEER, Role.WITCH, Role.HUNTER, Role.GUARD]
        )

        if not alive_werewolves:
            print("#! 游戏结束, 好人阵营胜利!")
            self.logger.log_public_event(
                "游戏结束, 好人阵营胜利!",
                self.all_player_names,
            )
            return True
        elif len(alive_werewolves) >= len(alive_villagers):
            print("#! 游戏结束, 狼人阵营胜利!")
            self.logger.log_public_event(
                "游戏结束, 狼人阵营胜利!",
                self.all_player_names,
            )
            return True
        return False

    def run_game(self):
        self.setup_game()
        while not self.check_game_over():
            self.night_phase()
            if self.check_game_over():
                break
            self.day_phase()


if __name__ == "__main__":
    game = WerewolfGame()
    game.run_game()
