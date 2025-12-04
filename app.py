from src.Server import app, socketio
from threading import Thread
import os


def open_app():
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        os.system('start "" msedge.exe --app="http://localhost:5000"')


if __name__ == "__main__":
    Thread(target=open_app).start()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
