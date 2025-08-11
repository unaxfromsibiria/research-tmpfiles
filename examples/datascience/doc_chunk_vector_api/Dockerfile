FROM python:3.12-slim-bookworm

RUN apt update
RUN apt install -y gcc g++ python3-dev && apt-get autoclean && apt-get autoremove

RUN mkdir -p /app/
WORKDIR /app
RUN mkdir -p /root/.local/share/

COPY sys_data_chunks /app/sys_data_chunks
RUN pip install -U pip
RUN install -U -r sys_data_chunks/requirements.txt

# web api
RUN echo '#!/bin/bash' > /app/run.sh && chmod 775 /app/run.sh
RUN echo 'cd /app && python -m uvicorn sys_data_chunks.server:app --reload --host 0.0.0.0' >> /app/run.sh
# migration
RUN echo '#!/bin/bash' > /app/migrate.sh && chmod 775 /app/migrate.sh
RUN echo "cd /app && python -c 'from sys_data_chunks.scripts import run_migration; run_migration()'" >> /app/migrate.sh

EXPOSE 8000/tcp

CMD ["/app/run.sh"]
