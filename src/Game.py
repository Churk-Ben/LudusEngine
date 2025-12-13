from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable, Tuple, Union
from pathlib import Path
import sys
import json

# Ensure project root is in path
BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.append(str(BASE))

from src.Logger import GameLogger
from src.Player import Player

# -----------------------------------------------------------------------------
# Core Engine Structures (DSL Support)
# -----------------------------------------------------------------------------


@dataclass
class ActionContext:
    game: Any  # "Game" subclass
    player: Optional[Player] = None
    target: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)


class GameAction(ABC):
    """Abstract base class for a game action defined in DSL."""

    @abstractmethod
    def execute(self, context: ActionContext) -> Any:
        pass

    @abstractmethod
    def description(self) -> str:
        pass


@dataclass
class GameStep:
    """A single step in a game phase (e.g. 'Werewolves wake up')."""

    name: str
    roles_involved: List[Any]
    action: GameAction
    condition: Optional[Callable[[Any], bool]] = None


@dataclass
class GamePhase:
    """A game phase consisting of multiple steps (e.g. 'Night', 'Day')."""

    name: str
    steps: List[GameStep] = field(default_factory=list)

    def add_step(self, step: GameStep):
        self.steps.append(step)


class Game(ABC):
    def __init__(self, game_name: str, players_data: List[Dict[str, str]]):
        self.game_name = game_name
        self.players: Dict[str, Player] = {}
        self.all_player_names: List[str] = [
            p.get("player_name", "") for p in players_data
        ]
        self._players_data = players_data

        # Initialize Logger
        self.logger = GameLogger(game_name, self._players_data)

        self.phases: List[GamePhase] = []
        self.day_number = 0

    @abstractmethod
    def _init_phases(self):
        """Initialize game phases and steps."""
        pass

    def run_phase(self, phase: GamePhase):
        """Run a single game phase."""
        for step in phase.steps:
            if self.check_game_over():
                return

            # Check condition if exists
            if step.condition and not step.condition(self):
                continue

            context = ActionContext(game=self)
            step.action.execute(context)

    @abstractmethod
    def check_game_over(self) -> bool:
        pass

    @abstractmethod
    def setup_game(self):
        """Load configuration and initialize players/roles."""
        pass

    def run_game(self):
        """Main game loop."""
        self.setup_game()
        self._init_phases()  # Ensure phases are initialized

        while not self.check_game_over():
            for phase in self.phases:
                self.run_phase(phase)
                if self.check_game_over():
                    break

    def get_alive_players(self, allowed_roles: Optional[List[Any]] = None) -> List[str]:
        """
        Get names of alive players.
        allowed_roles: List of role values (can be Enum members or strings).
        """
        alive_players = []

        target_roles = set()
        if allowed_roles:
            for r in allowed_roles:
                if hasattr(r, "value"):
                    target_roles.add(r.value)
                else:
                    target_roles.add(r)

        for name, p in self.players.items():
            if p.is_alive:
                if not allowed_roles or p.role in target_roles:
                    alive_players.append(name)
        return alive_players

    def get_player_by_role(self, role: Any) -> Optional[Player]:
        """
        Find the first alive player with the given role.
        role: Can be Enum member or string.
        """
        role_value = role.value if hasattr(role, "value") else role
        for p in self.players.values():
            if p.role == role_value and p.is_alive:
                return p
        return None

    def load_basic_config(self, game_dir: Path) -> Tuple[Dict, Dict, Dict[str, Dict]]:
        """
        Load config.json and prompt.json from the game directory.
        Merges player data from config with initial players data.
        Returns (config, prompts, player_config_map).
        """
        config_path = game_dir / "config.json"
        prompt_path = game_dir / "prompt.json"

        config = {}
        prompts = {}
        player_config_map = {}

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

                # Build a map for looking up config by name
                # First fill with config data
                for p in config.get("players", []):
                    player_config_map[p["name"]] = p
                # Then update/override with passed player data
                for p in self._players_data:
                    name = p.get("player_name")
                    if name:
                        if name not in player_config_map:
                            player_config_map[name] = {}
                        player_config_map[name].update(p)

            with open(prompt_path, "r", encoding="utf-8") as file:
                prompts = json.load(file)

        except (FileNotFoundError, KeyError, ValueError) as e:
            self.logger.system_logger.error(f"配置文件或提示词文件有错: {str(e)}")
            # In case of error, we might return empty dicts or re-raise
            # For now, print error is handled by logger, but we should ensure valid returns
            pass

        except Exception as e:
            self.logger.system_logger.error(f"未知错误: {str(e)}")
            pass

        return config, prompts, player_config_map

    def announce(
        self, message: str, visible_to: Optional[List[str]] = None, prefix: str = "#:"
    ):
        """
        Encapsulated method to handle game announcements.
        It prints to the console (standard output) and logs the event to the game logger.

        Args:
            message (str): The content of the announcement.
            visible_to (Optional[List[str]]): List of player names who can see this message.
                                              If None, it's public (all players).
            prefix (str): Prefix string for console output (e.g. '#:', '#@', '#!').
        """
        # Log to file with visibility scope
        self.logger.log_event(message, visible_to)

        # Print to console
        # Note: Console output typically shows everything for the administrator/spectator.
        # If we wanted to hide secrets from the console, we could check visible_to.
        # But for now, we assume console is "God view".

        if visible_to:
            # If limited visibility, maybe indicate it in console
            print(f"{prefix} [Visible to {visible_to}] {message}")
        else:
            print(f"{prefix} {message}")

    def process_discussion(
        self,
        participants: List[str],
        prompts: Dict[str, str],
        max_rounds: int = 1,
        enable_ready_check: bool = False,
        shuffle_order: bool = False,
        visibility: Optional[List[str]] = None,
        prefix: str = "#:",
    ):
        """
        Process a discussion phase.

        Args:
            participants: List of player names who can speak.
            prompts: Dictionary containing prompt templates:
                - 'start': Announcement at start (optional)
                - 'prompt': Input prompt for player (required, format {0}=name)
                - 'speech': Announcement of speech (required, format {0}=name, {1}=content)
                - 'ready_msg': Announcement when player is ready (optional, format {0}=name, {1}=ready_count, {2}=total)
                - 'timeout': Announcement when max rounds reached (optional, format {0}=max_rounds)
                - 'alive_players': Announcement of alive players (optional, format {0}=joined_names)
            max_rounds: Maximum number of discussion rounds.
            enable_ready_check: If True, input '0' marks player as ready to end discussion.
            shuffle_order: If True, randomize speaking order each round.
            visibility: Who can see the announcements (None for public).
            prefix: Prefix for announcements.
        """
        if "start" in prompts:
            self.announce(prompts["start"], visibility, "#@")

        if "alive_players" in prompts:
            self.announce(
                prompts["alive_players"].format(", ".join(participants)),
                visibility,
                "#@",
            )

        ready_to_vote = set()
        discussion_rounds = 0

        import random

        while len(ready_to_vote) < len(participants) and discussion_rounds < max_rounds:
            discussion_rounds += 1

            # Determine order
            speakers = list(participants)
            if shuffle_order:
                random.shuffle(speakers)

            for player_name in speakers:
                if player_name in ready_to_vote:
                    continue

                player = self.players[player_name]
                prompt = prompts["prompt"].format(player_name)
                action = player.speak(prompt)

                if enable_ready_check and action == "0":
                    ready_to_vote.add(player_name)
                    if "ready_msg" in prompts:
                        msg = prompts["ready_msg"].format(
                            player_name, len(ready_to_vote), len(participants)
                        )
                        self.announce(msg, visibility, "#@")
                elif action:
                    self.announce(
                        prompts["speech"].format(player_name, action),
                        visibility,
                        prefix,
                    )

        if (
            discussion_rounds >= max_rounds
            and len(ready_to_vote) < len(participants)
            and "timeout" in prompts
        ):
            msg = prompts["timeout"].format(max_rounds)
            self.announce(msg, visibility, "#@")

    def process_vote(
        self,
        voters: List[str],
        candidates: List[str],
        prompts: Dict[str, str],
        retry_on_tie: bool = False,
        visibility: Optional[List[str]] = None,
        prefix: str = "#:",
    ) -> Optional[str]:
        """
        Process a voting phase.

        Args:
            voters: List of player names who vote.
            candidates: List of player names who can be voted for.
            prompts: Dictionary containing prompt templates:
                - 'start': Announcement at start (optional)
                - 'prompt': Input prompt for voter (required, format {0}=name)
                - 'action': Announcement of vote action (required, format {0}=voter, {1}=target)
                - 'result_out': Announcement of result (required, format {0}=target)
                - 'result_tie': Announcement of tie (required)
            retry_on_tie: If True, loop until a single winner is chosen.
            visibility: Who can see the announcements (None for public).
            prefix: Prefix for announcements.

        Returns:
            The name of the selected target, or None if no result/tie (and not retrying).
        """
        if "start" in prompts:
            self.announce(prompts["start"], visibility, "#@")

        while True:
            votes = {name: 0 for name in candidates}
            for voter_name in voters:
                voter = self.players[voter_name]
                prompt = prompts["prompt"].format(voter_name)
                target = voter.choose(prompt, candidates)
                votes[target] += 1
                if "action" in prompts:
                    self.announce(
                        prompts["action"].format(voter_name, target),
                        visibility,
                        prefix,
                    )

            max_votes = 0
            if votes:
                max_votes = max(votes.values())

            targets = [
                name
                for name, count in votes.items()
                if count == max_votes and count > 0
            ]

            if len(targets) == 1:
                winner = targets[0]
                if "result_out" in prompts:  # Or result_win
                    # Try result_out first, generic key
                    self.announce(
                        prompts["result_out"].format(winner),
                        visibility,
                        "#@" if visibility else "#!",
                    )
                return winner
            else:
                if "result_tie" in prompts:
                    self.announce(prompts["result_tie"], visibility, "#@")

                if not retry_on_tie:
                    return None
                # If retry, loop continues
