import io
import os
from datetime import date

import pandas as pd
import pytest

from infobot.storage import RateStorage
from infobot.command import CommamdHandler


@pytest.fixture
def test_storage(tmpdir_factory) -> RateStorage:
    db_path = tmpdir_factory.mktemp("db").join("test.csv")
    content = """created,date,currency,rates
    2020-02-24 22:52:47.299808,2020-02-21 00:00:00.000000,TTT,31.63040459216739
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,PPP,50.8795481899824
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,EUR,0.9258401999814831
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,USD,1.0
    """
    data = pd.read_csv(io.StringIO(content))
    data.to_csv(db_path, index=False)
    storage = RateStorage(db_path)
    return storage


@pytest.mark.asyncio
async def test_help_cmd(test_storage: RateStorage):
    handler = CommamdHandler(test_storage)
    answer, data = await handler.execute("test", "hello")
    assert data is None
    assert len(answer) == 388


@pytest.mark.asyncio
async def test_list_cmd(test_storage: RateStorage):
    test_storage.actual_interval = 100 * 24 * 60 * 365
    handler = CommamdHandler(test_storage)
    answer, data = await handler.execute("test", "/list")
    assert data is None
    assert answer == "EUR: 0.9258401999814831\nPPP: 50.879548189982394\nTTT: 31.63040459216739\nUSD: 1.0"  # noqa


@pytest.mark.asyncio
async def test_exchange_cmd(test_storage: RateStorage):
    test_storage.actual_interval = 100 * 24 * 60 * 365
    handler = CommamdHandler(test_storage)
    answer, data = await handler.execute("test", "/exchange $10 to EUR")
    assert data is None
    assert answer == "9.26"

    answer, data = await handler.execute("test", "/exchange 1 EUR to USD")
    assert data is None
    assert answer == "1.08"

    answer, data = await handler.execute("test", "/exchange 1 EUR to BBB")
    assert data is None
    assert answer == "Unknown targer currency BBB or EUR"

    answer, data = await handler.execute("test", "/exchange 1 BBB to USD")
    assert data is None
    assert answer == "Unknown targer currency USD or BBB"


@pytest.mark.asyncio
async def test_history_cmd(test_storage: RateStorage):
    test_storage.actual_interval = 100 * 24 * 60 * 365
    handler = CommamdHandler(test_storage)
    day_count = 14
    answer, data = await handler.execute(
        "test", f"/history USD/EUR for {day_count}  days"
    )
    assert data
    assert len(data) > 1000
    assert answer
    assert "values" in answer
    assert answer in (f"{day_count - 1} values", f"{day_count} values")
