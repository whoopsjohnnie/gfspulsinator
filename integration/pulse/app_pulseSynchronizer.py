import asyncio

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

websocket_thread = None
websocket_thread_lock = Lock()

GFSHOST = "192.168.0.216" # "192.168.0.160"
#GFSHOST = "localhost" # "192.168.0.160"
GFSPORT = 5000
TYPE = ""

LISTENERADDR = "0.0.0.0"
LISTENERPORT = 5005

print (GFSHOST)

state = {
    "GFSHOST": GFSHOST, 
    "GFSPORT": GFSPORT, 
    "endpoint": "ws://" + GFSHOST + ":" + str(GFSPORT) + "/gfs1/graphql/subscriptions", 
    "active": False, 
    "type": TYPE, 
    "query": """subscription """ + TYPE + """Subscriber {
  """ + TYPE + """ {
    event, 
    id, 
    label, 
    sourceid, 
    sourcelabel, 
    targetid, 
    targetlabel, 
    chain, 
    node {
       id,
       name
    }
  }
}
""", 
    "models": []
}

client = GraphqlClient(
    endpoint=state.get("endpoint")
)

def callback(data = {}):

    typedata = data.get("data", {}).get(TYPE, {})
    typenode = typedata.get("node", {})

    if data and "message" in data:
        print("")
        print(" *** ")
        print(" *** GFS GraphQL subscription callback message. Please make sure TYPE " + TYPE + " exists.")
        print(data.get("message"))
        print(" *** ")
        print(" *** ")
        print(" ")
        # quit()
        exit()

    # print(" ")
    # print(" New " + TYPE + " event: ")
    # print(" Event: " + str( typedata.get("event", "")) )
    # print(" Id: " + str( typedata.get("id", "")) )
    # print(" Label: " + str( typedata.get("label", "")) )
    # print(" SourceId: " + str( typedata.get("sourceid", "")) )
    # print(" SourceLabel: " + str( typedata.get("sourceid", "")) )
    # print(" TargetId: " + str( typedata.get("targetid", "")) )
    # print(" TargetLabel: " + str( typedata.get("targetlabel", "")) )
    # print(" Chain: " + str( typedata.get("chain", "")) )
    # print(" ")

    event = typedata.get("event", None)
    id = typedata.get("id", None)
    label = typedata.get("label", None)
    sourceid = typedata.get("sourceid", None)
    sourcelabel = typedata.get("sourcelabel", None)
    targetid = typedata.get("targetid", None)
    targetlabel = typedata.get("targetlabel", None)
    chain = ", ".join(typedata.get("chain", []))

    typenodeid = typenode.get("id")
    typenodedesc = TYPE + "(" + typenodeid + ")"
    for key in typenode:
        typenodedesc += ", " + key + ": " + typenode.get(key, "[NONE]")

    statedata = {
        "event": event,
        "id": id,
        "label": label,
        "sourceid": sourceid,
        "sourcelabel": sourcelabel,
        "targetid": targetid,
        "targetlabel": targetlabel,
        "chain": chain,
        "data": typenode,
        "description": typenodedesc
    }

    socketio.emit(
        'update', statedata
    )

    if event == "create_node":
        create_handler(statedata)
    elif event == "update_node":
        update_handler(statedata)
    elif event == "delete_node":
        delete_handler(statedata)
    elif event == "create_link":
        link_handler(statedata)

def websocket_background_thread():
    state["active"] = True
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        client.subscribe(
            query=state.get("query"), 
            handle=callback
        )
    )
    state["active"] = False

def launch_websocket_background_thread():
    global websocket_thread
    with websocket_thread_lock:
        if websocket_thread is None:
            websocket_thread = socketio.start_background_task(websocket_background_thread)

launch_websocket_background_thread()

@app.route('/')
def index():
    status = "danger"
    if state.get("active", False):
        status = "success"
    return render_template(
        'index.html', 
        # state = state, 
        GFSHOST = state.get("GFSHOST"), 
        GFSPORT = state.get("GFSPORT"), 
        type = state.get("type", TYPE), 
        active = state.get("active", False), 
        status = status, 
        models = state.get("models", []), 
        async_mode = socketio.async_mode
    )

@socketio.event
def fromclient(message):
    emit('response', {
        'data': 'Received from client: ' + message['data']
    }
)

@socketio.event
def disconnect_request():

    def can_disconnect():
        disconnect()

    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit(
        'response', {
            'data': 'Disconnect!'
        },
        callback=can_disconnect
    )

@socketio.event
def connect():
    # 
    emit(
        'response', {
            'data': 'Connect'
        }
    )

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    client = GraphqlClient(
        endpoint=state.get("endpoint")
    )
    socketio.run(app, host=LISTENERADDR, port=LISTENERPORT)
