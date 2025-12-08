from flask import Blueprint, jsonify
from pathlib import Path
from flask_socketio import SocketIO, emit
import datetime
from ..Logger import get_logger

BASE = Path(__file__).resolve().parent.parent.parent
GAMES_DIR = BASE / ".games"

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
    @socketio.on("app:initGame")
    @games_log.decorate.info("初始化游戏请求")
    def on_init_game(data):
        game_id = data.get("gameId")
        player_ids = data.get("playerIds")
        session_id = data.get("sessionId")

        games_log.info(
            f"收到游戏初始化请求 - Session: {session_id}, Game: {game_id}, Players: {player_ids}"
        )

        # 模拟游戏状态
        game_info = {
            "name": game_id if game_id else "Unknown Game",
            "status": "Running",
            "statusType": "success",
        }
        emit("game:info", game_info)

        # 模拟玩家列表
        players = []
        if player_ids:
            # 假设 player_ids 是列表
            if isinstance(player_ids, list):
                for pid in player_ids:
                    players.append(
                        {"id": str(pid), "name": f"Player {pid}", "status": "Ready"}
                    )
            else:
                # 单个ID或者是字符串
                players.append(
                    {
                        "id": str(player_ids),
                        "name": f"Player {player_ids}",
                        "status": "Ready",
                    }
                )

        emit("game:players", players)

        # 回复客户端
        emit(
            "game:notification",
            {"type": "success", "content": f"游戏 {game_id} 初始化成功"},
        )

    @socketio.on("game:chat")
    def on_game_chat(data):
        sender = data.get("sender", "System")
        content = data.get("content", "")

        # 构建消息对象
        msg = {
            "sender": sender,
            "content": content,
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
        }

        # 广播给所有人 (包括发送者)
        emit("game:message", msg, broadcast=True)


if __name__ == "__main__":
    from flask import Flask
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(games_bp)

    app.run(debug=True)
