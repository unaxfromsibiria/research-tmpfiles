
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage.filters import gaussian_filter

SPACE_SIZE = 64
LIGHTNESS_LIMIT = 0.365
MIN_SIZE_VALUE = 3
ONE_FEATURE_COUNT = 7
SCALE_RATIO = 1000.0

base_tpl_points = {
    # templates
    0: [
        [[28, 5], [15, 13], [44, 12], [12, 25], [50, 24], [13, 37], [49, 37], [45, 50], [16, 48], [37, 59], [25, 57]],  # noqa
        [[44, 5], [28, 7], [55, 12], [19, 18], [54, 24], [15, 31], [52, 37], [47, 50], [17, 44], [37, 59], [25, 57]],  # noqa
    ],
    1: [
        [[20, 14], [30, 8], [33, 21], [30, 33], [27, 45], [25, 55]],
        [[13, 12], [26, 5], [28, 21], [30, 33], [32, 46], [38, 58]],
    ],
    2: [
        [[20, 14], [30, 7], [45, 9], [48, 20], [44, 30], [36, 39], [26, 48], [17, 58], [28, 60], [40, 58], [52, 58]],  # noqa
        [[10, 14], [22, 8], [33, 17], [35, 28], [27, 38], [20, 48], [8, 58], [19, 60], [32, 60], [43, 56], [55, 57]],  # noqa
    ],
    3: [
        [[20, 14], [30, 7], [45, 9], [48, 20], [44, 30], [30, 33], [48, 43], [49, 55], [36, 60], [22, 60], [12, 53]],  # noqa
        [[10, 10], [22, 7], [34, 4], [48, 6], [48, 20], [40, 30], [25, 33], [48, 43], [49, 55], [36, 60], [22, 60]],  # noqa
    ],
    4: [
        [[20, 6], [17, 18], [18, 30], [46, 8], [44, 22], [42, 33], [40, 45], [39, 56], [30, 33]],  # noqa
        [[10, 6], [11, 18], [12, 30], [40, 8], [42, 22], [42, 33], [44, 45], [47, 56], [27, 28]],  # noqa
    ],
    5: [
        [[10, 10], [20, 8], [32, 8], [44, 5], [12, 22], [14, 33], [26, 32], [38, 40], [40, 52], [30, 59], [18, 59], [7, 60]],  # noqa
        [[20, 7], [31, 8], [44, 6], [55, 5], [22, 22], [25, 33], [37, 32], [48, 40], [52, 52], [40, 59], [28, 59]],  # noqa
    ],
    6: [
        [[46, 6], [33, 10], [24, 18], [13, 30], [12, 43], [12, 56], [26, 56], [38, 55], [46, 45], [38, 33], [26, 30]],  # noqa
        [[43, 6], [29, 7], [15, 10], [12, 23], [9, 38], [10, 50], [21, 56], [35, 55], [46, 47], [38, 33], [26, 29]],  # noqa
    ],
    7: [
        [[10, 6], [23, 12], [44, 5], [40, 15], [39, 26], [34, 37], [30, 49], [27, 59]],  # noqa
        [[20, 6], [33, 7], [50, 5], [46, 15], [44, 26], [42, 37], [40, 49], [37, 59], [30, 33], [55, 34]],  # noqa
    ],
    8: [
        [[36, 4], [24, 12], [48, 12], [30, 25], [44, 24], [36, 34], [23, 40], [15, 50], [22, 59], [35, 60], [47, 54], [46, 40]],  # noqa
        [[37, 4], [23, 5], [16, 16], [48, 12], [24, 25], [44, 24], [36, 34], [23, 40], [24, 54], [35, 60], [47, 54], [46, 40]],  # noqa
    ],
    9: [
        [[38, 7], [21, 9], [50, 15], [51, 30], [50, 43], [45, 53], [45, 53], [32, 55], [21, 56], [22, 22], [28, 32], [39, 36]],  # noqa
        [[20, 6], [12, 16], [34, 9], [18, 29], [31, 30], [34, 9], [44, 22], [50, 33], [52, 49], [45, 58], [34, 57]],  # noqa
    ]
}


def create_templates(
    show: bool = True,
    tpl_points: dict = base_tpl_points
) -> (list, int):
    """Create digest templates by points.
    """
    tpls = []
    only = sorted(tpl_points.keys())
    for num in only:
        points_tpl = tpl_points[num]
        for points in points_tpl:
            tpl_img = np.zeros((SPACE_SIZE, SPACE_SIZE))
            for x, y in points:
                tpl_img[x, y] = 1

            tpl = create_tpl(tpl_img)
            tpls.append((num, tpl))
            if show:
                c_tpl = tpl_img.copy()
                point_count, *_ = tpl.shape

                for i in range(point_count):
                    c_tpl += tpl[i]

                plt.imshow(c_tpl, interpolation="nearest", cmap="gray")
                plt.title(f"{num} - {point_count} points")
                plt.show(block=True)

    fearure_size = len(tpls) * 5
    return tpls, fearure_size


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


def prepare_image(
    img: Image, blur_sigma: int = 2, discharge_ratio: float = 0.15
) -> (np.array, int):
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
    img_m = img_m / val_max
    volume = (img_m > 0).sum()
    limit = volume * discharge_ratio
    while volume > limit:
        nose = np.random.rand(*img_m.shape) > 0.5
        img_m = img_m * nose
        volume = (img_m > 0).sum()

    return img_m, volume


def create_tpl(img: np.array, radius_ratio: float = 0.08) -> np.array:
    """Create mask for image (radius around of templates points).
    """
    size, _ = img.shape
    radius = np.round(radius_ratio * size)
    x_points, y_points = np.where(img > 0)
    line_index = np.linspace(0, size - 1, size)
    x_indexes, y_indexes = np.meshgrid(line_index, line_index)
    masks = np.zeros((len(x_points), size, size))
    for i, x in enumerate(x_points):
        y = y_points[i]
        distances = np.sqrt(
            np.power(x_indexes - x, 2) + np.power(y_indexes - y, 2)
        )
        in_radius = distances <= radius
        masks[i, :, :][in_radius] = distances[in_radius]

    return masks


def templates_scores(
    img: np.array, tpl: np.array, precision: int = 4
) -> np.array:
    """
    """
    total_points = (img > 0).sum()
    size, _ = img.shape
    n, _, _ = tpl.shape  # point count
    close_img = np.zeros(img.shape)
    close_img[img > 0] = 1 - img[img > 0]
    result = np.zeros((4, n))
    for i in range(n):
        mask = tpl[i]
        distances = close_img * mask
        in_points = distances > 0
        point_count = in_points.sum()
        if point_count == 0:
            continue

        result[0, i] = point_count / total_points
        result[1, i] = distances[in_points].mean() / size
        result[2, i] = np.median(distances[in_points]) / size
        result[3] += 1 / n

    return np.round(
        (
            result[0].mean(),
            result[1].mean(),
            np.median(result[1]),
            result[2].mean(),
            result[3][0]
        ),
        precision
    )
