import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from flask import Blueprint, jsonify, request
from litellm import completion

from ..Logger import get_logger


BASE = Path(__file__).resolve().parent.parent.parent
USERS_DIR = BASE / ".users"

if not USERS_DIR.exists():
    os.mkdir(USERS_DIR)
    players_file = USERS_DIR / "players.json"
    apikeys_file = USERS_DIR / "apikeys.env"

    with open(players_file, "w", encoding="UTF-8") as f:
        init_players_file = {"human": [], "online": [], "local": []}
        json.dump(init_players_file, f, ensure_ascii=False, indent=2)


players_bp = Blueprint("players", __name__)
players_log = get_logger("PlayerService")
players_store = {"human": [], "online": [], "local": []}


# 从长期存储加载玩家到内存
if USERS_DIR.exists():
    with open(USERS_DIR / "players.json", "r", encoding="UTF-8") as f:
        players_store = json.load(f)


# 根据uuid获取玩家数据
def get_player_by_uuid(uuid: str):
    for player_type in players_store:
        for player in players_store[player_type]:
            if player["uuid"] == uuid:
                return player
    return None


@players_bp.route("/api/players", methods=["GET"])
@players_log.decorate.info("拉取玩家列表")
def api_players_get():
    data = players_store
    players_log.info(f"已加载 {len(data["human"]+data["online"]+data["local"])} 个玩家")
    return (
        jsonify({"ok": True, "data": data}),
        200,
    )


@players_bp.route("/api/players/providers", methods=["GET"])
@players_log.decorate.info("拉取供应商列表")
def api_players_providers_get():
    if os.getenv("debug", "0") == "1":
        players_log.info(f"已加载 1 个默认供应商")
        return (
            jsonify(
                {"ok": True, "data": [{"id": "default", "name": "default_provider"}]}
            ),
            200,
        )

    import litellm

    _providers = []
    for provider in litellm.provider_list:
        _providers.append({"id": provider, "name": provider.capitalize()})

    data = sorted(_providers, key=lambda x: x["name"])
    players_log.info(f"已加载 {len(data)} 个供应商: {data[:3]}等")
    return (
        jsonify({"ok": True, "data": data}),
        200,
    )


@players_bp.route("/api/players/add", methods=["POST"])
@players_log.decorate.info("唤起玩家添加函数")
def api_players_add_post():
    data = request.get_json(force=True) or {}
    player_type = data.get("type")
    player_data = data.get("player")

    if not player_type or not player_data:
        players_log.error("传入的玩家类型或数据缺失")
        return (
            jsonify({"ok": False, "error": "玩家类型或数据缺失"}),
            400,
        )

    if player_type not in players_store:
        players_log.error(f"传入未知的玩家类型: {player_type}")
        return (
            jsonify({"ok": False, "error": f"未知的玩家类型: {player_type}"}),
            400,
        )

    if "uuid" not in player_data or not player_data["uuid"]:
        player_data["uuid"] = str(uuid.uuid4())

    players_store[player_type].append(player_data)

    # 持久化
    try:
        with open(USERS_DIR / "players.json", "w", encoding="UTF-8") as f:
            json.dump(players_store, f, ensure_ascii=False, indent=2)
    except Exception as e:
        players_log.error(f"玩家数据保存失败: {e}")
        return (
            jsonify({"ok": False, "error": "玩家数据保存失败"}),
            500,
        )

    players_log.info(f"已添加玩家: {player_data}")
    return (
        jsonify({"ok": True, "data": player_data}),
        200,
    )


@players_bp.route("/api/players/<pid>", methods=["DELETE"])
@players_log.decorate.info("唤起玩家删除函数")
def api_players_remove_delete(pid):
    for player_type in players_store:
        players_store[player_type] = [
            x for x in players_store[player_type] if x.get("uuid") != pid
        ]

    # 将变更持久化到文件
    try:
        with open(USERS_DIR / "players.json", "w", encoding="UTF-8") as f:
            json.dump(players_store, f, ensure_ascii=False, indent=2)
    except Exception as e:
        players_log.error(f"玩家数据删除失败: {e}")
        return (
            jsonify({"ok": False, "error": "玩家数据删除失败"}),
            500,
        )

    players_log.info(f"已删除玩家: {pid}")
    return (
        jsonify({"ok": True}),
        200,
    )


# -----------------------------------------------------------------------------
# Core Player Class (Decoupled)
# -----------------------------------------------------------------------------
class Player:
    def __init__(
        self,
        name: str,
        role: str,
        config_data: Dict[str, Any],
        prompts: Dict[str, str],
        game_logger=None,
    ):
        self.name = name
        self.role = role
        self.config = config_data
        self.prompts = prompts
        self.game_logger = game_logger

        self.is_human = self.config.get("human", False)
        self.is_alive = True
        self.is_guarded = False
        self.is_first_night = True

        # Inject self into the main prompt
        self.prompt = self.prompts.get("PROMPT", "").format(self=self)

    def set_logger(self, logger):
        self.game_logger = logger

    def call_ai_response(self, prompt_text: str, valid_choices: List[str]):
        # Check debug flag from environment or config, here we assume passed via config or os
        if os.getenv("DEBUG_GAME", "0") == "1":
            import random

            return random.choice(valid_choices)

        history = []
        if self.game_logger:
            log_file = self.game_logger._get_player_log_file(self.name)
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    log_content = f.read()

                    # Construct context reminder using injected templates
                    context_reminder = self.prompts.get("REMINDER", "").format(
                        self.name, self.role
                    )

                    # Logic for Werewolf night discussion reminder
                    # Note: This logic is slightly game-specific but relies on prompts being present
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
            response = completion(
                model=self.config.get("model", "gpt-3.5-turbo"),
                messages=history,
                stream=False,
            )
            ai_choice = response.choices[0].message.content
            for choice in valid_choices:
                if choice in ai_choice:
                    return choice
            # Fallback
            import random

            return random.choice(valid_choices)
        except Exception as e:
            print(f"AI Error: {e}")
            import random

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
                    return display_choices[choice_index]

            if allow_skip and player_input_lower == "skip":
                return "skip"

            for choice in valid_choices:
                if choice.lower() == player_input_lower:
                    return choice

            print("[bold red]无效的选择, 请重新输入. [/bold red]")

    def call_ai_speak(self, prompt_text: str):
        if os.getenv("DEBUG_GAME", "0") == "1":
            return "ai_response<br>, and <strong>ai_response</strong>"

        history = []
        if self.game_logger:
            log_file = self.game_logger._get_player_log_file(self.name)
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

        print(f"{self.name} 正在思考...")
        try:
            response = completion(
                model=self.config.get("model", "gpt-3.5-turbo"),
                messages=history,
                stream=False,
            )
            speech = response.choices[0].message.content
            return speech
        except Exception as e:
            return f"(Error generating speech: {e})"

    def call_human_speak(self, prompt_text: str):
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


if __name__ == "__main__":
    from flask import Flask
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(players_bp)

    app.run(debug=True)
