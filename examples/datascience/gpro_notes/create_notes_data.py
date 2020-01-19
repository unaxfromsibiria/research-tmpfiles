# # #
#
# Script to generate CSV file with dataset contains music notes
# from all found GuitarPro files *.gp[3-4] (by default).
# Check how many files you have with:
# $ find /<full path>/gp_files/ -name '*.gp[3-4]' | wc -l
#
# # #

import asyncio
import gc
import itertools
import os
import re
import time
import typing

import guitarpro
import pandas as pd

word_re = re.compile(r"\s+")
# MIDI accuracy?
GROUP_PPQN_DURATION = 960 * 4 * 30
# notes in one futeres row (probably it will change to less)
NOTE_COUNT = 180
DEBUG = False  # to see asyncio mode

NOTE_PROPERTY = (
    "isBend",
    "isHarmonic",
    "isGrace",
    "isTrill",
    "isTremoloPicking",
    "isFingering",
)

NOTE_FIELDS = (
    "type",
    "value",
    "string",
    "duration",
    "swap",
    "bend",
    "harmonic",
    "grace",
    "trill",
    "tremoloPicking",
    "fingering",
)

COMMON_FIELDS = (
    "artist",
    "name",
    "tempo",
    "instrument",
    "volume",
    "balance",
    "ppqn_duration",
    "notes",
    "parts",
)

FORMATS = ("gp4", "gp5", "gp3")


def title_format(text: str) -> str:
    return "_".join(
        word_re.split(text.lower())
    ).replace("(", "").replace(")", "").strip("_")


def search_gpro_files(
    base_path: str, ext_list: tuple = FORMATS
) -> typing.Generator[str, None, None]:
    """Walk and search correct file path.
    """
    for root, dirs, files in os.walk(base_path, topdown=False):
        for file_path in files:
            *_, ext = os.path.splitext(file_path)
            ext = ext.replace(".", "").lower()
            if ext in ext_list:
                yield os.path.join(root, file_path)


def note_features(note: guitarpro.Note) -> tuple:
    """Return note data as [
        type,
        value,
        string,
        duration percent,
        swap accidentals,
        is bend,
        is harmonic,
        is grace,
        is trill,
        is tremoloPicking,
        is fingering,
    ]
    """
    return (
        note.type.value,
        note.value,
        note.string,
        note.durationPercent,
        int(note.swapAccidentals),
        *(
            int(getattr(note.effect, prop)) for prop in NOTE_PROPERTY
        )
    )


