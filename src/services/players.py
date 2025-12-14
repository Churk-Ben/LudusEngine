import json
import os
from pathlib import Path
import uuid

from flask import Blueprint, jsonify, request

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
else:
    players_file = USERS_DIR / "players.json"
    apikeys_file = USERS_DIR / "apikeys.env"

players_bp = Blueprint("players", __name__)
players_log = get_logger("PlayerService")
players_store = {"human": [], "online": [], "local": []}


# 从长期存储加载玩家到内存
if USERS_DIR.exists():
    with open(players_file, "r", encoding="UTF-8") as f:
        players_store = json.load(f)

    with open(apikeys_file, "r", encoding="UTF-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                _env_name, _api_key = line.split("=", 1)
                os.environ[_env_name] = _api_key
                players_log.info(f"已加载环境变量 {_env_name}")


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

    # 处理大语言模型APIKEY, 不存入玩家数据, 而是根据provider写入环境变量文件
    if "apiKey" in player_data:
        provider_id = player_data.get("providerId", "default")
        _env_name = f"{provider_id.upper()}_API_KEY"
        api_key = player_data.get("apiKey")
        os.environ[_env_name] = api_key
        player_data["apiKey"] = "SETED"

        with open(apikeys_file, "a+", encoding="UTF-8") as f:
            f.seek(0)
            # 检查文件中是否已存在该变量
            found = False
            for line in f:
                if line.startswith(_env_name):
                    found = True
                    players_log.warning(f"环境变量 {_env_name} 已存在, 不会重复写入")
                    break
            if not found:
                f.write(f"{_env_name}={api_key}\n")
                players_log.info(f"已写入环境变量 {_env_name}")

    players_store[player_type].append(player_data)

    # 非隐私数据持久化
    try:
        with open(players_file, "w", encoding="UTF-8") as f:
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
        with open(players_file, "w", encoding="UTF-8") as f:
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


if __name__ == "__main__":
    from flask import Flask
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(players_bp)

    app.run(debug=True)
