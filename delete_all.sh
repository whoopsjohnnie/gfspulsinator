#!/bin/bash
set -e

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
THIS_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
source $THIS_DIR/settings.sh

#########################################################
## Main Automation Pipeline
#########################################################

echo "Deleting Graph: curl -s -X 'DELETE' $GRAPH_URL"
DELETE_RETVAL=$(curl -s -X "DELETE" $GRAPH_URL)
echo "DELETE_RETVAL: $DELETE_RETVAL"
