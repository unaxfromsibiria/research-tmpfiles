import io
import os
from datetime import date

import pandas as pd
import pytest

from infobot.storage import RateStorage
from infobot.storage import create_history_table


@pytest.fixture
def test_db(tmpdir_factory):
    db_path = tmpdir_factory.mktemp("db").join("test.csv")
    content = """created,date,currency,rates
    2020-02-24 22:52:47.299808,2020-02-21 00:00:00.000000,TTT,31.63040459216739
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,PHP,50.8795481899824
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,MXN,18.996666975280064
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,MYR,4.19350060179613
    2020-02-24 22:56:52.260889,2020-02-21 00:00:00.000000,MYR,4.19310060179613
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,NOK,9.339227849273216
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,NZD,1.5835570780483288
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,PLN,3.965836496620683
    2020-02-24 22:56:52.160889,2020-02-22 00:00:00.000000,TRY,6.122673826497547
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,RUB,64.39033422831218
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,SEK,9.785205073604295
    2020-02-24 22:56:52.160889,2020-02-22 00:00:00.000000,SGD,1.400888806591982
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,SGD,1.300888806591982
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,THB,31.63040459216739
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,KRW,1212.3414498657532
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,USD,1.0
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,RON,4.447736320711045
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,JPY,111.9896305897602
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,HRK,6.896583649662068
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,INR,71.98777890936024
    2020-02-24 22:56:52.160889,2020-02-20 00:00:00.000000,AUD,1.514952319229701
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,BGN,1.8107582631237846
    2020-02-24 22:56:52.160889,2020-02-20 00:00:00.000000,BRL,4.402370150911953
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,CAD,1.3258031663734837
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,CHF,0.9823164521803536
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,CNY,7.031293398759374
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,ISK,128.04369965743913
    2020-02-24 22:56:52.160889,2020-02-20 00:00:00.000000,CZK,23.20248125173595
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,GBP,0.7731691510045365
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,HKD,7.787890010184242
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,ZAR,15.087954818998242
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,HUF,312.100731413758
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,IDR,13765.0032404407
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,ILS,3.4242199796315154
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,DKK,6.916211461901676
    2020-02-24 22:56:52.160889,2020-02-21 00:00:00.000000,EUR,0.9258401999814831
    """
    data = pd.read_csv(io.StringIO(content))
    data.to_csv(db_path, index=False)
    return db_path


@pytest.mark.asyncio
async def test_create_storage():
    storage = RateStorage()
    assert isinstance(storage.data, pd.DataFrame)
    assert len(storage.data) == 1


@pytest.mark.asyncio
async def test_update_wrong_storage():
    """Wrong currency.
    """
    storage = RateStorage()
    result, error = await storage.update(currency="NNN")
    assert error
    assert result == 0


@pytest.mark.asyncio
async def test_update_correct_storage(tmpdir_factory):
    """Correct currency.
    """
    storage = RateStorage()
    storage.db_file_path = tmpdir_factory.mktemp("db").join("test.csv")
    result, error = await storage.update(currency="EUR")
    assert not error
    assert result > 0
    assert os.path.exists(storage.db_file_path)


@pytest.mark.asyncio
async def test_currency_list(test_db: str):
    """List of currency.
    """
    storage = RateStorage(test_db)
    assert len(storage.data) > 1
    result = await storage.currency_list()
    assert len(result) < len(storage.data)
    assert result == [
        "AUD", "BGN", "BRL", "CAD", "CHF", "CNY", "CZK", "DKK", "EUR", "GBP",
        "HKD", "HRK", "HUF", "IDR", "ILS", "INR", "ISK", "JPY", "KRW", "MXN",
        "MYR", "NOK", "NZD", "PHP", "PLN", "RON", "RUB", "SEK", "SGD", "THB",
        "TRY", "TTT", "USD", "ZAR"
    ]


@pytest.mark.asyncio
async def test_currency_dict(test_db: str):
    """Dict of currency and rates.
    """
    storage = RateStorage(test_db)
    assert len(storage.data) > 1
    result = await storage.currency_rates()
    assert len(result) < len(storage.data)
    assert set(result) == {
        "AUD", "BGN", "BRL", "CAD", "CHF", "CNY", "CZK", "DKK", "EUR", "GBP",
        "HKD", "HRK", "HUF", "IDR", "ILS", "INR", "ISK", "JPY", "KRW", "MXN",
        "MYR", "NOK", "NZD", "PHP", "PLN", "RON", "RUB", "SEK", "SGD", "THB",
        "TRY", "TTT", "USD", "ZAR"
    }
    assert int(sum(result.values())) == 15922


@pytest.mark.asyncio
async def test_currency_convert(test_db: str):
    """Check value of currency.
    """
    storage = RateStorage(test_db)
    assert len(storage.data) > 1
    result = await storage.convert(35.33, src="RUB", target="EUR")
    assert result > 0
    assert str(result) == "0.51"
    result = await storage.convert(100, src="USD", target="EUR")
    assert str(result) == "92.58"


@pytest.mark.asyncio
async def test_currency_actual(test_db: str):
    """Check value of currency is actual.
    """
    storage = RateStorage(test_db)
    assert len(storage.data) > 1
    storage.actual_interval = 1
    result = await storage.is_rate_actual("RUB")
    assert not result
    storage.actual_interval = 100 * 24 * 60 * 365
    result = await storage.is_rate_actual("USD")
    assert result


@pytest.mark.asyncio
async def test_history_table():
    """Check history table data.
    Expected:
            currency      TTT     USD
        date                     
        2020-02-03  2.190  1.1066
        2020-02-04  2.200  1.1048
        2020-02-05  2.200  1.1023
        2020-02-06  2.210  1.1003
        2020-02-07  2.220  1.0969
        2020-02-08  2.230  1.0963
        2020-02-09  2.228  1.0957
        2020-02-10  2.226  1.0951
        2020-02-11  2.224  1.0901
        2020-02-12  2.222  1.0914
        2020-02-13  2.220  1.0867
        2020-02-14  2.250  1.0842
    """

    fake_answer = {
        "rates": {
            "2020-02-14": {"USD": 1.0842, "TTT": 2.25},
            "2020-02-05": {"USD": 1.1023, "TTT": 2.20},
            "2020-02-12": {"USD": 1.0914},
            "2020-02-07": {"USD": 1.0969},
            "2020-02-03": {"USD": 1.1066, "TTT": 2.19},
            "2020-02-13": {"USD": 1.0867, "TTT": 2.22},
            "2020-02-06": {"USD": 1.1003},
            "2020-02-08": {"TTT": 2.23},
            "2020-02-11": {"USD": 1.0901},
            "2020-02-10": {"USD": 1.0951},
            "2020-02-04": {"USD": 1.1048, "TTT": 2.20}
        },
        "start_at": "2020-02-01",
        "base": "EUR",
        "end_at": "2020-02-14"
    }

    result = create_history_table(fake_answer)
    assert not result.empty
    assert result["TTT"].sum() == 26.62
    assert result["USD"].sum() - 13.15 < 0.01


@pytest.mark.asyncio
async def test_requst_history():
    """Check history data.
    """
    storage = RateStorage()
    result, err = await storage.request_history(
        begin=date(2020, 2, 1),
        end=date(2020, 2, 14),
        currency="EUR",
        target="USD"
    )
    assert not err
    assert result is not None
    assert not result.empty
