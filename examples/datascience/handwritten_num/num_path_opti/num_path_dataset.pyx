# This implementation in ~15.5 times faster than base method.
# 1) Build methods as shared object library (handwritten_num/num_path_opti/num_path_dataset.cpython-<arch>.so):
#   cd handwritten_num/num_path_opti/
#   python setup_num_path_dataset.py build_ext --inplace
#   
# This code tested in python 3.7.4 with cython 0.29.14.
#
# 2) Enjoy.

import itertools
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
from scipy.ndimage.filters import gaussian_filter

cdef int SPACE_SIZE = 64
cdef float LIGHTNESS_LIMIT = 0.35
cdef int MIN_SIZE_VALUE = 3


cdef float _point_distance(int x1, int y1, int x2, int y2):
    cdef long param_a = y1 - y2, param_b = x1 - x2
    return float(np.sqrt(param_a ** 2 + param_b ** 2))


cdef float _angle_calc(int x0, int y0, int x1, int y1, int x2, int y2):
    """Calc angle.
    """
    # A1 * x + B1 * y + C1 = 0
    # A2 * x + B2 * y + C2 = 0
    # A = y1 - y2
    # B = x2 - x1
    # C = x1 * y2 - x2 * y1
    cdef long a1 = y0 - y1, b1 = x1 - x0
    cdef long a2 = y0 - y2, b2 = x2 - x0
    return np.degrees(
        np.arccos(
            (a1 * a2 + b1 * b2) / (np.sqrt(a1 ** 2 + b1 ** 2) * np.sqrt(a2 ** 2 + b2 ** 2))
        )
    )


cdef float _triangle_sq(int x0, int y0, int x1, int y1, int x2, int y2):
    """Area of triangle.
    """
    return (
        _point_distance(x0, y0, x1, y1) *
        _point_distance(x0, y0, x2, y2) *
        float(np.sin(np.deg2rad(_angle_calc(x0, y0, x1, y1, x2, y2))))
    ) / 2


cdef object _find_content_rect(object img):
    """Search submatrix with content.
    """
    cdef int w = 0, h = 0
    cdef int x1 = 0, y1 = 0, x2 = 0, y2 = 0
    w, h = img.shape
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


cdef list _line_eq(int x1, int y1, int x2, int y2):
    """Equation of the line.
    """
    cdef i = 0, a, w, x, y
    cdef float k, a_dx, a_dy, dx = float(x2 - x1), dy = float(y2 - y1)
    result = []
    # abs
    a_dx = abs(dx)
    a_dy = abs(dy)
    if a_dx > a_dy:
        k = dy / dx
        if x1 < x2:
            a = x1
            w = x2 - a
        else:
            a = x2
            w = x1 - a

        for i in range(w):
            x = a + i
            result.append((x, int(round((x - x1) * k + y1))))

    elif a_dy > 0:
        k = dx / dy
        if y1 < y2:
            a = y1
            w = y2 - a
        else:
            a = y2
            w = y1 - a

        for i in range(w):
            y = a + i
            result.append((int(round((y - y1) * k + x1)), y))

    return result


cdef object _img_resize(object img, int size):
    """Resize source image to base image with "size X size".
    Source image in position center after scaling.
    """
    cdef int w, h, i, j, delta_i, delta_j
    cdef int t_w, t_h
    w, h = img.shape
    if w >= MIN_SIZE_VALUE and h >= MIN_SIZE_VALUE:
        if w > h:
            t_w = int(size * h / w)
            t_h = size
        else:
            t_w = size
            t_h = int(size * w / h)

        new_img = np.array(
            Image.fromarray(img * 256).resize((t_w, t_h), Image.ANTIALIAS)
        )
        new_img = new_img / new_img.max()
        w, h = new_img.shape

        result_img = np.zeros((size, size))
        delta_i = int((size - w) / 2)
        delta_j = int((size - h) / 2)
        for i in range(w):
            for j in range(h):
                result_img[i + delta_i, j + delta_j] = new_img[i, j]

        return result_img
    else:
        return None


cdef _next_path_step(
    int step_limit,
    object all_points, # list
    object distance_mx, # np.array
    object result_points, # list
    bint left
):
    """Bypass points with maximization of area of triangles.
    Triangles created by lines of current step and previous.
    """
    cdef int p0, x1, y1, p1, x2, y2, new_p, x3, y3
    cdef float next_sq, sq
    cdef int next_point_p = 0, next_point_x = 0, next_point_y = 0
    cdef bint next_point

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
    next_point = False

    for distance in other_x_distace[other_x_distace > 0]:
        (new_p, *_), *_ = np.where(other_x_distace == distance)
        x3, y3 = all_points[new_p]
        # point as tuple
        if (new_p, x3, y3) in result_points:
            continue

        sq = _triangle_sq(x1, y1, x2, y2, x3, y3)
        if sq > next_sq:
            next_sq = sq
            next_point_p = new_p
            next_point_x = x3
            next_point_y = y3
            next_point = True

    if next_point:
        if left:
            result_points.insert(0, (next_point_p, next_point_x, next_point_y))
        else:
            result_points.append((next_point_p, next_point_x, next_point_y))
        # reuse var
        # not left -> (!(__pyx_v_left != 0));
        # left != True -> (__pyx_v_left != 1);
        next_point = left != True
        _next_path_step(
            step_limit, all_points, distance_mx, result_points, next_point
        )


