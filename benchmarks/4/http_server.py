
import asyncio
import sys

from aiohttp import web

cmd_args = set(sys.argv[1:])

if "-uvloop" in cmd_args:
    import uvloop
    print("Used uvloop.")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def main_page(request):
    return web.Response(text="Use url /calc/ and method POST.")


async def calc_handler(request):
    data = await request.json()
    a = map(float, data["a"])
    b = map(float, data["b"])
    sum_a = sum(a)
    avg_b = sum(b) / len(data["b"])
    c = sum_a / avg_b
    return web.json_response({
        "a": "{0:.6f}".format(sum_a),
        "b": "{0:.6f}".format(avg_b),
        "c": "{0:.6f}".format(c),
    })


def run(*args, **kwargs):
    """Run server method.
    python -m aiohttp.web -H 0.0.0.0 -P 8888 http_server:run
    """
    app = web.Application()
    app.router.add_get('/', main_page)
    app.router.add_post('/calc/', calc_handler)
    return app
