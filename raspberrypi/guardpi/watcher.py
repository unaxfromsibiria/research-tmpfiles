import time
from enum import Enum
from threading import Thread

from .conf import ProcessOption
from .const import (
    CAMERA_FRAMERATE, LIGHT_PIN, SENSOR_PIN, SIREN_PIN,
    LIGHT_AUTO_OFF)
from .log import get_logger
from .helpers import pin_on, pin_off, pin_send


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


class AutoOffDevice(EquipmentThread):
    """Devices with state and auto off mode.
    """
    state = DeviceState.OFF
    next_state = DeviceState.ON
    pin = 0
    dev_active_option_name = None
    auto_off_time = 1800
    _last_change = 0

    def turn_on(self):
        """Turn on siren.
        """
        self.next_state = DeviceState.ON

    def turn_off(self):
        """Turn off siren.
        """
        self.next_state = DeviceState.OFF

    def read_global_state(self):
        """Check option.
        """
        if self.dev_active_option_name is None:
            return DeviceState.ON
        else:
            value = self.option.get(self.dev_active_option_name)
            return DeviceState.ON if value else DeviceState.NOT_ACTIVE

    def change_state(self) -> bool:
        """Change state.
        """
        if self.state == self.next_state:
            return False

        try:
            pin_send(self.pin, self.next_state == DeviceState.ON)
        except Exception as err:
            self.logger.error(
                "Problem with pin {}: {}".format(self.pin, err))
        else:
            self.state = self.next_state
            self._last_change = time.time()

    def check_timeout(self) -> bool:
        """Check auto turn off.
        """
        if self._last_change:
            return self.auto_off_time <= time.time() - self._last_change
        else:
            return False

    def action(self):
        """Advanced action.
        """
        pass

    def stop(self):
        self.turn_off()
        # wait action
        time.time(self.iter_delay + 0.1)
        return super().stop()

    def run(self):
        with self.is_alive():
            global_state = self.read_global_state()
            if global_state == DeviceState.NOT_ACTIVE:
                self.next_state = global_state
            elif self.check_timeout():
                self.turn_off()

            self.change_state()
            self.action()
            time.sleep(self.iter_delay)


class SirenControl(AutoOffDevice):
    """Siren control thread.
    """

    iter_delay = 0.2
    pin = SIREN_PIN
    dev_active_option_name = None
    auto_off_time = 1800

    def action(self):
        """Sound with pauses.
        """
        # TODO
        for _ in range(5):
            #self.shout()
            time.sleep(0.6)
            #self.quiet()
            time.sleep(0.2)


class LightControl(AutoOffDevice):
    """Light control thread.
    """
    # TODO
    iter_delay = 2


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
