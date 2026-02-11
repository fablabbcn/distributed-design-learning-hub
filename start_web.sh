#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

COMMAND="gunicorn"
ARGS="-k gevent ddlh.app:app --max-requests ${GUNICORN_MAX_REQUESTS:-1200} -w 1"
watchmedo auto-restart -d ddlh/ -R --patterns="*.py" $COMMAND -- $ARGS
