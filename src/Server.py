import os
from pathlib import Path
import signal

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from .Logger import get_logger
from .services.games import games_bp, init_game_socket_events
from .services.players import players_bp

BASE = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE / "res" / "app" / "static"

# 初始化日志
log = get_logger("MainServer")

# 用于跟踪已连接的客户端
connected_client_sid = None

# 初始化Flask应用
app = Flask(
    __name__,
    static_folder=str(STATIC_DIR),
    static_url_path="/static",
)
CORS(app)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet",
)

# 初始化游戏Socket事件
init_game_socket_events(socketio)

app.register_blueprint(games_bp)
app.register_blueprint(players_bp)


# 全局变量，用于跟踪已连接的客户端
connected_client_sid = None


@app.get("/")
def index_root():
    if (STATIC_DIR / "index.html").exists():
        return send_from_directory(app.static_folder, "index.html")
    return jsonify({"ok": True})


@app.get("/<path:path>")
def serve_static(path):
    log.debug(f"请求静态资源: {path}")
    target = STATIC_DIR / path
    if target.exists():
        return send_from_directory(app.static_folder, path)

    # 检查是否是 API 调用或其他不应 fallback 的路径
    if path.startswith("api/") or path.startswith("socket.io"):
        return jsonify({"ok": False, "error": "Not Found"}), 404

    if (STATIC_DIR / "index.html").exists():
        log.debug(f"Fallback to index.html for: {path}")
        return send_from_directory(app.static_folder, "index.html")
    return jsonify({"ok": True})


@socketio.on("connect")
@log.decorate.info("捕获到链接请求")
def on_connect():
    global connected_client_sid
    if connected_client_sid is not None:
        log.warning(f"检测到新的客户端连接，替换旧连接: {connected_client_sid}")
        # 这里我们允许新连接，并更新 connected_client_sid
        # 旧连接断开时，我们需要确保不关闭服务器
        pass
    connected_client_sid = request.sid
    log.info(f"客户端已连接, 会话ID: {connected_client_sid}")
    emit("server:ready", {"ok": True})


@socketio.on("disconnect")
def on_disconnect():
    global connected_client_sid
    if request.sid == connected_client_sid:
        log.info(f"客户端 {request.sid} 已断开, 正在关闭服务器...")
        connected_client_sid = None

        # 检查是否允许关闭
        # 默认允许关闭 (0), 除非 DEBUG_SERVER 明确设为 1
        DEBUG_SERVER = os.getenv("DEBUG_SERVER", "0") == "1"

        if DEBUG_SERVER:
            log.info("Debug 模式下保持服务器运行 (DEBUG_SERVER=1)")
        else:
            # 正常退出
            log.info("正在停止服务器...")
            os._exit(0)
    else:
        log.warning(f"一个旧的或未被追踪的客户端 {request.sid} 已断开.")
