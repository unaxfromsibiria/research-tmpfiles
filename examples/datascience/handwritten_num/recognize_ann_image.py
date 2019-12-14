import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

from ann_numbers.common import prepare_image
from ann_numbers.create import create_model

_, dataset_path, *images = sys.argv
dataset = pd.read_csv(dataset_path)

model, *_ = create_model(dataset, sample=0.90)

print(dataset.info())

for img_path in images:
    try:
        img = Image.open(img_path).convert("L")
    except TypeError as err:
        print(f"Image format problem '{err}' in '{img_path}'")
        continue

    plt.imshow(img, interpolation="nearest", cmap="gray")
    plt.title(
        f"Source image: {img_path}"
    )
    plt.show(block=True)

    try:
        img_m = prepare_image(img)
    except Exception as err:
        print(img_path, err)
    else:
        features = img_m.ravel()
        plt.imshow(img_m, interpolation="nearest", cmap="gray")
        predict_data = model.predict(features.reshape((1, len(features))))
        predicted = np.argmax(predict_data[0])
        for val in predict_data[0]:
            print(">", np.round(val, 3))

        plt.title(
            f"Prepared image: {img_m.shape} features: {len(features)} "
            f"predict: {predicted}"
        )
        plt.show(block=True)
