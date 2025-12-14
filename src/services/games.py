import datetime
import importlib.util
import os
from pathlib import Path
import queue
import sys
import threading

from flask import Blueprint, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room

from ..Logger import get_logger
from ..services.players import get_player_by_uuid

BASE = Path(__file__).resolve().parent.parent.parent
GAMES_DIR = BASE / ".games"

os.makedirs(GAMES_DIR, exist_ok=True)

games_bp = Blueprint("games", __name__)
games_log = get_logger("GameService")

# session_id -> { "game": game_instance, "thread": thread, "queues": {player_name: Queue} }
game_sessions = {}
_socketio_instance = None


class GameStopError(Exception):
    """当游戏被手动停止时抛出此异常"""

    pass


def load_game_class(game_name):
    """从.games目录动态加载游戏类"""
    game_path = GAMES_DIR / game_name / "game.py"
    if not game_path.exists():
        raise FileNotFoundError(f"在目录 {GAMES_DIR} 中未找到游戏 {game_name}")

    spec = importlib.util.spec_from_file_location(f"games.{game_name}", game_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"games.{game_name}"] = module
    spec.loader.exec_module(module)

    # Return the 'Game' class or attribute from the module
    if hasattr(module, "Game"):
        return getattr(module, "Game")
    raise AttributeError(f"在模块 {game_name} 中未找到 'Game' 类")


def make_event_emitter(session_id, socketio):
    def emitter(message, visible_to=None):
        # 构造消息对象
        msg = {
            "sender": {"name": "System", "id": "system", "type": "system"},
            "content": message,
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "visible_to": visible_to,
        }
        # 如果指定了可见性，可能需要更复杂的逻辑，目前广播到房间
        # TODO: 基于 visible_to 筛选目标客户端
        games_log.info(f"向 {session_id} 发送消息: {message}")
        socketio.emit("game:message", msg, room=session_id)

    return emitter


def make_input_handler(session_id, input_queues, socketio):
    def handler(player_name, input_type, prompt, choices, allow_skip):
        # 发送输入请求
        req = {
            "player_name": player_name,
            "type": input_type,
            "prompt": prompt,
            "choices": choices,
            "allow_skip": allow_skip,
        }
        # 发送给所有客户端，客户端根据 player_name 判断是否显示输入框
        socketio.emit("game:input_request", req, room=session_id)

        # 同时也作为消息发送，方便查看历史
        socketio.emit(
            "game:message",
            {
                "sender": {"name": "System", "id": "system", "type": "system"},
                "content": f"等待 {player_name} 输入: {prompt}",
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
            },
            room=session_id,
        )

        # 确保队列存在
        if player_name not in input_queues:
            input_queues[player_name] = queue.Queue()

        # 阻塞等待输入
        games_log.info(f"等待 {player_name} 输入, 会话ID: {session_id}")
        response = input_queues[player_name].get()

        if response == "__GAME_STOP__":
            games_log.info(f"游戏手动停止, 会话ID: {session_id}")
            raise GameStopError()

        games_log.info(f"从 {player_name} 接收输入: {response}")
        return response

    return handler


@games_bp.route("/api/games", methods=["GET"])
@games_log.decorate.info("拉取游戏列表")
def api_games_get():
    items = []
    if GAMES_DIR.exists():
        for p in GAMES_DIR.iterdir():
            if p.is_dir() and not p.name.startswith("logs"):
                items.append(p.name)

    games_log.info(f"游戏列表: {items}")
    return (
        jsonify({"ok": True, "data": items}),
        200,
    )


