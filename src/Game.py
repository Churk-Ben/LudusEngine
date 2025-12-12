from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from pathlib import Path
import sys

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
