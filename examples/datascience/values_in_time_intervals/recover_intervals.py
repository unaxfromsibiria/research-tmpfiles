# # pip install pytest-cov pytest-sugar
# MPLBACKEND=Qt5Agg py.test ./recover_intervals.py
from collections.abc import Iterable
from datetime import datetime, timedelta
from itertools import chain

import pytest
import numpy as np
import pandas as pd


def create_intervals(data: str) -> Iterable:
    """Create from data.
    """
    for line in data.split("\n"):
        if not line:
            continue
        try:
            begin, end, value = line.split("|")
            begin = pd.Timestamp(begin.strip()[:19])
            end = pd.Timestamp(end.strip()[:19])
            value = float(value.strip())
        except Exception:
            continue
        else:
            yield (begin.to_pydatetime(), end.to_pydatetime(), value)


@pytest.fixture
def test_data_1() -> list:
    """Correct intervals.
    """
    return list(create_intervals(
        """
        2018-03-17 10:16:50+00 | 2018-03-17 11:16:49+00 |    600
        2018-03-17 11:20:36+00 | 2018-03-17 12:00:59+00 |    800
        2018-03-17 12:40:39+00 | 2018-03-17 12:55:00+00 |    400
        2018-03-17 12:55:00+00 | 2018-03-17 13:05:00+00 |    43
        2018-03-17 13:05:00+00 | 2018-03-17 13:10:00+00 |    189
        """
    ))


@pytest.fixture
def test_data_2() -> list:
    """With long useless interval.
    """
    return list(create_intervals(
        """
        2018-03-17 07:47:27+00 | 2018-03-17 12:40:39+00 |     60
        2018-03-17 10:16:50+00 | 2018-03-17 11:26:49+00 |    600
        2018-03-17 11:20:36+00 | 2018-03-17 12:00:59+00 |    800
        2018-03-17 12:40:39+00 | 2018-03-17 12:55:00+00 |    400
        2018-03-17 12:45:00+00 | 2018-03-17 13:05:00+00 |    43
        2018-03-17 12:55:00+00 | 2018-03-17 13:10:00+00 |    189
        """
    ))


@pytest.fixture
def test_data_3() -> list:
    """
    """
    return list(create_intervals(
        """
        2018-03-17 02:47:27+00 | 2018-03-17 02:53:39+00 |     6
        2018-03-17 11:16:50+00 | 2018-03-17 11:26:49+00 |    36
        2018-03-17 11:54:36+00 | 2018-03-17 12:00:59+00 |     4
        2018-03-17 12:09:28+00 | 2018-03-17 12:19:27+00 |    18
        2018-03-17 12:19:27+00 | 2018-03-17 12:28:44+00 |   222
        2018-03-17 12:28:44+00 | 2018-03-17 12:38:30+00 |    36
        2018-03-17 12:58:27+00 | 2018-03-17 13:08:27+00 |    43
        2018-03-17 13:08:27+00 | 2018-03-17 13:20:02+00 |    47
        2018-03-17 13:17:02+00 | 2018-03-17 13:31:14+00 |    71
        2018-03-17 13:26:14+00 | 2018-03-17 13:35:48+00 |    49
        2018-03-17 13:35:48+00 | 2018-03-17 13:45:42+00 |    13
        2018-03-17 13:45:42+00 | 2018-03-17 13:55:40+00 |    54
        2018-03-17 13:55:40+00 | 2018-03-17 14:05:39+00 |    54
        2018-03-17 14:05:39+00 | 2018-03-17 14:15:26+00 |   194
        2018-03-17 14:15:26+00 | 2018-03-17 14:20:45+00 |     9
        2018-03-17 14:27:40+00 | 2018-03-17 14:31:57+00 |    11
        2018-03-17 14:41:22+00 | 2018-03-17 14:51:22+00 |    96
        2018-03-17 16:23:27+00 | 2018-03-17 16:33:27+00 |    52
        2018-03-17 16:33:27+00 | 2018-03-17 16:43:26+00 |    67
        2018-03-17 16:43:26+00 | 2018-03-17 16:52:49+00 |    53
        2018-03-17 17:02:48+00 | 2018-03-17 17:12:47+00 |   148
        2018-03-17 17:12:47+00 | 2018-03-17 17:25:46+00 |    94
        2018-03-17 17:22:46+00 | 2018-03-17 17:28:53+00 |   165
        2018-03-17 17:49:44+00 | 2018-03-17 17:59:43+00 |    32
        2018-03-17 17:59:43+00 | 2018-03-17 18:09:14+00 |    47
        2018-03-17 18:09:14+00 | 2018-03-17 18:19:13+00 |    32
        2018-03-17 18:19:13+00 | 2018-03-17 18:29:12+00 |   125
        2018-03-17 18:29:12+00 | 2018-03-17 18:35:24+00 |    99
        2018-03-17 18:44:29+00 | 2018-03-17 18:57:30+00 |    65
        2018-03-17 19:16:41+00 | 2018-03-17 19:25:52+00 |    53
        2018-03-17 19:25:52+00 | 2018-03-17 19:35:51+00 |    51
        2018-03-17 19:35:51+00 | 2018-03-17 19:45:15+00 |   144
        2018-03-17 19:54:58+00 | 2018-03-17 20:02:55+00 |    30
        2018-03-17 22:13:04+00 | 2018-03-17 22:20:39+00 |    61
        2018-03-17 22:41:40+00 | 2018-03-17 22:52:28+00 |    25
        2018-03-17 23:24:39+00 | 2018-03-17 23:31:07+00 |    10
        """
    ))