def socket_on_init_game(data):
    game_id = data.get("gameId")
    player_ids = data.get("playerIds")
    session_id = data.get("sessionId")
    sid = request.sid

    games_log.info(
        f"收到游戏初始化请求 - SID: {sid}, Session: {session_id}, Game: {game_id}, Players: {player_ids}"
    )

    # 初始化游戏状态
    game_info = {
        "name": game_id if game_id else "未命名",
        "status": "已连接, 初始化中...",
        "statusType": "success",
    }
    emit("game:info", game_info)

    # 准备玩家配置
    players_config = []
    players_display = []

    if player_ids:
        for uuid in player_ids:
            player_data = get_player_by_uuid(uuid)
            name = player_data["name"] if player_data else f"Player {uuid}"
            p_type = player_data["type"] if player_data else "unknown"

            # 构造传递给 Game 的配置
            p_conf = {
                "player_name": name,
                "player_uuid": uuid,
                "name": name,  # 兼容性保留
                "uuid": uuid,
                "human": (p_type == "human"),  # 标记是否为人类玩家
                # 可以合并其他配置
            }
            if player_data:
                p_conf.update(player_data)

            players_config.append(p_conf)

            # 构造前端显示列表
            players_display.append(
                {
                    "id": str(uuid),
                    "name": name,
                    "type": p_type,
                    "data": {},
                    # TODO: 向特定玩家注入data
                }
            )

    emit("game:players", players_display)

    try:
        # 加载游戏类
        GameClass = load_game_class(game_id)

        # 准备会话数据
        input_queues = {}

        # 实例化游戏
        # 注意：这里我们需要传入 emitter 和 input_handler
        # 此时我们需要 socketio 实例来创建 emitter
        if _socketio_instance is None:
            games_log.error("SocketIO 实例未初始化")
            emit(
                "game:notification",
                {
                    "type": "error",
                    "content": "服务器内部错误: SocketIO 未初始化",
                },
            )
            return

        emitter = make_event_emitter(session_id, _socketio_instance)
        input_handler = make_input_handler(session_id, input_queues, _socketio_instance)

        game = GameClass(
            players_config, event_emitter=emitter, input_handler=input_handler
        )

        # 启动游戏线程
        def run_game_wrapper():
            try:
                games_log.info(f"开始游戏循环, 会话ID: {session_id}")
                game.run_game()
                games_log.info(f"游戏循环结束, 会话ID: {session_id}")
                _socketio_instance.emit(
                    "game:info",
                    {"status": "游戏结束", "statusType": "info"},
                    room=session_id,
                )
            except GameStopError:
                games_log.info(f"游戏会话 {session_id} 手动停止")
                _socketio_instance.emit(
                    "game:info",
                    {"status": "游戏已停止", "statusType": "warning"},
                    room=session_id,
                )
            except Exception as e:
                games_log.error(f"游戏运行时错误: {e}")
                import traceback

                traceback.print_exc()
                _socketio_instance.emit(
                    "game:notification",
                    {"type": "error", "content": f"游戏运行时错误: {e}"},
                    room=session_id,
                )

        if _socketio_instance:
            thread = _socketio_instance.start_background_task(run_game_wrapper)
        else:
            thread = threading.Thread(target=run_game_wrapper, daemon=True)
            thread.start()

        # 存储会话
        game_sessions[session_id] = {
            "game": game,
            "thread": thread,
            "queues": input_queues,
        }
        games_log.info(f"游戏会话 {session_id} 已初始化")
        games_log.debug(f"当前线程池: {threading.enumerate()}")

        # 将当前 socket 加入房间
        # 注意: socket_on_init_game 是在请求上下文中调用的，所以可以使用 flask_socketio.join_room
        join_room(session_id)
        games_log.debug(f"Socket {request.sid} 加入房间 {session_id}")
        games_log.info(f"游戏会话 {session_id} 线程已启动")

        # 回复客户端
        emit(
            "game:notification",
            {"type": "success", "content": f"游戏 {game_id} 初始化成功"},
        )
        emit(
            "game:info",
            {"status": "游戏进行中", "statusType": "success"},
        )

    except Exception as e:
        games_log.error(f"启动游戏 {game_id} 失败: {e}")
        import traceback

        traceback.print_exc()
        emit(
            "game:notification", {"type": "error", "content": f"启动游戏失败: {str(e)}"}
        )


def socket_on_game_chat(data):
    sender = data.get("sender", {})
    content = data.get("content", "")
    session_id = data.get("sessionId")  # 需要前端传

    sender_name = sender.get("name", "Unknown")

    # 构建消息对象
    msg = {
        "sender": sender,
        "content": content,
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
    }
    games_log.debug(f"收到游戏聊天消息 - 发送者: {sender_name}, 内容: {content}")

    # 广播给所有人
    # 如果有 session_id，广播到房间
    if session_id:
        emit("game:message", msg, room=session_id)

        # 检查是否为游戏输入
        if session_id in game_sessions:
            session = game_sessions[session_id]
            queues = session["queues"]

            # 如果该玩家有正在等待的队列，将内容放入队列
            if sender_name in queues:
                # 只有当队列为空（正在等待）时才放入？
                # 或者直接放入，游戏那边会取
                # 为了防止多余的聊天信息干扰，这里可以做得更细致，但目前假设所有聊天都是输入
                games_log.info(f"路由输入到玩家 {sender_name} 在会话 {session_id}")
                queues[sender_name].put(content)
            else:
                games_log.debug(f"玩家 {sender_name} 没有活跃的输入队列")
    else:
        # 降级：广播给所有连接的客户端（不推荐，但作为 fallback）
        games_log.warning("没有 sessionId 在聊天中，广播给所有连接的客户端")
        emit("game:message", msg, broadcast=True)


def socket_on_game_leave(data):
    session_id = data.get("sessionId")
    games_log.info(f"收到游戏离开请求 - Session: {session_id}")

    if session_id in game_sessions:
        # 优雅停止游戏线程
        session = game_sessions[session_id]
        if "game" in session and hasattr(session["game"], "stop_game"):
            session["game"].stop_game()

        # 解除所有输入队列的阻塞
        if "queues" in session:
            for q_name, q in session["queues"].items():
                games_log.info(f"向会话 {session_id} 的队列 {q_name} 放入停止信号")
                q.put("__GAME_STOP__")

        # 不立即删除，等待线程结束？或者直接删除，线程会因为 _running False 而退出
        # 这里为了安全，我们还是删除引用
        del game_sessions[session_id]
        games_log.info(f"游戏会话 {session_id} 已标记停止并移除")
        games_log.debug(f"当前线程池: {threading.enumerate()}")

    leave_room(session_id)
    games_log.debug(f"Socket {request.sid} 从房间 {session_id} 退出")


def init_game_socket_events(socketio: SocketIO):
    global _socketio_instance
    _socketio_instance = socketio

    @games_log.decorate.info("初始化游戏请求")
    @socketio.on("app:initGame")
    def on_init_game(data):
        socket_on_init_game(data)

    @games_log.decorate.info("游戏聊天请求")
    @socketio.on("game:chat")
    def on_game_chat(data):
        socket_on_game_chat(data)

    @games_log.decorate.info("游戏离开请求")
    @socketio.on("game:leave")
    def on_game_leave(data):
        socket_on_game_leave(data)


if __name__ == "__main__":
    from flask import Flask
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(games_bp)

    app.run(debug=True)
