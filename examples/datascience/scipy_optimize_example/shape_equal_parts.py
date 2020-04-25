# howto use (with example image):
# img = open_img("examples/3.png")
# create_gif(img, "examples/3_res.gif")
#    Optimization terminated successfully.
#         Current function value: 30.000000
#         Iterations: 18
#         Function evaluations: 40

import typing
from collections.abc import Iterable

import numpy as np
from matplotlib import pyplot as plt
from PIL import Image
from scipy.optimize import minimize

SCALE_RATIO: float = 1000


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


def show_img(img: np.array):
    plt.imshow(img, interpolation="nearest", cmap="gray")
    plt.title("Size: {}x{}".format(*img.shape))
    plt.show()


def open_img(file_path: str) -> np.array:
    try:
        img = Image.open(file_path).convert("L")
        result = (np.asarray(img) / 255 == 0) * 1
    except TypeError as err:
        print(f"Image format problem '{err}' in '{file_path}'")
        result = None
    return result


def img_halfs(
    img: np.array,
    a_index: float,
    b_index: float
) -> typing.Tuple[np.array, np.array]:
    """Divide shape on image by two parts by line.
    """
    h, w = img.shape
    part_left: np.array = np.zeros(img.shape)
    part_right: np.array = np.zeros(img.shape)
    line = {
        y: x for x, y in line_eq(int(w * a_index), 0, int(w * b_index), h)
    }
    for i in range(h):
        j = line[i]
        part_left[i, :j] = img[i, :j]
        part_right[i, j:] = img[i, j:]

    return part_left, part_right


def calc_halfs_diff(x0: np.array, img: np.array, way: list) -> float:
    """Shape area diff.
    """
    x, y = x0
    if not(0 <= x <= 1 and 0 <= y <= 1):
        return np.inf

    part_left, part_right = img_halfs(img, x, y)
    diff = np.abs((part_right > 0).sum() - (part_left > 0).sum())
    way.append((x, y, diff))
    return diff


def div_image(
    img: np.array, step: float = 0.01
) -> typing.Tuple[np.array, np.array, list]:
    """Divide shape on image by two parts with equal area.
    """
    way = []
    res = minimize(
        calc_halfs_diff,
        np.array([0.5, 0.5]),
        args=(img, way),
        method="nelder-mead",
        options={"disp": True, "xatol": step}
    )
    part_left, part_right = img_halfs(img, *res.x)
    return part_left, part_right, way


def create_gif(img: np.array, out_file: str):
    """Run research and save result image as animation.
    """
    left, right, way = div_image(img)
    img_res = Image.fromarray((left + right / 2) * 255)
    data = []
    for x, y, _ in way:
        step_left, step_right = img_halfs(img, x, y)
        img_step = Image.fromarray((step_left + step_right / 2) * 255)
        data.append(img_step)

    for _ in range(5):
        data.append(img_res)

    img_res.save(
        out_file,
        format="GIF",
        append_images=data,
        save_all=True,
        duration=200,
        loop=0
    )
