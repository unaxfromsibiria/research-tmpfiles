import os
from collections import defaultdict
from collections.abc import Iterable
from time import monotonic

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from keras import Sequential
from keras.layers import Dense
from PIL import Image

from .common import SPACE_VOLUME, prepare_image


def _sort_fields(field: str) -> int:
    _, num = field.split("p")
    return int(num)


def create_model(
    data_set: pd.DataFrame, sample: float = 0.86, random_state=10
) -> (Sequential, np.array, np.array):
    """Model-classificator.
    """
    train = data_set.sample(frac=sample, random_state=random_state)
    test = data_set.drop(train.index)
    y_test = test.number.astype("int")
    y_train = train.number.astype("int")

    fields = []
    for field in set(data_set.columns.values):
        if "number" in field:
            continue
        if "Unnamed" in field:
            continue

        fields.append(field)

    fields.sort(key=_sort_fields)

    print("using fields:", fields)
    x_train = train[fields]
    x_test = test[fields]

    model = Sequential([
        Dense(256, activation="relu"),
        Dense(128, activation="relu"),
        Dense(10, activation="softmax")
    ])

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )
    model.fit(x_train.values, y_train.values, epochs=16)
    return model, x_test.values, y_test.values


def numbers_data_files(base_dir: str) -> Iterable:
    """Images and numbers.
    """
    for root, dirs, files in os.walk(base_dir, topdown=False):
        for img_name in files:
            if ".png" not in img_name:
                continue

            try:
                num = int(root.split("/")[-1])
            except (ValueError, IndexError, TypeError):
                continue
            else:
                if 0 <= num <= 9:
                    yield (num, os.path.join(root, img_name))

        for sub_dir in dirs:
            yield from numbers_data_files(sub_dir)


def images(
    base_dir: str = "numbers",
    limit_group_size: int = 100
) -> dict:
    """
    """
    result = defaultdict(list)
    limits = defaultdict(int)
    count = 0
    for num, file_path in numbers_data_files(base_dir):
        if limits[num] >= limit_group_size:
            continue

        result[num].append(file_path)
        limits[num] += 1
        count += 1

    return result


def create_dataset(
    base_dir: str = "numbers",
    limit_group_size: int = 1000,
    show: bool = False,
    only: list = []
) -> Iterable:
    """Create image view.
    """
    start_time = monotonic()
    good_values = bad_values = 0
    for num, images_list in images(base_dir, limit_group_size).items():
        if only and num not in only:
            continue

        for img_path in images_list:
            try:
                img = Image.open(img_path).convert("L")
                img_m = prepare_image(img)
            except (TypeError, ValueError) as err:
                print(f"Image format problem '{err}' in '{img_path}'")
                continue

            if show:
                plt.imshow(img_m, interpolation="nearest", cmap="gray")
                plt.title(f"num: {num}")
                plt.show(block=True)

            features = np.append(img_m.ravel(), float(num))
            good_values += 1
            yield features

    exec_time = monotonic() - start_time
    exec_min = exec_time // 60
    exec_sec = round(exec_time - exec_min * 60)
    print(
        "Good:", good_values,
        "Bad:", bad_values,
        "exec time", f"{exec_min} min {exec_sec} sec",
        "time per image", round(exec_time / (good_values + bad_values), 3)
    )


def create_df(
    base_dir: str = "numbers",
    limit_group_size: int = 1000,
    show: bool = False,
    random_sort: bool = True,
    only: list = []
) -> pd.DataFrame:
    """Create features as DataFreame.
    """
    fields = [f"p{i + 1}" for i in range(SPACE_VOLUME)]
    fields.append("number")

    data_set = pd.DataFrame(
        data=create_dataset(
            base_dir=base_dir,
            limit_group_size=limit_group_size,
            show=show,
            only=only
        ),
        columns=fields
    )
    if random_sort:
        data_set.insert(0, "rand", np.random.random(len(data_set)))
        data_set.sort_values(by="rand", inplace=True)
        del data_set["rand"]

    for field in fields:
        if field == "number":
            continue
        under_zero_error = (data_set[field] < 0).sum()
        print(
            f"Estimation of distribution in {field} (skew)",
            data_set[field].skew(),
            f"in {field} under zero values: {under_zero_error}"
        )

    return data_set
