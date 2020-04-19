import gc
import os
import re
import io
import typing
import random
from datetime import datetime, time, timedelta

import pandas as pd
import numpy as np


dt_search = re.compile(
    r"(?P<dt>[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})"
)


def create_data(
    # src dir expected in work dir
    work_dir: str,
    out_file: str = "pulse_and_sleep.csv",
    bad_score: int = 50,
    providers: typing.List[str] = [],
    min_count_in_day: int = 288
):
    """Preparation of the single dataset CSV file with
    sleep interval and pulse measurements.
    WARNING: necessary a lot of RAM (or SWAP)
    Pulse measurements in many csv files:
    /<work dir>/src/sleep_pulse_gr<file number>.csv
    Format:
    user_1;withings;integration.api;2020-04-05T12:40:33+03:00;55.0;False;False
    user_2;withings;integration.api;2020-04-05T12:40:33+03:00;49.73;True;False
    user_3;applehealth;com.garmin.connect.mobile;2020-02-19T00:00:00+00:00;64.0;False;True
    user_3;applehealth;com.garmin.connect.mobile;2020-02-19T00:02:00+00:00;66.0;False;False
    user_3;applehealth;com.garmin.connect.mobile;2020-02-19T00:04:00+00:00;66.0;False;False

    All sleep data from file /<work dir>/src/sleep_groups.csv
    intervals in format:
    id        <user 1>  20      2020-03-08      2020-03-08 21:29:00+00  2020-03-08 23:40:00+00  0
    id        <user 2>  80      2020-02-24      2020-02-24 12:14:00+00  2020-02-24 12:26:00+00  39600
    id        <user 3> 10      2020-03-09      2020-03-08 22:38:00+00  2020-03-09 05:32:00+00  3600
    id        <user 4> 40      2020-02-17      2020-02-17 05:40:00+00  2020-02-17 13:10:00+00  -21600
    id        <user 5> 10      2020-02-26      2020-02-26 07:02:27+00  2020-02-26 17:00:04+00  -18000
    id        <user 4> 50      2020-02-19      2020-02-19 02:40:00+00  2020-02-19 14:05:00+00  -21600
    id        <user 4> 50      2020-02-20      2020-02-20 05:15:00+00  2020-02-20 13:15:00+00  -21600
    Columns: id, user id, score, day date, begin datetime, end datetime, offset
    score - is estimate of quality of current row
    """
    data = pd.read_csv(
        os.path.join(work_dir, "src", "sleep_groups.csv"),
        sep="\t",
        header=None
    )

    data.columns = ["id", "user_id", "score", "day", "begin", "end", "offset"]
    data.day = data.day.astype("datetime64")
    data.begin = data.begin.astype("datetime64")
    data.end = data.end.astype("datetime64")
    data.set_index("id", inplace=True)
    data["offset_time"] = "Sec"
    data["offset"] = (
        (data.offset.astype(str) + data.offset_time).apply(pd.Timedelta)
    )
    del data["offset_time"]
    data["begin"] = data.begin + data.offset
    data["end"] = data.end + data.offset

    mask = (
        (
            data.begin.dt.time.between(time(21, 0), time(23, 59, 59)) |
            data.begin.dt.time.between(time(0, 0), time(3, 30))
        ) &
        data.end.dt.time.between(time(4, 0), time(11, 0))
    ) | (
        data.begin.dt.time.between(time(12, 0), time(16, 0)) &
        data.end.dt.time.between(time(12, 30), time(16, 30))
    )

    good_sleep = data[mask & (data.score < bad_score)]
    actual_sleep_days = set()
    one_day = pd.Timedelta("1Day")
    for dt, user in good_sleep[["day", "user_id"]].itertuples(index=False):
        actual_sleep_days.add((dt - one_day, user))
        actual_sleep_days.add((dt + one_day, user))
        actual_sleep_days.add((dt, user))

    path_data = []
    path = os.path.join(work_dir, "src")
    for root, _, files in os.walk(path, topdown=False):
        for file_path in files:
            *_, ext = os.path.splitext(file_path)
            ext = ext.replace(".", "").lower()
            if "sleep_pulse" in file_path and "csv" == ext:
                path_data.append(os.path.join(root, file_path))

    actual_pulse: pd.DataFrame = None
    used_providers = {provider: True for provider in providers}

    for csv_path in path_data:
        pulse_part: pd.DataFrame = pd.read_csv(csv_path, sep=";", header=None)
        pulse_part.columns = [
            "user", "provider", "src", "dt", "value", "sdnn", "resting"
        ]
        pulse_part = pulse_part[~pulse_part.sdnn]
        pulse_part.provider = pulse_part.provider.astype("category")
        if used_providers:
            mask = pulse_part.provider.apply(used_providers.get)
            mask.fillna(False, inplace=True)
            pulse_part = pulse_part[mask]
            print(
                f"Provider filtered rows in {csv_path}:",
                len(mask) - mask.sum()
            )

        pulse_part.src = pulse_part.src.astype("category")
        pulse_part.dt = pulse_part.dt.str.extract(
            dt_search
        ).dt.astype("datetime64")

        pulse_part.insert(1, "day", pulse_part.dt.dt.date.astype("datetime64"))
        pulse_part.insert(1, "with_sleep", [
            (dt, user) in actual_sleep_days
            for dt, user in pulse_part[["day", "user"]].itertuples(index=False)
        ])

        pulse_part = pulse_part[pulse_part.with_sleep]
        if pulse_part.empty:
            continue

        day_pulse_count = pulse_part[
            ["day", "user", "value"]
        ].groupby(
            ["day", "user"]
        ).count()

        good_days = set(
            day_pulse_count[
                day_pulse_count.value >= min_count_in_day
            ].index
        )

        pulse_part.insert(1, "enough", [
            (dt, user) in good_days
            for dt, user in pulse_part[["day", "user"]].itertuples(index=False)
        ])
        good_days.clear()
        pulse_part = pulse_part[pulse_part.enough]
        if pulse_part.empty:
            continue

        del pulse_part["enough"]
        del pulse_part["with_sleep"]
        del pulse_part["sdnn"]

        if actual_pulse is None:
            actual_pulse = pulse_part.copy()
        else:
            actual_pulse = actual_pulse.append(pulse_part)

        del pulse_part

    actual_pulse.insert(3, "is_end", 0)
    actual_pulse.insert(3, "is_begin", 0)
    del actual_pulse["src"]

    columns = [
        "user",
        "dt",
        "day",
        "resting",
        "provider",
        "is_end",
        "is_begin"
    ]

    sleep_labels = pd.DataFrame(
        (
            (user, dt, day, False, "unknown", 1, 0)
            for user, dt, day in good_sleep[
                ["user_id", "end", "day"]
            ].itertuples(index=False)
        ),
        columns=columns
    )

    sleep_labels = sleep_labels.append(
        pd.DataFrame(
            (
                (user, dt, day, False, "unknown", 0, 1)
                for user, dt, day in good_sleep[
                    ["user_id", "begin", "day"]
                ].itertuples(index=False)
            ),
            columns=columns
        )
    )

    del data
    del good_sleep

    gc.collect()

    data = actual_pulse.append(sleep_labels)
    data.provider = data.provider.astype("category")
    gc.collect()
    print(data.info())
    data.sort_values(["user", "dt"], inplace=True)
    data.to_csv(os.path.join(work_dir, out_file), index=None)


