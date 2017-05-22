import codecs
import json
import os
import time

from .const import CONF_FILEPATH, CONF_UPDATE_TIME
from .log import get_logger


class ProcessOption:
    """Options for current process.
    """
    logger = None
    _default = {
        "active_guard": True,
        "active_light": True,
        "active_siren": True,
        "auto_on_time": 1800,
        "stopped_at": None,
    }
    _state = None
    _last_sync = 0
    _service_delay = 0.1
    _sleep_method = time.sleep
    _file = CONF_FILEPATH
    _retry_limit = 100

    def __init__(self):
        self.logger = logger = get_logger()
        if self.read(wait=False):
            logger.info(
                "Use configuration from '{}'".format(
                    self._file))
        else:
            self._state = self._default.copy()
            if self.write():
                logger.info(
                    "New configuration created in '{}'".format(
                        self._file))

    def set(self, field, value) -> bool:
        """Setup value and update.
        """
        if field not in self._default:
            return
        need_update = value != self._state.get(field)
        self._state[field] = value
        return need_update and self.write()

    def get(self, field):
        """Get value by field.
        """
        if time.time() - self._last_sync > CONF_UPDATE_TIME:
            self.read()

        return self._state.get(field)

    @property
    def active_guard(self) -> bool:
        return self.get("active_guard")

    @active_guard.setter
    def active_guard(self, value):
        value = bool(value)
        if not value:
            self.set("stopped_at", time.time())
        return self.set("active_guard", value)

    @property
    def active_light(self) -> bool:
        return self.get("active_light")

    @active_light.setter
    def active_light(self, value):
        return self.set("active_light", bool(value))

    @property
    def active_siren(self) -> bool:
        return self.get("active_siren")

    @active_siren.setter
    def active_siren(self, value):
        return self.set("active_siren", bool(value))

    @property
    def auto_on_time(self) -> int:
        return self.get("auto_on_time")

    @property
    def stopped_at(self) -> float:
        return self.get("stopped_at")

    @property
    def time_to_start(self) -> bool:
        """It's time to start again.
        """
        result = False
        if self.active_guard:
            dt = time.time() - self.stopped_at
            result = dt > self.auto_on_time
        return result

    def write(self, wait=True) -> bool:
        """Write state.
        """
        retry = True
        result = False
        try_count = 0
        while retry:
            try:
                data = json.dumps(self._state)
                with codecs.open(self._file, mode="w") as conf:
                    conf.write(data)

            except Exception as err:
                try_count += 1
                if try_count > self._retry_limit:
                    retry = False
                    self.logger.error(
                        "Write conf: {}".format(err))
                else:
                    retry = wait
                    self._sleep_method(self._service_delay)
            else:
                result = True
                retry = False
                self._last_sync = time.time()

        return result

    def read(self, wait=True) -> bool:
        """Read configuration.
        """
        retry = True
        result = False
        try_count = 0
        while retry:
            try:
                with codecs.open(self._file) as conf:
                    data = conf.read()
                state = json.loads(data)
            except Exception as err:
                try_count += 1
                if try_count > self._retry_limit:
                    retry = False
                    self.logger.error(
                        "Read conf: {}".format(err))
                else:
                    retry = wait
                    self._sleep_method(self._service_delay)
            else:
                result = True
                retry = False
                self._state = state
                self._last_sync = time.time()

        return result