cdef object _find_angle_features(
    img: object, # np.array
    int step,
    int result_size,
    float dispersion_center_limit,
    int with_label
):
    """ Cython based method 'find_angle_features'.
    """
    cdef int w, h, step_half, i, p_i, p_j, x, y, n, center_x, center_y
    cdef float direc, val, cur_direc, distance
    cdef int index, index1, x1, y1, index2, x2, y2, index3, x3, y3
    cdef int p_index1, p_index2
    cdef float distance_a, distance_b, angle_a, a, b
    cdef float estimation_distance_incenter

    w, h = img.shape
    center_x = w // 2
    center_y = h // 2
    points = {}
    lines = {}
    step_half = step // 2

    for i in range(w):
        p_i = i // step + step_half
        for j in range(h):
            p_j = j // step + step_half
            val = img[i, j]
            if not val:
                continue

            if (p_i, p_j) in points:
                direc, x, y = points[p_i, p_j]
            else:
                direc = SPACE_SIZE * 2
                x = y = 1

            cur_direc = np.sqrt(
                (y - j) ** 2 + (x - i) ** 2
            )
            if cur_direc < direc:
                points[p_i, p_j] = cur_direc, i, j

    path_points = sorted((x, y) for _, x, y in points.values())
    n = len(path_points)
    distance_mx = np.zeros((n, n))

    for i in range(n):
        x1, y1 = path_points[i]
        for j in range(n):
            x2, y2 = path_points[j]
            line = _line_eq(x1, y1, x2, y2)
            distance = np.sqrt((y1 - y2) ** 2 + (x1 - x2) ** 2)
            if len(line) > 0 and all(img[x, y] > 0 for x, y in line):
                # direct
                lines[x1, y1, x2, y2] = lines[x2, y2, x1, y1] = line
                distance_mx[i, j] = distance
            elif len(line) > 0:
                # not direct
                distance_mx[i, j] = -1 * distance
            else:
                distance_mx[i, j] = 0

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

    _next_path_step(
        result_size * 2, path_points, distance_mx.copy(), result_points, False
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
        angle_a = _angle_calc(x1, y1, x2, y2, x3, y3)
        if distance_a > distance_b:
            a = distance_a
            b = distance_b
            direc = np.sqrt((center_y - y2) ** 2 + (center_x - x2) ** 2) / max_direction
            cur_direc = np.sqrt((center_y - y3) ** 2 + (center_x - x3) ** 2) / max_direction
        else:
            a = distance_b
            b = distance_a
            direc = np.sqrt((center_y - y3) ** 2 + (center_x - x3) ** 2) / max_direction
            cur_direc = np.sqrt((center_y - y2) ** 2 + (center_x - x2) ** 2) / max_direction

        distance = np.sqrt((y1 - center_y) ** 2 + (x1 - center_x) ** 2) / max_direction
        featues.append(
            (a + b, distance, a, direc, b, cur_direc, np.deg2rad(angle_a))
        )

    if len(featues) < result_size:
        return None

    try:
        estimation_distance_incenter = np.abs(np.stack(
            distance_mx[p_index1, p_index2]
            for p_index1, p_index2 in itertools.combinations(center_points, 2)
        )).std()
    except (ValueError, IndexError):
        return None

    angles = np.zeros((result_size, 6))
    featues.sort(reverse=True)
    n = 6 * result_size

    if estimation_distance_incenter < dispersion_center_limit:
        return None

    j = 0
    for i in range(result_size):
        if len(featues[i]) == 7:
            (
                _,
                angles[i, 0],
                angles[i, 1],
                angles[i, 2],
                angles[i, 3],
                angles[i, 4],
                angles[i, 5]
            ) = featues[i]
            j += 1

    if j == result_size:
        angles = np.round(np.reshape(angles, n), 4)

        if with_label >= 0:
            angles = np.append(angles, with_label)

        return angles
    else:
        return None


# # modeule interface # #
def prepare_image(img: Image, blur_sigma: int = 2) -> np.array:
    """Create matrix with content.
    """
    # ImageEnhance.Contrast(img
    img_m = np.array(
        ImageOps.invert(img).resize(
            (SPACE_SIZE, SPACE_SIZE), Image.BICUBIC
        )
    ) / 256
    img_m = _img_resize(_find_content_rect(img_m), SPACE_SIZE)
    if img_m is None:
        raise TypeError("Image size problem")

    img_m = gaussian_filter(img_m, sigma=blur_sigma)
    val_mean = img_m.mean()
    img_m = img_m - val_mean
    img_m *= img_m > 0
    val_max = img_m.max()
    return img_m / val_max


def find_angle_features(
    img: np.array,
    step: int = 6,
    result_size: int = 6,
    dispersion_center_limit: float = 0.1,
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
    #print("Cython version 'find_angle_features'.")
    assert not show, "Not supported in optimized method."

    return _find_angle_features(
        img, step, result_size, dispersion_center_limit, with_label
    )
