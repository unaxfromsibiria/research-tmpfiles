import os
from collections import defaultdict
from collections.abc import Iterable
from time import monotonic

import numpy as np
import pandas as pd
from PIL import Image

try:
    from num_path_opti.num_path_dataset import find_angle_features
except ImportError as err:
    print("Not available cython implementation:", err)
    from num_path_base.num_path_dataset import find_angle_features
    from num_path_base.num_path_dataset import prepare_image
else:
    from num_path_opti.num_path_dataset import prepare_image


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
    features_count: int = 6,
    limit_group_size: int = 1000,
    show: bool = False
) -> Iterable:
    """Create image view.
    """
    start_time = monotonic()
    good_values = bad_values = 0
    for num, images_list in images(base_dir, limit_group_size).items():
        for img_path in images_list:
            try:
                img = Image.open(img_path).convert("L")
                img_m = prepare_image(img)
            except TypeError as err:
                print(f"Image format problem '{err}' in '{img_path}'")
                continue

            features = find_angle_features(
                img_m,
                show=show,
                result_size=features_count,
                with_label=num
            )

            if features is None:
                bad_values += 1
                print(f"Bad image in '{img_path}'")
            else:
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
    features_count: int = 6,
    limit_group_size: int = 1000,
    show: bool = False,
    random_sort: bool = True,
) -> pd.DataFrame:
    """Create features as DataFreame.
    """
    fields = []
    for index in range(1, features_count + 1):
        fields.append(f"center_distance{index}")
        fields.append(f"line_a{index}")
        fields.append(f"center_distance_a{index}")
        fields.append(f"line_b{index}")
        fields.append(f"center_distance_b{index}")
        fields.append(f"angle{index}")
    fields.append("number")

    data_set = pd.DataFrame(
        data=create_dataset(
            base_dir=base_dir,
            features_count=features_count,
            limit_group_size=limit_group_size,
            show=show
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

        print(f"Estimation of distribution in {field}", data_set[field].skew())

    return data_set
