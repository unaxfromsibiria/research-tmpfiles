import sys

from dataset_api import create_dataset

_, source_dir, target_dir, dataset_dir, *other = sys.argv

params = dict(
    source_dir=source_dir,
    target_dir=target_dir,
    dataset_dir=dataset_dir
)

try:
    rows_limit, *_ = other
    rows_limit = int(rows_limit)
except Exception:
    pass
else:
    print("Rows limit:", rows_limit)
    params["rows_limit"] = rows_limit

try:
    _, core_size = other
    core_size = int(core_size)
except Exception:
    pass
else:
    print(f"Core size {core_size}x{core_size}")
    params["core_size"] = core_size


good_path, bad_path = create_dataset(**params)

print(
    f"Dataset high quality: {good_path}\n"
    f"and low quality: {bad_path}"
)