def open_days(file_path: str, sep: str = ",") -> typing.Iterable[pd.DataFrame]:
    """Open big CSV file structure with ordering by users:
    user,day,provider,is_begin,is_end,dt,value,resting
    user 1,2020-01-28 00:00:00,unknown,1,0,2020-01-28 01:19:09,,False
    user 1,2020-01-28 00:00:00,unknown,0,1,2020-01-28 09:12:12,,False
    ....
    user 2,2020-01-04 00:00:00,unknown,1,0,2020-01-04 01:35:57,,False
    user 2,2020-01-04 00:00:00,unknown,0,1,2020-01-04 10:09:49,,False
    """
    users_data: io.StringIO = None
    head_line: str = ""
    current_user: int = 0
    index: int = 0

    with open(file_path) as csv_file:
        for line in csv_file:
            user, _, *_ = line.split(sep, 3)
            try:
                user = int(user)
            except (ValueError, TypeError):
                head_line = line
                continue

            if current_user != user:
                if current_user > 0:
                    users_data.seek(0)
                    data: pd.DataFrame = pd.read_csv(users_data)
                    data.dt = data.dt.astype("datetime64")
                    data.day = data.day.astype("datetime64")
                    if (data.value > 0).sum() > 0:
                        yield data
                        index = 0

                current_user = user
                users_data = io.StringIO()
                users_data.write(head_line)

            users_data.write("\n")
            users_data.write(line)
            index += 1
            if index % 10000 == 0:
                print(f"for user {current_user} lines: +{index}")


