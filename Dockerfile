FROM python:3.12.5-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPYCACHEPREFIX=/tmp/pycache
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_CREATE=0
ENV POETRY_CACHE_DIR=/tmp/poetry_cache
ENV MYPY_CACHE_DIR=/tmp/mypy_cache

ARG uid=1000

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential git \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Additional dependencies
  && apt-get install -y telnet netcat-traditional psmisc procps \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

WORKDIR /app

RUN adduser --disabled-password --gecos '' -u ${uid} ddlh
RUN chown -R ddlh:ddlh /app

USER ddlh
COPY pyproject.toml poetry.lock ./

USER root
RUN chown -R ddlh:ddlh /app

USER ddlh
RUN poetry lock --no-update

USER root
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

USER ddlh
COPY . .
RUN git config --global --add safe.directory /app

USER root
RUN chmod +x ./entrypoint.sh
RUN chmod +x ./start_web.sh
RUN chmod +x ./start_celeryworker.sh
RUN chmod +x ./start_flower.sh

USER ddlh
ENTRYPOINT ["./entrypoint.sh"]
