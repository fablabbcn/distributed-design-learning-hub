#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

COMMAND="python"
ARGS="-m ddlh.app"
watchmedo auto-restart -d ddlh/ -R --patterns="*.py" $COMMAND -- $ARGS
