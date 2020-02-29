# python -m aiohttp.web -H localhost -P 8080 fast_server:run

import asyncio
import os
import time
import typing
from concurrent.futures import ThreadPoolExecutor

from aiohttp import web

WITH_DELAY: bool = True
WORKER: int = 4


def mult_sync_data(data: typing.Dict[str, str]) -> float:
    """Sync delay.
    """
    x: float = float(data["x"])
    y: float = float(data["y"])
    # delay in thread
    if WITH_DELAY:
        time.sleep(0.01)

    return x * y


class PlusDataView(web.View):
    """Full async handler.
    """

    async def post(self):
        request = self.request
        data = await request.json()
        x: float = float(data["x"])
        y: float = float(data["y"])
        return web.json_response({"result": str(x + y)})


class MultDataView(web.View):
    """Handler with execution in thread.
    """

    loop = None
    executor = None

    async def post(self):
        request = self.request
        if self.loop is None:
            self.loop = asyncio.get_running_loop()

        executor: ThreadPoolExecutor = request.app["thread_executor"]
        result = await self.loop.run_in_executor(
            executor, mult_sync_data, dict(await request.json())
        )

        return web.json_response({"result": result})


async def on_start(app):
    pid = os.getpid()
    print(f"server {pid}")


async def on_down(app):
    executor: ThreadPoolExecutor = app["thread_executor"]
    executor.shutdown()


def run(argv):
    app = web.Application()
    app["thread_executor"] = ThreadPoolExecutor(
        max_workers=WORKER, thread_name_prefix="support_"
    )

    app.router.add_routes([
        web.view("/plus", PlusDataView),
        web.view("/mult", MultDataView),
    ])
    app.on_startup.append(on_start)
    app.on_cleanup.append(on_down)
    return app
