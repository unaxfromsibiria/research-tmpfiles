# Service for searching document chunk using vector search with an embedding model

The service uses a PostgreSQL database and the [pgvector](https://github.com/pgvector/pgvector) extension. The web interface is implemented using FastAPI.
Model settings in the environment variable `MODEL_NAME`.
By default [ai-forever/ru-en-RoSBERTa](https://huggingface.co/ai-forever/ru-en-RoSBERTa) is used. For other languages, you will need to find something suitable.
All environment variables can be viewed in the module `settings.py`."

## Starting the Service in Docke

```bash
docker build -t emb-chunks-api .
mkdir .container_cache
docker run -d --gpus=all -e DB_CONNECTION="postgresql+psycopg2://user:pass@host:5432/db" --name=emb-chunks-api-service -v .container_cache:/root/.cache/ -p 8000:8000 emb-chunks-api
docker logs emb-chunks-api-service
```

## Migration (using Alembic)

```bash
docker exec -it emb-chunks-api-service bash -c /app/migrate.sh
```

If necessary, you can even create migrations directly in the container if it's required to change the data model description (eg embedding dimensionality)

```bash
docker exec -it emb-chunks-api-service python -c 'from sys_data_chunks.scripts import create_migration; create_migration("it got new column")'
```

## Example of an API request and response

Search by limits of L2 and cosine distances for vectors is performed using OR logic. Large requests are developed on chunks in the same way as document data for saving.

```bash
curl -X 'POST' \
  'http://service:8000/find-chunks' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "l2_rate_limit": 0.6,
  "cosine_rate_limit": 0.3,
  "text": "The service uses a PostgreSQL database and the pgvector extension",
  "prompt_limit": 150,
  "collect": false}'
```

response structure:

```json
{
  "doc_1.txt": [
    {
      "data": "chunk data 1",
      "l2": 0.756524948707151,
      "cosine": 0.2861650415560464
    },
    {
      "data": "chunk data 2",
      "l2": 0.7254190779340424,
      "cosine": 0.2631164789199777
    },
    {
      "data": "chunk data 3",
      "l2": 0.1939038596363264,
      "cosine": 0.018799336445271764
    }
  ],
  "doc_2.txt": [
    {
      "data": "chunk data 1",
      "l2": 0.756524948707151,
      "cosine": 0.2861650415560464
    },
    {
      "data": "chunk data 2",
      "l2": 0.7254190779340424,
      "cosine": 0.2631164789199777
    },
    {
      "data": "chunk data 3",
      "l2": 0.1939038596363264,
      "cosine": 0.018799336445271764
    }
  ],
}
```

In any case, see `http://service:8000/docs`
