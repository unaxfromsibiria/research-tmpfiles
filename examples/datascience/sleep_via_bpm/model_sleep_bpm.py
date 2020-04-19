import json
import numpy as np
import os
import random
import sys
import typing

import matplotlib.pyplot as plt
import pandas as pd

from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.layers import LSTM
from keras.layers import Bidirectional
from keras.layers import TimeDistributed

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["THEANO_FLAGS"] = "mode=FAST_RUN,device=gpu,floatX=float32"


def open_data_set(
    json_file_path: str,
    random_sort: bool = False
) -> typing.Tuple[int, int, np.array, np.array]:
    """Open prepared data set from json file.
    """
    data = []
    with open(json_file_path) as json_file:
        data.extend(json.loads(json_file.read()))

    n = len(data)
    assert n > 0, "Empity dataset"
    intervals_count = min(
        len(pulse)
        for pulse, sleep in data
        if len(pulse) == len(sleep)
    )
    if random_sort:
        data.sort(key=lambda _: random.random())

    x_data = np.zeros((n, intervals_count))
    y_data = np.zeros((n, intervals_count))
    for i, (pulse, sleep) in enumerate(data):
        x_data[i, :] = pulse[:intervals_count]
        y_data[i, :] = sleep[:intervals_count]

    return n, intervals_count, x_data, y_data


def create_model(unit_size: int, intervals_count: int) -> Sequential:
    model = Sequential([
        Bidirectional(
            LSTM(unit_size, input_shape=(intervals_count, 1), return_sequences=True),
            merge_mode="concat"
        ),
        Dropout(0.4),
        Bidirectional(
            LSTM(unit_size, return_sequences=True),
            merge_mode="sum"
        ),
        TimeDistributed(Dense(intervals_count, activation="softmax")),
    ])

    model.compile(
        optimizer="rmsprop",
        metrics=["accuracy"],
        loss="sparse_categorical_crossentropy"
    )
    return model


num_epochs = 30
train_sample_size = 98  # %

_, *params = sys.argv
dataset_path, *_ = params
try:
    _, num_epochs, *_ = params
    num_epochs = int(num_epochs)
except (ValueError, IndexError, TypeError):
    pass

n, m, data_x, data_y = open_data_set(dataset_path)
train_sample_n = int(n * train_sample_size / 100)
print(f"Data set size: {n} train data set: {train_sample_n}")

train_x = data_x[:train_sample_n, :]
train_y = data_y[:train_sample_n, :]

model = create_model(80, intervals_count=m)

history = model.fit(
    train_x.reshape(*(train_x.shape), 1),
    train_y.reshape(*(train_y.shape), 1),
    epochs=num_epochs,
    batch_size=128,
    callbacks=None,
    verbose=1
)

test_x = data_x[train_sample_n:, :]
test_y = data_y[train_sample_n:, :]

answer = model.predict_classes(test_x.reshape(*(test_x.shape), 1),)

for _ in range(20):
    a, _ = answer.shape
    i = random.randint(0, a)
    (
        pd.Series(test_x[i]).plot() and
        pd.Series(test_y[i]).plot() and
        pd.Series(answer[i]).plot() and
        plt.show(block=True)
    )
