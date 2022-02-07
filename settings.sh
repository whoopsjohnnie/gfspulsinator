#!/bin/bash

##################################################
export DEBUG_LEVEL="DEBUG"
#
#  Common settings and vars for the reference spec of automating via GFS
# 
export COMMON_NETWORK="botcanics"
export CONTAINER_NAME="gremlincl-dev"
export GIT_SHA=$(git rev-parse HEAD | cut -c 1-8)
export IMAGE="jeremykuhnash/$CONTAINER_NAME:$GIT_SHA"
export IMAGE_LATEST="jeremykuhnash/$CONTAINER_NAME:latest"

export GFS_NAMESPACE="gfs1"
# export GFS_HOST="botwork"
# export GFS_HOST="10.88.88.60"
# export GFS_HOST="10.88.88.61"
export GFS_HOST="10.88.88.62"
export GFS_PORT="5000"
export GFS_USERNAME="root"
export GFS_PASSWORD="root"
# export VERBOSE="--verbose"
export VERBOSE=""

export GRAPH_URL="http://$GFS_HOST:$GFS_PORT/api/v1.0/gfs1/graph"
export GRAPH_API_URL="http://$GFS_HOST:$GFS_PORT"

##################################################
## Functions
debug () { 
    if [ "$DEBUG_LEVEL" == "DEBUG" ]; then
        echo "debug: $1"
    fi
}
