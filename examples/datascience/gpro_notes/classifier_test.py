# classification of instruments by notes from dataset
import gc
import re
import typing

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

regexp_note_field = re.compile(r"b([0-9]+)_n([0-9]+)_([\w]+)")


def num_and_name_field_sort(field: str) -> typing.Tuple[int, int, str]:
    beat = note = 0
    name = ""
    r_search = regexp_note_field.search(field)
    if r_search:
        beat, note, name = r_search.groups()
        beat = int(beat)
        note = int(note)

    return (beat, note, name)


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
    relevance_limit_percent: float = 0.5,
    with_names: bool = False
) -> typing.Tuple[pd.DataFrame, typing.List[str]]:
    """Notes and volume.
    """
    data = pd.read_csv(path, sep=";", error_bad_lines=False)
    main_fields = []
    data.insert(0, "rand", np.random.random(len(data)))
    data.sort_values(["rand"], inplace=True)

    for field in data.columns:
        if regexp_note_field.search(field):
            main_fields.append(field)

    n = len(data)
    print(f"Dataset size {n}")

    main_fields.sort(key=num_and_name_field_sort)
    fields = [
        "instrument",
        "tempo",
        "volume",
        "balance",
        "ppqn_duration",
        "measure_index",
        *main_fields
    ]
    if with_names:
        fields.insert(0, "name")
        fields.insert(0, "artist")

    result: pd.DataFrame = data[fields].copy()
    for field in (
        "volume", "tempo", "balance", "ppqn_duration", "measure_index", *main_fields  # noqa
    ):
        # #
        try:
            result[field] = result[field].astype(float)
        except Exception as err:
            raise TypeError(f"In field {field}: {err}")

    result.instrument = result.instrument.astype(int)

    return result, fields


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
