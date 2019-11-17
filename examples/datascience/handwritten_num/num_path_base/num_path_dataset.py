import itertools
from collections.abc import Iterable

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage.filters import gaussian_filter

SPACE_SIZE = 64
LIGHTNESS_LIMIT = 0.365
MIN_SIZE_VALUE = 3
ONE_FEATURE_COUNT = 7
SCALE_RATIO = 1000.0


def find_content_rect(img: np.array) -> np.array:
    """Search submatrix with content.
    """
    w, h = img.shape
    x1 = y1 = x2 = y2 = 0
    for i in range(w):
        if img[i, :h].max() > LIGHTNESS_LIMIT:
            x1 = i
            break

    for i in range(h):
        if img[:w, i].max() > LIGHTNESS_LIMIT:
            y1 = i
            break

    for i in range(w):
        j = w - i - 1
        if img[j, :h].max() > LIGHTNESS_LIMIT:
            x2 = j
            break

    for i in range(h):
        j = h - i - 1
        if img[:w, j].max() > LIGHTNESS_LIMIT:
            y2 = j
            break

    return img[x1: x2, y1: y2]


def img_resize(img: np.array, size: int = SPACE_SIZE) -> np.array:
    """Resize source image to base image with "size X size".
    Source image in position center after scaling.
    """
    w, h = img.shape
    if w >= MIN_SIZE_VALUE and h >= MIN_SIZE_VALUE:
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
    else:
        return None


def prepare_image(img: Image, blur_sigma: int = 3) -> np.array:
    """Create matrix with content.
    """
    # ImageEnhance.Contrast(img
    img_m = np.array(
        ImageOps.invert(img).resize(
            (SPACE_SIZE, SPACE_SIZE), Image.BICUBIC
        )
    ) / 256
    img_m = img_resize(find_content_rect(img_m))
    if img_m is None:
        raise TypeError("Image size problem")

    img_m = gaussian_filter(img_m, sigma=blur_sigma)
    val_mean = img_m.mean()
    img_m = img_m - val_mean
    img_m *= img_m > 0
    val_max = img_m.max()
    return img_m / val_max


