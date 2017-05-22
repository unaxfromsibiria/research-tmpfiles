import os
import tempfile

DEFAULT_PINS = (
    24,  # move sensor pin (HCSR501)
    12,  # modem power
    7,  # light pin
    8,  # siren power
)
# setup pins
pins = os.environ.get("PINS")
pin_values = list(DEFAULT_PINS)
if pins:
    pins = pins.split(",")
    assert len(pins) == len(DEFAULT_PINS), (
        "You need: 'move sensor,modem power,light,siren' pins."
    )
    for index, new_pin in enumerate(pins):
        try:
            pin_values[index] = int(new_pin)
        except (ValueError, TypeError):
            pass

    assert len(set(pin_values)) == len(DEFAULT_PINS), (
        "Values of PINS are matching in {}".format(pin_values)
    )

SENSOR_PIN, MODEM_POWER_PIN, LIGHT_PIN, SIREN_PIN = (
    pin_values
)
LIGHT_AUTO_OFF = int(os.environ.get("LIGHT_AUTO_OFF") or 1800)
WORK_DIR = os.environ.get("WORK_DIR") or tempfile.mkdtemp()
LOG_FILEPATH = os.path.join(WORK_DIR, "guardpi.log")
LOG_LEVEL = os.environ.get("LOG_LEVEL") or "INFO"
LOGGER_NAME = "guardpi"
CONF_FILEPATH = os.path.join(WORK_DIR, "guardpi-conf.json")
CONF_UPDATE_TIME = int(os.environ.get("CONF_UPDATE_TIME") or 3)

try:
    img_size = os.environ.get("IMAGE_SIZE") or "640,480"
    w, h = map(int, img_size.split(","))
except (ValueError, TypeError):
    w, h = (640, 480)
IMAGE_SIZE = w, h

PHOTO_SERIES = int(os.environ.get("PHOTO_SERIES") or 3)
CAMERA_FRAMERATE = int(os.environ.get("CAMERA_FRAMERATE") or 30)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") or ""
TELEGRAM_ADMINS = os.environ.get("TELEGRAM_ADMINS") or ""
