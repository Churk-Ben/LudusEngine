from dataclasses import dataclass, field
from enum import Enum
import json
import time
import random
from typing import Any, Dict, List, Optional
from pathlib import Path
import sys

# Ensure project root is in path (for direct execution)
BASE = Path(__file__).resolve().parent.parent.parent
if str(BASE) not in sys.path:
    sys.path.append(str(BASE))

from src.Game import Game, GameAction, GamePhase, GameStep, ActionContext
from src.Player import Player
from src.Logger import (
    GameLogger,
)  # Imported for type hinting if needed, though Game handles instantiation

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# Concrete Actions Implementation
# -----------------------------------------------------------------------------


class NightStartAction(GameAction):
    def description(self) -> str:
        return "入夜初始化"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        game.day_number += 1
        print(f"#@ 第 {game.day_number} 天夜晚降临")
        game.logger.log_event(f"第 {game.day_number} 天夜晚降临", game.all_player_names)
        game.killed_player = None
        for p in game.players.values():
            p.is_guarded = False


class DayStartAction(GameAction):
    def description(self) -> str:
        return "天亮初始化"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        print("#: 天亮了.")
        print(f"#@ 现在是第 {game.day_number} 天白天")
        game.logger.log_event(
            f"天亮了. 现在是第 {game.day_number} 天白天", game.all_player_names
        )

        if game.killed_player:
            game.handle_death(game.killed_player, DeathReason.KILLED_BY_WEREWOLF)
        else:
            print("#@ 今晚是平安夜")
            game.logger.log_event("今晚是平安夜", game.all_player_names)


class GuardAction(GameAction):
    def description(self) -> str:
        return "守卫守护"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        guard = game._get_player_by_role(Role.GUARD)
        if not guard:
            return

        print("#@ 守卫请睁眼")
        prompt = "守卫, 请选择你要守护的玩家 (不能连续两晚守护同一个人): "
        game.logger.log_event("守卫请睁眼" + prompt, [guard.name])

        alive_players = game._get_alive_players()
        valid_targets = [p for p in alive_players if p != game.last_guarded]

        target = guard.choose(prompt, valid_targets)

        game.players[target].is_guarded = True
        game.last_guarded = target

        print("#@ 守卫请闭眼")
        game.logger.log_event(f"你守护了 {target}", [guard.name])
        game.logger.log_event("守卫行动了", game.all_player_names)


