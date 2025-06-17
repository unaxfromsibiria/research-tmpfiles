FROM python:3.11-slim-bookworm

RUN apt update
RUN apt install -y gcc g++ python3-dev && apt-get autoclean && apt-get autoremove

RUN mkdir -p /app/data/
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN mkdir -p /root/.local/share/
RUN ln -sf /app/data/models/ /root/.local/share/tts

RUN pip install -U pip
RUN MAX_JOBS=32 pip install -U -r requirements.txt
RUN MAX_JOBS=32 pip install --no-deps TTS==0.22.0

COPY prepare.py /app/prepare.py
COPY server.py /app/server.py

RUN echo '#!/bin/bash' > /app/run.sh && chmod 777 /app/run.sh
RUN echo 'mkdir -p /app/data/models' >> /app/run.sh
RUN echo 'cd /app && python -m uvicorn server:app --reload' >> /app/run.sh

EXPOSE 8000/tcp

CMD ["/app/run.sh"]
