FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Additional dependencies
  && apt-get install -y telnet netcat-traditional \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*


# Requirements are installed here to ensure they will be cached.
COPY ./requirements.txt /requirements.txt
RUN pip install --ignore-installed -r /requirements.txt

COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY ./start_web.sh /start_web.sh
RUN chmod +x /start_web.sh

COPY ./start_celeryworker.sh /start_celeryworker.sh
RUN chmod +x /start_celeryworker.sh


COPY ./start_flower.sh /start_flower.sh
RUN chmod +x /start_flower.sh

WORKDIR /app

ENTRYPOINT ["/entrypoint.sh"]

