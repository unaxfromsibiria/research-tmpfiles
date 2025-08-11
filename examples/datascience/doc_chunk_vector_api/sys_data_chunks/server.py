import asyncio
import importlib
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import _base
from contextlib import asynccontextmanager
from time import monotonic

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .api import add_document_content_to_storage
from .api import create_vectors
from .api import preapare_state
from .api import select_chunks_for_request
from .settings import ServerSettings

manager = None
STOP_WORD = "quit"


def task_create_vec(task: str, document: str) -> str:
    result = create_vectors(document)
    if not result:
        return f"problem in task {task}"

    return ""


def get_pool_class(path: str = "") -> _base.Executor:
    """
    Returns the executor class based on the provided path.

    Args:
        path (str): The module and class name of the executor to be used. If empty, returns ThreadPoolExecutor.

    Returns:
        _base.Executor: The executor class.
    """
    if not path:
        return ThreadPoolExecutor
    module_name, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


@asynccontextmanager
async def lifespan(_):
    global manager

    # Startup event
    if manager is None:
        manager = Manager()
        asyncio.create_task(manager.process())
        preapare_state(settings=manager.settings)

    # This line represents the running server
    yield

    # Shutdown event
    if manager:
        manager.stop()

app = FastAPI(lifespan=lifespan)


class Manager:
    settings: ServerSettings
    queue: asyncio.Queue
    select_result: asyncio.Queue
    active: bool = False
    error: str

    def __init__(self):
        self.active = True
        self.queue = asyncio.Queue()
        self.select_result = asyncio.Queue()
        self.settings = ServerSettings()
        self.error = ""

    def add_document(self, document: str, text: str) -> int:
        info = add_document_content_to_storage(document, text, True)
        task_id = uuid.uuid4()
        self.queue.put_nowait((False, task_id, document))
        return f"{info} background task {task_id} for creation embedding"

    async def select(
        self, request: str, l2_rate: float, cosine_rate: float, prompt_limit: int, collect: bool
    ) -> dict:
        task_id = uuid.uuid4()
        self.queue.put_nowait((True, task_id, request, l2_rate, cosine_rate, prompt_limit, collect))
        timeout = self.settings.wait_limit
        correct_task = False
        spent_time = 0
        start_time = monotonic()
        while not correct_task:
            correct_task = True
            try:
                valid_result = await asyncio.wait_for(self.select_result.get(), timeout=timeout)
                if valid_result:
                    res_task_id, data = valid_result
                    if res_task_id == task_id:
                        return data
                    else:
                        self.error = f"Lost task: {res_task_id}"
                        correct_task = False
                        spent_time = start_time - monotonic()
            except asyncio.TimeoutError:
                return {}
            finally:
                timeout -= spent_time

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
        pool = get_pool_class(self.settings.pool_class)
        with pool(max_workers=self.settings.pool_size) as executor:
            while self.active:
                req = await self.queue.get()
                if req == STOP_WORD:
                    self.active = False
                    continue

                is_select, task_id, *req_data = req
                try:
                    if is_select:
                        result = await loop.run_in_executor(executor, select_chunks_for_request, *req_data)
                        self.select_result.put_nowait((task_id, result))
                    else:
                        result = await loop.run_in_executor(executor, task_create_vec, task_id, *req_data)
                        if result:
                            self.error = result
                except Exception as err:
                    self.error = f"Critical error: {err}"


class RequestAdd(BaseModel):
    document: str
    text: str


class RequestSelect(BaseModel):
    l2_rate_limit: float = 0.6
    cosine_rate_limit: float = 0.3
    text: str
    prompt_limit: int = 0
    collect: bool = False  # collect prompt to text

    def api_kwargs(self) -> dict:
        return {
            "request": self.text,
            "l2_rate": self.l2_rate_limit,
            "cosine_rate": self.cosine_rate_limit,
            "prompt_limit": self.prompt_limit,
            "collect": self.collect,
        }


@app.get("/")
async def read_root():
    global manager
    return {
        "model_name": manager.settings.model_name,
        "latest_error": manager.latest_error,
    }


@app.put("/document")
async def add_document(req: RequestAdd):
    """Save document as chunks"""
    global manager
    return {"result": manager.add_document(req.document, req.text)}


@app.post("/find-chunks")
async def find_chunks(request: RequestSelect):
    global manager
    data = await manager.select(**request.api_kwargs())
    return JSONResponse(content=data, status_code=200 if data else 404)


@app.post("/find-chunks-sync")
async def find_chunks_sync(request: RequestSelect):
    global manager
    data = select_chunks_for_request(**request.api_kwargs())
    return JSONResponse(content=data, status_code=200 if data else 404)
