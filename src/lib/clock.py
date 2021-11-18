"""
Clock
author: awonak
version: 1.0

Provide a master clock tempo from internal or external source.

This library provides scripts with a set of functions for providing an internal
clock set by a knob that includes average run smoothing to account for analog
fluxuation. Additionally, read a GPIO pin from the Expander module to use a
clock from an external source.


tempo_knob: Knob
    internal master clock tempo
clock_switch: Button
    switch between internal or external clock source.
clock_bus: Pin
    GPIO pin to send or receive clock pulse.

Expander:

# Digital pin to read input clock from the expander.
Pin(8): cv clock output
bus_clock = Pin(8, Pin.OUT)


Examples

Internal Clock Source:
    clock = Clock(knob_1)

Internal Clock Source with child:
    clock = Clock(knob_1, Pin(8, Pin.OUT))

External Clock Source:
    clock = Clock(clock_bus = Pin(8, Pin.OUT), internal_clock = False)

TODO: allow external clock source to receive clock and pass-through.

"""
from machine import Pin
from utime import sleep_ms

from lib.europi import Button, Knob

MIN_BPM = 20
MAX_BPM = 280


class Clock:
    """Define a master clock either using internal or external source."""
    
    def __init__(self, tempo_knob: Knob,
                 clock_switch: Button = None,
                 clock_bus: Pin = None,
                 min_bpm: int = MIN_BPM,
                 max_bpm: int = MAX_BPM,
                 internal_clock: bool = True,
                 avg_run_len: int = 1) -> None:
        # Default clock source.
        self._internal_clock = internal_clock
        # Enable/disable ability to change tempo.
        self.edit_mode = True

        # Input controls for internal clock.
        self.tempo_knob = tempo_knob
        self.clock_switch = clock_switch
        if clock_switch is not None:
            clock_switch.handler(self.switch_clock_source)
            self.switch_clock_source()

        # GPIO Pin for clock bus, either external clock source or pass internal clock.
        self.clock_bus = clock_bus
        self._prev_clock = 0

        # Tempo range vars
        self.min_bpm = min_bpm
        self.max_bpm = max_bpm

        # Running average vars for smoothing analog input for tempo.
        self._run_len = avg_run_len
        self._run = [120] * self._run_len

    def toggle_edit(self, enabled=None):
        """Enable/disable ability to change tempo."""
        if enabled is not None:
            self.edit_mode = enabled
        else:
            self.edit_mode = not self.edit_mode

    def switch_clock_source(self) -> None:
        """Switch between internal and external clock source."""
        self._internal_clock = not bool(self.clock_switch.value())
    
    @property
    def tempo(self) -> float:
        """Take a reading from the tempo knob to determine internal tempo."""
        # Return current tempo if edit mode disabled:
        if not self.edit_mode:
            return round(sum(self._run) / self._run_len, 1)
        # Set the clock speed via Knob 1.
        # tempo range default is between 20 and 280 BPM.
        # Knob 12 o'clock position is 150 BPM.
        _tempo =  (self.tempo_knob.percent() * (self.max_bpm - self.min_bpm)) + self.min_bpm
        # Get the running average tempo.
        self._run = self._run[1:]
        self._run.append(_tempo)
        return round(sum(self._run) / self._run_len, 1)

    def wait_ms(self) -> int:
        """The duration of a quarter note in ms for the current tempo."""
        return int(((60 / self.tempo) / 4) * 1000)

    def internal_clock_wait(self) -> None:
        """Wait for a quarter note of the internal tempo."""
        sleep_ms(self.wait_ms())
        # Send clock pulse to clock bus.
        #if self.clock_bus:
        #    self.clock_bus.value(1); sleep_ms(10); self.clock_bus.value(0)

    def external_clock_wait(self) -> None:
        """Wait for clock pulse to go high to advance."""
        while not self._internal_clock:
            if self.clock_bus.value() != self._prev_clock:
                self._prev_clock = 1 if self._prev_clock == 0 else 0
                if self._prev_clock == 0:
                    return

    def wait(self) -> None:
        """Wait for a clock cycle of the current selected clock source."""
        if self._internal_clock:
            self.internal_clock_wait()
        else:
            self.external_clock_wait()
