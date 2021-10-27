from machine import ADC, Pin
from time import ticks_ms

from lib.constants import UINT_16


class AnalogInput:
    def __init__(self, pin: int):
        self.pin = ADC(Pin(pin))

    def value(self) -> int:
        """Read the received voltage as uint16 value between 0 and 65535."""
        return self.pin.read_u16()

    def percent(self) -> float:
        """Read the current relative voltage returned as a float between 0 and 1."""
        return self.pin.read_u16() / UINT_16


class DigitalInput:
    def __init__(self, pin: int):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_DOWN)

    def value(self) -> int:
        """Read the digital pin, HIGH (1) or LOW (0)."""
        return self.pin.value()


class DigitalSwitch:
    def __init__(self, pin: int, debounce_delay: int = 500):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.debounce_delay = debounce_delay  # delay in ms
        self.last_pressed = 0
        self.debounce_done = True

    def value(self):
        """Read the digital pin, plug present (1) or removed (0)."""
        return self.pin.value()
    
    def _debounce_check(self):
        if (ticks_ms() - self.last_pressed) > self.debounce_delay:
            self.debounce_done = True

    # Handler takes a callback func to call when this button is pressed.
    def handler(self, func):
        def bounce(func):
            def wrap_bounce(*args, **kwargs):
                self._debounce_check()
                if self.debounce_done:
                    self.last_pressed = ticks_ms()
                    self.debounce_done = False
                    func()

            return wrap_bounce

        self.pin.irq(trigger=Pin.IRQ_RISING, handler=bounce(func))


# Analog & Digital input jacks
analog_in = AnalogInput(26)
digital_in = DigitalInput(0)
digital_sw = DigitalSwitch(1)
