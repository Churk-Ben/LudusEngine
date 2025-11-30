import json
import uuid
from flask import Blueprint, jsonify, request
from pathlib import Path
from ..Logger import get_logger


BASE = Path(__file__).resolve().parent.parent.parent
USERS_DIR = BASE / ".users"


players_bp = Blueprint("players", __name__)
players_log = get_logger("PlayerService")
players_store = {"human": [], "online": [], "local": []}


# 从长期存储加载玩家到内存
if USERS_DIR.exists():
    with open(USERS_DIR / "players.json", "r", encoding="UTF-8") as f:
        players_store = json.load(f)


@players_bp.route("/api/players", methods=["GET"])
@players_log.decorate.info("拉取玩家列表")
def api_players_get():
    data = players_store
    players_log.info(f"玩家列表: {data}")
    return (
        jsonify({"ok": True, "data": data}),
        200,
    )


@players_bp.route("/api/players/providers", methods=["GET"])
@players_log.decorate.info("拉取供应商列表")
def api_players_providers_get():
    import litellm

    _providers = []
    for provider in litellm.provider_list:
        _providers.append({"id": provider, "name": provider.capitalize()})

    data = sorted(_providers, key=lambda x: x["name"])
    players_log.info(f"已加载 {len(data)} 个供应商")
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
