import sys

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from PIL import Image

try:
    from num_path_opti.num_path_dataset import find_angle_features
except ImportError as err:
    print("Not available cython implementation:", err)
    from num_path_base.num_path_dataset import find_angle_features
    from num_path_base.num_path_dataset import prepare_image
else:
    from num_path_opti.num_path_dataset import prepare_image
    from num_path_opti.num_path_dataset import ONE_FEATURE_COUNT


classifier_params = dict(
    n_estimators=800,
    max_depth=180,
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

features_count = len(fields) // ONE_FEATURE_COUNT

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

    img_m = prepare_image(img)
    features = find_angle_features(img_m, result_size=features_count)
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
