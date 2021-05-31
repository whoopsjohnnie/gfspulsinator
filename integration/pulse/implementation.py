import requests
import polling2
import json
import threading
import time
from requests_toolbelt.utils import dump
from python_graphql_client import GraphqlClient

requests.packages.urllib3.disable_warnings() 

GFSAPI_HOST = "192.168.0.160" # "192.168.0.160"
GFSAPI_PORT = 5000

# GFSAPI = "https://" + GFSAPI_HOST + ":" + str(GFSAPI_PORT)
GFSAPI = "http://" + GFSAPI_HOST + ":" + str(GFSAPI_PORT)

GFSAPI_TEMPLATE_URL = GFSAPI + "/api/v1.0/gfs1/context/{GFSID}"
GFSAPI_ALL_NODES_URL = GFSAPI + "/api/v1.0/gfs1/graph"

GFSAPI_ALL_INSTANCES_OF_TYPE = GFSAPI + "/api/v1.0/gfs1/vertex?label={type}"

GFSAPI_GRAPHQL_URL = GFSAPI + "/gfs1/graphql"
gfs_gqlclient = GraphqlClient(endpoint=GFSAPI_GRAPHQL_URL)
# from gfsgql import GFSGQL

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

GET_ALL_TYPES = "query allTypes {  types {    id,    name  } }"

GET_INSTANCES_BY_TYPE = GFSAPI + "/api/v1.0/gfs1/vertex?label={type}"

UPDATE_STATUS_QUERY = """
mutation updateStatus
(
        $id:String!,
        $status: String,
        $lastPulseModifiedTime: Int,
    ) 
{{                
    update{type} (
        id:$id,
        status:$status,
        lastPulseModifiedTime:$lastPulseModifiedTime,
        ) {{
        instance {{
            id,
            status,
            lastPulseModifiedTime,
        }},              
        ok
    }}
}}
"""

UPDATE_STATUS_VARIABLES = """
{{
  "id": {id},
  "status": "{status}",
  "lastPulseModifiedTime": {lastPulseModifiedTime}
}}
"""

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

    response_dict = json.loads(response.text)
    types = response_dict['data']['types']
    for type in types:
        print ("name: " + type['name'])
        instances_retval = requests.get(
            GET_INSTANCES_BY_TYPE.format(
                type=type['name']
            ), 
            verify=False)
        instances_vertex_dict = json.loads(instances_retval.content)
        # API vertex endpoint returns instances OR 'message':'notfound' then skip --
        if 'message' in instances_vertex_dict:
            continue

        for instance in instances_vertex_dict:
            instance = instance['@value']['properties']
            print ("Candidate: {name}".format(
                name = instance['name']
            ))
            # print (instance)

            if not 'status' in instance:
                print ("No status property found in '{name}', skipping.".format(name = instance['name']))
                continue

            delta = current_sec_time() - int(instance['lastPulseModifiedTime']['@value'])
            timeout_policy = delta > int(instance['statusTimeoutSecs']['@value'])
            print ('timeout_policy for {name}: {timeout_policy}'.format(name = instance['name'], timeout_policy = timeout_policy))

            status = "PENDING"
            if (timeout_policy):
                # exceeded timeout, the agent has failed us all.
                status = "FAILING"

            update_query = log( UPDATE_STATUS_QUERY.format(
                type = type['name'])
            )
            update_variables = log( UPDATE_STATUS_VARIABLES.format(
                id = instance['id']['@value'],
                status = status,
                lastPulseModifiedTime = current_sec_time())
            )

            retval = log(
                gfs_gqlclient.execute(
                    query = update_query,
                    variables = update_variables
                )
            )

            log ("------------------------------------")
    print ("Tick: " + str(tick))

    return False

def pulse_worker(query):
    try:
        polling2.poll(
            lambda: requests.post(
                GFSAPI_GRAPHQL_URL, 
                verify=False,
                json={
                    "query": GET_ALL_TYPES,
                    "variables": {}
                }
            ),
            check_success=poll,
            step=1,
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

