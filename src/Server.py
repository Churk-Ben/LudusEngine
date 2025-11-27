from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pathlib import Path
import json
import os
from .Logger import get_logger
from .Config import load_config

BASE = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE / "res" / "app" / "static"
GAMES_DIR = BASE / ".games"
USERS_DIR = BASE / ".users"

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

# TODO 加载玩家
if USERS_DIR.exists():
    with open(USERS_DIR / "players.json", "r", encoding="UTF-8") as f:
        players_store = json.load(f)


# config 断点
@app.get("/api/config")
def api_config():
    pass


# games 断点
@app.get("/api/games")
def api_games():
    items = []
    if GAMES_DIR.exists():
        for p in GAMES_DIR.iterdir():
            if p.is_dir():
                items.append(p.name)
    return jsonify(items)


# players 断点
@app.get("/api/players")
def api_get_players():
    return jsonify({"ok": True, "data": players_store})


@app.post("/api/players")
def api_save_players():
    data = request.get_json(force=True) or {}
    with open(USERS_DIR / "players.json", "w", encoding="UTF-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return jsonify({"ok": True})


@app.get("/api/players/providers")
@log.decorate.info("拉取供应商列表")
def api_providers():
    import litellm

    _providers = []
    for provider in litellm.provider_list:
        _providers.append({"id": provider, "name": provider.capitalize()})

    _providers = sorted(_providers, key=lambda x: x["name"])
    return jsonify({"ok": True, "data": _providers})


@app.post("/api/players/llm/online")
def api_players_add_online():
    data = request.get_json(force=True) or {}
    item = {
        "id": data.get("id") or os.urandom(8).hex(),
        "name": data.get("name") or "",
        "providerId": data.get("providerId") or "",
        "model": data.get("model") or None,
    }
    players_store["online"].append(item)
    return jsonify(item)


@app.post("/api/players/llm/local")
def api_players_add_local():
    data = request.get_json(force=True) or {}
    item = {
        "id": data.get("id") or os.urandom(8).hex(),
        "name": data.get("name") or "",
        "modelPath": data.get("modelPath") or "",
        "parameters": data.get("parameters") or "",
    }
    players_store["local"].append(item)
    return jsonify(item)


@app.post("/api/players/human/local")
def api_players_add_human():
    data = request.get_json(force=True) or {}
    item = {
        "id": data.get("id") or os.urandom(8).hex(),
        "name": data.get("name") or "",
    }
    players_store["human"].append(item)
    return jsonify({"ok": True, "data": item})


@app.delete("/players/<pid>")
def api_players_remove(pid):
    players_store["online"] = [x for x in players_store["online"] if x.get("id") != pid]
    players_store["local"] = [x for x in players_store["local"] if x.get("id") != pid]
    players_store["human"] = [x for x in players_store["human"] if x.get("id") != pid]
    return jsonify({"ok": True})


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


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
