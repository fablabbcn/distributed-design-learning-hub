#!/bin/bash

set -o errexit
set -o nounset

celery -A ddlh.tasks worker --loglevel=info
