from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pathlib import Path
import os
from .Logger import get_logger

BASE = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE / "res" / "app" / "static"
GAMES_DIR = BASE / "games"

log = get_logger("LudusServer")

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/")
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

providers = [
    {"id": "openai", "name": "OpenAI", "kind": "api"},
    {"id": "azure_openai", "name": "Azure OpenAI", "kind": "api"},
    {"id": "ollama", "name": "Ollama", "kind": "local"},
    {"id": "local", "name": "本地模型", "kind": "local"},
]

players_store = {"llm": [], "human": []}

@app.get("/api/providers")
def api_providers():
    return jsonify(providers)

@app.get("/api/games")
def api_games():
    items = []
    if GAMES_DIR.exists():
        for p in GAMES_DIR.iterdir():
            if p.is_dir():
                items.append(p.name)
    return jsonify(items)

@app.get("/api/players")
def api_players_list():
    return jsonify(players_store)

@app.post("/api/players/llm")
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

@app.post("/api/players/human")
def api_players_add_human():
    data = request.get_json(force=True) or {}
    item = {
        "id": data.get("id") or os.urandom(8).hex(),
        "name": data.get("name") or "",
    }
    players_store["human"].append(item)
    return jsonify(item)

@app.delete("/api/players/<pid>")
def api_players_remove(pid):
    players_store["llm"] = [x for x in players_store["llm"] if x.get("id") != pid]
    players_store["human"] = [x for x in players_store["human"] if x.get("id") != pid]
    return jsonify({"ok": True})

@app.post("/api/llm/<providerId>/completions")
def api_llm_completions(providerId):
    data = request.get_json(force=True) or {}
    prompt = data.get("prompt") or ""
    return jsonify({"provider": providerId, "output": f"echo: {prompt[:200]}"})

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
    socketio.run(app, host="0.0.0.0", port=5000)
