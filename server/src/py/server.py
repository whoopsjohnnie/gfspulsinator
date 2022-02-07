import logging
import os

# 
# Enable DEBUG here for detailed GraphQL logging
# 
# Need a clever play on 
# https://matrix.fandom.com/wiki/Electromagnetic_pulse
# EUP? Electro-Update-Pulse ? :) 

logging.basicConfig(level=logging.WARNING)
# logging.basicConfig(level=logging.INFO)
# logging.basicConfig(level=logging.DEBUG)

import requests
import polling2
import json
import threading
import time
from requests_toolbelt.utils import dump

# from python_graphql_client import GraphqlClient
from gfsgql import GFSGQL

requests.packages.urllib3.disable_warnings()

AGENT_ID='__PULSE_AGENT'
PULSE_POLL_STEP=3

STATUS_FAILING = "FAILING"
STATUS_UP_SYNCRONIZED = "UP"
STATUS_PENDING_UPDATE = "PENDING"
STATUS_LAGGING_UPDATE = "LAGGING"

STEP_CALC_PAD_FACTOR = 1.5

listen_addr = os.environ.get("LISTEN_ADDR", "0.0.0.0")
listen_port = os.environ.get("LISTEN_PORT", "5005")

gfs_ns = os.environ.get("GFS_NAMESPACE", "gfs1")
gfs_host = os.environ.get("GFS_HOST", "gfsapi")
gfs_port = os.environ.get("GFS_PORT", "5000")
gfs_username = os.environ.get("GFS_USERNAME", "root")
gfs_password = os.environ.get("GFS_PASSWORD", "root")

# TODO: What to do about this?
GFSAPI_NS = gfs_ns # 
GFSAPI_HOST = gfs_host # os.getenv('GFSAPI_HOST')
GFSAPI_PORT = gfs_port # os.getenv('GFSAPI_PORT')

# GFSAPI = "https://" + GFSAPI_HOST + ":" + str(GFSAPI_PORT)
GFSAPI = "http://" + GFSAPI_HOST + ":" + str(GFSAPI_PORT)
print(GFSAPI)

gfs_gqlclient = GFSGQL(
    gfs_host = GFSAPI_HOST, # gfs_host,
    gfs_port = str(GFSAPI_PORT), # gfs_port,
    gfs_username = None, # gfs_username,
    gfs_password = None, # gfs_password,
)

def current_sec_time():
    return round(time.time())

#########################################################
# 🔆 🔆 🔆 🔆    Handler Boilerplate    🔆 🔆 🔆 🔆
#########################################################

def create_handler(statedata):
    print ("---------Create Handler----------------")

def update_handler(statedata):
    print ("---------Update Handler----------------")

def delete_handler(statedata):
    print ("---------Delete Handler----------------")

def link_handler(statedata):
    print ("---------Link Handler------------------")

#########################################################
# 🧐 🧐 🧐 🧐         Queries           🧐 🧐 🧐 🧐
#########################################################

# GET_INSTANCES_BY_TYPE = GFSAPI + "/api/v1.0/gfs1/vertex?label={type}"
# GFSAPI_TEMPLATE_URL = GFSAPI + "/api/v1.0/gfs1/context/{GFSID}"
# GFSAPI_ALL_NODES_URL = GFSAPI + "/api/v1.0/gfs1/graph"
# GFSAPI_ALL_INSTANCES_OF_TYPE = GFSAPI + "/api/v1.0/gfs1/vertex?label={type}"
# GFSAPI_GRAPHQL_URL = GFSAPI + "/gfs1/graphql"

#########################################################
# 🔥 🔥 🔥 🔥 🔥    The Pulsinator    🔥 🔥 🔥 🔥 🔫
#########################################################

def log(string):
    # print (string)
    return string

