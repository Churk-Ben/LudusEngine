from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pathlib import Path
import os
from .Logger import get_logger

BASE = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE / "res" / "app" / "static"
GAMES_DIR = BASE / "games"

# 初始化日志
log = get_logger("LudusServer")

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

providers = [
    {"id": "openai", "name": "OpenAI", "kind": "api"},
    {"id": "azure_openai", "name": "Azure OpenAI", "kind": "api"},
    {"id": "ollama", "name": "Ollama", "kind": "api"},
]

players_store = {"llm": [], "human": []}


@app.get("/providers")
def api_providers():
    return jsonify(providers)


@app.get("/games")
def api_games():
    items = []
    if GAMES_DIR.exists():
        for p in GAMES_DIR.iterdir():
            if p.is_dir():
                items.append(p.name)
    return jsonify(items)


@app.get("/players")
def api_players_list():
    return jsonify(players_store)


@app.post("/players/llm")
def api_players_add_llm():
    data = request.get_json(force=True) or {}
    item = {
        "id": data.get("id") or os.urandom(8).hex(),
        "name": data.get("name") or "",
        "providerId": data.get("providerId") or "",
        "model": data.get("model") or None,
    }
    players_store["llm"].append(item)
    return jsonify(item)


@app.post("/players/human")
def api_players_add_human():
    data = request.get_json(force=True) or {}
    item = {
        "id": data.get("id") or os.urandom(8).hex(),
        "name": data.get("name") or "",
    }
    players_store["human"].append(item)
    return jsonify(item)


@app.delete("/players/<pid>")
def api_players_remove(pid):
    players_store["llm"] = [x for x in players_store["llm"] if x.get("id") != pid]
    players_store["human"] = [x for x in players_store["human"] if x.get("id") != pid]
    return jsonify({"ok": True})


@app.post("/llmol/<providerId>/completions")
def api_llmol_completions(providerId):
    data = request.get_json(force=True) or {}
    prompt = data.get("prompt") or ""
    api = data.get("api") or ""
    model = data.get("model") or ""
    return jsonify(
        {
            "kind": "online",
            "provider": providerId,
            "api": api,
            "model": model,
            "output": f"echo: {prompt[:200]}",
        }
    )


@app.post("/llmlc/completions")
def api_llmlc_completions():
    data = request.get_json(force=True) or {}
    prompt = data.get("prompt") or ""
    model_path = data.get("modelPath") or ""
    return jsonify(
        {"kind": "local", "modelPath": model_path, "output": f"echo: {prompt[:200]}"}
    )


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
def on_connect():
    emit("server:ready", {"ok": True})


@socketio.on("client:ping")
def on_ping(data=None):
    emit("server:pong", {"ok": True, "echo": data})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
