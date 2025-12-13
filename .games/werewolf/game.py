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
        game.announce(
            game.prompts["phases"]["night"]["start"].format(game.day_number),
            game.all_player_names,
            "#@",
        )
        game.killed_player = None
        for p in game.players.values():
            p.is_guarded = False


class DayStartAction(GameAction):
    def description(self) -> str:
        return "天亮初始化"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        game.announce(
            game.prompts["phases"]["day"]["start"].format(game.day_number),
            game.all_player_names,
            "#:",
        )

        if game.killed_player:
            game.handle_death(game.killed_player, DeathReason.KILLED_BY_WEREWOLF)
        else:
            game.announce(
                game.prompts["phases"]["day"]["safe_night"],
                game.all_player_names,
                "#@",
            )


class GuardAction(GameAction):
    def description(self) -> str:
        return "守卫守护"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        guard = game.get_player_by_role(Role.GUARD)
        if not guard:
            return

        prompt = game.prompts["roles"]["guard"]["choose"]
        game.announce(
            game.prompts["roles"]["guard"]["wake"],
            [guard.name],
            "#@",
        )

        alive_players = game.get_alive_players()
        valid_targets = [p for p in alive_players if p != game.last_guarded]

        target = guard.choose(prompt, valid_targets)

        game.players[target].is_guarded = True
        game.last_guarded = target

        game.announce(
            game.prompts["roles"]["guard"]["action_done"].format(target),
            [guard.name],
            "#@",
        )
        game.announce(
            game.prompts["roles"]["guard"]["sleep"],
            game.all_player_names,
            "#@",
        )


class WerewolfNightAction(GameAction):
    def description(self) -> str:
        return "狼人夜间行动"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        werewolves = game.get_alive_players([Role.WEREWOLF])
        if not werewolves:
            return

        game.announce(
            game.prompts["roles"]["werewolf"]["wake"].format(", ".join(werewolves)),
            werewolves,
            "#@",
        )

        if len(werewolves) == 1:
            game.announce(
                game.prompts["roles"]["werewolf"]["lone_wolf"],
                werewolves,
                "#@",
            )
        else:
            self._handle_discussion(game, werewolves)

        self._handle_voting(game, werewolves)

        if game.killed_player:
            game.announce(
                game.prompts["roles"]["werewolf"]["kill_success"].format(
                    game.killed_player
                ),
                werewolves,
                "#@",
            )
        game.announce(
            game.prompts["roles"]["werewolf"]["sleep"],
            game.all_player_names,
            "#@",
        )

    def _handle_discussion(self, game, werewolves):
        prompts = {
            "start": game.prompts["roles"]["werewolf"]["discuss_start"],
            "prompt": game.prompts["roles"]["werewolf"]["discuss_prompt"],
            "speech": game.prompts["roles"]["werewolf"]["discuss_channel"],
            "ready_msg": game.prompts["roles"]["werewolf"]["discuss_ready"],
            "timeout": game.prompts["roles"]["werewolf"]["discuss_timeout"],
        }
        game.process_discussion(
            participants=werewolves,
            prompts=prompts,
            max_rounds=5,
            enable_ready_check=True,
            visibility=werewolves,
            prefix="#:",
        )

    def _handle_voting(self, game, werewolves):
        alive_players = game.get_alive_players()
        prompts = {
            "start": game.prompts["roles"]["werewolf"]["vote_start"],
            "prompt": game.prompts["roles"]["werewolf"]["vote_prompt"],
            "result_out": game.prompts["roles"]["werewolf"]["vote_result"],
            "result_tie": game.prompts["roles"]["werewolf"]["vote_tie"],
        }
        winner = game.process_vote(
            voters=werewolves,
            candidates=alive_players,
            prompts=prompts,
            retry_on_tie=True,
            visibility=werewolves,
            prefix="#@",
        )
        if winner:
            game.killed_player = winner


class SeerAction(GameAction):
    def description(self) -> str:
        return "预言家查验"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        seer = game.get_player_by_role(Role.SEER)
        if not seer:
            return

        prompt = game.prompts["roles"]["seer"]["choose"]
        game.announce(
            game.prompts["roles"]["seer"]["wake"],
            [seer.name],
            "#@",
        )

        alive_players = game.get_alive_players()
        target = seer.choose(prompt, alive_players)

        role = game.players[target].role
        identity = "狼人" if role == Role.WEREWOLF.value else "好人"
        game.announce(
            game.prompts["roles"]["seer"]["result"].format(target, identity),
            [seer.name],
            "#@",
        )

        game.announce(
            game.prompts["roles"]["seer"]["sleep"],
            game.all_player_names,
            "#@",
        )


