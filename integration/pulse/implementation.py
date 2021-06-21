import logging

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

AGENT_ID='PULSINATOR_AGENT'
PULSE_POLL_STEP=3

GFSAPI_HOST = "192.168.56.60" # "192.168.0.160"
GFSAPI_PORT = 5000

# GFSAPI = "https://" + GFSAPI_HOST + ":" + str(GFSAPI_PORT)
GFSAPI = "http://" + GFSAPI_HOST + ":" + str(GFSAPI_PORT)

GFSAPI_TEMPLATE_URL = GFSAPI + "/api/v1.0/gfs1/context/{GFSID}"
GFSAPI_ALL_NODES_URL = GFSAPI + "/api/v1.0/gfs1/graph"
GFSAPI_ALL_INSTANCES_OF_TYPE = GFSAPI + "/api/v1.0/gfs1/vertex?label={type}"
GFSAPI_GRAPHQL_URL = GFSAPI + "/gfs1/graphql"

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

GET_INSTANCES_BY_TYPE = GFSAPI + "/api/v1.0/gfs1/vertex?label={type}"

#########################################################
# 🔥 🔥 🔥 🔥 🔥    The Pulsinator    🔥 🔥 🔥 🔥 🔫
#########################################################

def log(string):
    # print (string)
    return string

tick = 0
def poll(response):
    global tick 
    tick = tick + 1

    status_not_found = 0

    types = response

    tstamp = time.strftime('%X %x %Z')

    print ("")
    # print ("---[" + str(tick) + " @ " + tstamp + "] ------------------------------------")

    for type in types:
        log ("name: " + type['name'])
        instances_retval = requests.get(
            GET_INSTANCES_BY_TYPE.format(
                type=type['name']
            ), 
            verify=False
        )
        instances_vertex_dict = json.loads(instances_retval.content)
        # API vertex endpoint returns instances OR 'message':'notfound' then skip --
        if 'message' in instances_vertex_dict:
            continue

        for instance in instances_vertex_dict:
            instance = instance.get('@value', {}).get('properties', {})
            log (str(tick) + " Candidate: {name}".format(name = instance.get('name')))
            log (instance)

            if not 'status' in instance:
                log ("No status property found in '{name}', skipping.".format(name = instance.get('name')))
                status_not_found = status_not_found + 1
                continue

            print ("---[" + str(tick) + " @ " + tstamp + "]--[ status-less: " + str(status_not_found) + " ]----------------------------------")
            print ("⏩ " + instance.get('name') + " [" + str(type['name']) + "]")
            pulse_delta_secs = current_sec_time() - int(instance.get('lastPulseModifiedTime', {}).get('@value', 0))
            status_delta_secs = current_sec_time() - int(instance.get('lastStatusModifiedTime', {}).get('@value', 0))
            step = int(instance.get('step', {}).get('@value', 0))
            print ("   [ △ pulse_delta: " + str(pulse_delta_secs) + " ]  [ △ status_delta: " + str(status_delta_secs) + " ] [ ✳️  step: " + str(step) + " ]")
            
            # skip if the step time is larger than the time 
            # elapsed since last pulse
            if (pulse_delta_secs < step):
                print ("  ⚪ Not pulsing (step delay) ")
                print ('')
                continue
            else: 
                print ("  ✅ Pulsing ")

            status = "PENDING"
            if (status_delta_secs > int(instance.get('statusTimeoutSecs', {}).get('@value', 0))):
                # exceeded timeout, the agent has failed us all.
                print ("    🤬 FAILING (Updating Status!)")
                status = "FAILING"
                retval = log(
                    gfs_gqlclient.update(
                        resource = type['name'], 
                        arguments = {
                            "id": "String!", 
                            "status": "String", 
                            "lastPulseModifiedTime": "Int",
                            'lastAgentUpdateID': 'String'
                        },
                        variables = {
                            "id": instance.get('id', {}).get('@value'), 
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
                print ("      " + str(retval))
            else:
                print ("    ⏭️  PENDING Update (Updating Only lastPulseModifiedTime)")
                retval = log(
                    gfs_gqlclient.update(
                        resource = type['name'], 
                        arguments = {
                            "id": "String!", 
                            "lastPulseModifiedTime": "Int",
                            'lastAgentUpdateID': 'String'
                        },
                        variables = {
                            "id": instance.get('id', {}).get('@value'), 
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
                print ("      " + str(retval))
            print ('')

    # print ("Status not found on #nodes: " + str(status_not_found))
    status_not_found = 0
    return False

def pulse_worker(query):
    try:
        polling2.poll(
            lambda: gfs_gqlclient.query(
                resource = "type", 
                fields = [
                    "id", 
                    "name"
                ]
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
