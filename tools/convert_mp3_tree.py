# run as:
# python convert_mp3_tree.py media/music/Iron\ Maiden/ media/music/all_files
# python convert_mp3_tree.py media/music/Nightwish/ media/music/all_files 20

import os
import sys
import re
import typing


def clear_path(
    path: str,
    replace_parts: typing.List[typing.Tuple[str, str]] = [
        (" ", "\\ "),
        ("(", "\\("),
        (")", "\\)"),
    ]
) -> str:
    """Format to cli file path.
    """
    for item in replace_parts:
        path = path.replace(*item)

    return path


bitrate_class = 5
# lame option	Average kbit/s	Bitrate range kbit/s	ffmpeg option
# -b 320	320	320 CBR (non VBR) example	-b:a 320k (NB this is 32KB/s, or its max)
# -V 0	245	220-260	-q:a 0 (NB this is VBR from 22 to 26 KB/s)
# -V 1	225	190-250	-q:a 1
# -V 2	190	170-210	-q:a 2
# -V 3	175	150-195	-q:a 3
# -V 4	165	140-185	-q:a 4
# -V 5	130	120-150	-q:a 5
# -V 6	115	100-130	-q:a 6
# -V 7	100	80-120	-q:a 7
# -V 8	85	70-105	-q:a 8
# -V 9	65	45-85	-q:a 9

nums_rx = re.compile(r"\d+")
bad_ch_rx = re.compile(r"[)('`]+")
_, src_path, res_path, *other = sys.argv

input_formats = [
    "m4a", "mp3", "flac", "aac", "alac"
]

cmd_tmp = "ffmpeg -i {} -codec:a libmp3lame -qscale:a {} {}"  # -ar 44100
input_formats = set(map(".{}".format, input_formats))
albums = {}

albums_index = count = res_file_size = src_file_size = 0
if other:
    start_index, *_ = other
    albums_index = int(start_index) - 1

all_tree = sorted(
    (root, name)
    for root, _, files in os.walk(src_path, topdown=False)
    for name in files
    if any(ext in name for ext in input_formats)
)

for root, name in all_tree:
    if root in albums:
        index, prefix = albums[root]
    else:
        albums_index += 1
        index = albums_index
        sub_path = root.replace(src_path, "")
        nums = " ".join(nums_rx.findall(sub_path))
        prefix = f"{index:0>3} {nums}"
        albums[root] = index, prefix

    new_name = " ".join(name.lower().split(" "))
    *parts, _ = new_name.split(".")
    new_name = " ".join(parts)
    new_name = f"{prefix}_{new_name}"
    new_name = "_".join(bad_ch_rx.split(new_name))
    new_name = f"{new_name}.mp3".replace("  ", " ")
    res_file = os.path.join(res_path, f"{prefix}_{new_name}")
    src = os.path.join(root, name)
    cmd = cmd_tmp.format(
        clear_path(src), bitrate_class, clear_path(res_file)
    )
    print("---------------------------------\n", name, "->", new_name)
    os.system(cmd)
    count += 1
    src_file_size += int(os.path.getsize(src) or 0)
    try:
        res_file_size += int(os.path.getsize(res_file) or 0)
    except Exception:
        continue

print(
    f"files count: {count}\n"
    f"source files size: {src_file_size / 1048576:.2f} mb\n"
    f"result files size: {res_file_size / 1048576:.2f} mb\n"
    "albums (max index {}):\n{}\n".format(
        albums_index,
        "\n".join(map(" {}".format, albums))
    )
)