class WitchAction(GameAction):
    def description(self) -> str:
        return "女巫毒药与解药"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        witch = game.get_player_by_role(Role.WITCH)
        if not witch:
            return

        game.announce(
            game.prompts["roles"]["witch"]["wake"],
            [witch.name],
            "#@",
        )

        alive_players = game.get_alive_players()
        actual_killed = None

        # Check death info
        if game.killed_player:
            if game.players[game.killed_player].is_guarded:
                game.announce(
                    game.prompts["roles"]["witch"]["night_safe"].format(
                        game.killed_player
                    ),
                    game.all_player_names,
                    "#@",
                )
            else:
                game.announce(
                    game.prompts["roles"]["witch"]["night_kill"].format(
                        game.killed_player
                    ),
                    [witch.name],
                    "#@",
                )
                actual_killed = game.killed_player

        # Save Potion
        if not game.witch_save_used and actual_killed:
            prompt = game.prompts["roles"]["witch"]["save_prompt"]
            if witch.choose(prompt, ["y", "n"]) == "y":
                actual_killed = None
                game.witch_save_used = True
                game.announce(
                    game.prompts["roles"]["witch"]["save_action"].format(
                        game.killed_player
                    ),
                    [witch.name],
                    "#@",
                )
                game.announce(
                    game.prompts["roles"]["witch"]["save_broadcast"],
                    game.all_player_names,
                    "#@",
                )

        # Poison Potion
        if not game.witch_poison_used:
            prompt = game.prompts["roles"]["witch"]["poison_prompt"]
            if witch.choose(prompt, ["y", "n"]) == "y":
                poison_prompt = game.prompts["roles"]["witch"]["poison_target_prompt"]
                target = witch.choose(poison_prompt, alive_players)
                if actual_killed is None:
                    actual_killed = target
                else:
                    game.handle_death(target, DeathReason.POISONED_BY_WITCH)

                game.witch_poison_used = True
                game.announce(
                    game.prompts["roles"]["witch"]["poison_action"].format(target),
                    [witch.name],
                    "#@",
                )
                game.announce(
                    game.prompts["roles"]["witch"]["poison_broadcast"],
                    game.all_player_names,
                    "#@",
                )

        # Update killed player to the final result
        game.killed_player = actual_killed

        game.announce(
            game.prompts["roles"]["witch"]["sleep"],
            game.all_player_names,
            "#@",
        )


class DayDiscussionAction(GameAction):
    def description(self) -> str:
        return "白天讨论"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        alive_players = game.get_alive_players()

        prompts = {
            "alive_players": game.prompts["phases"]["day"]["discussion"][
                "alive_players"
            ],
            "prompt": game.prompts["phases"]["day"]["discussion"]["speak_prompt"],
            "speech": game.prompts["phases"]["day"]["discussion"]["speech"],
        }
        game.process_discussion(
            participants=alive_players,
            prompts=prompts,
            max_rounds=1,
            enable_ready_check=False,
            prefix="#:",
        )


