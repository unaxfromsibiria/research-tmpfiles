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
