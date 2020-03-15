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
import sys
import time
import numpy as np
import typing

import guitarpro
import pandas as pd
from guitarpro.models import Measure, Voice, NoteEffect, SlideType, NoteType

word_re = re.compile(r"\s+")
# MIDI accuracy?
GROUP_PPQN_DURATION: int = 960 * 4 * 30
# notes in one futeres row (probably it will change to less)
NOTE_IN_BEAT_COUNT: int = 7
BEAT_COUNT: int = 280  # 175
MIN_TOTAL_BEAT_COUNT: int = 32
DEBUG: bool = False  # to see asyncio mode

NOTE_MAX_STRING: int = 7
NOTE_TYPE_SIZE: int = max(
    NoteType.dead.value,
    NoteType.normal.value,
    NoteType.rest.value,
    NoteType.tie.value
)

trill_values = (
    (21, 32),
    (9, 16),
    (-np.inf, -np.inf),
)

slide_values = {
    SlideType.none: 0,
    SlideType.intoFromAbove: 1,
    SlideType.intoFromBelow: 2,
    SlideType.shiftSlideTo: 3,
    SlideType.legatoSlideTo: 4,
    SlideType.outDownwards: 5,
    SlideType.outUpwards: 6,
}


def extract_harmonic(effect: NoteEffect) -> float:
    """Type of harmonic effect
    """
    return effect.harmonic.type


def extract_zero_effect(effect: NoteEffect) -> float:
    """Type of harmonic effect
    """
    return 0


def extract_is_exists_effect(effect: NoteEffect) -> float:
    """Only is use effect or no.
    """
    return 1


def extract_slide_effect(effect: NoteEffect) -> float:
    """Slide type of first slide.
    """
    slide, *_ = effect.slides
    return slide_values[slide]


def extract_trill_intensity(effect: NoteEffect) -> int:
    """Only as possible combinations.
    TrillEffect(fret=14, duration=Duration(value=32, isDotted=False, isDoubleDotted=False, tuplet=Tuplet(enters=1, times=1)))
    """
    fret = effect.trill.fret
    duration = effect.trill.duration.value
    # research
    print(f"trill {fret} {duration}")

    return next(
        i for i, (in_fret, in_dur) in enumerate(trill_values, 1)
        if fret >= in_fret and duration >= in_dur
    )


NOTE_PROPERTY: tuple = (
    ("hammer", extract_is_exists_effect),
    ("vibrato", extract_is_exists_effect),
    # complex
    ("isGrace", extract_is_exists_effect),
    ("isBend", extract_is_exists_effect),
    ("isTrill", extract_trill_intensity),
    ("isTremoloPicking", extract_is_exists_effect),
    ("isFingering", extract_is_exists_effect),
    ("isHarmonic", extract_harmonic),
    ("slides", extract_slide_effect),
)

NOTE_FIELDS: tuple = (
    "value",
    "string",
    "type",
    "duration",
    "swap",
    "hammer",
    "vibrato",
    "grace",
    "bend",
    "trill",
    "tremoloPicking",
    "fingering",
    "harmonic",
    "slides",
)

NOTE_VIEW_FIELDS: tuple = (
    "string",
    "type",
    "value_rate",
    "comb_feature",
)

COMMON_FIELDS: tuple = (
    "artist",
    "name",
    "tempo",
    "instrument",
    "volume",
    "balance",
    "ppqn_duration",
    "measure_count",
    "measure_occupancy",
)

FORMATS: tuple = ("gp4", "gp5", "gp3")


combination_index: typing.Dict[tuple, float] = {
    (i_dur, i_swap, i_ham, i_vib, i_gr, i_bend, i_trill, i_tr, i_fing, i_har, i_sl): 0  # noqa
    # duration
    for i_dur in (0, 1)
    # swap
    for i_swap in (0, 1)
    # hammer
    for i_ham in (0, 1)
    # vibrato
    for i_vib in (0, 1)
    # grace
    for i_gr in (0, 1)
    # bend
    for i_bend in (0, 1)
    # trill
    for i_trill in range(0, len(trill_values) + 1)
    # tremoloPicking
    for i_tr in (0, 1)
    # fingering
    for i_fing in (0, 1)
    # harmonic
    for i_har in range(0, 6)
    # slides
    for i_sl in range(0, 7)
}

