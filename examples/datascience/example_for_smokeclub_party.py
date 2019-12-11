import numpy as np
import pandas as pd
import io
import random
import itertools
import math


# # examlpe 1 # #

def directions_py(point: tuple, with_points: list) -> list:
    """Only python.
    """
    result = []
    for with_point in with_points:
        s = 0
        for i, with_location in enumerate(with_point):
            location = point[i]
            s += math.pow(with_location - location, 2)

        result.append(round(math.sqrt(s), 2))

    return result


def directions_np(size: int, point: tuple, with_points: list) -> list:
    """Cache as distance matrix in space of a given size.
    """
    dimension = len(point)
    line = np.arange(size)
    indexes = np.meshgrid(
        *(line for _ in range(dimension)), sparse=True, indexing="ij"
    )
    distances = np.round(np.sqrt(
        np.sum(
            np.power(indexes[i] - loc, 2) for i, loc in enumerate(point)
        )
    ), 2)
    return [distances[p] for p in with_points]


def directions_py_cached(size: int, point: tuple, with_points: list) -> list:
    """Only python cache as distance dict in space of a given size
    """
    cache = {}
    dimension = len(point)
    for idx in itertools.product(*(range(size) for _ in range(dimension))):
        s = 0
        for i, with_location in enumerate(point):
            location = idx[i]
            s += math.pow(with_location - location, 2)

        cache[idx] = round(math.sqrt(s), 2)

    return list(map(cache.get, with_points))


point = (3, 7, 12, 19)
size = 32
print(32 ** 4)  # >> 1048576
points = [(0, 0, 0, 0), (0, 1, 0, 1), (1, 0, 1, 0), (3, 8, 12, 19)]

directions_np(size, point, points)  # >> [23.73, 22.65, 23.13, 1.0]
directions_py(point, points)  # >> [23.73, 22.65, 23.13, 1.0]
points = [
    tuple(random.randint(0, size - 1) for _ in range(4))
    for _ in range(20000)
]

# %timeit directions_py(point, points)

# %timeit directions_np(size, point, points)

# %timeit directions_py_cached(size, point, points)


# # example 2 # #
# Search for the worst sensor.

data = """
sensor 01,2019-12-08 12:00:00,-2.5
sensor 02,2019-12-08 12:32:00,-2.6
sensor_01,2019-12-08 12:30:30,-2.55
sensor 02,2019-12-08 12:40:00,-3.0
sensor 01,2019-12-08 12:45:00,-2.9
sensor_04,2019-12-08 12:20:00,-2.6
sensor 03,2019-12-08 12:25:30,-3.0
sensor 04,2019-12-08 12:48:00,-3.5
sensor_01,2019-12-08 12:50:00,-3.48
sensor 02,2019-12-08 12:49:00,-3.55
sensor 01,2019-12-08 12:59:50,-3.9
sensor 04,2019-12-08 13:02:00,-4.1
sensor 03,2019-12-08 13:01:00,-3.8
sensor 02,2019-12-08 13:05:40,-4.1
sensor 01,2019-12-08 13:20:00,-4.3
sensor 02,2019-12-08 13:10:00,-4.0
sensor 03,2019-12-08 13:15:00,-3.8
sensor_01,2019-12-08 13:30:00,-4.3
sensor_02,2019-12-08 13:40:00,-4.4
sensor 01,2019-12-08 13:40:00,-4.3
sensor 04,2019-12-08 13:38:00,-4.5
sensor 03,2019-12-08 13:30:00,-4.1
sensor 02,2019-12-08 14:00:00,-4.3
sensor_01,2019-12-08 14:03:00,-4.2
sensor 03,2019-12-08 14:10:00,-4.5
sensor_01,2019-12-08 14:05:00,-4.2
sensor 02,2019-12-08 14:04:00,-4.1
sensor 03,2019-12-08 14:15:00,-4.4
sensor 02,2019-12-08 14:16:00,-4.05
sensor 04,2019-12-08 14:15:30,-4.1
"""

tab = pd.read_csv(io.StringIO(data))
tab.columns = ["sensor", "dt", "temp"]
tab.dt = tab.dt.astype("datetime64")
tab.sort_index(ascending=False, inplace=True)
tab.sensor = tab.sensor.str.replace(" ", "_")
tab.set_index(["dt", "sensor"], inplace=True)
sensor_tab = tab.unstack(level="sensor")
sensor_temp = sensor_tab["temp"]

sensor_temp.interpolate(method="linear", inplace=True)
sensor_temp.sort_index(ascending=False, inplace=True)
sensor_temp.interpolate(method="linear", inplace=True)
sensor_temp.sort_index(inplace=True)

fields = sorted(sensor_temp.columns, reverse=True)
index = len(fields)
d_fields = []
for field in fields:
    other_fields = [
        in_field for in_field in fields if field != in_field
    ]
    st_d = sensor_temp[other_fields].std(axis=1)
    new_field = f"d_{field}"
    d_fields.append(new_field)
    sensor_temp.insert(index, new_field, st_d)

print(sensor_temp[d_fields].mean())
# The minimal dispersion is expected in column without worst sensor.
# sensor
# d_sensor_04    0.166708
# d_sensor_03    0.110524 <<< Sensor 03 is most inaccurate.
# d_sensor_02    0.177540
# d_sensor_01    0.158499
# dtype: float64
