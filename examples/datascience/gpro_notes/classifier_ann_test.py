import gc
import os
import re
from collections import defaultdict
from collections.abc import Iterable
from time import monotonic

import numpy as np
import pandas as pd
from keras import Sequential
from keras.layers import LSTM, Dense

from classifier_test import open_dataset, roc_auc_score_all

num_search = re.compile(r"n(\d+)_(\w+)")


def reshape_dataset(dataset: pd.DataFrame, fields: list) -> np.array:
    """Source dataset to view with origin sequence.
    """
    note_fields = []
    track_fields = []
    numbers = []

    for field in fields:
        search = num_search.search(field)
        if search:
            index, field_name = num_search.search(field).groups()
            index = int(index)
            if index not in numbers:
                numbers.append(index)

            if field_name not in note_fields:
                note_fields.append(field_name)
        else:
            track_fields.append(field)

    track_fields.sort()
    note_fields.sort()
    numbers.sort()
    n = len(dataset)
    k = len(note_fields)
    m = (len(fields) - len(track_fields)) // k
    assert m == len(numbers)

    data = np.zeros((n, m + 1, k))
    for index in numbers:
        point_fields = [
            f"n{index}_{note_field}" for note_field in note_fields
        ]
        data[:, index, :] = dataset[point_fields].values

    data[:, 0, :len(track_fields)] = dataset[track_fields].values

    return data


def run_test(
    path: str,
    sample_rate: float = 0.85,
    random_state: float = 101,
    epochs: int = 20,
    **hyperparameters
):
    """ANN classifier of instrument by notes.
    """
    start_time = monotonic()
    dataset, fields = open_dataset(path)
    gc.collect()
    dataset.instrument = dataset.instrument.astype("int")
    instruments = dataset.instrument.unique()
    instruments.sort()
    instrument_index = {
        instrument: index for index, instrument in enumerate(instruments)
    }
    dataset.insert(
        0, "instrument_index", dataset.instrument.map(instrument_index)
    )
    train = dataset.sample(frac=sample_rate, random_state=random_state)
    test = dataset.drop(train.index)
    y_test = test.instrument_index
    y_train = train.instrument_index
    x_train = reshape_dataset(train[fields], fields)
    x_test = reshape_dataset(test[fields], fields)

    cls_count = len(instrument_index)
    _, note_count, features_count = x_train.shape

    print(
        f"Dataset train shape: {x_train.shape} prepared:",
        monotonic() - start_time,
        "sec."
    )
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(note_count, features_count)),  # noqa
        LSTM(64, return_sequences=True),
        LSTM(64),
        Dense(cls_count * 2),
        Dense(cls_count, activation="softmax")
    ])
    model.compile(
        loss="sparse_categorical_crossentropy",
        optimizer="rmsprop",
        metrics=["accuracy"]
    )

    model.fit(x_train, y_train.values, epochs=epochs, batch_size=128)
    predict_data = model.predict(x_test)
    predicted = np.argmax(predict_data, axis=1)
    real_data = pd.Series(
        instruments[index] for index in y_test
    )
    result = [instruments[index] for index in predicted]

    roc_auc_score_all(real_data, result)