def track_part(file_path: str) -> typing.Generator[tuple, None, None]:
    """Notes by parts as rows.
    """
    try:
        gpro = guitarpro.parse(file_path)
    except Exception as err:
        print(f"File '{file_path}' error: {err}")
    else:
        artist = title_format(gpro.artist)
        name = title_format(gpro.title)

        for track in gpro.tracks:
            if track.isMute:
                continue

            track_name = track.name.lower()

            if "vocal" in track_name or "voice" in track_name:
                continue

            instrument = track.channel.instrument
            volume = track.channel.volume
            balance = track.channel.balance
            total_duration = 0
            note_groups = [[]]
            group_index = 0
            duration = 0
            n_count = 0

            for measure in track.measures:
                m_n = measure.header.length
                duration += m_n
                total_duration += m_n
                if duration > GROUP_PPQN_DURATION:
                    duration = m_n
                    note_groups.append([])
                    group_index += 1

                for voice in measure.voices:
                    for beat in voice.beats:
                        for note in beat.notes:
                            n_count += 1
                            note_groups[group_index].append(
                                note_features(note)
                            )

            for group in note_groups:
                n = len(group)
                if n < NOTE_COUNT:
                    continue

                for index in range(n // NOTE_COUNT):
                    notes = group[index * NOTE_COUNT:(index + 1) * NOTE_COUNT]
                    if len(notes) < NOTE_COUNT:
                        continue

                    yield (
                        artist,
                        name,
                        gpro.tempo,
                        instrument,
                        volume,
                        balance,
                        total_duration,
                        n_count,
                        len(group),
                        *itertools.chain(*notes),
                    )


def read_notes_create(
    base_path: str, limit: int = 0
) -> typing.Generator[tuple, None, None]:
    """All notes.
    """
    skip_count = 0
    track_count = 0
    file_count = 0
    for file_path in search_gpro_files(base_path):
        yield from track_part(file_path)
        file_count += 1
        if limit and file_count > limit:
            break

        gc.collect()

    print(f"Skip: {skip_count} track count: {track_count}")


def create(base_path: str, n: int = 0) -> pd.DataFrame:
    """Create dataset.
    WARNING overloading ram.
    """
    fields = []
    for index in range(NOTE_COUNT):
        fields.extend(f"n{index + 1}_{field}" for field in NOTE_FIELDS)

    data = pd.DataFrame(
        read_notes_create(base_path, n),
        columns=[*COMMON_FIELDS, *fields]
    )
    return data


async def record_csv_file(
    csv_file: str, result_queue: asyncio.Queue, workers: int
):
    """Save rows from queue.
    """
    fields = list(COMMON_FIELDS)
    for index in range(NOTE_COUNT):
        fields.extend(f"n{index + 1}_{field}" for field in NOTE_FIELDS)

    count = 0
    done_worker = 0
    with open(csv_file, "a") as out_file:
        line = f"{';'.join(fields)}\n"
        out_file.write(line)
        if DEBUG:
            print(f"In file {csv_file} header {line}")

        while done_worker < workers:
            row = await result_queue.get()
            if row:
                line = f"{';'.join(map(str, row))}\n"
                out_file.write(line)
                count += 1
                if DEBUG:
                    if count % 10 == 0:
                        print(f"{count} lines in file")

            else:
                done_worker += 1

            result_queue.task_done()

    print(f"In file {count} lines")


async def read_gp_worker(
    index: int,
    queue: asyncio.Queue,
    result_queue: asyncio.Queue
):
    """Parce file worker.
    """
    print(f"worker {index} started")
    file_path = await queue.get()
    part_total = 0
    while file_path:
        parts = 0
        for row in track_part(file_path):
            result_queue.put_nowait(row)
            parts += 1

        part_total += parts
        queue.task_done()

        if DEBUG:
            print(f"in worker {index} from {file_path} parts: {parts}")

        file_path = await queue.get()
        await asyncio.sleep(0)

    print(f"worker {index} parts processed {part_total}")
    result_queue.put_nowait(False)


async def input_files_queue(
    base_path: str,
    queue: asyncio.Queue,
    workers: int,
    ext_list: tuple = FORMATS,
    limit: int = 0
):
    count = 0
    for file_path in search_gpro_files(base_path, ext_list):
        count += 1
        if limit == 0 or count < limit:
            await queue.put(file_path)
        else:
            break

    for _ in range(workers):
        queue.put_nowait(False)

    print("Search files count:", count)


async def run_async_create_csv(
    base_path: str, csv_file: str, file_count_limit: int = 0, workers: int = 4
):
    """Read and create csv.
    """

    in_queue = asyncio.Queue()
    out_queue = asyncio.Queue()
    tasks = [record_csv_file(csv_file, out_queue, workers)]
    for i in range(workers):
        tasks.append(read_gp_worker(i + 1, in_queue, out_queue))

    tasks.append(
        input_files_queue(base_path, in_queue, workers, limit=file_count_limit)
    )
    await asyncio.gather(*tasks)


# # to use this methods in ipython (python) # #


def create_csv_file(
    base_path: str, csv_file: str, file_count_limit: int = 0
) -> int:
    """Record csv. Default method.
    """
    start_time = time.monotonic()
    fields = list(COMMON_FIELDS)
    for index in range(NOTE_COUNT):
        fields.extend(f"n{index + 1}_{field}" for field in NOTE_FIELDS)

    with open(csv_file, "a") as out_file:
        line = f"{';'.join(fields)}\n"
        out_file.write(line)
        for row in read_notes_create(base_path, file_count_limit):
            line = f"{';'.join(map(str, row))}\n"
            out_file.write(line)

    print("Time: ", time.monotonic() - start_time)


def async_create_csv(base_path: str, csv_file: str, file_count_limit: int = 0):
    """Main files processing method:
    from create_notes_data import async_create_csv
    async_create_csv("/gp_files/", "/tmp/notes_set_120_10_1.csv", 100)
    base_path - guitar pro files
    csv_file - new data set file (possible a huge file)
    """
    start_time = time.monotonic()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        run_async_create_csv(base_path, csv_file, file_count_limit)
    )
    print("Time: ", time.monotonic() - start_time)
