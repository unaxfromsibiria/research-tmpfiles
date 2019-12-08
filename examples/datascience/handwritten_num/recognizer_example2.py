
import sys

import numpy as np
import pandas as pd
from scipy.stats import boxcox
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

classifier_params = dict(
    n_estimators=400,
    max_depth=30,
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

    params = classifier_params.copy()
    params.update(options)
    forest_model = RandomForestClassifier(**params)
    forest_model.fit(x_train, y_train)
    test_result = forest_model.predict_proba(x_test)
    value = roc_auc_score(y_test, test_result[:, 1])
    return forest_model, value


example_dataset = pd.read_csv(sys.argv[1])
print(example_dataset.info())
numbers = set()
for field in set(example_dataset.columns.values):
    if "number" in field:
        continue

    _, num, *_ = field.split("_")
    numbers.add(int(num))
    fields.append(field)

numbers = sorted(numbers)
values = []
for num in numbers:
    _, auc_value = get_one_feature_model(example_dataset, num)
    values.append((num, round(auc_value * 100, 3)))

for num, auc_value in values:
    print(f"AUC for '{num}': {auc_value}%")
