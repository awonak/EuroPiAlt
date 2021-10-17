"""
EuroPi Library
author: awonak
version: 1.0

EuroPi module library providing pin wrappers classes for each of the
module's input and output interfaces.


https://github.com/awonak/EuroPiAlt
https://github.com/roryjamesallen/EuroPi
https://allensynthesis.co.uk/europi_assembly.html
"""
from random import random
from typing import Iterable

from machine import Pin, PWM, ADC
from utime import sleep_ms, ticks_ms

from src.lib.constants import UINT_16


# Disable power saving mode and switch to PWM mode.
# This reduces the noise from analog reads.
Pin(23, Pin.OUT).value(1)


class Knob:
    def __init__(self, pin: int):
        self.pin = ADC(Pin(pin))

    def percent(self) -> float:
        """Provide the relative percent value between 0 and 1."""
        return self.value() / UINT_16
    
    def choice(self, options: int):
        """Return a value from a range chosen by the knob position."""
        return int((self.percent() - 0.001) * options)
    
    def value(self) -> int:
        """Provide the current value of the knob position between 0 and 65535 (max 16 bit int)."""
        return self.pin.read_u16()


class Button:
    def __init__(self, pin: int, debounce_delay: int = 500):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self.debounce_delay = debounce_delay  # delay in ms
        self.last_pressed = 0
        self.debounce_done = True
    
    def value(self) -> int:
        """Current button state. Default state is HIGH (1) and LOW (0) is pressed.""" 
        return self.pin.value()

    def _debounce_check(self) -> None:
        if (ticks_ms() - self.last_pressed) > self.debounce_delay:
            self.debounce_done = True

    def handler(self, func: function) -> None:
        """Handler takes a callback func to call when this button is pressed."""
        def bounce(func):
            def wrap_bounce(*args, **kwargs):
                self._debounce_check()
                if self.debounce_done:
                    self.last_pressed = ticks_ms()
                    self.debounce_done = False
                    func()

            return wrap_bounce

        self.pin.irq(trigger=Pin.IRQ_RISING, handler=bounce(func))
    
    def reset_handler(self) -> None:
        """Disable the handler function."""
        self.pin.irq(trigger=Pin.IRQ_RISING)


class AnalogOut:
    def __init__(self, pin: int):
        self.pin = PWM(Pin(pin, Pin.OUT))

    def value(self, new_duty: int) -> None:
        """Set the duty value to the given unsigned 16 bit int value."""
        self.pin.duty_u16(new_duty)


class DigitalOut:
    def __init__(self, pin: int):
        self.pin = Pin(pin, Pin.OUT)

    def value(self, value: int) -> None:
        """Set the digital pin to the given value, HIGH (1) or LOW (0)."""
        self.pin.value(value)

    def trigger(self, duration: int = 50):
        """Set the digital pin to HIGH for the optional duration (default to 50ms)."""
        self.value(1)
        sleep_ms(duration)
        self.value(0)

    def toggle(self):
        """Invert the digital pin's current value."""
        self.pin.toggle()


# Construct each module interface class.
knob_1 = Knob(28)
knob_2 = Knob(27)
button_1 = Button(15)
button_2 = Button(18)
analog_1 = AnalogOut(14)
analog_2 = AnalogOut(11)
analog_3 = AnalogOut(10)
analog_4 = AnalogOut(7)
digital_1 = DigitalOut(21)
digital_2 = DigitalOut(22)
digital_3 = DigitalOut(19)
digital_4 = DigitalOut(20)

# Each analog and digital output object in a list.
analog_outputs = [analog_1, analog_2, analog_3, analog_4]
digital_outputs = [digital_1, digital_2, digital_3, digital_4]
