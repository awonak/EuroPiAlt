"""
Smooth Random Voltages
author: awonak
version: 1.0

Random cv with adjustable slew rate.
Inspired by:
https://youtu.be/tupkx3q7Dyw


knob_1: master clock speed
knob_2: slew rate
analog_1: smooth random voltage
digital_1: Trigger on whole note
digital_2: Trigger on slew reached target volatge
"""
from random import randint
from scripts.arpeggiator import DEBUG

import uasyncio as asyncio
from utime import ticks_ms

from lib.clock import Clock
from lib.constants import UINT_16
from lib.europi import knob_1
from lib.europi import knob_2
from lib.europi import analog_1
from lib.europi import digital_1
from lib.europi import digital_2
from lib.helpers import trigger


DEBUG = False


class SmoothRandomVoltages:

    def __init__(self, clock: Clock):
        self.clock = clock
        self.slew_rate = lambda: 1 << knob_2.choice(14)

        self.voltage = 0
        self.next_voltage = 0
        self.deadline = 0  # Trigger on slew reached target volatge

    def get_next_voltage(self):
        """Get next random voltage value."""
        return randint(0, UINT_16)

    def get_next_tick(self):
        """Get the deadline for next clock tick whole note."""
        return ticks_ms() + (self.clock.wait_ms() * 4)

    def check_deadline(self):
        """Check the cpu ticks against the clock deatline and update if ready."""
        if ticks_ms() > self.deadline:
            self.next_voltage = self.get_next_voltage()
            self.deadline = self.get_next_tick()
            trigger(digital_1)  # Trigger on whole note tick.
    
    def debug(self):
        if DEBUG:
            print("t: {} d: {} v: {} t: {}".format(
                ticks_ms(), self.deadline, self.voltage, self.next_voltage))
    
    async def start(self):
        # Start the main loop.
        while True:
            self.check_deadline()

            if self.voltage < self.next_voltage:
                self.voltage += self.slew_rate()
                self.voltage = min(self.voltage, self.next_voltage)
                trigger(digital_2)  # Trigger on slew reached target volatge

            elif self.voltage > self.next_voltage:
                self.voltage -= self.slew_rate()
                self.voltage = max(self.voltage, self.next_voltage)
                trigger(digital_2)  # Trigger on slew reached target volatge

            # Set the current voltage.
            analog_1.value(self.voltage)

            self.debug()
            await asyncio.sleep_ms(0)


if __name__ == '__main__':
    clock = Clock(knob_1)
    srv = SmoothRandomVoltages(clock)

    # Main script function
    async def main():
        loop = asyncio.get_event_loop()
        loop.create_task(srv.start())
        loop.run_forever()

    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()
