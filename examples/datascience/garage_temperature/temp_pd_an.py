# run exaple:
# MPLBACKEND=Qt5Agg LOG=~/tpm/content_18.log ipython --matplotlib -m temp_pd_an

import re
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta

ONE_MIN = timedelta(minutes=1)
line_regx = re.compile(
    r"(\d{4}-\d{2}-\d{2}.+\d{2}:\d{2}:\d{2}).+\s([-]{0,1}[0-9.]+)"
)


def get_minutes_temp_data(
    path: str = "/tpm/content.log",
    from_dt: str = "2018-11-10"
) -> pd.DataFrame:
    """Smoothed temperature log per minute.
    Logfile content:
    2018-09-23 10:25:15,740 INFO - 24.310000
    2018-09-23 10:26:15,754 INFO - Stopped
    2018-09-23 10:28:52,858 INFO - 24.380000
    """
    lines = open(path).read().split("\n")
    data = set(
        m.groups()
        for m in (line_regx.match(line) for line in lines if line) if m
    )
    df_temp = pd.DataFrame({
        "temp": pd.Series(
            (float(item) for _, item in data),
            index=(pd.Timestamp(item) for item, _ in data)
        )
    })
    actual_temp = df_temp[df_temp.index > pd.Timestamp(from_dt)]
    actual_temp.sort_index(inplace=True)
    min_dt = actual_temp.index.min()
    max_dt = actual_temp.index.max()
    interval_begin, interval_end = (
        min_dt.replace(second=0) + ONE_MIN, max_dt.replace(second=0)
    )
    total_minutes = int(
        (interval_end - interval_begin).total_seconds() // 60
    ) + 1
    minute_index = [
        interval_begin + (ONE_MIN * i) for i in range(total_minutes)
    ]
    minute_index.insert(0, min_dt)
    minute_index[-1] = max_dt
    minute_result = actual_temp.reindex(minute_index, fill_value=np.nan)
    minute_result.interpolate(method="quadratic", inplace=True)
    return minute_result


def create_chart_data(
    minute_temp: pd.DataFrame,
    time_window_minutes: int = 60 * 19  # 12-24 h
) -> pd.DataFrame:
    hours_changes = (
        minute_temp.rolling(time_window_minutes).max().temp -
        minute_temp.rolling(time_window_minutes).min().temp
    )
    limit = hours_changes.median()
    mask = hours_changes > limit
    minute_temp.insert(0, "clear_temp", minute_temp.temp)
    minute_temp.clear_temp[mask] = np.nan
    minute_temp.clear_temp.interpolate(method="slinear", inplace=True)

    new_index = minute_temp.index.to_frame()
    new_index.columns = ["timeline"]
    new_index.insert(0, "day_dt", minute_temp.index.map(pd.Timestamp.date))  # noqa
    minute_temp.index = pd.MultiIndex.from_frame(new_index)
    group_data = minute_temp.copy()
    del group_data["temp"]
    group_data = group_data.groupby("day_dt")
    in_day_temp = group_data.mean()
    min_day_temp = group_data.min()
    min_day_temp.columns = ["approx_temp"]
    day_temp = minute_temp.index.get_level_values(0).map(
        in_day_temp.clear_temp
    )
    minute_temp.insert(0, "clear_day_temp", day_temp)
    minute_temp.index = minute_temp.index.droplevel(0)
    minute_temp = minute_temp.join(min_day_temp)
    minute_temp.approx_temp.interpolate(method="polynomial", order=3, inplace=True)  # noqa
    return minute_temp


log_path = os.environ.get("LOG")
params = {}
if log_path:
    params["path"] = log_path

chart_data = create_chart_data(get_minutes_temp_data(**params))

chart_data.plot(kind="line")
plt.show(block=True)
