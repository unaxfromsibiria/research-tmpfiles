try:
    import torch
    from TTS.api import TTS
except ImportError:
    torch = None

import asyncio
import concurrent.futures
import os
import uuid

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic import Field
from pydantic_settings.main import BaseSettings


AUDIO_EXT = "wav"
STOP_WORD = "quit"


def use_tts(data_dir: str, name: str, voice: str, text: str, lang: str) -> str:
    """Non empty result is an error."""
    try:
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
        file_path = os.path.join(data_dir, name)
        tts.tts_to_file(
            text=text,
            file_path=file_path,
            speaker_wav=[os.path.join(data_dir, f"{voice}.{AUDIO_EXT}")],
            language=lang,
            split_sentences=True
        )
    except Exception as err:
        return f"Problem: {err}"

    return ""


class ServerSettings(BaseSettings):
    pool_size: int = Field(env="PARALLEL_REQUESTS", default=2)
    data_dir: str = Field(env="DATA_DIR", default="/app/data/")
    iter_chek_delay: float = Field(env="ITER_DELAY", default=1)
    wait_limit: float = Field(env="WAIT_LIMIT", default=35)


app = FastAPI()
manager = None


class Manager:
    settings: ServerSettings
    queue: asyncio.Queue
    active: bool = False
    error: str

    def __init__(self):
        self.active = True
        self.queue = asyncio.Queue()
        self.settings = ServerSettings()
        self.error = ""

    def add(self, output: str, voice: str, text: str, lang: str) -> int:
        self.queue.put_nowait((output, voice, text, lang))
        return self.queue.qsize()

    def res_file(self, name: str):
        path = os.path.join(self.settings.data_dir, f"{name}.{AUDIO_EXT}")
        with open(path, mode="rb") as file:
            yield from file

    async def wait_res_file(self, name: str) -> bool:
        wait = 0
        path = os.path.join(self.settings.data_dir, f"{name}.{AUDIO_EXT}")
        while wait <= self.settings.wait_limit:
            wait += self.settings.iter_chek_delay
            if os.path.exists(path):
                wait = self.settings.wait_limit + 1
            else:
                await asyncio.sleep(self.settings.iter_chek_delay)

        return os.path.exists(path)

    def stop(self):
        self.active = False
        self.queue.put_nowait(STOP_WORD)

    @property
    def latest_error(self) -> str:
        value = str(self.error or "")
        self.error = ""
        return value

    async def process(self):
        """Waiting requests from buffer queue."""
        loop = asyncio.get_event_loop()
        pool = concurrent.futures.ProcessPoolExecutor
        with pool(max_workers=self.settings.pool_size) as executor:
            while self.active:
                req = await self.queue.get()
                if req == STOP_WORD:
                    self.active = False
                    continue

                result = await loop.run_in_executor(
                    executor,
                    use_tts,
                    self.settings.data_dir,
                    *req
                )
                if result:
                    self.error = result


class Request(BaseModel):
    voice: str = "voice_1"
    lang: str = "ru"
    text: str


@app.get("/")
async def read_root():
    global manager
    return {
        "torch_version": torch.__version__ if torch else "does not work",
        "latest_error": manager.latest_error,
    }


@app.put("/create")
async def create_audio(req: Request):
    code = uuid.uuid4().hex[:8]
    name = f"output_{code}.{AUDIO_EXT}"
    global manager
    return {
        "file": name,
        "queue": manager.add(name, req.voice, req.text, req.lang),
    }


@app.on_event("startup")
async def startup_event():
    global manager
    if manager is None:
        manager = Manager()
        asyncio.create_task(manager.process())


@app.on_event("shutdown")
async def shutdown_event():
    global manager
    if manager:
        manager.stop()


@app.get("/results/{output}." + AUDIO_EXT)
async def read_file(output: str):
    global manager
    exists = await manager.wait_res_file(output)
    if exists:
        return StreamingResponse(
            manager.res_file(output), media_type=f"audio/{AUDIO_EXT}"
        )
    else:
        return JSONResponse(
            content={"message": "Check error in main page."}, status_code=404
        )