class DayVoteAction(GameAction):
    def description(self) -> str:
        return "白天投票"

    def execute(self, context: ActionContext) -> Any:
        game: "WerewolfGame" = context.game
        alive_players = game.get_alive_players()
        prompts = {
            "start": game.prompts["phases"]["day"]["vote"]["start"],
            "prompt": game.prompts["phases"]["day"]["vote"]["prompt"],
            "action": game.prompts["phases"]["day"]["vote"]["action"],
            "result_out": game.prompts["phases"]["day"]["vote"]["result_out"],
            "result_tie": game.prompts["phases"]["day"]["vote"]["result_tie"],
        }

        voted_out_player = game.process_vote(
            voters=alive_players,
            candidates=alive_players,
            prompts=prompts,
            retry_on_tie=False,
            prefix="#:",
        )

        if voted_out_player:
            game.handle_death(voted_out_player, DeathReason.VOTED_OUT)


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
        self.prompts: Dict[str, str] = {}
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

    def _cancel(self):
        self.announce(game.prompts["game"]["cancel"], self.all_player_names, "#!")
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
        config, prompts, player_config_map = self.load_basic_config(game_dir)
        self.prompts = prompts

        # Note: self.all_player_names and self._players_data are updated by load_basic_config

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

        role_config = []
        for role, count in self.roles.items():
            if count > 0:
                role_config.append(f"{role.capitalize()} {count}人")

        self.announce(self.prompts["game"]["config_roles"], self.all_player_names, "#@")
        self.announce(", ".join(role_config), self.all_player_names, "#@")
        self.announce(
            self.prompts["game"]["player_count"].format(player_count),
            self.all_player_names,
            "#@",
        )
        self.announce(
            self.prompts["game"]["players_joined"].format(self.all_player_names),
            self.all_player_names,
            "#@",
        )

        role_list = []
        for role, count in self.roles.items():
            for _ in range(count):
                role_list.append(role)
        random.shuffle(role_list)

        for name, role in zip(self.all_player_names, role_list):
            p_config = player_config_map.get(name, {})
            player = Player(name, role, p_config, prompts, self.logger)
            self.players[name] = player

        werewolves = self.get_alive_players([Role.WEREWOLF])

        self.announce(self.prompts["game"]["assigning"], self.all_player_names, "#@")
        for name, player in self.players.items():
            time.sleep(0.3)
            self.announce(
                self.prompts["game"]["identity"].format(name, player.role.capitalize()),
                [player.name],
                "#:",
            )
            if player.role == Role.WEREWOLF.value:
                teammates = []
                for w in werewolves:
                    if w != name:
                        teammates.append(w)
                if teammates:
                    self.announce(
                        self.prompts["game"]["wolf_teammates"].format(
                            ", ".join(teammates)
                        ),
                        [player.name],
                        "",
                    )
                else:
                    self.announce(self.prompts["game"]["lone_wolf"], [player.name], "")

        self.announce(self.prompts["game"]["start"], self.all_player_names, "#:")

    def handle_death(self, player_name: str, reason: DeathReason):
        if player_name and self.players[player_name].is_alive:
            self.players[player_name].is_alive = False
            self.announce(
                self.prompts["game"]["death"].format(player_name, reason.value),
                self.all_player_names,
                "#!",
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
                prompt = self.prompts["game"]["last_words_prompt"].format(player_name)
                last_words = player.speak(prompt)
                if last_words:
                    self.announce(
                        self.prompts["game"]["last_words_content"].format(
                            player_name, last_words
                        ),
                        self.all_player_names,
                        "#:",
                    )
                else:
                    self.announce(
                        self.prompts["game"]["last_words_silence"].format(player_name),
                        self.all_player_names,
                        "#@",
                    )

            if self.players[player_name].role == Role.HUNTER.value:
                self.handle_hunter_shot(player_name)

    def handle_hunter_shot(self, hunter_name: str):
        self.announce(
            self.prompts["roles"]["hunter"]["death_trigger"].format(hunter_name),
            self.all_player_names,
            "#@",
        )
        alive_players_for_shot = []
        for p in self.get_alive_players():
            if p != hunter_name:
                alive_players_for_shot.append(p)
        hunter_player = self.players[hunter_name]
        prompt = self.prompts["roles"]["hunter"]["shoot_prompt"].format(hunter_name)
        target = hunter_player.choose(prompt, alive_players_for_shot, allow_skip=True)

        if target == "skip":
            self.announce(
                self.prompts["roles"]["hunter"]["skip"], self.all_player_names, "#@"
            )
        else:
            self.announce(
                self.prompts["roles"]["hunter"]["shot"].format(hunter_name, target),
                self.all_player_names,
                "#@",
            )
            self.handle_death(target, DeathReason.SHOT_BY_HUNTER)

    def check_game_over(self):
        alive_werewolves = self.get_alive_players([Role.WEREWOLF])
        alive_villagers = self.get_alive_players(
            [Role.VILLAGER, Role.SEER, Role.WITCH, Role.HUNTER, Role.GUARD]
        )

        if not alive_werewolves:
            self.announce(
                self.prompts["game"]["over_villager_win"], self.all_player_names, "#!"
            )
            return True
        elif len(alive_werewolves) >= len(alive_villagers):
            self.announce(
                self.prompts["game"]["over_werewolf_win"], self.all_player_names, "#!"
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
