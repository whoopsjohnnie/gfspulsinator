import requests
import polling2
import json
from threading import Lock
import threading
from requests_toolbelt.utils import dump

requests.packages.urllib3.disable_warnings() 

headers = {
    'user-agent': "botcanics-restclient",
    'content-type': "application/json",
    'authorization': "PVEAPIToken=bots@pam!botcanics=bc1f0af3-49f1-41a2-8729-003e99ec3625"
}

GFSAPI_HOST = "localhost" # "192.168.0.160"
GFSAPI_PORT = 5000

# GFSAPI = "https://" + GFSAPI_HOST + ":" + str(GFSAPI_PORT)
GFSAPI = "http://" + GFSAPI_HOST + ":" + str(GFSAPI_PORT)

GFSAPI_TEMPLATE_URL= GFSAPI + "/api/v1.0/gfs1/context/{GFSID}"

def create_handler(statedata):
    print ("---------Create Handler----------------")

def update_handler(statedata):
    print ("---------Update Handler----------------")

def delete_handler(statedata):
    print ("---------Delete Handler----------------")

def link_handler(statedata):
    print ("---------Link Handler----------------")

# The Pulsatinator.
def templatePoller(response):
    print (response.text)
    return False

def pulse_worker(query):
    try:
        print(" CALLING: " + GFSAPI_TEMPLATE_URL.format(GFSID = "646"))
        polling2.poll( 
            lambda: requests.get(GFSAPI_TEMPLATE_URL.format(GFSID = "646"), 
            headers=headers,
            verify=False,
            data=query),
            check_success=templatePoller,
            step=.25,
            poll_forever=True)
    except polling2.TimeoutException as te:
        while not te.values.empty():
        # Print all of the values that did not meet the exception
            print (te.values.get())
    return

threads = []
def thread_launcher():
    # t = threading.Thread(target=pulse_worker(""))
    t = threading.Thread(target=pulse_worker, args=("",))
    threads.append(t)
    t.start()

thread_launcher()


# Proxmox Poller example
# def templatePoller(response):
#     """Check that the response returned 'success'"""
#     print (response.text)
#     return False

# try:
#     polling2.poll( 
#         lambda: requests.get(PMOXAPI_NEXTID_ENDPOINT, 
#         headers=headers, 
#         verify=False),
#         check_success=templatePoller,
#         step=.25,
#         poll_forever=True)
# except polling2.TimeoutException as te:
#     while not te.values.empty():
#         # Print all of the values that did not meet the exception
#         print (te.values.get())


