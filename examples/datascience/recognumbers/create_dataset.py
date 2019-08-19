import os
import sys
import random
import numpy as np
import matplotlib.pyplot as plt
from collections import Iterable, defaultdict
import math
from PIL import Image, ImageOps

from recognumbers.numimg import (
    fill_by_surr, find_content_rect, base_points, slope_rank, resize
)


def numbers_data_files(base_dir: str):
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


def run(size: int=64):
    path = sys.argv[1]
    # #
    numbers = sorted((
        (random.random(), num, img_path)
        for num, img_path in numbers_data_files(path)
    ))

    out_path = sys.argv[2]

    with open(out_path, "w") as out_file:
        out_file.write("[\n")
        for _, num, img_path in numbers:
            try:
                img = np.array(ImageOps.invert(Image.open(img_path).convert("L")))
                img = img / img.max()
                img = find_content_rect(img)
                w_img = fill_by_surr(resize(img, size))
            except Exception as err:
                print("Error", err, "in", img_path)
                continue

            w_img = w_img / w_img.max()
            points = base_points(w_img)
            rank_list = list(slope_rank(w_img, points))

            out_file.write(
                "[{},{}],\n".format(num, ",".join(map(str, rank_list)))
            )

        out_file.write("[]\n]\n")


run()
