from flask import Flask
from flask_socketio import SocketIO, send, emit
import src.Server


if (__name__ == "__main__"):
    app = Flask(__name__)
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
