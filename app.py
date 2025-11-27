# TODO 整理路由
@app.get("/config")
def config():
    return jsonify({})


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


@app.post("/players/online")
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


@app.post("/players/local")
def api_players_add_local():
    data = request.get_json(force=True) or {}
    item = {
        "id": data.get("id") or os.urandom(8).hex(),
        "modelName": data.get("modelName") or "",
        "modelPath": data.get("modelPath") or "",
        "parameters": data.get("parameters") or "",
    }
    players_store["local"].append(item)
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
    players_store["online"] = [x for x in players_store["online"] if x.get("id") != pid]
    players_store["local"] = [x for x in players_store["local"] if x.get("id") != pid]
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
@log.decorate.info("客户端连接函数")
def on_connect():
    log.info("客户端连接")
    emit("server:ready", {"ok": True})


@socketio.on("client:ping")
@log.decorate.info("客户端发送 ping 消息, 参数 data={data}")
def on_ping(data=None):
    emit("server:pong", {"ok": True, "echo": data})
