import datetime
import json
import os
from pathlib import Path

from flask import Blueprint, jsonify
from flask_socketio import SocketIO, emit

from ..Logger import get_logger
from ..services.players import get_player_by_uuid, get_player_type_by_uuid

BASE = Path(__file__).resolve().parent.parent.parent
GAMES_DIR = BASE / ".games"

if not GAMES_DIR.exists():
    os.mkdir(GAMES_DIR)

games_bp = Blueprint("games", __name__)
games_log = get_logger("GameService")


@games_bp.route("/api/games", methods=["GET"])
@games_log.decorate.info("拉取游戏列表")
def api_games_get():
    items = []
    if GAMES_DIR.exists():
        for p in GAMES_DIR.iterdir():
            if p.is_dir():
                items.append(p.name)

    games_log.info(f"游戏列表: {items}")
    return (
        jsonify({"ok": True, "data": items}),
        200,
    )


def init_game_socket_events(socketio: SocketIO):
    @games_log.decorate.info("初始化游戏请求")
    @socketio.on("app:initGame")
    def on_init_game(data):
        game_id = data.get("gameId")
        player_ids = data.get("playerIds")
        session_id = data.get("sessionId")

        games_log.info(
            f"收到游戏初始化请求 - Session: {session_id}, Game: {game_id}, Players: {player_ids}"
        )

        # 初始化游戏状态
        game_info = {
            "name": game_id if game_id else "未命名",
            "status": "已连接, 初始化中...",
            "statusType": "success",
        }
        games_log.info(f"游戏会话 {session_id} 初始化游戏信息: {game_info}")
        emit("game:info", game_info)

        # 初始化玩家列表
        players = []
        if player_ids:
            for uuid in player_ids:
                player = get_player_by_uuid(uuid)
                # TODO 完善远程玩家类型
                players.append(
                    {
                        "id": str(uuid),
                        "name": player["name"] if player else f"Player {uuid}",
                        "type": get_player_type_by_uuid(uuid) if player else "remote",
                        "data": {},
                    }
                )

        emit("game:players", players)
        games_log.info(f"游戏会话 {session_id} 初始化玩家列表: {players}")

        # 回复客户端
        emit(
            "game:notification",
            {"type": "success", "content": f"游戏 {game_id} 初始化成功"},
        )
        emit("game:info", {"status": "等待游戏开始"})
        games_log.info(f"游戏会话 {session_id} 初始化完成")

    @socketio.on("game:chat")
    def on_game_chat(data):
        sender = data.get("sender", None)
        content = data.get("content", "")

        # 构建消息对象
        msg = {
            "sender": sender,
            "content": content,
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
        }

        # 广播给所有人 (包括发送者)
        # TODO 这里暂时先广播给所有玩家，后续根据玩家类型筛选
        emit("game:message", msg, broadcast=True)
        games_log.info(f"处理聊天消息: {msg}")


if __name__ == "__main__":
    from flask import Flask
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(games_bp)

    app.run(debug=True)