print("Note combinations", len(combination_index))


for i, combination in enumerate(sorted(combination_index.keys()), start=1):
    combination_index[combination] = i / len(combination_index)


def note_feature_combination(*note_feature: float) -> float:
    """Combination of note features as level.
    """
    combination = tuple(map(int, note_feature))
    return combination_index[combination]


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


def note_features(
    note: guitarpro.Note, max_value: int = 100
) -> typing.Tuple[float, float, float, float]:
    """Return note data (4 value) as NOTE_VIEW_FIELDS [
        value,
        string,
        type,
        combination(
            # + 10 features
            duration percent,
            swap accidentals,
            hammer,
            vibrato,
            is bend
            is grace,
            is trill,
            is tremoloPicking,
            is fingering,
            is harmonic,
            slides,
        )
    ]
    """
    if max_value < note.value:
        raise ValueError(f"Value of note {note.value}")

    string_ratio = note.string / NOTE_MAX_STRING
    if string_ratio > 1:
        raise ValueError(f"Note string value: {note.string}")

    return (
        note.value / max_value,
        string_ratio,
        note.type.value / NOTE_TYPE_SIZE,
        note_feature_combination(
            note.durationPercent,
            int(note.swapAccidentals),
            *(
                extract(note.effect)
                if getattr(note.effect, prop) else 0
                for prop, extract in NOTE_PROPERTY
            )
        )
    )


def get_main_voice(measure: Measure) -> Voice:
    """Voice with max notes count.
    """
    n = len(measure.voices)
    if n == 1:
        return measure.voices[0]

    counts = [0] * n
    for index, voice in enumerate(measure.voices):
        for beat in voice.beats:
            counts[index] += len(beat.notes)

    return measure.voices[counts.index(max(counts))]


def setup_fields(fields: typing.List[str]):
    """Notes field.
    """
    for b_index in range(BEAT_COUNT):
        for n_index in range(NOTE_IN_BEAT_COUNT):
            fields.extend(
                f"b{b_index}_n{n_index}_{field}" for field in NOTE_VIEW_FIELDS
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
            measure_count = len(track.measures)
            if measure_count < 1:
                continue

            duration = 0
            beat_index = measure_index = 0
            note_sapce: np.array = np.zeros(
                (BEAT_COUNT, NOTE_IN_BEAT_COUNT, len(NOTE_VIEW_FIELDS))
            )

            for measure in track.measures:
                m_n = measure.header.length
                duration += m_n

                voice = get_main_voice(measure)
                if voice is None:
                    continue

                empty_measure = True

                for beat in voice.beats:
                    beat_index += 1
                    beat_notes = beat.notes
                    if beat_notes:

                        if len(beat_notes) >= NOTE_IN_BEAT_COUNT:
                            print("many notes in beat", len(beat_notes))
                            continue

                        for n_index, note in enumerate(beat_notes):
                            notes_ch = note_features(note)
                            empty_measure = False

                            if beat_index >= BEAT_COUNT:
                                continue

                            # print(">> ", notes_ch)
                            note_sapce[beat_index, n_index, :] = notes_ch  # noqa

                if not empty_measure:
                    # not empty measure
                    measure_index += 1

            if beat_index >= MIN_TOTAL_BEAT_COUNT:
                yield (
                    artist,
                    name,
                    gpro.tempo,
                    instrument,
                    volume,
                    balance,
                    duration / measure_count,
                    measure_count,
                    measure_index / measure_count,
                    *(note_sapce.ravel()),
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
    setup_fields(fields)

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
    setup_fields(fields)

    count = 0
    done_worker = 0
    print("Fields count:", len(fields))

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
):
    """Record csv. Default method.
    """
    start_time = time.monotonic()
    fields = list(COMMON_FIELDS)
    setup_fields(fields)

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


def run():
    """Run from shell.
    python -c "from create_notes_data import run; run()" data/gp_files/ dataset/notes.csv
    """
    *_, path, csv_file_path = sys.argv
    print(
        "Search files from", path, "\n"
        "Save to file", csv_file_path,
    )
    async_create_csv(path, csv_file_path)
