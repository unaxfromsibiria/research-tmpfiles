import gc
import os
import ujson
import sys
import numpy as np
import matplotlib.pyplot as plt
from collections import Iterable, defaultdict
import math
import random
from PIL import Image, ImageOps


BASE_POINTS_COUNT = 40
SLOPE_STEP = 6

SHOW = []


def sort_random(item) -> float:
    return random.random()


def find_content_rect(img: np.array, intensity: float=0.6) -> np.array:
    """Search submatrix with content.
    """
    w, h = img.shape
    mid = img.max() * intensity
    x1 = y1 = x2 = y2 = 0
    for i in range(w):
        if img[i, :h].max() > mid:
            x1 = i
            break

    for i in range(h):
        if img[:w, i].max() > mid:
            y1 = i
            break

    for i in range(w):
        j = w - i - 1
        if img[j, :h].max() > mid:
            x2 = j
            break

    for i in range(h):
        j = h - i - 1
        if img[:w, j].max() > mid:
            y2 = j
            break

    return img[x1: x2, y1: y2]


def fill_by_surr(img: np.array, surr_rate: float=0.02) -> np.array:
    """Filter. Points by surrounded points.
    """
    w_arr = np.zeros(img.shape)
    w, h = w_arr.shape
    m_limit = img.max()
    l_limit = m_limit * 0.4
    h_limit = m_limit * 0.8
    dx = int(np.round(w * surr_rate))
    dy = int(np.round(h * surr_rate))
    for i in range(w):
        for j in range(h):
            for x in range(i - dx, i + dx):
                if x < 0 or x >= w:
                    continue

                for y in range(j - dy, j + dy):
                    if y < 0 or y >= h:
                        continue
                    if img[x, y] > h_limit:
                        w_arr[i, j] += 2
                    elif img[x, y] > l_limit:
                        w_arr[i, j] += 1

    return w_arr / w_arr.max()


def base_points(
        img: np.array,
        step_rate: float=0.05,
        center_rate: float=0.03) -> list:
    """Base points and distances between those.
    """
    w, h = img.shape
    step_x = int(np.round(step_rate * w))
    step_y = int(np.round(step_rate * h))
    surr_x = int(np.round(center_rate * w))
    surr_y = int(np.round(center_rate * h))

    last_x = last_y = 0
    limit = img.mean()
    points = set()

    for i in range(w):
        for j in range(h):
            dist = math.sqrt((last_x - i) ** 2 + (last_y - j) ** 2)
            if dist < step_x or dist < step_y:
                continue

            val = img[i, j]
            if val < limit:
                continue

            last_x, last_y = i, j
            for x in range(i - surr_x, i + surr_x):
                if x < 0 or x >= w:
                    continue
                for y in range(j - surr_y, j + surr_y):
                    if y < 0 or y >= h:
                        continue
                    # #
                    if img[x, y] >= val:
                        val = img[x, y]
                        last_x, last_y = x, y

            points.add((last_x, last_y))

    has_lump = True
    while has_lump:
        has_lump = False
        bad_point = None
        for x1, y1 in points:
            for x2, y2 in points:
                if x1 == x2 and y1 == y2:
                    continue
                dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                if dist < step_x or dist < step_y:
                    has_lump = True
                    bad_point = (x2, y2)
                    break

            if has_lump:
                break

        if has_lump:
            points.remove(bad_point)

    points = sorted(points, key=sort_random)
    count_points = len(points)
    if count_points < BASE_POINTS_COUNT:
        for _ in range(BASE_POINTS_COUNT - count_points):
            points.append(random.choice(points))

    return points[:BASE_POINTS_COUNT]


def sort_by_first(item):
    val, *_ = item
    return val


def angle_center(x: float, y: float) -> float:
    """Degrees from origin to point [x, y] in [0..360].
    """
    a = math.degrees(math.atan2(x, y))
    if a < 0:
        a += 360
    return a


def slope_rank(
        src_area: np.array,
        points: list,
        step: int=SLOPE_STEP) -> Iterable:
    """Distance from center to points as groups of valuses:
        For each circle sector with step N degrees [min, mean, median, max]
    """
    w, h = src_area.shape
    dx, dy = w - w // 2, h - h // 2
    m_dist = math.sqrt(dx ** 2 + dy ** 2)
    n = 360 // step
    distance_data = defaultdict(list)

    for x, y in points:
        x1, y1 = x - dx, y - dy
        a = angle_center(x1, y1)
        index = int(np.round(a / step))
        if index >= n:
            index = n - 1

        dist = math.sqrt(x1 ** 2 + y1 ** 2)
        distance_data[index].append(dist / m_dist)

    for i in range(n):
        values = distance_data[i]
        if values:
            # statistic group
            yield np.min(values)
            yield np.mean(values)
            yield np.median(values)
            yield np.max(values)
        else:
            yield from (0 for _ in range(4))

    distance_data.clear()


def resize(img: np.array, size: int=64) -> np.array:
    """Resize source image to base image with "size X size".
    Source image in position center after scaling.
    """
    w, h = img.shape
    if w > h:
        t_size = (int(size * h / w), size)
    else:
        t_size = (size, int(size * w / h))

    new_img = np.array(
        Image.fromarray(img * 256).resize(t_size, Image.ANTIALIAS)
    )
    new_img = new_img / new_img.max()
    w, h = new_img.shape

    result_img = np.zeros((size, size))
    delta_i = (size - w) // 2
    delta_j = (size - h) // 2
    for i in range(w):
        for j in range(h):
            result_img[i + delta_i, j + delta_j] = new_img[i, j]

    return result_img
