import asyncio
import os
import typing
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from datetime import datetime
from decimal import Decimal
from time import monotonic

import aiohttp
import numpy as np
import pandas as pd

from .common import BASE_PATH
from .common import env_var_int
from .common import env_var_line
from .common import logger
from .img_helper import create_image

MIN_DT = pd.Timedelta("1M")


def save_new_rates(
    path: str, source: pd.DataFrame, dt: pd.Timestamp, rates: pd.Series
) -> pd.DataFrame:
    """Update data and save data actual rows.
    """
    new_data: pd.DataFrame = source.append(
        pd.DataFrame({
            "rates": rates.values,
            "currency": rates.index,
            "date": dt,
            "created": datetime.now()
        })
    )
    new_data.sort_values("created", inplace=True)
    new_data.drop_duplicates(
        ["currency", "date"], keep="last", inplace=True
    )
    new_data.index = range(len(new_data))
    try:
        new_data.to_csv(path, index=False)
    except Exception as err:
        logger.error(f"Save in '{path}' error: {err}")
        return source
    else:
        return new_data


def create_history_table(response_data: dict) -> pd.DataFrame:
    """Create table with currency for period.
    """
    rates = response_data.get("rates")
    tab = pd.DataFrame(
        (
            (dt, code, rate)
            for dt, values in rates.items() for code, rate in values.items()
        ),
        columns=["date", "currency", "rate"]
    )
    # transform for use currency as columns
    tab.date = tab.date.astype("datetime64")
    tab.sort_index(ascending=False, inplace=True)
    tab.set_index(["date", "currency"], inplace=True)
    currency_tab = tab.unstack(level="currency")
    # resample to fill gap
    data = currency_tab["rate"].resample("1D").max()
    # fill NaN by linear interpolation for nice image
    data.interpolate(method="linear", inplace=True)
    return data


