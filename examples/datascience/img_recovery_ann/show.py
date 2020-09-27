import sys

from dataset_api import check_dataset

_, low_path, high_path, *other = sys.argv

params = dict(low_path=low_path, high_path=high_path)

try:
    count, *_ = other
    count = int(count)
except Exception:
    pass
else:
    print(f"Search {count} random rows")
    params["count"] = count


check_dataset(**params)
