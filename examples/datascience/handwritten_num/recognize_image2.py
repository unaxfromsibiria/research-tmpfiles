import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.ensemble import RandomForestClassifier

from num_tpl_base.image_tpl import base_tpl_points
from num_tpl_base.image_tpl import create_templates
from num_tpl_base.image_tpl import prepare_image
from num_tpl_base.image_tpl import templates_scores

classifier_params = dict(
    n_estimators=400,
    max_depth=30,
    n_jobs=1,
    warm_start=True,
    verbose=1
)
random_state = 77

_, dataset_path, *images = sys.argv
dataset = pd.read_csv(dataset_path)

print(dataset.info())

fields = []

for field in dataset.columns.values:
    if "number" in field:
        continue
    if "Unnamed" in field:
        continue

    fields.append(field)

print("Fields: ", fields)
only = sorted(base_tpl_points.keys())

# new templates
tpls, fearure_size = create_templates(False, base_tpl_points)

x_train = dataset[fields]
y_train = dataset.number.astype("int")
forest_model = RandomForestClassifier(**classifier_params)
forest_model.fit(x_train, y_train)


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

    img_m, _ = prepare_image(img)
    features = np.zeros((fearure_size, ))

    i = 0
    for tpl_num, tpl in tpls:
        num_fearure = templates_scores(img_m, tpl)
        for val in num_fearure:
            features[i] = val
            i += 1

    plt.imshow(img_m, interpolation="nearest", cmap="gray")
    if features is None:
        plt.title(
            f"Bad image: {img_m.shape}"
        )
        continue
    else:
        result = forest_model.predict([features])
        plt.title(
            f"Prepared image: {img_m.shape} features: {len(features)} "
            f"predict: {result}"
        )

    plt.show(block=True)
