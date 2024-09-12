#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

COMMAND="gunicorn"
ARGS="-k gevent ddlh.app:app"
watchmedo auto-restart -d ddlh/ -R --patterns="*.py" $COMMAND -- $ARGS
