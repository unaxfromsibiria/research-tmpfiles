import os
from collections import defaultdict
from collections.abc import Iterable
from time import monotonic

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

from num_tpl_base.image_tpl import create_templates
from num_tpl_base.image_tpl import base_tpl_points
from num_tpl_base.image_tpl import prepare_image
from num_tpl_base.image_tpl import templates_scores


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
    show: bool = True,
    tpl_points: dict = base_tpl_points
) -> Iterable:
    """Create image view.
    """
    start_time = monotonic()
    good_values = bad_values = 0
    only = sorted(tpl_points.keys())

    # new templates
    tpls, fearure_size = create_templates(show, tpl_points)
    i = 0

    for num, images_list in images(base_dir, limit_group_size).items():
        if only and num not in only:
            continue

        for img_path in images_list:
            try:
                img = Image.open(img_path).convert("L")
                img_m, volume = prepare_image(img)
            except TypeError as err:
                print(f"Image format problem '{err}' in '{img_path}'")
                bad_values += 1
                continue
            else:
                if show:
                    plt.imshow(img_m, interpolation="nearest", cmap="gray")
                    plt.title(
                        f"{img_m.shape} - {volume}"
                    )
                    plt.show(block=True)

            features = np.zeros((fearure_size + 1, ))
            features[fearure_size] = num
            i = 0
            for tpl_num, tpl in tpls:
                num_fearure = templates_scores(img_m, tpl)
                for val in num_fearure:
                    features[i] = val
                    i += 1
                if show:
                    print(f"{tpl_num}>{num_fearure}")

            assert fearure_size == i

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
    only: list = [],
    tpl_points: dict = base_tpl_points
) -> pd.DataFrame:
    """Create features as DataFreame.
    """
    actual_tpl_points = {}
    tpl_fields = []
    for num, points_tpl in tpl_points.items():
        if only and num not in only:
            continue

        actual_tpl_points[num] = points_tpl
        tpl_fields.append((num, len(points_tpl)))

    tpl_fields.sort()
    fields = []
    for num, point_count in tpl_fields:
        for index in range(point_count):
            for f_index in range(5):
                fields.append(f"feature_{num}_{index + 1}_{f_index + 1}")

    fields.append("number")

    data_set = pd.DataFrame(
        data=create_dataset(
            base_dir=base_dir,
            limit_group_size=limit_group_size,
            tpl_points=actual_tpl_points,
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
        under_zero_error = (data_set[field] < 0).sum()
        print(
            f"Estimation of distribution in {field} (skew)",
            data_set[field].skew(),
            f"in {field} under zero values: {under_zero_error}"
        )

    return data_set