def second_values(data: Iterable) -> Iterable:
    """Records as (
        (begin, end, value), ...
    )
    """

    for index, (dt_begin, dt_end, value) in enumerate(data):
        begin = np.round(dt_begin.timestamp())
        end = np.round(dt_end.timestamp())
        duration = int(end - begin)
        rate = np.round(value / duration, 3)
        for val_index in range(duration):
            yield (rate, int(begin + val_index), index)


def create_index(data: pd.DataFrame) -> Iterable:
    max_index = int(data.index.max())
    new_index = set(map(float, range(max_index)))
    new_index.update(data.index)
    return sorted(new_index)


def recover_clear_intervals(
    records: list,
    period_min_window: int = 60,
    filter_limit: int = 40,  # 40%
    true_min_rate_limit: float = 0
) -> list:
    """Recover correct sequence without crossing.
    """
    result = []
    rate_data = pd.DataFrame(
        second_values(records), columns=["rate", "seconds", "interval"]
    )
    rate_data.sort_values("seconds", inplace=True)
    rate_data.set_index(["seconds"], inplace=True)
    cross_data = rate_data.interval.groupby("seconds").count()
    cross_seconds = cross_data[cross_data > 1].index
    bad_intervals = rate_data.interval.loc[cross_seconds].unique()
    bad_intervals = {
        index: True
        for index in chain(
            bad_intervals, bad_intervals + 1, bad_intervals - 1
        )
    }

    if len(bad_intervals):
        shift_rate = rate_data.rate.rolling(period_min_window).mean().dropna()
        limit = shift_rate.quantile(filter_limit / 100.0)
        limit = min(
            true_min_rate_limit if true_min_rate_limit else limit, limit
        )
        rate_data = rate_data[
            rate_data.interval.apply(bad_intervals.get).fillna(False)
        ].rate
        rate_data = rate_data.loc[rate_data > limit].groupby(
            "seconds"
        ).mean()

        rate_data = pd.DataFrame(
            {"seconds": rate_data.index}, index=rate_data.values
        )
        rate_data.index.name = "rate"
        rate_intevals = rate_data.groupby("rate").agg([np.min, np.max])
        rate_intevals.columns = ["begin", "end"]
        for rate in rate_intevals.index:
            dt_begin, dt_end = rate_intevals.loc[rate]
            duration = dt_end - dt_begin
            result.append((
                datetime.fromtimestamp(dt_begin),
                datetime.fromtimestamp(dt_end),
                np.round(duration * rate),
            ))

    for index, (begin, end, val) in enumerate(records):
        if index in bad_intervals:
            continue

        result.append((begin, end, val))

    result.sort()
    return result


def test_intervals_creation_1(test_data_1):
    rate_data = recover_clear_intervals(test_data_1)
    assert rate_data
    result = [
        "{}; {}; {}".format(*row) for row in rate_data
    ]
    assert result == [
        "2018-03-17 10:16:50; 2018-03-17 11:16:49; 600.0",
        "2018-03-17 11:20:36; 2018-03-17 12:00:59; 800.0",
        "2018-03-17 12:40:39; 2018-03-17 12:55:00; 400.0",
        "2018-03-17 12:55:00; 2018-03-17 13:05:00; 43.0",
        "2018-03-17 13:05:00; 2018-03-17 13:10:00; 189.0",
    ]


