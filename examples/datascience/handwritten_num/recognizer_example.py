# An example with sklearn random forest classifier.
# run as:
# python ./recognizer_example.py ./data/a_dsta_set_1000_8_0.csv
# RangeIndex: 9663 entries, 0 to 9662
# Data columns (total 50 columns):
# Unnamed: 0            9663 non-null int64
# center_distance1      9663 non-null float64
# line_a1               9663 non-null float64
# center_distance_a1    9663 non-null float64
# line_b1               9663 non-null float64
# center_distance_b1    9663 non-null float64
# angle1                9663 non-null float64
# ...
# angle7                9663 non-null float64
# center_distance8      9663 non-null float64
# line_a8               9663 non-null float64
# center_distance_a8    9663 non-null float64
# line_b8               9663 non-null float64
# center_distance_b8    9663 non-null float64
# angle8                9663 non-null float64
# number                9663 non-null float64
# dtypes: float64(49), int64(1)
# memory usage: 3.7 MB
#
# This dataset built by create.py on MNIST database of handwritten digits. In ipython:
# # I advise to build Cython implementation first (see code of create.py).
# from create import create_df
# df = create_df("/<path to MNIST project (cloned from github)>/", features_count=5, limit_group_size=800, random_sort=True)
# # after ~2 minutes
# df.to_csv("./data/a_dsta_set_1500_5_01.csv ", index=False)
#
# Result in the dataset:
# AUC for '0': 97.532%
# AUC for '1': 98.579%
# AUC for '2': 97.45%
# AUC for '3': 95.16%
# AUC for '4': 93.731%
# AUC for '5': 94.938%
# AUC for '6': 94.642%
# AUC for '7': 97.442%
# AUC for '8': 92.144%
# AUC for '9': 94.12%


import sys

import numpy as np
import pandas as pd
from scipy.stats import boxcox
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

classifier_params = dict(
    n_estimators=500,
    max_depth=140,
    n_jobs=1,
    warm_start=True,
    verbose=1
)
fields = []
random_state = 77


def get_one_feature_model(
    data_set: pd.DataFrame, feature: int, **options
) -> (RandomForestClassifier, float):
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
    rand = np.random.RandomState(random_state)
    sub_dataset.insert(0, "rand", rand.random(len(sub_dataset)))
    sub_dataset.sort_values(by="rand", inplace=True)
    del sub_dataset["rand"]

    train = sub_dataset.sample(frac=0.9, random_state=random_state)
    test = sub_dataset.drop(train.index)
    y_test = test.number.astype("int")
    y_train = train.number.astype("int")

    x_train = train[fields]
    x_test = test[fields]
    # normalization with boxcox
    for field in fields:
        feature_set = x_train[field]
        skew = round(feature_set.skew(), 3)
        if abs(skew) > 0.1:
            under_zero = (feature_set == 0).sum()
            assert under_zero == 0, f"0 in {field}"
            x_train[field], ratio = boxcox(feature_set)
            new_skew = round(x_train[field].skew(), 3)
            x_test[field] = boxcox(x_test[field], ratio)
            print(
                f"For '{feature}' in '{field}' skew: {skew} -> "
                f"{new_skew} Box-Cox ratio: {ratio}"
            )

    params = classifier_params.copy()
    params.update(options)
    forest_model = RandomForestClassifier(**params)
    forest_model.fit(x_train, y_train)
    test_result = forest_model.predict_proba(x_test)
    value = roc_auc_score(y_test, test_result[:, 1])
    return forest_model, value


example_dataset = pd.read_csv(sys.argv[1])
print(example_dataset.info())
for field in set(example_dataset.columns.values):
    if "number" in field:
        continue
    if "Unnamed" in field:
        continue

    fields.append(field)

values = []
for num in range(10):
    _, auc_value = get_one_feature_model(example_dataset, num)
    values.append((num, round(auc_value * 100, 3)))

for num, auc_value in values:
    print(f"AUC for '{num}': {auc_value}%")
