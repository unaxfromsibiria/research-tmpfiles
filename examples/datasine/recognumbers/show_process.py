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


SHOW = []

try:
    SHOW.extend(
        map(int, (sys.argv[2] or "0").split(","))
    )
except:
    SHOW.append(0)


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


def show_points(points: Iterable, size: (int, int)) -> np.array:
    img = np.zeros(size)
    for x, y in points:
        img[x, y] = 1
    return img


def run(size: int=64):
    try:
        path = sys.argv[1]
    except:
        path = "numbers"

    # #
    numbers = sorted((
        (random.random(), img_path)
        for num, img_path in numbers_data_files(path) if num in SHOW
    ))

    for _, img_path in numbers:
        try:
            img = np.array(ImageOps.invert(Image.open(img_path).convert("L")))
            img = img / img.max()
            img = find_content_rect(img)
            size_w, size_h = img.shape
            plt.imshow(img, interpolation="nearest", cmap="gray")
            plt.title("Source (size: {}x{})".format(size_w, size_h))
            plt.show()

            w_img = fill_by_surr(resize(img, size))
        except Exception as err:
            print("Error", err, "in", img_path)
            continue

        w_img = w_img / w_img.max()

        size_w, size_h = w_img.shape
        plt.imshow(w_img, interpolation="nearest", cmap="gray")
        plt.title("After filter")
        plt.show()

        points = base_points(w_img)
        img_points = show_points(points, w_img.shape)
        plt.imshow(img_points, interpolation="nearest", cmap="gray")
        plt.title("Points count {}".format(len(points)))
        plt.show()

        rank_list = list(slope_rank(w_img, points))
        plt.plot(range(1, len(rank_list) + 1), rank_list, color="green")
        plt.xlabel("values index (from {})".format(len(rank_list)))
        plt.ylabel("distance statistic")
        plt.show()


run()
