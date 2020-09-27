import os
import random
import typing
import uuid

import matplotlib.pyplot as plt
import numba
import numpy as np
from PIL import Image

LAYERS: int = 3

# dataset preparation activity:
# 1) copy good images to dir "<good images path>"
# 2) create two numpy array dumps:
#   python create.py good_img/ bad_img/ data/ 10000
# 3) check dataset content:
#   python show.py data/dataset_32_low_b9f36eff.npy data/dataset_32_high_b9f36eff.npy 5


def new_img(path: str) -> np.array:
    """Open image.
    """
    img = Image.open(path)
    return np.array(img)


@numba.jit(nopython=False, forceobj=True)
def fill_rows(
    img: np.array,
    rows: np.array,
    layers: int,
    core_size: int,
    w: int,
    h: int
):
    """Split area by core size rects and fill result rows
    using indexes.
    """
    n = -1
    index = 0
    m = core_size ** 2
    size = (m,)
    for x in range(w):
        for y in range(h):
            n += 1
            for l in range(layers):
                row = np.reshape(
                    img[
                        x * core_size: (x + 1) * core_size,
                        y * core_size: (y + 1) * core_size,
                        l
                    ],
                    size
                )
                for index in range(m):
                    rows[n, l * m + index] = row[index]


def create_rows(img: np.array, core_size: int = 64) -> np.array:
    """Split area by core size rects and create rows
    using indexes.
    """
    w, h, layers = img.shape
    assert layers == LAYERS
    x = w // core_size
    y = h // core_size
    n = x * y
    result = np.zeros((n, (core_size ** 2) * LAYERS), dtype=img.dtype)
    fill_rows(img, result, layers, core_size, x, y)
    return result


def search_images(
    current_dir: str,
    exts={"jpg", "png", "jpeg", "gif"}
) -> typing.Iterable[typing.Tuple[str, str]]:
    """Images files in dir.
    """
    for root, _, files in os.walk(current_dir):
        for file_name in files:
            ext = file_name.rsplit('.', 1)[-1].lower()
            if ext in exts:
                yield os.path.join(root, file_name), file_name


def create_bad_images(
    source_dir: str,
    target_dir: str
) -> typing.List[typing.Tuple[str, str]]:
    """Convert images (using imagemagick as OS process).
    """
    result = []
    for img_path, img_name in search_images(source_dir):
        try:
            img: Image = Image.open(img_path)
        except Exception:
            continue

        target_img_path = os.path.join(target_dir, img_name)
        if os.path.exists(target_img_path):
            result.append((img_path, target_img_path))
            continue

        w, h = img.size
        percent = random.randint(30, 52)
        rate = percent / 100
        new_w, new_h = int(w * rate), int(h * rate)
        src_size = f"{w}x{h}"
        new_size = f"{new_w}x{new_h}"
        tmp_img_path = img_path.replace(img_name, f"tmp_{new_size}_{img_name}")
        quality = random.randint(60, 80)

        cmd = (
            f"convert -resize {percent}% '{img_path}' '{tmp_img_path}' && "
            f"convert -resize {src_size}! -quality {quality} "
            f"'{tmp_img_path}' '{target_img_path}' && rm '{tmp_img_path}'"
        )
        os.system(cmd)
        if os.path.exists(target_img_path):
            try:
                img: Image = Image.open(target_img_path)
            except Exception:
                continue

            res_w, res_h = img.size
            assert res_w == w and res_h == h, (
                f"Size {w}x{h} != {res_w}x{res_h} cmd: {cmd}"
            )
            result.append((img_path, target_img_path))
            print(f"{img_path} -> {target_img_path}")
        else:
            print("Problem with:", img_path)

    return result


