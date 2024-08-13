#!/bin/bash

set -o errexit
set -o nounset

COMMAND="celery -- "
ARGS="-A ddlh.celery worker -P gevent --loglevel=info"
watchmedo auto-restart -d ddlh/ -R --patterns="*.py" $COMMAND -- $ARGS
