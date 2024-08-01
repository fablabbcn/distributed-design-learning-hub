#!/bin/bash

set -o errexit
set -o nounset

celery -A app.tasks worker --loglevel=info
