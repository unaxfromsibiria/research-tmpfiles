# Running the Web API

Voice generation with text and voice sample (~15 seconds is enough)

Build the image and launch:

```bash
docker build -t tts-gen .
docker run -d -p 8000:8000 -v ./data:/app/data -ti --name=tts-web-api --gpus=all tts-gen
```

Preparing the models (after start the container):

```bash
docker exec tts-web-api bash -c 'yes | python prepare.py'
```

It supports proxy (for downloading files):

```bash
docker exec tts-web-api bash -c 'yes | HTTP_PROXY="http://<host>:<port>" HTTPS_PROXY="http://<host>:<port>" python prepare.py'
```

## Using as API

Go to API http://<server with container>:8000/docs
