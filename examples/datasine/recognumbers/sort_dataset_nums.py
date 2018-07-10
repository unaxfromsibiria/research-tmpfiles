
import random
import sys
import ujson

dataset_path = sys.argv[1]
out_path = sys.argv[2]


def sort_random(item) -> float:
    return random.random()


with open(dataset_path) as datafile:
    data = sorted(
        ujson.loads(datafile.read()), key=sort_random
    )
    n = len(data)
    print("Dataset size: ", n)
    with open(out_path, "w") as out_file:
        out_file.write(ujson.dumps(data))
