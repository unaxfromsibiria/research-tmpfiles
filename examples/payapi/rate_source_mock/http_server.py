# python -m aiohttp.web -H localhost -P 8080 http_server:start

import random
from datetime import datetime
from copy import deepcopy

from aiohttp import web

source_data = {
    "rates": {
        "CAD": 1.323470865,
        "HKD": 7.7671914586,
        "ISK": 123.3260948245,
        "PHP": 51.0152008686,
        "DKK": 6.7617625769,
        "HUF": 304.9674267101,
        "CZK": 22.8103510677,
        "GBP": 0.7616268549,
        "RON": 4.3240137532,
        "SEK": 9.6605139341,
        "IDR": 13655.0036192544,
        "INR": 71.3947701773,
        "BRL": 4.2668295331,
        "RUB": 63.6423271806,
        "HRK": 6.7354325009,
        "JPY": 108.8943177705,
        "THB": 31.1798769453,
        "CHF": 0.9676076728,
        "EUR": 0.9048136084,
        "MYR": 4.098534202,
        "BGN": 1.7696344553,
        "TRY": 5.9823561346,
        "CNY": 6.9366630474,
        "NOK": 9.2194173,
        "NZD": 1.5456930872,
        "ZAR": 14.9203764025,
        "USD": 1,
        "MXN": 18.8241042345,
        "SGD": 1.3655446978,
        "AUD": 1.4923995657,
        "ILS": 3.4464350344,
        "KRW": 1195.801664857,
        "PLN": 3.8915128484
    },
    "base": "USD",
    "date": ""
}


async def random_exchange_rates(request):
    new_rates = deepcopy(source_data)
    new_rates["date"] = datetime.now().isoformat()[:19]
    for currency, rate in source_data["rates"].items():
        # 10% variation
        size = rate * 0.1
        half = size / 2
        new_rates["rates"][currency] = rate + (random.random() * size - half)

    return web.json_response(new_rates)


def start(*args):
    app = web.Application()
    app.add_routes([
        web.get("/exchange_rates.json", random_exchange_rates)
    ])
    return app