def create_rows_const(
    file_path: str,
    sep: str = ",",
    max_resting_bpm: int = 67,
    fullness_rate: float = 0.89,
    time_quantile: int = 5,  # min
) -> typing.Iterable[typing.Tuple[np.array, np.array]]:
    """Deprecated.
    """
    count_in_day: int = int((24 * 3600) / (60 * time_quantile))
    day_half = pd.Timedelta("12H")
    dt_quant = pd.Timedelta(f"{time_quantile}Min")
    records = open_days(file_path, sep)
    emp_row = {"value": None, "is_begin": 0, "is_end": 0}
    for user_df in records:
        resting: float = 0
        if len(user_df[user_df.resting]) > 0:
            resting = user_df[user_df.resting].value.mean()
        else:
            resting = user_df[(user_df.value < max_resting_bpm)].value.mean()

        user_df = user_df[["dt", "day", "value", "is_begin", "is_end"]]
        for day in pd.unique(user_df.day):
            begin = day - day_half
            end = day + day_half
            day_df = user_df[user_df.dt.between(begin, end)]
            day_df = day_df.append([
                {"dt": begin + dt_quant, "day": day, **emp_row},
                {"dt": end, "day": day, **emp_row},
            ])
            day_df.sort_values("dt", inplace=True)
            interval_count = (
                day_df.is_begin.sum() + day_df.is_end.sum()
            ) / 2
            if interval_count < 1 or len(day_df) < count_in_day:
                continue

            day_df.loc[:, "value"] = day_df.value.fillna(
                method="ffill"
            ) / resting
            day_df.set_index("dt", inplace=True)
            row_data = day_df.resample(dt_quant).mean()
            sum_nan = row_data.value.isna().sum()
            if fullness_rate > (1 - (sum_nan / count_in_day)):
                continue

            if sum_nan > 0:
                row_data.value.interpolate(method="linear", inplace=True)
                row_data.value.interpolate(method="ffill", inplace=True)
                row_data.value.interpolate(method="bfill", inplace=True)

            row_data.is_begin.fillna(0, inplace=True)
            row_data.is_end.fillna(0, inplace=True)

            indexes = []
            intervals = np.zeros((count_in_day,))
            rows = row_data[["is_begin", "is_end"]].itertuples(index=False)
            for index, (is_begin, is_end) in enumerate(rows):
                if is_begin > 0:
                    indexes.append((index, True))
                if is_end > 0:
                    indexes.append((index, False))

            indexes.sort()
            prev_index = 0
            for i, (index, is_begin) in enumerate(indexes):
                if is_begin:
                    prev_index = index
                else:
                    intervals[prev_index:index] = 1

                if i == len(indexes) - 1 and is_begin:
                    intervals[index:] = 1

            yield (row_data.value.values, intervals)


