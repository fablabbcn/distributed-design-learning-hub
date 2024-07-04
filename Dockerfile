FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONPYCACHEPREFIX=/tmp/pycache
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_CREATE=0
ENV POETRY_CACHE_DIR=/tmp/poetry_cache
ENV MYPY_CACHE_DIR=/tmp/mypy_cache

WORKDIR /app

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential git \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Additional dependencies
  && apt-get install -y telnet netcat-traditional \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*


COPY pyproject.toml poetry.lock ./

RUN pip install poetry
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

WORKDIR /app

COPY . .

RUN git config --global --add safe.directory /app

RUN chmod +x ./entrypoint.sh

RUN chmod +x ./start_web.sh

RUN chmod +x ./start_celeryworker.sh

RUN chmod +x ./start_flower.sh


ENTRYPOINT ["./entrypoint.sh"]

