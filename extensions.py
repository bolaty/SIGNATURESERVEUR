#import eventlet
#eventlet.monkey_patch()  # Patch eventlet AVANT les imports Flask
from flask_socketio import SocketIO, emit
from flask import Flask

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')