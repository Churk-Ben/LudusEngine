from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pathlib import Path

from .Logger import get_logger
from .Config import load_config
from .services.games import games_bp
from .services.players import players_bp

BASE = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE / "res" / "app" / "static"

# 初始化日志
log = get_logger("Server")

# 加载配置
config = load_config()


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
    log.info("客户端已连接")
    emit("server:ready", {"ok": True})
