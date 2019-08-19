import sys
import ujson
import numpy as np
from sklearn.svm import SVC
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageOps

from recognumbers.numimg import (
    fill_by_surr, find_content_rect, base_points, slope_rank, resize
)

param_size = int(sys.argv[1])

assert 12 <= param_size <= 512
assert param_size % 2 == 0

dataset_path = sys.argv[2]
img_base_size = int(sys.argv[4])


def show_points(points: list, size: (int, int)) -> np.array:
    img = np.zeros(size)
    for x, y in points:
        img[x, y] = 1
    return img


def prepare_img(img_path: str) -> np.array:
    result = np.zeros((1, param_size))
    try:
        img = np.array(ImageOps.invert(Image.open(img_path).convert("L")))
        img = img / img.max()
        img = find_content_rect(img)
        size_w, size_h = img.shape
        plt.imshow(img, interpolation="nearest", cmap="gray")
        plt.title("Source image (size: {}x{})".format(size_w, size_h))
        plt.show()
        w_img = fill_by_surr(resize(img, img_base_size))

    except Exception as err:
        print("Error", err, "in", img_path)
        return result

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

    for i in range(len(rank_list)):
        result[0, i] = rank_list[i]

    return result


with open(dataset_path) as datafile:
    data = [
        item for item in ujson.loads(datafile.read())
        if len(item) == param_size + 1
    ]

n = len(data)

print("Dataset size:", n)

numbers = [data[i][0] for i in range(n)]
data_set = np.zeros((n, param_size))
user_data = prepare_img(sys.argv[3])

for i in range(n):
    for j in range(param_size):
        data_set[i, j] = data[i][j + 1]


model = SVC(
    kernel="rbf",
    random_state=0,
    decision_function_shape="ovr",
    tol=0.01,
    gamma=0.09,
    C=50
)

model.fit(data_set, numbers)
errors = 0

res = model.predict(user_data)

for val in res:
    print("This is", val, "?")