def pulse_query(id, resource, status):
    if (status != None):
        retval = log (
            gfs_gqlclient.update(
                resource = resource, 
                arguments = {
                    "id": "String!", 
                    "status": "String", 
                    "lastPulseModifiedTime": "Int",
                    'lastAgentUpdateID': 'String'
                },
                variables = {
                    "id": id, 
                    "status": status,
                    "lastPulseModifiedTime": current_sec_time(),
                    "lastAgentUpdateID": AGENT_ID
                }, 
                fields = [
                    "id", 
                    "status", 
                    "lastStatusModifiedTime",
                    "lastPulseModifiedTime"
                ]
            )
        )
    else:
        retval = log (
            gfs_gqlclient.update(
                resource = resource, 
                arguments = {
                    "id": "String!", 
                    "lastPulseModifiedTime": "Int",
                    'lastAgentUpdateID': 'String'
                },
                variables = {
                    "id": id, 
                    "lastPulseModifiedTime": current_sec_time(),
                    "lastAgentUpdateID": AGENT_ID
                }, 
                fields = [
                    "id", 
                    "status", 
                    "lastStatusModifiedTime",
                    "lastPulseModifiedTime"
                ]
            )
        )
    return retval

tick = 0
def poll(response):
    global tick 
    tick = tick + 1
    tstamp = time.strftime('%X %x %Z')

    status_not_found = 0

    types = None
    # if type(response) in [list, tuple]:
    if type(response) in (tuple, list):
        types = response
    else:
        types = [response]

    print ("")
    print ("")
    print ("---[" + str(tick) + " @ " + tstamp + "] ------------------------------------")
    print ("")

    for _type in types:
        log ("name: " + _type['name'])

        valid = False
        if "properties" in _type:
            # if "status" in _type.get("properties", {}) and \
            #     "lastStatusModifiedTime" in _type.get("properties", {}) and \
            #     "statusTimeoutSecs" in _type.get("properties", {}) and \
            #     "lastPulseModifiedTime" in _type.get("properties", {}) and \
            #     "step" in _type.get("properties", {}) and \
            #     "lastAgentUpdateID" in _type.get("properties", {}):
            if {"name": "status", "type": "string"} in _type.get("properties", []) and \
                {"name": "lastStatusModifiedTime", "type": "integer"} in _type.get("properties", []) and \
                {"name": "statusTimeoutSecs", "type": "integer"} in _type.get("properties", []) and \
                {"name": "lastPulseModifiedTime", "type": "integer"} in _type.get("properties", []) and \
                {"name": "step", "type": "integer"} in _type.get("properties", []) and \
                {"name": "lastAgentUpdateID", "type": "string"} in _type.get("properties", []):
                valid = True

        if not valid:
            continue

        # instances_retval = requests.get(
        #     GET_INSTANCES_BY_TYPE.format(
        #         type=_type['name']
        #     ), 
        #     verify=False
        # )

        instances = []
        try:
            # instances_retval = gfs_gqlclient.query(
            instances = gfs_gqlclient.query(
                resource = _type['name'], # "type", 
                fields = [
                    "id", 
                    "name", 
                    "label", 
                    "status", 
                    "lastStatusModifiedTime", 
                    "statusTimeoutSecs", 
                    "lastPulseModifiedTime", 
                    "step", 
                    "lastAgentUpdateID"
                ]
            )
        except Exception as e:
            print(e)
            instances = []

        # instances_vertex_dict = instances # json.loads(instances_retval) # .content)
        # API vertex endpoint returns instances OR 'message':'notfound' then skip --
        # if 'message' in instances: # instances_vertex_dict:
        #     continue

        if not instances:
            continue

        for instance in instances: # instances_vertex_dict:
            # instance = instance.get('@value', {}).get('properties', {})
            log (str(tick) + " Candidate: {name}".format(name = instance.get('name')))
            log (instance)

            if not 'status' in instance:
                log ("No status property found in '{name}', skipping.".format(name = instance.get('name')))
                status_not_found = status_not_found + 1
                continue
            status = instance['status']
            if (status == STATUS_UP_SYNCRONIZED):  
                status_output = "🟩 UP"
            elif (status == STATUS_LAGGING_UPDATE):
                status_output = "⚠️  LAGGING"
            elif (status == STATUS_FAILING):
                status_output = "🤬 FAILING"
            else: 
                status_output = status + " UKNOWN STATE"

            # tstamp = time.strftime('%X %x %Z')
            id = instance.get('id') # , {}).get('@value')            
            status_timeout = int(instance.get('statusTimeoutSecs', 0)) # , {}).get('@value', 0))
            pulse_delta_secs = current_sec_time() - int(instance.get('lastPulseModifiedTime', 0)) # , {}).get('@value', 0))
            status_delta_secs = current_sec_time() - int(instance.get('lastStatusModifiedTime', 0)) # , {}).get('@value', 0))
            step = int(instance.get('step', 0)) # , {}).get('@value', 0))
 
            print ("---[" + str(tick) + " @ " + tstamp + "]--[ status-less GFS instances: " + str(status_not_found) + " ]-------------------------------")
            print ("🔭   [ current: " + status_output + " ]   " + instance.get('name') + "  [ " + instance.get('label') + " ]" + " [ " + instance.get('id') + " ]")
            print ("      [ 💓 last pulse: " + str(pulse_delta_secs) + "s ] [ 💤 step: " + str(step) + "s ] [ △ last status: " + str(status_delta_secs) + "s ] [ ⏰  timeout: " + str(status_timeout) +"s ]")

            # skip if the step time is larger than the time 
            # elapsed since last pulse, or if its already failing to 
            # shortcut recovery time
            if ((pulse_delta_secs < step) and (status != STATUS_FAILING) and (status != STATUS_LAGGING_UPDATE)):
                print ("  💤  Not pulsing ... (following step delay: " + str(step - pulse_delta_secs) + "s remaining)")
                print ('')
                continue
            else:
                print ("   〽️ Pulsing     ...")

            # pulse = None
            if (status_delta_secs >= status_timeout):
                # exceeded timeout, the agent has failed us all.
                print ("      --> Updating: status = " + STATUS_FAILING + " and lastPulseModifiedTime")
                status = STATUS_FAILING
                try:
                    # pulse = 
                    pulse_query(
                        id=id, 
                        resource=instance.get('label'), # _type['name'], 
                        status=status
                    )
                except Exception as e:
                    print ("      --> Updating: status = " + STATUS_FAILING + " and lastPulseModifiedTime FAILED ")
                    print(e)
            elif (status_delta_secs > (step * STEP_CALC_PAD_FACTOR)):
                # exceeded timeout, the agent has failed us all.
                print ("      --> Updating: status = " + STATUS_LAGGING_UPDATE + " and lastPulseModifiedTime")
                status = STATUS_LAGGING_UPDATE
                try:
                    # pulse = 
                    pulse_query(
                        id=id, 
                        resource=instance.get('label'), # _type['name'], 
                        status=status
                    )
                except Exception as e:
                    print ("      --> Updating: status = " + STATUS_LAGGING_UPDATE + " and lastPulseModifiedTime FAILED ")
                    print(e)
            else:
                print ("      --> Updating lastPulseModifiedTime")
                try:
                    # pulse = 
                    pulse_query(
                        id=id, 
                        resource=instance.get('label'), # _type['name'], 
                        status=None
                    )
                except Exception as e:
                    print ("      --> Updating lastPulseModifiedTime FAILED ")
                    print(e)
            # print ("      " + str(pulse))
            print ('')

    # print ("Status not found on #nodes: " + str(status_not_found))
    status_not_found = 0
    return False

def pulse_worker(query):
    try:
        polling2.poll(
            lambda: gfs_gqlclient.query(
                resource = "type", 
                fields = {
                    "id": "id", 
                    "name": "name", 
                    "typelabel": "typelabel", 
                    "properties": {
                        "name": "name",
                        "type": "type"
                    }
                }
            ),
            check_success=poll,
            step=PULSE_POLL_STEP,
            poll_forever=True
        )
    except polling2.TimeoutException as te:
        while not te.values.empty():
        # Print all of the values that did not meet the exception
            print (te.values.get())
    return

threads = []
def thread_launcher():
    t = threading.Thread(target=pulse_worker, args=("",))
    threads.append(t)
    t.start()

thread_launcher()