def create_dataset(
    *,
    source_dir: str,
    target_dir: str,
    dataset_dir: str,
    core_size: int = 32,
    rows_limit: int = 1_000_000,
) -> typing.Tuple[str, str]:
    """Create dataset from files.
    Result: (dataset with high quality, dataset with low quality)
    """
    # # create rows # #
    images = create_bad_images(source_dir, target_dir)
    images_count = len(images)
    # get rows from each image
    rows_from_img = rows_limit // images_count

    good_data = bad_data = None
    code = uuid.uuid4().hex[:8]
    n = 0

    for src_img, bad_img in images:
        images_count -= 1
        if rows_from_img <= 1:
            continue

        src_rows = create_rows(new_img(src_img), core_size)
        bad_rows = create_rows(new_img(bad_img), core_size)
        assert src_rows.shape == bad_rows.shape, (
            f"Size {src_rows.shape} != {bad_rows.shape}"
        )
        print(f"size: {src_rows.shape}")

        src_rows = src_rows[:rows_from_img]
        bad_rows = bad_rows[:rows_from_img]

        if good_data is None:
            good_data = src_rows
        else:
            good_data = np.append(good_data, src_rows, axis=0)

        if bad_data is None:
            bad_data = bad_rows
        else:
            bad_data = np.append(bad_data, bad_rows, axis=0)

        n, count = good_data.shape
        rows_from_img = (rows_limit - n) // (images_count or 1)

        print(f"Data from '{src_img}' added, size: {n} columns {count}'")
        if n >= rows_limit:
            break

    # # save # #
    bad_path = os.path.join(
        dataset_dir, f"dataset_{core_size}_low_{code}.npy"
    )
    good_path = os.path.join(
        dataset_dir, f"dataset_{core_size}_high_{code}.npy"
    )

    if bad_data is None or good_data is None:
        bad_path = good_path = ""
    else:
        # # random ratation # #
        keys = sorted(range(n), key=lambda _: random.random())
        for i, j in enumerate(keys):
            buff = bad_data[i].copy()
            bad_data[i] = bad_data[j]
            bad_data[j] = buff

            buff = good_data[i].copy()
            good_data[i] = good_data[j]
            good_data[j] = buff

        with open(bad_path, "wb") as of:
            np.save(of, bad_data)

        with open(good_path, "wb") as of:
            np.save(of, good_data)

    return good_path, bad_path


@numba.jit(nopython=False, forceobj=True)
def nopy_restore_area(
    res: np.array,
    row: np.array,
    core_size: int,
    levels: int
):
    """Fill result area.
    """

    m = core_size ** 2
    size = (core_size, core_size)
    for l in range(levels):
        src = np.reshape(row[m * l: m * l + m], size)
        res[0: core_size, 0: core_size, l] = src


def create_percent_diff(area_high: np.array, area_low: np.array) -> np.array:
    """Mask with expected loss of quality.
    [-100%..1%] - [0..99]
    [1%..100%] - [101..200]
    0% - 100
    """
    diff = np.round(
        (area_high.astype(float) - area_low.astype(float)) / 256 * 100
    ) + 100
    assert (diff < 0).sum() + (diff > 200).sum() == 0
    return diff.astype("uint8")


def apply_diff(area_low: np.array, diff: np.array) -> np.array:
    """Apply diff.
    """
    rates = (diff.astype(float) - 100) / 100 * 256
    res = np.round(area_low + rates)
    res[res > 255] = 255
    res[res < 1] = 0
    return res.astype("uint8")


def check_dataset(*, low_path: str, high_path: str, count: int = 1):
    """Open and show an image or images.
    """
    with open(high_path, "rb") as s_file:
        src_data: np.array = np.load(s_file)

    with open(low_path, "rb") as s_file:
        res_data: np.array = np.load(s_file)

    assert src_data.shape == res_data.shape
    n, m = res_data.shape
    core_size = int(np.sqrt(m / LAYERS))
    assert core_size ** 2 * LAYERS == m
    k = core_size * 4

    for _ in range(count):
        img = np.zeros(
            (core_size, k, LAYERS), dtype=res_data.dtype
        )
        i = random.randint(0, n)
        res_row = res_data[i]
        src_row = src_data[i]

        mask = create_percent_diff(src_row, res_row)
        restored_src = apply_diff(res_row, mask)
        for l_i, layer_mask in enumerate(np.reshape(mask, (LAYERS, core_size, core_size))):  # noqa
            print(f"layer {l_i} mask:")
            for row in layer_mask:
                print(",".join(map("{: >3}".format, row)))

        nopy_restore_area(
            img[:, 0:core_size, :], src_row, core_size, LAYERS
        )
        nopy_restore_area(
            img[:, core_size:core_size * 2, :], res_row, core_size, LAYERS
        )
        nopy_restore_area(
            img[:, core_size * 2:core_size * 3, :], mask, core_size, LAYERS
        )
        nopy_restore_area(
            img[:, core_size * 3:k, :], restored_src, core_size, LAYERS
        )
        plt.imshow(Image.fromarray(img))
        plt.show(block=True)


def open_dataset(
    low_path: str,
    high_path: str,
    train_sample_size: int = 98
) -> typing.Tuple[np.array, np.array, np.array, np.array]:
    """Create train and test data.
    """

    with open(high_path, "rb") as s_file:
        src_data: np.array = np.load(s_file)

    with open(low_path, "rb") as s_file:
        res_data: np.array = np.load(s_file)

    assert src_data.shape == res_data.shape
    n, m = res_data.shape
    core_size = int(np.sqrt(m / LAYERS))
    assert core_size ** 2 * LAYERS == m
    train_sample_n = int(n * train_sample_size / 100)

    print(f"Data set size: {n} train data set: {train_sample_n}")
    train_x = res_data[:train_sample_n]
    train_y = src_data[:train_sample_n]
    test_x = res_data[train_sample_n:]
    test_y = src_data[train_sample_n:]

    return train_x, train_y, test_x, test_y
