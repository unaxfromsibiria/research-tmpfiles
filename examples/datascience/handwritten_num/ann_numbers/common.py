
import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage.filters import gaussian_filter

SPACE_SIZE = 28
SPACE_VOLUME = SPACE_SIZE ** 2
LIGHTNESS_LIMIT = 0.365
MIN_SIZE_VALUE = 3


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
    img: Image,
    out_size=(SPACE_SIZE, SPACE_SIZE),
    blur_sigma: int = 2,
    fullness: float = 0.3
) -> np.array:
    """Create matrix with content.
    """
    # ImageEnhance.Contrast(img
    img_m = np.array(
        ImageOps.invert(img).resize((128, 128), Image.BICUBIC)
    ) / 256
    img_m = img_resize(find_content_rect(img_m))
    if img_m is None:
        raise TypeError("Image size problem")

    img_m = gaussian_filter(img_m, sigma=blur_sigma)
    val_mean = img_m.mean()
    img_m = img_m - val_mean
    img_m *= img_m > 0
    val_max = img_m.max()

    new_img = np.array(
        Image.fromarray(img_m / val_max * 256).resize(
            out_size, Image.ANTIALIAS
        )
    )
    img = (new_img / new_img.max()) + LIGHTNESS_LIMIT
    img[img >= 0.9] = 1.0
    if img.sum() / SPACE_VOLUME < fullness:
        n = 100 - (img.sum() / SPACE_VOLUME * 100)
        raise ValueError(f"{n}% of area is empty")

    return img