class WerewolfNightAction(GameAction):
    def description(self) -> str:
        return "狼人夜间行动"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        werewolves = game._get_alive_players([Role.WEREWOLF])
        if not werewolves:
            return

        print("#@ 狼人请睁眼")
        print(f"#@ 现在的狼人有: {', '.join(werewolves)}")
        game.logger.log_event(
            "狼人请睁眼" + f"现在的狼人有: {', '.join(werewolves)}",
            werewolves,
        )

        if len(werewolves) == 1:
            print("#@ 独狼无需讨论，直接进入投票阶段")
            game.logger.log_event("独狼无需讨论，直接进入投票阶段", werewolves)
        else:
            self._handle_discussion(game, werewolves)

        self._handle_voting(game, werewolves)

        print(f"#@ 狼人请闭眼")
        if game.killed_player:
            game.logger.log_event(f"你击杀了 {game.killed_player}", werewolves)
        game.logger.log_event("狼人行动了", game.all_player_names)

    def _handle_discussion(self, game, werewolves):
        print("#@ 狼人请开始讨论")
        print("#@ 请轮流发言, 输入 '0' 表示准备好投票")
        game.logger.log_event(
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
                wolf_player = game.players[wolf]
                action = wolf_player.speak(f"{wolf}, 请发言或输入 '0' 准备投票: ")

                if action == "0":
                    ready_to_vote.add(wolf)
                    msg = (
                        f"({wolf} 已准备好投票 {len(ready_to_vote)}/{len(werewolves)})"
                    )
                    print(f"#@ {msg}")
                    game.logger.log_event(msg, werewolves)
                elif action:
                    print(f"#: [狼人频道] {wolf} 发言: {action}")
                    game.logger.log_event(
                        f"[狼人频道] {wolf} 发言: {action}", werewolves
                    )

        if discussion_rounds >= max_discussion_rounds and len(ready_to_vote) < len(
            werewolves
        ):
            msg = f"讨论已达到最大轮次({max_discussion_rounds}轮)，强制进入投票阶段"
            print(f"#@ {msg}")
            game.logger.log_event(msg, werewolves)

    def _handle_voting(self, game, werewolves):
        alive_players = game._get_alive_players()
        print("#@ 狼人请投票")
        game.logger.log_event("狼人请投票", werewolves)

        while True:
            votes = {name: 0 for name in alive_players}
            for wolf_name in werewolves:
                wolf_player = game.players[wolf_name]
                prompt = f"{wolf_name}, 请投票选择要击杀的目标: "
                target = wolf_player.choose(prompt, alive_players)
                votes[target] += 1

            max_votes = 0
            kill_targets = []
            if votes:
                max_votes = max(votes.values())
                if max_votes > 0:
                    kill_targets = [
                        name for name, count in votes.items() if count == max_votes
                    ]

            if len(kill_targets) == 1:
                game.killed_player = kill_targets[0]
                print(f"#@ 狼人达成一致, 选择了击杀 {game.killed_player}")
                game.logger.log_event(
                    f"狼人投票决定击杀 {game.killed_player}", werewolves
                )
                break
            else:
                print("#@ 狼人投票出现平票, 请重新商议并投票")
                game.logger.log_event("狼人投票出现平票, 请重新商议并投票", werewolves)


class SeerAction(GameAction):
    def description(self) -> str:
        return "预言家查验"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        seer = game._get_player_by_role(Role.SEER)
        if not seer:
            return

        print("#@ 预言家请睁眼")
        prompt = "预言家, 请选择要查验的玩家: "
        game.logger.log_event("预言家请睁眼. 请选择要你要查验的玩家: ", [seer.name])

        alive_players = game._get_alive_players()
        target = seer.choose(prompt, alive_players)

        role = game.players[target].role
        identity = "狼人" if role == Role.WEREWOLF.value else "好人"
        print(f"#@ 查验结果: {target} 的身份是 {identity}")

        print("#@ 预言家请闭眼")
        game.logger.log_event(
            f"你查验了 {target} 的身份, 结果为 {identity}", [seer.name]
        )
        game.logger.log_event("预言家行动了", game.all_player_names)


class WitchAction(GameAction):
    def description(self) -> str:
        return "女巫毒药与解药"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        witch = game._get_player_by_role(Role.WITCH)
        if not witch:
            return

        print("#@ 女巫请睁眼")
        game.logger.log_event("女巫请睁眼", [witch.name])

        alive_players = game._get_alive_players()
        actual_killed = None

        # Check death info
        if game.killed_player:
            if game.players[game.killed_player].is_guarded:
                print(f"#@ 今晚是个平安夜, {game.killed_player} 被守护了")
                game.logger.log_event(
                    f"今晚是个平安夜, {game.killed_player} 被守护了",
                    game.all_player_names,
                )
            else:
                print(f"#@ 今晚 {game.killed_player} 被杀害了")
                game.logger.log_event(
                    f"今晚 {game.killed_player} 被杀害了", [witch.name]
                )
                actual_killed = game.killed_player

        # Save Potion
        if not game.witch_save_used and actual_killed:
            prompt = "女巫, 你要使用解药吗? "
            if witch.choose(prompt, ["y", "n"]) == "y":
                actual_killed = None
                game.witch_save_used = True
                print(f"#@ 你使用解药救了 {game.killed_player}")
                game.logger.log_event(
                    f"你使用解药救了 {game.killed_player}", [witch.name]
                )
                game.logger.log_event("女巫使用了解药", game.all_player_names)

        # Poison Potion
        if not game.witch_poison_used:
            prompt = "女巫, 你要使用毒药吗? "
            if witch.choose(prompt, ["y", "n"]) == "y":
                poison_prompt = "请选择要毒杀的玩家: "
                target = witch.choose(poison_prompt, alive_players)
                if actual_killed is None:
                    actual_killed = target
                else:
                    game.handle_death(target, DeathReason.POISONED_BY_WITCH)

                game.witch_poison_used = True
                print(f"#@ 你使用毒药毒了 {target} ")
                game.logger.log_event(f"你使用毒药毒了 {target}", [witch.name])
                game.logger.log_event("女巫使用了毒药", game.all_player_names)

        # Update killed player to the final result
        game.killed_player = actual_killed

        print("#@ 女巫请闭眼")
        game.logger.log_event("女巫行动了", game.all_player_names)


class DayDiscussionAction(GameAction):
    def description(self) -> str:
        return "白天讨论"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        alive_players = game._get_alive_players()
        print(f"#@ 场上存活的玩家: {', '.join(alive_players)}")
        game.logger.log_event(
            f"场上存活的玩家: {', '.join(alive_players)}", game.all_player_names
        )

        for player_name in alive_players:
            player = game.players[player_name]
            speech = player.speak(f"{player_name}, 请发言: ")
            print(f"#: {player_name} 发言: {speech}")
            game.logger.log_event(
                f"{player_name} 发言: {speech}", game.all_player_names
            )


class DayVoteAction(GameAction):
    def description(self) -> str:
        return "白天投票"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        alive_players = game._get_alive_players()
        print("#@ 请开始投票")
        game.logger.log_event("请开始投票", game.all_player_names)

        votes = {name: 0 for name in alive_players}
        for voter_name in alive_players:
            voter = game.players[voter_name]
            prompt = f"{voter_name}, 请投票: "
            target = voter.choose(prompt, alive_players)
            votes[target] += 1
            print(f"#: {voter_name} 投票给 {target}")
            game.logger.log_event(
                f"{voter_name} 投票给 {target}", game.all_player_names
            )

        max_votes = max(votes.values())
        voted_out_players = [
            name for name, count in votes.items() if count == max_votes
        ]

        if len(voted_out_players) == 1:
            voted_out_player = voted_out_players[0]
            print(f"#! 投票结果: {voted_out_player} 被投票出局")
            game.logger.log_event(
                f"投票结果: {voted_out_player} 被投票出局",
                game.all_player_names,
            )
            game.handle_death(voted_out_player, DeathReason.VOTED_OUT)
        else:
            print("#@ 投票平票, 无人出局")
            game.logger.log_event(
                "投票平票, 无人出局",
                game.all_player_names,
            )


# -----------------------------------------------------------------------------
# Game Class
# -----------------------------------------------------------------------------


class WerewolfGame(Game):
    def __init__(self, players: List[Dict[str, str]]):
        super().__init__("werewolf", players)
        self.roles: Dict[str, int] = {}
        self.killed_player: Optional[str] = None
        self.last_guarded: Optional[str] = None
        self.witch_save_used = False
        self.witch_poison_used = False
        # self._players_data is available from base

    def _init_phases(self):
        # Night Phase
        night = GamePhase("Night")
        night.add_step(GameStep("NightStart", [], NightStartAction()))
        night.add_step(GameStep("Guard", [Role.GUARD], GuardAction()))
        night.add_step(GameStep("Werewolf", [Role.WEREWOLF], WerewolfNightAction()))
        night.add_step(GameStep("Seer", [Role.SEER], SeerAction()))
        night.add_step(GameStep("Witch", [Role.WITCH], WitchAction()))
        self.phases.append(night)

        # Day Phase
        day = GamePhase("Day")
        day.add_step(GameStep("DayStart", [], DayStartAction()))
        day.add_step(GameStep("Discussion", [], DayDiscussionAction()))
        day.add_step(GameStep("Vote", [], DayVoteAction()))
        self.phases.append(day)

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
        self.logger.log_event(
            f"游戏已取消.",
            self.all_player_names,
        )
        self.players.clear()
        self.roles.clear()
        self.all_player_names.clear()
        self.killed_player = None
        self.last_guarded = None
        self.witch_save_used = False
        self.witch_poison_used = False
        self.day_number = 0

    def setup_game(self):
        game_dir = Path(__file__).resolve().parent
        config_path = game_dir / "config.json"
        prompt_path = game_dir / "prompt.json"

        try:
            with open(config_path, "r", encoding="utf-8") as file:
                config = json.load(file)
                # If players are not provided in __init__, load from config
                if not self._players_data:
                    player_configs = config.get("players", [])
                    self._players_data = []
                    for p in player_configs:
                        self._players_data.append(
                            {
                                "player_name": p["name"],
                                "player_uuid": p.get("uuid", p["name"]),
                                # Merge other config if needed
                                **p,
                            }
                        )

                # Use the current _players_data list to set up names and map
                self.all_player_names = [
                    p.get("player_name", "") for p in self._players_data
                ]
                player_names = self.all_player_names

                # Build a map for looking up config by name
                self.player_config_map = {}
                # First fill with config data
                for p in config.get("players", []):
                    self.player_config_map[p["name"]] = p
                # Then update/override with passed player data
                for p in self._players_data:
                    name = p.get("player_name")
                    if name:
                        if name not in self.player_config_map:
                            self.player_config_map[name] = {}
                        self.player_config_map[name].update(p)
                player_config_map = self.player_config_map

            with open(prompt_path, "r", encoding="utf-8") as file:
                prompts = json.load(file)

        except (FileNotFoundError, KeyError, ValueError) as e:
            self.logger.system_logger.error(f"配置文件或提示词文件有错: {str(e)}")
            return

        except Exception as e:
            self.logger.system_logger.error(f"未知错误: {str(e)}")
            return

        player_count = len(self.all_player_names)

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

        self.logger.log_event(
            f"本局玩家人数: {player_count}",
            self.all_player_names,
        )
        self.logger.log_event(
            f"角色卡配置: {role_config}",
            self.all_player_names,
        )
        self.logger.log_event(
            f"玩家 {player_names} 已加入游戏.",
            self.all_player_names,
        )

        role_list = []
        for role, count in self.roles.items():
            for _ in range(count):
                role_list.append(role)
        random.shuffle(role_list)

        for name, role in zip(player_names, role_list):
            p_config = player_config_map.get(name, {})
            player = Player(name, role, p_config, prompts, self.logger)
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

        self.logger.log_event(
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
        self.logger.log_event(
            "游戏开始. 天黑, 请闭眼.",
            self.all_player_names,
        )

    def handle_death(self, player_name: str, reason: DeathReason):
        if player_name and self.players[player_name].is_alive:
            self.players[player_name].is_alive = False
            print(f"#! {player_name} 死了, 原因是{reason.value}")
            self.logger.log_event(
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
                    self.logger.log_event(
                        f"[遗言] {player_name} 发言: {last_words}",
                        self.all_player_names,
                    )
                else:
                    print(f"#@ {player_name} 选择保持沉默, 没有留下遗言")
                    self.logger.log_event(
                        f"{player_name} 选择保持沉默, 没有留下遗言",
                        self.all_player_names,
                    )

            if self.players[player_name].role == Role.HUNTER.value:
                self.handle_hunter_shot(player_name)

    def handle_hunter_shot(self, hunter_name: str):
        print(f"#@ {hunter_name} 是猎人, 可以在临死前开枪带走一人")
        self.logger.log_event(
            f"{hunter_name} 是猎人, 可以在临死前开枪带走一人",
            self.all_player_names,
        )
        alive_players_for_shot = []
        for p in self._get_alive_players():
            if p != hunter_name:
                alive_players_for_shot.append(p)
        hunter_player = self.players[hunter_name]
        prompt = f"{hunter_name}, 请选择你要带走的玩家: "
        target = hunter_player.choose(prompt, alive_players_for_shot, allow_skip=True)

        if target == "skip":
            print("#@ 猎人放弃了开枪")
            self.logger.log_event(
                "猎人放弃了开枪",
                self.all_player_names,
            )
        else:
            self.logger.log_event(
                f"猎人 {hunter_name} 开枪带走了 {target}",
                self.all_player_names,
            )
            self.handle_death(target, DeathReason.SHOT_BY_HUNTER)

    def check_game_over(self):
        alive_werewolves = self._get_alive_players([Role.WEREWOLF])
        alive_villagers = self._get_alive_players(
            [Role.VILLAGER, Role.SEER, Role.WITCH, Role.HUNTER, Role.GUARD]
        )

        if not alive_werewolves:
            print("#! 游戏结束, 好人阵营胜利!")
            self.logger.log_event(
                "游戏结束, 好人阵营胜利!",
                self.all_player_names,
            )
            return True
        elif len(alive_werewolves) >= len(alive_villagers):
            print("#! 游戏结束, 狼人阵营胜利!")
            self.logger.log_event(
                "游戏结束, 狼人阵营胜利!",
                self.all_player_names,
            )
            return True
        return False


if __name__ == "__main__":
    # Load config to get players
    game_dir = Path(__file__).resolve().parent
    config_path = game_dir / "config.json"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            # Construct players list for GameLogger
            init_players = []
            for p in config_data.get("players", []):
                init_players.append(
                    {
                        "player_name": p["name"],
                        "player_uuid": p.get(
                            "uuid", p["name"]
                        ),  # Use name as uuid if missing
                    }
                )
    except Exception as e:
        print(f"Error loading config for main: {e}")
        init_players = []

    game = WerewolfGame(init_players)
    game.run_game()

Game = WerewolfGame