def create_rows_shifted(
    file_path: str,
    sep: str = ",",
    max_resting_bpm: int = 68,
    time_quantile: int = 5,  # min
    expected_in_quant: float = 1.5,
    fullness_rate: float = 0.89,
    median_limit_ratio: float = 1.7
) -> typing.Iterable[typing.Tuple[np.array, np.array]]:
    """Actual method to crate dataset.
    Create random intervals with suitable sleep
    time and pulse stream with good fullness.
    How to use:
    gen = create_rows_shifted(
        csv_file_path,
        # 0.85 - 85% and 15% will be interpolated
        fullness_rate=0.85,
        # resample to time quantil all measurements
        time_quantile=6,
        # 2 pulse measurement in time quant (6 min)
        expected_in_quant=2,
        # expected that measurements median in sleep interval less than
        # individual resting heart rate * the ratio
        # median(bpm) < median_limit_ratio * long_time_resting_pulse
        median_limit_ratio=1.7
    )
    with open("/<dir>/dataset_6min_sleep_and_pulse.json", "w") as of:
        import json
        import random
        data = sorted(
            ([list(pulse), list(sleep)] for pulse, sleep in gen),
            key=lambda _: random.random()
        )
        of.write(json.dumps(data))
    """

    count_in_day: int = int((24 * 3600) / (60 * time_quantile))
    day_half = pd.Timedelta("12H")
    dt_quant = pd.Timedelta(f"{time_quantile}Min")
    records = open_days(file_path, sep)
    emp_row = {"value": None, "is_begin": 0, "is_end": 0}
    count = 0
    for user_df in records:
        resting: float = 0
        if len(user_df[user_df.resting]) > 0:
            resting = user_df[user_df.resting].value.mean()
        else:
            resting = user_df[(user_df.value < max_resting_bpm)].value.mean()

        user_df = user_df[["dt", "day", "value", "is_begin", "is_end"]]
        for sleep_end in map(pd.Timestamp, user_df.dt[user_df.is_end > 0].unique()):  # noqa
            day = pd.Timestamp(sleep_end.date())
            sec_delta = random.randint(5400, 23400)
            t_delta = pd.Timedelta(f"{sec_delta}Sec")
            mid = random.choice((sleep_end - t_delta, sleep_end + t_delta))

            begin = mid - day_half
            end = mid + day_half
            day_df = user_df[user_df.dt.between(begin, end)]
            day_df = day_df.append([
                {"dt": begin + dt_quant, "day": day, **emp_row},
                {"dt": end, "day": day, **emp_row},
            ])
            day_df.sort_values("dt", inplace=True)
            interval_label_count = (
                (day_df.is_begin > 0).sum() + (day_df.is_end > 0).sum()
            )
            if interval_label_count < 1:
                continue

            value_count = (day_df.value > 0).sum()
            if value_count < count_in_day * expected_in_quant:
                print(f"Not enough values {value_count}")
                continue

            day_df.loc[:, "value"] = day_df.value.fillna(
                method="ffill"
            ) / resting
            day_df.set_index("dt", inplace=True)
            row_data = day_df.resample(dt_quant).mean()
            row_data.is_begin = day_df.is_begin.resample(dt_quant).max()
            row_data.is_end = day_df.is_end.resample(dt_quant).max()

            sum_nan = row_data.value.isna().sum()
            if fullness_rate > (1 - (sum_nan / count_in_day)):
                continue

            if sum_nan > 0:
                row_data.value.interpolate(method="linear", inplace=True)
                row_data.value.interpolate(method="ffill", inplace=True)
                row_data.value.interpolate(method="bfill", inplace=True)

            row_data.is_begin.fillna(0, inplace=True)
            row_data.is_end.fillna(0, inplace=True)

            indexes = []
            intervals = np.zeros((count_in_day,))
            rows = row_data[["is_begin", "is_end"]].itertuples(index=False)
            for index, (is_begin, is_end) in enumerate(rows):
                if is_begin > 0:
                    indexes.append((index, True))
                if is_end > 0:
                    indexes.append((index, False))

            indexes.sort()
            prev_index = 0
            for i, (index, is_begin) in enumerate(indexes):
                if is_begin:
                    prev_index = index
                else:
                    intervals[prev_index:index] = 1

                if i == len(indexes) - 1 and is_begin:
                    intervals[index:] = 1

            assert (row_data.value <= 0).sum() == 0

            stream = row_data.value.values[:count_in_day]
            in_sleep_stream = stream[intervals > 0]
            # exclude sleep with high pulse
            max_limit_value = np.median(in_sleep_stream) * median_limit_ratio
            if (in_sleep_stream > max_limit_value).sum() == 0:
                yield (row_data.value.values, intervals)
                count += 1

    print("Rows count:", count)
