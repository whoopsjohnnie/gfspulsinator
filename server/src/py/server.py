import asyncio
import os

from threading import Lock

from flask import Flask
from flask import render_template
from flask import request
from flask import Response

from flask_socketio import SocketIO
from flask_socketio import emit
from flask_socketio import disconnect

from python_graphql_client import GraphqlClient

# from proxmoxer import ProxmoxAPI
from implementation import create_handler
from implementation import update_handler
from implementation import delete_handler
from implementation import link_handler

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)

# websocket_thread = None
# websocket_thread_lock = Lock()