def line_eq(x1, y1, x2, y2) -> Iterable:
    """Equation of the line.
    """
    dx, dy = (x2 - x1), (y2 - y1)
    a_dx, a_dy = abs(dx), abs(dy)
    if a_dx > a_dy:
        k = dy / dx * SCALE_RATIO
        if x1 < x2:
            a = x1
            w = x2 - a
        else:
            a = x2
            w = x1 - a

        for i in range(w):
            x = a + i
            yield (x, int(round((x - x1) * k) // SCALE_RATIO) + y1)

    elif a_dy > 0:
        k = dx / dy * SCALE_RATIO
        if y1 < y2:
            a = y1
            w = y2 - a
        else:
            a = y2
            w = y1 - a

        for i in range(w):
            y = a + i
            yield (int(round((y - y1) * k) // SCALE_RATIO) + x1, y)


def point_distance(x1, y1, x2, y2) -> float:
    return np.sqrt((y1 - y2) ** 2 + (x1 - x2) ** 2)


def angle_calc(x0, y0, x1, y1, x2, y2) -> float:
    """Calc angle.
    """
    # A1 * x + B1 * y + C1 = 0
    # A2 * x + B2 * y + C2 = 0
    # A = y1 - y2
    # B = x2 - x1
    # C = x1 * y2 - x2 * y1
    a1, b1 = y0 - y1, x1 - x0
    a2, b2 = y0 - y2, x2 - x0
    return np.degrees(np.arccos((a1 * a2 + b1 * b2) / (
        np.sqrt(a1 ** 2 + b1 ** 2) * np.sqrt(a2 ** 2 + b2 ** 2)
    )))


def triangle_sq(x0, y0, x1, y1, x2, y2) -> float:
    """Area of triangle.
    """
    return (
        point_distance(x0, y0, x1, y1) *
        point_distance(x0, y0, x2, y2) *
        np.sin(np.deg2rad(angle_calc(x0, y0, x1, y1, x2, y2)))
    ) / 2


def next_path_step(
    step_limit: int,
    all_points: list,
    distance_mx: np.array,
    result_points: list,
    left: bool = False
):
    """Bypass points with maximization of area of triangles.
    Triangles created by lines of current step and previous.
    """
    if len(result_points) > step_limit:
        return

    if left:
        # left
        (p0, x1, y1), (p1, x2, y2), *_ = result_points
    else:
        # right
        *_, (p1, x2, y2), (p0, x1, y1) = result_points

    distance_mx[p0, p1] = 0
    distance_mx[p1, p0] = 0
    other_x_distace = distance_mx[p0, :]

    next_sq = 0
    next_point = None

    for distance in other_x_distace[other_x_distace > 0]:
        (new_p, *_), *_ = np.where(other_x_distace == distance)
        x3, y3 = all_points[new_p]
        if (new_p, x3, y3) in result_points:
            continue

        sq = triangle_sq(x1, y1, x2, y2, x3, y3)
        if sq > next_sq:
            next_sq = sq
            next_point = new_p, x3, y3

    if next_point:
        if left:
            result_points.insert(0, next_point)
        else:
            result_points.append(next_point)

        next_path_step(
            step_limit, all_points, distance_mx, result_points, not left
        )


def find_angle_features(
    img: np.array,
    step: int = 6,
    result_size: int = 6,
    dispersion_center_limit: float = 0.215,
    show: bool = False,
    with_label: int = None
) -> np.array:
    """Create features from image as array with:
    [
        distance from angle point C1 to center,
        straight line A1 length,
        distance from angle point A1 to center,
        straight line B1 length,
        distance from angle point B1 to center,
        angle a1,
        distance from angle point C2 to center,
        straight line A2 length,
        distance from angle point A2 to center,
        straight line B2 length,
        distance from angle point B2 to center,
        angle a2,
        ...
        distance from angle point C<result_size> to center,
        straight line A<result_size> length,
        distance from angle point A<result_size> to center,
        straight line B<result_size> length,
        distance from angle point B<result_size> to center,
        angle a<result_size>
    ]
    """
    w, h = img.shape
    center_x = w // 2
    center_y = h // 2
    points = {}
    step_half = step // 2

    for i in range(w):
        p_i = i // step + step_half
        for j in range(h):
            p_j = j // step + step_half
            val = img[i, j]
            if not val:
                continue

            p = (p_i, p_j)
            if p in points:
                direc, x, y = points[p]
            else:
                direc = SPACE_SIZE * 2
                x = y = 1

            cur_direc = np.sqrt((y - j) ** 2 + (x - i) ** 2)
            if cur_direc < direc:
                points[p] = cur_direc, i, j

    if show:
        img_area = np.zeros((w, h))

    path_points = sorted((x, y) for _, x, y in points.values())
    n = len(path_points)
    if show:
        for x, y in path_points:
            img_area[x, y] = 0.3

    distance_mx = np.zeros((n, n))
    lines = {}
    for i in range(n):
        x1, y1 = path_points[i]
        for j in range(n):
            if distance_mx[i, j] == 0:
                x2, y2 = path_points[j]
                line = list(line_eq(x1, y1, x2, y2))
                if line:
                    distance = np.sqrt((y1 - y2) ** 2 + (x1 - x2) ** 2)
                else:
                    distance = 0

                if line and all(img[x, y] > 0 for x, y in line):
                    # direct
                    lines[x1, y1, x2, y2] = lines[x2, y2, x1, y1] = line
                    distance_mx[i, j] = distance_mx[j, i] = distance
                else:
                    # not direct
                    distance_mx[i, j] = distance_mx[j, i] = -1 * distance

    # max line as first step in path
    (i, *_), (j, *_) = np.where(distance_mx == np.amax(distance_mx))

    max_direction = max(np.abs(distance_mx.min()), distance_mx.max())
    # normalization with space size
    distance_mx = np.round(distance_mx / max_direction, 4)

    result_points = []
    x1, y1 = path_points[i]
    x2, y2 = path_points[j]
    result_points.append((i, x1, y1))
    result_points.append((j, x2, y2))

    next_path_step(
        result_size * 2, path_points, distance_mx.copy(), result_points
    )
    angles = []
    for index, x, y in result_points:
        if not angles:
            angles.append([])

        *_, angle = angles
        if len(angle) == 3:
            *_, last_point = angle
            angle = [last_point]
            angles.append(angle)

        angle.append((index, x, y))

    featues = []
    center_points = []
    for angle in angles:
        if len(angle) < 3:
            continue

        (index2, x2, y2), (index1, x1, y1), (index3, x3, y3) = angle
        center_points.append(index1)
        distance_a = distance_mx[index1, index2]
        distance_b = distance_mx[index1, index3]
        angle_a = angle_calc(x1, y1, x2, y2, x3, y3)

        if distance_a > distance_b:
            a = distance_a
            b = distance_b
            distance_c_a = np.sqrt(
                (center_y - y2) ** 2 + (center_x - x2) ** 2) / max_direction
            distance_c_b = np.sqrt(
                (center_y - y3) ** 2 + (center_x - x3) ** 2) / max_direction
        else:
            a = distance_b
            b = distance_a
            distance_c_a = np.sqrt(
                (center_y - y3) ** 2 + (center_x - x3) ** 2) / max_direction
            distance_c_b = np.sqrt(
                (center_y - y2) ** 2 + (center_x - x2) ** 2) / max_direction

        distance = np.sqrt(
            (y1 - center_y) ** 2 + (x1 - center_x) ** 2) / max_direction

        angle_c = angle_calc(x1, y1, center_x, center_y, 0, 0)
        angle_c_rad = np.deg2rad(angle_c or 180)
        angle_a_rad = np.deg2rad(angle_a or 180)

        featues.append(
            (a + b, distance, angle_c_rad, a, distance_c_a or 0.1, b, distance_c_b or 0.1, angle_a_rad)  # noqa
        )

        if show:
            result_tmp = img_area.copy()
            for x, y in lines[x1, y1, x2, y2]:
                result_tmp[x, y] = 1
            for x, y in lines[x3, y3, x1, y1]:
                result_tmp[x, y] = 1

            plt.imshow(result_tmp, interpolation="nearest", cmap="gray")
            plt.title(
                f"line: {distance_a} {distance_b} {angle_a}"
                f" r: {distance}"
            )
            plt.show(block=True)

    if len(featues) < result_size:
        return None

    try:
        estimation_distance_incenter = np.abs(np.stack(
            distance_mx[p_index1, p_index2]
            for p_index1, p_index2 in itertools.combinations(center_points, 2)
        )).std()
    except (ValueError, IndexError):
        return None

    angles = np.zeros((result_size, ONE_FEATURE_COUNT))
    featues.sort(reverse=True)
    n = ONE_FEATURE_COUNT * result_size
    if estimation_distance_incenter < dispersion_center_limit:
        return None

    for i in range(result_size):
        (
            _,
            angles[i, 0],
            angles[i, 1],
            angles[i, 2],
            angles[i, 3],
            angles[i, 4],
            angles[i, 5],
            angles[i, 6],
        ) = featues[i]  # noqa

    angles = np.round(np.reshape(angles, n), 4)

    if with_label is not None:
        angles = np.append(angles, with_label)

    return angles