class RateStorage:
    """Storage of actual data.
    """

    main_currency: str = "USD"
    db_file_path: str = ""
    actual_interval: int = 0  # in minutes
    data: pd.DataFrame
    executor: ThreadPoolExecutor
    actual_loop: asyncio.AbstractEventLoop

    service_urls: typing.Tuple[str, str] = (
        "https://api.exchangeratesapi.io/latest/",
        "https://api.exchangeratesapi.io/history/",
    )

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if self.actual_loop is None:
            self.actual_loop = asyncio.get_running_loop()

        return self.actual_loop

    def __init__(self, db_path: str = "", pool_workers: int = 0):
        """Setup from env options.
        """
        self.actual_loop = None
        if pool_workers <= 0:
            pool_workers = os.cpu_count() // 2
            if pool_workers < 2:
                pool_workers = 2

        self.executor = ThreadPoolExecutor(
            max_workers=pool_workers, thread_name_prefix="storage_"
        )
        self.db_file_path = db_file_path = (
            db_path or
            env_var_line("DB_FILE") or
            (os.path.join(BASE_PATH, "db.csv"))
        )
        self.actual_interval = env_var_int("ACTUAL_INTERVAL")  # in min
        start_time = monotonic()
        if os.path.exists(db_file_path):
            data = pd.read_csv(db_file_path)
        else:
            data = pd.DataFrame({
                "created": datetime.fromtimestamp(0),
                "date": datetime.fromtimestamp(0),
                "currency": [self.main_currency],
                "rates": [1]
            })

        data.created = data.created.astype("datetime64")
        data.date = data.date.astype("datetime64")
        exec_time = monotonic() - start_time
        logger.info(
            f"db file '{db_file_path}' size {len(data)} (loading {exec_time})"
        )
        self.data = data

    def close(self):
        """Finishing of storage usage.
        """
        self.executor.shutdown()

    async def update(
        self, currency: str, param: str = "base"
    ) -> typing.Tuple[int, str]:
        """Update rates data.
        """
        n = 0
        error = ""
        url, *_ = self.service_urls
        currency = currency or self.main_currency
        params = {param: currency}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == aiohttp.web.HTTPOk.status_code:
                        new_data = await resp.json()
                        if isinstance(new_data, dict):
                            data = pd.DataFrame(new_data)
                            if currency != self.main_currency:
                                new_retes = (
                                    data.rates / data.rates[self.main_currency]
                                )
                                new_retes[currency] = (
                                    1 / data.rates[self.main_currency]
                                )
                            else:
                                new_retes = data.rates

                            self.data = await self.loop.run_in_executor(
                                self.executor,
                                save_new_rates,
                                self.db_file_path,
                                self.data,
                                data.date.astype("datetime64").max(),
                                new_retes
                            )
                            n = len(new_retes)
                    else:
                        error = await resp.json()
                        if error:
                            logger.error(
                                f"Request {currency} error: {error}"
                            )
                        error = f"Wrong currency '{currency}'"

        except Exception as err:
            logger.critical(f"Update error: {err}")
            error = "Intrtnal error"

        return n, error

    async def request_history(
        self,
        *,
        begin: date,
        end: date,
        target: str,
        currency: str = "",
    ) -> typing.Tuple[pd.DataFrame, str]:
        """Request histiry data.
        """
        data = None
        error = ""
        _, url = self.service_urls
        if begin > end:
            begin, end = end, begin

        currency = currency or self.main_currency
        params = {
            "base": currency,
            "start_at": begin.isoformat(),
            "end_at": end.isoformat(),
            "symbols": target,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == aiohttp.web.HTTPOk.status_code:
                        new_data = await resp.json()
                        if isinstance(new_data, dict):
                            data = await self.loop.run_in_executor(
                                self.executor, create_history_table, new_data
                            )
                    else:
                        error = await resp.json()
                        if error:
                            logger.error(
                                f"Request {currency} or {target} error: {error}"  # noqa
                            )
                        error = f"Wrong currency '{currency}/{target}'"

        except Exception as err:
            logger.critical(f"Update error: {err}")
            error = "Intrtnal error"

        return data, error

    async def history_chart(
        self,
        *,
        begin: date,
        end: date,
        target: str,
        currency: str = "",
    ) -> typing.Tuple[str, bytes]:
        """
        """
        img: bytes = b""
        data, err = await self.request_history(
            begin=begin, end=end, target=target, currency=currency
        )
        if err:
            result = err
        else:
            n = len(data)
            result = f"{n} values"
            if n > 0:
                img: bytes = await self.loop.run_in_executor(
                    self.executor, create_image, data
                )

        return result, img

    async def is_rate_actual(
        self, currency: str, to_dt: datetime = None
    ) -> bool:
        """Check rate in actual.
        """
        if to_dt is None:
            to_dt = datetime.now()

        last_update = self.data[
            (self.data.currency == currency) |
            (self.data.currency == self.main_currency)
        ].created.min()

        return (to_dt - last_update) / MIN_DT <= self.actual_interval

    async def currency_list(self) -> typing.List[str]:
        """Actual list of currency.
        """
        return sorted(self.data.currency.unique())

    async def currency_rates(self) -> typing.Dict[str, float]:
        """Actual list of currency.
        """
        actual = self.data.sort_values(
            ["date", "created"]
        )[["currency", "rates"]].drop_duplicates(
            ["currency"], keep="last"
        )
        return dict(actual.itertuples(index=False))

    async def convert(
        self,
        value: typing.Union[Decimal, float, int],
        *,
        src: str,
        target: str = ""
    ) -> Decimal:
        """Convert from currence <src> to <target> currency.
        """
        target = target or self.main_currency
        # convert to main currency
        value = np.float(value)
        in_rate = self.data[self.data.currency == src].rates
        result = 0
        if target == self.main_currency and not in_rate.empty:
            in_rate, *_ = in_rate
            result = 1 / in_rate * value
        elif not in_rate.empty:
            out_rate = self.data[self.data.currency == target].rates
            if not out_rate.empty:
                in_rate, *_ = in_rate
                out_rate, *_ = out_rate
                result = 1 / in_rate * value * out_rate

        return Decimal(float(np.round(result, 2))).quantize(Decimal("0.01"))
