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

from classifier_test import open_dataset
from classifier_test import num_and_name_field_sort
from classifier_test import roc_auc_score_all
from classifier_test import regexp_note_field

from create_notes_data import BEAT_COUNT
from create_notes_data import NOTE_IN_BEAT_COUNT
from create_notes_data import NOTE_FIELDS


def reshape_dataset(dataset: pd.DataFrame, fields: list) -> np.array:
    """Source dataset to 3D view.
    """
    note_fields = []
    for field in fields:
        if regexp_note_field.search(field):
            note_fields.append(field)

    n = len(dataset)
    m = len(NOTE_FIELDS)
    common_fields = [
        "tempo",
        "instrument",
        "volume",
        "balance",
        "ppqn_duration",
        "measure_index",
    ]
    # dimension of position in time
    k = BEAT_COUNT * NOTE_IN_BEAT_COUNT
    data = np.zeros((n, k + 1, m))
    note_fields.sort(key=num_and_name_field_sort)
    data[:, 1:, :] = np.reshape(
        dataset[note_fields].values, (n, k, m)
    )
    data[:, 0, :len(common_fields)] = dataset[common_fields].values

    return data


def run_test(
    path: str,
    sample_rate: float = 0.85,
    random_state: float = 101,
    epochs: int = 4,
    **hyperparameters
):
    """ANN classifier of instrument by notes.
    """
    start_time = monotonic()
    dataset, fields = open_dataset(path)
    gc.collect()
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
    _, time_dimension, features_dimension = x_train.shape

    print(
        f"Dataset train shape: {x_train.shape} prepared:",
        monotonic() - start_time,
        "sec."
    )
    model = Sequential([
        LSTM(32, return_sequences=True, input_shape=(time_dimension, features_dimension)),  # noqa
        LSTM(32, return_sequences=True),
        LSTM(32),
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
