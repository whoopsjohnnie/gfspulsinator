#!/bin/bash
set -e

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
THIS_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
COMPOSES_DIR=${THIS_DIR}/composes
source $THIS_DIR/settings.sh

#########################################################
## Main Automation Pipeline
#########################################################

gfscompose apply --host $GFS_HOST --namespace $GFS_NAMESPACE --file ${COMPOSES_DIR}/proxmoxinstances.yaml $VERBOSE # > /dev/null
