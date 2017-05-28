import time
from datetime import datetime
from enum import Enum
from threading import Thread

from .conf import ProcessOption
from .const import (
    CAMERA_FRAMERATE, LIGHT_PIN, SENSOR_PIN, SIREN_PIN,
    LIGHT_AUTO_OFF)
from .log import get_logger
from .helpers import (
    pin_on, pin_off, pin_send, check_move, make_photos, record_event)


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

    def __str__(self):
        return self.__class__.__name__

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
                else:
                    self.logger.info("{} finished..".format(sub_th))
        try:
            self._tstate_lock.release()
            self._stop()
        except Exception as err:
            self.logger.error(err)
        else:
            self.logger.info("{} finished..".format(self))

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

    def change_state(self, update_time: bool=True) -> bool:
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
            if update_time:
                self._last_change = time.time()

    def check_timeout(self) -> bool:
        """Check auto turn off.
        """
        if self._last_change:
            return self.auto_off_time < time.time() - self._last_change
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
        run_action = False
        while self.is_alive():
            run_action = False
            global_state = self.read_global_state()
            if global_state == DeviceState.NOT_ACTIVE:
                self.next_state = global_state
            elif self.check_timeout():
                self.logger.warning(
                    "Timeout in {}".format(self))
                self.turn_off()
            else:
                run_action = True

            self.change_state()
            run_action and self.action()
            time.sleep(self.iter_delay)


class SirenControl(AutoOffDevice):
    """Siren control thread.
    """
    pin = SIREN_PIN
    dev_active_option_name = "active_siren"
    auto_off_time = 10 * 60
    sound_pause = 1.0

    def action(self):
        """Sound with pauses.
        """
        time.sleep(self.sound_pause)
        self.turn_off()
        self.change_state(update_time=False)
        time.sleep(self.sound_pause)
        self.turn_on()
        self.change_state(update_time=False)


class LightControl(AutoOffDevice):
    """Light control thread.
    """
    iter_delay = 2.5
    pin = LIGHT_PIN
    dev_active_option_name = "active_light"
    auto_off_time = 15


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
    iter_delay = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.siren_control = SirenControl(option=self.option)
        self.light_control = LightControl(option=self.option)
        self.sub_threads.append(self.siren_control)
        self.sub_threads.append(self.light_control)

    def make_package(self, datet: datetime, photos: list, code: str) -> None:
        """Record JSON file with this event.
        """
        try:
            record_event(code, {"files": photos, "date": datet.isoformat()})
        except Exception as err:
            self.logger.error(
                "Event '{}' recording error: {}".format(code, err))

    def run(self):
        while self.is_alive():
            if self.option.active_guard and check_move():
                self.logger.info("Detected!")
                now = datetime.now()
                self.light_control.turn_on()
                photos, event_code = make_photos(
                    logger=self.logger)
                if photos:
                    self.logger.info(
                        "Photo in: {}".format(", ".join(photos)))
                    make_photos(now, photos, event_code)
                else:
                    self.logger.warning("Photos do not done.")

                self.siren_control.turn_on()

            time.sleep(self.iter_delay)
