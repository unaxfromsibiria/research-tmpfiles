# SERVICE_URL=http://localhost:8088/exchange_rates.json python -m aiohttp.web -H localhost -P 8080 http_server:start

import asyncio
import os

from aiohttp import ClientSession
from aiohttp import web


def env_var_line(key: str) -> str:
    """Reading a environment variable as text.
    """
    return str(os.environ.get(key) or "").strip()


SERVICE_URL = env_var_line("SERVICE_URL")


async def exchange_rates_request(request):
    """Rates from cache.
    """
    return web.json_response(request.app["rate_cahce"])


async def update_rates(app):
    """Periodic background request for external service.
    """
    time_out = 0.05  # first delay
    while True:
        await asyncio.sleep(time_out)
        time_out = 10.0  # default delay
        async with ClientSession() as session:
            async with session.get(SERVICE_URL) as resp:
                if resp.status == web.HTTPOk.status_code:
                    data = await resp.json()
                    if isinstance(data, dict):
                        rates = data.get("rates")
                        if rates:
                            print(f"New currency rates {len(rates)}")
                            app["rate_cahce"].update(rates)


async def run_update_task(app):
    """Run background tasks for application.
    """
    app["rate_updater"] = asyncio.create_task(update_rates(app))
    app["rate_cahce"] = {}


def start(*args):
    assert SERVICE_URL, "Set env variable SERVICE_URL."
    app = web.Application()
    app.add_routes([
        web.get("/actual_rates.json", exchange_rates_request)
    ])
    app.on_startup.append(run_update_task)

    return app
