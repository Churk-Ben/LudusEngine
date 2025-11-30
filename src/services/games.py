from flask import Blueprint, jsonify
from pathlib import Path
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

    data = {"ok": True, "data": items}
    return jsonify(data)


if __name__ == "__main__":
    from flask import Flask
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(games_bp)

    app.run(debug=True)
