FROM        python:3.7.6-slim-buster

RUN         mkdir /app && apt-get update && apt-get install -y python3-pip && pip install -U pip
COPY        rate_source_mock/requirements.txt /app/requirements.txt
COPY        rate_source_mock/http_server.py /app/http_server.py
WORKDIR     /app
RUN         pip install -r requirements.txt
RUN         apt-get clean && rm -r ~/.cache

EXPOSE 8000
ENTRYPOINT  python -m aiohttp.web -H 0.0.0.0 -P 8000 http_server:start
