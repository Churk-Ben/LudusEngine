from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable, Tuple, Union
from pathlib import Path
import sys
import json
import os

# 确保项目根目录在路径中
BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.append(str(BASE))

from src.Logger import GameLogger
from src.Player import Player

# -----------------------------------------------------------------------------
# 核心引擎结构 (DSL 支持)
# -----------------------------------------------------------------------------


@dataclass
class ActionContext:
    game: Any  # "Game" 子类
    player: Optional[Player] = None
    target: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)


class GameAction(ABC):
    """在 DSL 中定义的游戏动作抽象基类."""

    @abstractmethod
    def execute(self, context: ActionContext) -> Any:
        pass

    @abstractmethod
    def description(self) -> str:
        pass


@dataclass
class GameStep:
    """游戏阶段中的单个步骤 (例如 '狼人醒来') ."""

    name: str
    roles_involved: List[Any]
    action: GameAction
    condition: Optional[Callable[[Any], bool]] = None


@dataclass
class GamePhase:
    """由多个步骤组成的游戏阶段 (例如 '夜晚', '白天') ."""

    name: str
    steps: List[GameStep] = field(default_factory=list)

    def add_step(self, step: GameStep):
        self.steps.append(step)


class Game(ABC):
    def __init__(
        self,
        game_name: str,
        players_data: List[Dict[str, str]],
        event_emitter: Optional[Callable[[str, Optional[List[str]]], None]] = None,
        input_handler: Optional[Callable[[str, str, str, List[str], bool], str]] = None,
    ):
        self.game_name = game_name
        self.players: Dict[str, Player] = {}
        self.all_player_names: List[str] = [
            p.get("player_name", "") for p in players_data
        ]
        self._players_data = players_data
        self.event_emitter = event_emitter
        self.input_handler = input_handler

        # 初始化日志记录器
        self.logger = GameLogger(game_name, self._players_data)

        self.phases: List[GamePhase] = []
        self.day_number = 0
        self._running = True

    def stop_game(self):
        """停止游戏运行"""
        self._running = False
        self.logger.system_logger.info("接收到游戏停止请求")

    @abstractmethod
    def _init_phases(self):
        """初始化游戏阶段和步骤."""
        pass

    def run_phase(self, phase: GamePhase):
        """运行单个游戏阶段."""
        for step in phase.steps:
            if not self._running:
                return
            if self.check_game_over():
                return

            # 如果存在条件则检查
            if step.condition and not step.condition(self):
                continue

            context = ActionContext(game=self)
            step.action.execute(context)

    @abstractmethod
    def check_game_over(self) -> bool:
        pass

    @abstractmethod
    def setup_game(self):
        """加载配置并初始化玩家/角色."""
        pass

    def run_game(self):
        """主游戏循环."""
        self.setup_game()
        self._init_phases()  # 确保阶段已初始化

        while self._running and not self.check_game_over():
            for phase in self.phases:
                if not self._running:
                    break
                self.run_phase(phase)
                if self.check_game_over():
                    break

    def get_alive_players(self, allowed_roles: Optional[List[Any]] = None) -> List[str]:
        """
        获取存活玩家的姓名.
        allowed_roles: 角色值列表 (可以是 Enum 成员或字符串) .
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
        查找具有给定角色的第一个存活玩家.
        role: 可以是 Enum 成员或字符串.
        """
        role_value = role.value if hasattr(role, "value") else role
        for p in self.players.values():
            if p.role == role_value and p.is_alive:
                return p
        return None

    def load_basic_config(self, game_dir: Path) -> Tuple[Dict, Dict, Dict[str, Dict]]:
        """
        从游戏目录加载 config.json 和 prompt.json.
        同时从 .users/players.json 加载玩家信息, 从 .users/apikeys.env 加载环境变量.
        将配置中的玩家数据与初始玩家数据合并.
        返回 (config, prompts, player_config_map).
        """
        config_path = game_dir / "config.json"
        prompt_path = game_dir / "prompt.json"

        users_dir = BASE / ".users"
        players_path = users_dir / "players.json"
        apikeys_path = users_dir / "apikeys.env"

        config = {}
        prompts = {}
        player_config_map = {}

        # 1. Load API keys
        if apikeys_path.exists():
            try:
                with open(apikeys_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            try:
                                key, value = line.split("=", 1)
                                os.environ[key] = value
                            except ValueError:
                                pass
            except Exception as e:
                self.logger.system_logger.error(f"加载环境变量失败: {e}")

        try:
            # 2. Load players from players.json
            loaded_players = []
            if players_path.exists():
                with open(players_path, "r", encoding="utf-8") as f:
                    p_data = json.load(f)
                    for p_type in ["human", "online", "local"]:
                        for p in p_data.get(p_type, []):
                            p["human"] = p_type == "human"
                            p["type"] = p_type
                            loaded_players.append(p)

            with open(config_path, "r", encoding="utf-8") as file:
                config = json.load(file)

                # 如果没从 players.json 加载到玩家，尝试从 config.json 加载 (兼容旧版)
                if not loaded_players:
                    loaded_players = config.get("players", [])

                # 如果 __init__ 中未提供玩家, 则使用加载的玩家
                if not self._players_data:
                    self._players_data = []
                    for p in loaded_players:
                        self._players_data.append(
                            {
                                "player_name": p["name"],
                                "player_uuid": p.get("uuid", p["name"]),
                                # 如果需要, 合并其他配置
                                **p,
                            }
                        )

                # 使用当前的 _players_data 列表设置名称和映射
                self.all_player_names = [
                    p.get("player_name", "") for p in self._players_data
                ]

                # 构建按名称查找配置的映射
                # 首先填充配置数据
                for p in loaded_players:
                    player_config_map[p["name"]] = p
                # 然后使用传递的玩家数据更新/覆盖
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
            # 如果出错, 我们可能会返回空字典或重新引发异常
            # 目前, 打印错误由 logger 处理, 但我们需要确保返回值有效
            pass

        except Exception as e:
            self.logger.system_logger.error(f"未知错误: {str(e)}")
            pass

        return config, prompts, player_config_map

    def announce(
        self, message: str, visible_to: Optional[List[str]] = None, prefix: str = "#:"
    ):
        """
        封装的游戏公告处理方法.
        它打印到控制台 (标准输出) 并将事件记录到游戏日志记录器.

        Args:
            message (str): 公告内容.
            visible_to (Optional[List[str]]): 可以看到此消息的玩家名称列表.
                                              如果为 None, 则为公开 (所有玩家).
            prefix (str): 控制台输出的前缀字符串 (例如 '#:', '#@', '#!') .
        """
        # 记录到文件, 带可见性范围
        self.logger.log_event(message, visible_to)

        # 发送事件
        if self.event_emitter:
            try:
                self.event_emitter(message, visible_to)
            except Exception as e:
                # 防止循环触发, 且防止由于logger错误
                if "announce" not in str(e):
                    self.logger.system_logger.error(f"发送公告事件时出错: {e}")
                    print(f"发送公告事件时出错: {e}")

        # 打印到控制台
        # 注意：控制台输出通常显示管理员/旁观者的所有内容.
        # 如果我们想向控制台隐藏秘密, 我们可以检查 visible_to.
        # 但目前, 我们假设控制台是“上帝视角”.

        if visible_to:
            # 如果可见性受限, 可能需要在控制台中指出
            self.logger.system_logger.info(f"公告: {message} (仅对 {visible_to} 可见)")
            print(f"{prefix} [Visible to {visible_to}] {message}")
        else:
            self.logger.system_logger.info(f"公告: {message} (公开)")
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
        处理讨论阶段.

        Args:
            participants: 可以发言的玩家姓名列表.
            prompts: 包含提示模板的字典：
                - 'start': 开始时的公告 (可选)
                - 'prompt': 玩家的输入提示 (必需, 格式 {0}=name)
                - 'speech': 演讲公告 (必需, 格式 {0}=name, {1}=content)
                - 'ready_msg': 玩家准备好时的公告 (可选, 格式 {0}=name, {1}=ready_count, {2}=total)
                - 'timeout': 达到最大轮次时的公告 (可选, 格式 {0}=max_rounds)
                - 'alive_players': 存活玩家公告 (可选, 格式 {0}=joined_names)
            max_rounds: 最大讨论轮数.
            enable_ready_check: 如果为 True, 输入 '0' 标记玩家准备结束讨论.
            shuffle_order: 如果为 True, 每轮随机打乱发言顺序.
            visibility: 谁可以看到公告 (None 表示公开) .
            prefix: 公告前缀.
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

        while (
            self._running
            and len(ready_to_vote) < len(participants)
            and discussion_rounds < max_rounds
        ):
            discussion_rounds += 1

            # 确定顺序
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
        max_retries: int = 5,
        visibility: Optional[List[str]] = None,
        prefix: str = "#:",
    ) -> Optional[str]:
        """
        处理投票阶段.

        Args:
            voters: 投票的玩家姓名列表.
            candidates: 可以被投票的玩家姓名列表.
            prompts: 包含提示模板的字典：
                - 'start': 开始时的公告 (可选)
                - 'prompt': 投票者的输入提示 (必需, 格式 {0}=name)
                - 'action': 投票动作公告 (必需, 格式 {0}=voter, {1}=target)
                - 'result_out': 结果公告 (必需, 格式 {0}=target)
                - 'result_tie': 平局公告 (必需)
            retry_on_tie: 如果为 True, 循环直到选出唯一的获胜者.
            max_retries: 重试最大次数, 防止死循环.
            visibility: 谁可以看到公告 (None 表示公开) .
            prefix: 公告前缀.

        Returns:
            选定目标的名称, 如果没有结果/平局 (且不重试) 则为 None.
        """
        if "start" in prompts:
            self.announce(prompts["start"], visibility, "#@")

        retries = 0
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
                if "result_out" in prompts:  # 或 result_win
                    # 先尝试 result_out, 通用键
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

                retries += 1
                if retries >= max_retries:
                    self.logger.system_logger.warning(
                        "投票达到最大重试次数, 将随机选择一个获胜者"
                    )
                    import random

                    if targets:
                        winner = random.choice(targets)
                    else:
                        winner = random.choice(candidates)

                    if "result_out" in prompts:
                        self.announce(
                            prompts["result_out"].format(winner),
                            visibility,
                            "#@" if visibility else "#!",
                        )
                    return winner
