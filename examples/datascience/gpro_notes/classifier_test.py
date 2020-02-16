# classification of instruments by notes from dataset
import gc
import re
import typing

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

regexp_note_field = re.compile(r"n([0-9]+)_([\w]+)")


def num_and_name_field_sort(field: str) -> tuple:
    index = 0
    name = ""
    r_search = regexp_note_field.search(field)
    if r_search:
        index, name = r_search.groups()
        index = int(index)

    return (index, name)


def roc_auc_score_all(
    result: pd.Series,
    predicted: np.array,
    average: str = "macro"
):
    unique = result.unique()
    other_cls = set()
    unique.sort()

    for cls_name in unique:
        other_cls.update(val for val in unique if val != cls_name)
        view_result = [int(val not in other_cls) for val in result]
        view_predicted = [int(val not in other_cls) for val in predicted]
        auc = roc_auc_score(view_result, view_predicted, average=average)
        print(f"ROC-AUC for {cls_name}:", auc)
        view_result.clear()
        view_predicted.clear()
        other_cls.clear()


def open_dataset(
    path: str,
    relevance_limit_percent: float = 0.5
) -> typing.Tuple[pd.DataFrame, typing.List[str]]:
    """Notes and volume.
    """
    data = pd.read_csv(path, sep=";", error_bad_lines=False)
    fields = []
    data.insert(0, "rand", np.random.random(len(data)))
    data.sort_values(["rand"], inplace=True)

    fields_class = set()
    for field in data.columns:
        if regexp_note_field.search(field):
            fields.append(field)
            *_, cls_name = field.split("_")
            fields_class.add(cls_name)

    # search useless zero-features.
    fields_class = sorted(fields_class)
    zero_fields = set()
    n = len(data)
    print(f"Dataset size {n}")

    for field in fields_class:
        part_fields = [
            field_value
            for field_value in fields
            if f"_{field}" in field_value
        ]
        no_zero_percent = (data[part_fields] != 0).sum().sum() / n * 100
        if no_zero_percent < relevance_limit_percent:
            print(f"Useless fields 'n[i..n]_{field}'")
            zero_fields.update(part_fields)

    fields = list(set(fields) - zero_fields)
    fields.sort(key=num_and_name_field_sort)
    fields = [
        "instrument",
        "tempo",
        "volume",
        "balance",
        "ppqn_duration",
        *fields
    ]
    result = data[fields].copy(), fields

    return result


def run_test(
    path: str,
    sample_rate: float = 0.85,
    random_state: float = 101,
    **hyperparameters
):
    """Classification of instruments by notes from dataset.
    """
    dataset, fields = open_dataset(path)
    gc.collect()
    dataset.instrument = dataset.instrument.astype("int")
    train = dataset.sample(frac=sample_rate, random_state=random_state)
    test = dataset.drop(train.index)
    y_test = test.instrument
    y_train = train.instrument
    x_train = train[fields]
    x_test = test[fields]
    # defult
    params = dict(
        n_estimators=300,
        max_depth=20,
        n_jobs=1,
        warm_start=True,
        verbose=1
    )
    params.update(hyperparameters)
    forest_model = RandomForestClassifier(**params)
    forest_model.fit(x_train, y_train)
    predicted = forest_model.predict(x_test)
    roc_auc_score_all(y_test, predicted)
