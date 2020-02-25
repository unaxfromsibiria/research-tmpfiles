FROM        python:3.7.6-slim-buster

RUN         mkdir /app && apt-get update && apt-get install -y python3-pip && pip install -U pip
COPY        requirements.txt /app/requirements.txt
COPY        infobot /app/infobot
WORKDIR     /app
RUN         pip install -r requirements.txt
RUN         apt-get clean && rm -r ~/.cache

ENTRYPOINT  python -m infobot.run
