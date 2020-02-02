FROM        python:3.7.6-slim-buster

RUN         mkdir /app && apt-get update && apt-get install -y python3-pip && pip install -U pip
COPY        ps_common/requirements.txt /app/requirements.txt
COPY        ps_common/manage.py /app/manage.py
COPY        ps_common/common /app/common
WORKDIR     /app
RUN         pip install -r requirements.txt
RUN         apt-get clean && rm -r ~/.cache

EXPOSE 8000
ENTRYPOINT  python manage.py runserver 0.0.0.0:8000
