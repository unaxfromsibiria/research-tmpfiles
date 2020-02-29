# python client.py plus & python client.py save

import asyncio
import random
import sys
import typing
from time import monotonic

import aiohttp
import aiohttp.web

REQUEST_COUNT = 1000
DELAY = 0
WORKER = 6

TARGET = "http://127.0.0.1:8080"


async def run_requests(index: int, url: str):
    """Client requests.
    """
    params: typing.Dict[str, str] = {"x": "", "y": ""}
    count: int = 0
    errors: int = 0
    start: float = monotonic()
    async with aiohttp.ClientSession() as session:
        for _ in range(REQUEST_COUNT):
            params["x"] = str(random.random())
            params["y"] = str(random.random())
            try:
                async with session.post(url, json=params) as resp:
                    if resp.status == aiohttp.web.HTTPOk.status_code:
                        new_data = await resp.json()
                        if new_data.get("result"):
                            count += 1
                    else:
                        errors += 1

            except Exception as err:
                errors += 1
                print(err)

            if DELAY:
                await asyncio.sleep(DELAY)

    et: float = monotonic() - start
    print(
        f"worker {index} {url} count: {count} errors: {errors} time: {et}"
    )


async def main():
    """
    """
    loop = asyncio.get_running_loop()
    loop.set_debug(True)

    coroutines: list = []
    *_, method = sys.argv
    url = f"{TARGET}/{method}"
    for index in range(WORKER):
        coroutines.append(
            run_requests(index + 1, url)
        )

    await asyncio.gather(*coroutines)


asyncio.run(main())
