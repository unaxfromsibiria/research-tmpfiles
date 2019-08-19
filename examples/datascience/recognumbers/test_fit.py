import sys
import ujson
import numpy as np
from sklearn.svm import SVC

size = int(sys.argv[1])

assert 12 <= size <= 512
assert size % 2 == 0

dataset_path = sys.argv[2]


with open(dataset_path) as datafile:
    data = [
        item for item in ujson.loads(datafile.read())
        if len(item) == size + 1
    ]

n = len(data)

m = int(n * 0.99)

print("Dataset size:", n)
print("Fit by rows:", m)

numbers = [data[i][0] for i in range(m)]

data_set = np.zeros((m, size))

for i in range(m):
    for j in range(size):
        data_set[i, j] = data[i][j + 1]


model = SVC(
    kernel="rbf",
    random_state=0,
    decision_function_shape="ovr",
    tol=0.01,
    gamma=0.09,
    C=50
)

model.fit(data_set, numbers)

k = 100
test_index = m + 10
test = np.zeros((k, size))
errors = 0

for i in range(size):
    for j in range(k):
        test[j, i] = data[test_index + j][i + 1]

res = model.predict(test)

for j in range(k):
    print(res[j], "=", data[test_index + j][0], "?")
    if res[j] != data[test_index + j][0]:
        errors += 1

print("Errors:", errors, "({}%)".format(np.round(100 * errors / k)))
