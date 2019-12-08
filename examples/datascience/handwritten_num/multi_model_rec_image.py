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
    n_estimators=400,
    max_depth=44,
    n_jobs=1
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


def get_one_feature_model(
    data_set: pd.DataFrame, feature: int, **options
) -> RandomForestClassifier:
    """Model of binary classification for one class.
    """
    in_class_dataset = data_set[data_set.number == feature]
    size = len(in_class_dataset)
    out_class_dataset = data_set.drop(in_class_dataset.index)
    sub_dataset = out_class_dataset.sample(
        frac=round(size / len(out_class_dataset), 2),
        random_state=random_state
    )
    sub_dataset.number = 0
    in_class_dataset.number = 1
    sub_dataset = sub_dataset.append(in_class_dataset)

    x_train = sub_dataset[fields]
    y_train = sub_dataset.number.astype("int")

    params = classifier_params.copy()
    params.update(options)
    forest_model = RandomForestClassifier(
        random_state=random_state, **params
    )
    forest_model.fit(x_train, y_train)

    return forest_model


models = {}
for num in range(10):
    models[num] = get_one_feature_model(dataset, num)


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
        result = []
        best_results = []
        for number, forest_model in models.items():
            res = forest_model.predict_proba([features])
            (_, is_num), *_ = res
            best_results.append((is_num, number))
            result.append((number, *res))
            print(number, ":", res)

        best_results.sort()
        *_, (_, this_num) = best_results
        plt.title(
            f"Prepared image: {img_m.shape} features: {len(features)} "
            f"predict: {this_num}"
        )
        plt.show(block=True)