def test_intervals_creation_2(test_data_2):
    rate_data = recover_clear_intervals(test_data_2)
    assert rate_data
    result = [
        "{}; {}; {}".format(*row) for row in rate_data
    ]
    assert result == [
        "2018-03-17 10:16:50; 2018-03-17 11:20:35; 547.0",
        "2018-03-17 11:20:36; 2018-03-17 11:26:48; 88.0",
        "2018-03-17 11:26:49; 2018-03-17 12:00:58; 676.0",
        "2018-03-17 12:40:39; 2018-03-17 12:44:59; 121.0",
        "2018-03-17 12:45:00; 2018-03-17 12:54:59; 150.0",
        "2018-03-17 12:55:00; 2018-03-17 13:04:59; 74.0",
        "2018-03-17 13:05:00; 2018-03-17 13:09:59; 63.0",
    ]


def test_intervals_creation_3(test_data_3):
    rate_data = recover_clear_intervals(test_data_3)
    assert rate_data
    result = [
        "{}; {}; {}".format(*row) for row in rate_data
    ]
    assert result == [
        "2018-03-17 02:47:27; 2018-03-17 02:53:39; 6.0",
        "2018-03-17 11:16:50; 2018-03-17 11:26:49; 36.0",
        "2018-03-17 11:54:36; 2018-03-17 12:00:59; 4.0",
        "2018-03-17 12:09:28; 2018-03-17 12:19:27; 18.0",
        "2018-03-17 12:19:27; 2018-03-17 12:28:44; 222.0",
        "2018-03-17 12:28:44; 2018-03-17 12:38:30; 36.0",
        "2018-03-17 13:17:02; 2018-03-17 13:26:13; 46.0",
        "2018-03-17 13:26:14; 2018-03-17 13:31:13; 25.0",
        "2018-03-17 13:31:14; 2018-03-17 13:35:47; 23.0",
        "2018-03-17 13:45:42; 2018-03-17 13:55:40; 54.0",
        "2018-03-17 13:55:40; 2018-03-17 14:05:39; 54.0",
        "2018-03-17 14:05:39; 2018-03-17 14:15:26; 194.0",
        "2018-03-17 14:15:26; 2018-03-17 14:20:45; 9.0",
        "2018-03-17 14:27:40; 2018-03-17 14:31:57; 11.0",
        "2018-03-17 14:41:22; 2018-03-17 14:51:22; 96.0",
        "2018-03-17 16:23:27; 2018-03-17 16:33:27; 52.0",
        "2018-03-17 16:33:27; 2018-03-17 16:43:26; 67.0",
        "2018-03-17 16:43:26; 2018-03-17 16:52:49; 53.0",
        "2018-03-17 17:02:48; 2018-03-17 17:12:46; 148.0",
        "2018-03-17 17:12:47; 2018-03-17 17:22:45; 72.0",
        "2018-03-17 17:22:46; 2018-03-17 17:25:45; 51.0",
        "2018-03-17 17:25:46; 2018-03-17 17:28:52; 84.0",
        "2018-03-17 17:59:43; 2018-03-17 18:09:14; 47.0",
        "2018-03-17 18:09:14; 2018-03-17 18:19:13; 32.0",
        "2018-03-17 18:19:13; 2018-03-17 18:29:12; 125.0",
        "2018-03-17 18:29:12; 2018-03-17 18:35:24; 99.0",
        "2018-03-17 18:44:29; 2018-03-17 18:57:30; 65.0",
        "2018-03-17 19:16:41; 2018-03-17 19:25:52; 53.0",
        "2018-03-17 19:25:52; 2018-03-17 19:35:51; 51.0",
        "2018-03-17 19:35:51; 2018-03-17 19:45:15; 144.0",
        "2018-03-17 19:54:58; 2018-03-17 20:02:55; 30.0",
        "2018-03-17 22:13:04; 2018-03-17 22:20:39; 61.0",
        "2018-03-17 22:41:40; 2018-03-17 22:52:28; 25.0",
        "2018-03-17 23:24:39; 2018-03-17 23:31:07; 10.0",
    ]
