from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pathlib import Path
import os
import signal

from .Logger import get_logger
from .services.games import games_bp
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
    target = STATIC_DIR / path
    if target.exists():
        return send_from_directory(app.static_folder, path)
    if (STATIC_DIR / "index.html").exists():
        return send_from_directory(app.static_folder, "index.html")
    return jsonify({"ok": True})


@socketio.on("connect")
@log.decorate.info("捕获到链接请求")
def on_connect():
    global connected_client_sid
    if connected_client_sid is not None:
        log.warning(f"拒绝新的客户端连接, 因为已有连接: {connected_client_sid}")
        return False  # 拒绝连接
    connected_client_sid = request.sid
    log.info(f"客户端已连接, 会话ID: {connected_client_sid}")
    emit("server:ready", {"ok": True})


@socketio.on("disconnect")
def on_disconnect():
    global connected_client_sid
    if request.sid == connected_client_sid:
        log.info(f"客户端 {request.sid} 已断开, 正在关闭服务器...")
        connected_client_sid = None
        os.kill(os.getpid(), signal.SIGINT)
    else:
        log.warning(f"一个未被追踪的客户端 {request.sid} 已断开.")
