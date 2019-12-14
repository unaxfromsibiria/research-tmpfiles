# 1) creation of dataset
# from ann_numbers.create import create_df
# df = create_df("/home/dir/with/mnist", limit_group_size=1500)
# Good: 14991 Bad: 0 exec time 0.0 min 29 sec time per image 0.002
# df.to_csv("/home/my/datasets_dir/a_dsta_set_28x28_1500_01.csv", index=False)
# 2) using
# python ./recognizer_ann_example.py /home/my/datasets_dir/a_dsta_set_28x28_1500_01.csv
# loss 0.25481912520682604 accuracy 0.9337779879570007
# AUC for '0.0': 98.3%
# AUC for '1.0': 98.8%
# AUC for '2.0': 98.7%
# AUC for '3.0': 96.1%
# AUC for '4.0': 97.8%
# AUC for '5.0': 96.1%
# AUC for '6.0': 94.9%
# AUC for '7.0': 96.3%
# AUC for '8.0': 94.3%
# AUC for '9.0': 95.2%

import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from ann_numbers.create import create_model

example_dataset = pd.read_csv(sys.argv[1])
print(example_dataset.info())

values = []
model, x_data, y_data = create_model(example_dataset)
loss, accuracy = model.evaluate(x_data, y_data, verbose=2)
print("loss", loss, "accuracy", accuracy)

predict_data = model.predict(x_data)
predicted = np.argmax(predict_data, axis=1)


for num in sorted(example_dataset.number.unique()):
    true_num = np.round(y_data == num)
    predicted_num = np.round(predicted == num)
    auc_value = np.round(roc_auc_score(true_num, predicted_num) * 100, 1)
    print(f"AUC for '{num}': {auc_value}%")
