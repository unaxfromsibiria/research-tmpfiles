import time
from enum import Enum
from threading import Thread

from .conf import ProcessOption
from .const import (
    CAMERA_FRAMERATE, LIGHT_PIN, SENSOR_PIN, SIREN_PIN,
    LIGHT_AUTO_OFF)
from .log import get_logger
from .helpers import pin_on, pin_off


class EquipmentThread(Thread):
    """Management of peripheral equipment in thread.
    """
    iter_delay = 0.5
    logger = option = None

    sub_threads = None

    def __init__(self, option=None):
        super().__init__(name=self.__class__.__name__)
        self.sub_threads = []
        self.logger = get_logger()
        if not isinstance(option, ProcessOption):
            option = ProcessOption()
        self.option = option

    def stop(self):
        """Dropping threads.
        """
        for sub_th in self.sub_threads:
            if isinstance(sub_th, Thread):
                try:
                    sub_th._tstate_lock.release()
                    sub_th._stop()
                except Exception as err:
                    self.logger.error(err)
        try:
            self._tstate_lock.release()
            self._stop()
        except Exception as err:
            self.logger.error(err)

    def start(self):
        super().start()
        for sub_th in self.sub_threads:
            if isinstance(sub_th, Thread):
                sub_th.start()


class DeviceState(Enum):
    """Device states.
    """
    ON = 1
    OFF = 2
    NOT_ACTIVE = 3


class SirenControl(EquipmentThread):
    """Siren control thread.
    """

    _siren_sounds = False  # on / off
    iter_delay = 0.2
    state = None

    def turn_on(self):
        """Turn on siren.
        """
        self._siren_sounds = True

    def turn_off(self):
        """Turn off siren.
        """
        self._siren_sounds = False

    def quiet(self):
        """Immediately shut up siren.
        """
        try:
            pin_off(SIREN_PIN)
        except Exception as err:
            self.logger.error(
                "Problem with siren pin: {}".format(err))
        else:
            self.state = DeviceState.OFF

    def shout(self):
        """Turn on siren.
        """
        try:
            pin_on(SIREN_PIN)
        except Exception as err:
            self.logger.error(
                "Problem with siren pin: {}".format(err))
        else:
            self.state = DeviceState.ON

    def action(self):
        """Sound with pauses.
        """
        for _ in range(5):
            self.shout()
            time.sleep(0.6)
            self.quiet()
            time.sleep(0.2)

    def run(self):
        while self.is_alive():
            if self._siren_sounds:
                if self.option.active_siren:
                    self.action()
                else:
                    if self.state != DeviceState.NOT_ACTIVE:
                        self.quiet()
                        self.logger.warning(
                            "Siren active changed to OFF.")
                        self.state = DeviceState.NOT_ACTIVE
                    self._siren_sounds = False

            time.sleep(self.iter_delay)


class LightControl(EquipmentThread):
    """Light control thread.
    """

    iter_delay = 2
    state = None
    auto_off = LIGHT_AUTO_OFF
    _last_on = 0

    def turn_on(self):
        """Turn on siren.
        """
        self._last_on = time.time()

    def turn_off(self):
        """Turn off siren.
        """
        self._last_on = 0

    def action(self):
        """Light on/off.
        """
        try:
            if self._last_on and self.state != DeviceState.ON:
                pin_on(LIGHT_PIN)
            else:
                pin_off(LIGHT_PIN)

        except Exception as err:
            self.logger.error(
                "Problem with light pin: {}".format(err))
        else:
            if self.state != DeviceState.NOT_ACTIVE:
                self.state = (
                    DeviceState.ON if self._last_on else DeviceState.OFF
                )

    def run(self):
        while self.is_alive():
            if self.option.active_light:
                if self.auto_off > time.time() - self._last_on:
                    self.turn_off()
            else:
                self.state = DeviceState.NOT_ACTIVE
                self.turn_off()

            self.action()
            time.sleep(self.iter_delay)


class MoveWatcher(EquipmentThread):
    """General class of this guardion system.
    Functions:
        - detecting of move
        - turn on of lighting
        - recording photo series with a camera
        - turn on of a siren
        - prepare packages for sending
    """

    light_control = siren_control = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.siren_control = SirenControl(option=self.option)
        self.light_control = LightControl(option=self.option)
        self.sub_threads.append(self.siren_control)
        self.sub_threads.append(self.light_control)

    def run(self):
        while self.is_alive():
            # TODO
            self.logger.info("watcher =>")
            time.sleep(2)
            self.siren_control.turn_on()
            time.sleep(1)
            self.siren_control.turn_off()
