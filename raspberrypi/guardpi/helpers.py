import codecs
import json
import os
import random
import time
import uuid
from datetime import datetime
from os.path import join as path_join

from .const import (
    WORK_DIR, PHOTO_SERIES, IMAGE_SIZE, CAMERA_FRAMERATE, SENSOR_PIN)
from .log import get_logger
try:
    import picamera
except ImportError:
    picamera = None
try:
    import RPi.GPIO as gpio
except ImportError:
    gpio = None


def pin_on(pin: int):
    if gpio:
        gpio.output(pin, True)
    else:
        print("fake pin ON: ", pin)


def pin_off(pin: int):
    if gpio:
        gpio.output(pin, False)
    else:
        print("fake pin OFF: ", pin)


def pin_send(pin: int, value: bool):
    value = bool(value)
    if gpio:
        gpio.output(pin, value)
    else:
        print("fake pin ", pin, " to: ", value)


def find_images(current_dir: str="./", exts=("jpg", "png", "jpeg", "gif")):
    """Images files in dir.
    """
    for root, _, files in os.walk(current_dir):
        for file_name in files:
            ext = file_name.rsplit('.', 1)[-1].lower()
            if ext in exts:
                yield path_join(root, file_name)


def check_move() -> bool:
    """Read logical signal from gpio.
    """
    if gpio:
        return bool(gpio.input(SENSOR_PIN))
    else:
        # fake data
        return random.randint(1, 10) < 3


def make_photos(
        count: int=PHOTO_SERIES,
        logger=None,
        prepare_delay: float=0.1) -> tuple:
    """Make photos to files.
    """
    if logger is None:
        logger = get_logger()
    call_code = uuid.uuid4().hex[:6]
    result = []
    if picamera is None:
        logger.warning()
        return result, call_code
    result.extend((
        os.path.join(WORK_DIR, "{}_{}{:02}.jpg".format(
            datetime.now().strftime("%d%m%y%H%M%S"),
            call_code,
            index))
        for index in range(count)
    ))
    try:
        with picamera.PiCamera(
                framerate=int(CAMERA_FRAMERATE or 30),
                resolution=IMAGE_SIZE) as cam:
            #
            cam.start_preview()
            time.sleep(prepare_delay)
            cam.capture_sequence(
                result, use_video_port=True)
            cam.stop_preview()
    except Exception as err:
        logger.error("Make photo error: {}".format(err))

    return filter(os.path.isfile, result), call_code


def record_event(code: str, content: dict) -> bool:
    """Save event to file in work dir.
    """
    file_path = os.path.join(
        WORK_DIR,
        "{}_{}.event".format(code, int(time.time())))
    with codecs.open(file_path, mode="w") as fevent:
        fevent.write(json.dumps(content))
    return os.path.isfile(file_path)
