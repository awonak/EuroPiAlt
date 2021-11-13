"""
Smooth/Stepped Random Voltages
author: awonak
version: 1.1

Random cv with adjustable slew rate.
Inspired by: https://youtu.be/tupkx3q7Dyw

Next voltage clocked:
New voltage assigned according master clock set by knob 1.
Analog 1 moves towards target voltage according to slew
rate set by knob 2.

Next voltage unclocked:
New voltage assigned when analog 1 voltage reaches value.


knob_1: master clock speed
knob_2: slew rate
button_1: next voltage clocked/unclocked
analog_1: smooth random voltage
analog_2: stepped random voltage
digital_1: Trigger on new voltage
digital_2: Trigger on slew reached target volatge
digital_3: (state display) off when clocked, on when unclocked
"""
from random import randint
from scripts.arpeggiator import DEBUG

import uasyncio as asyncio
from utime import ticks_ms

from lib.clock import Clock
from lib.constants import UINT_16
from lib.europi import knob_1
from lib.europi import knob_2
from lib.europi import button_1
from lib.europi import analog_1
from lib.europi import analog_2
from lib.europi import digital_1
from lib.europi import digital_2
from lib.europi import digital_3
from lib.helpers import trigger


DEBUG = False


class SmoothRandomVoltages:

    def __init__(self, clock: Clock):
        self.clock = clock
        self.clocked = True
        self.slew_rate = lambda: 1 << knob_2.choice(14) + 1

        self.voltage = 0
        self.next_voltage = self.get_next_voltage()
        self.deadline = self.get_next_deadline()

    def get_next_voltage(self):
        """Get next random voltage value."""
        return randint(0, UINT_16)

    def get_next_deadline(self):
        """Get the deadline for next clock tick whole note."""
        return ticks_ms() + (self.clock.wait_ms() * 4)

    def check_next(self):
        """Check if next voltage conditions and update if ready."""
        if self.clocked and ticks_ms() < self.deadline:
            return
        
        if not self.clocked and self.voltage != self.next_voltage:
            return
    
        self.next_voltage = self.get_next_voltage()
        self.deadline = self.get_next_deadline()
        trigger(digital_1)  # Trigger on whole note tick.
        digital_2.value(0)  # Gate off on new voltage.
    
    def debug(self):
        v = lambda v: (v / UINT_16) * 3.3
        if DEBUG:
            print("SMOOTH: {:>.2f}  STEPPED: {:>.2f}".format(
                v(self.voltage), v(self.next_voltage)))
    
    async def start(self):
        # Register button handlers
        @button_1.handler
        def toggle_next_voltage_condition():
            self.clocked = not self.clocked
            digital_3.toggle()

        # Start the main loop.
        while True:
            self.check_next()

            # Smooth voltage rising
            if self.voltage < self.next_voltage:
                self.voltage += self.slew_rate()
                self.voltage = min(self.voltage, self.next_voltage)

            # Smooth voltage falling
            elif self.voltage > self.next_voltage:
                self.voltage -= self.slew_rate()
                self.voltage = max(self.voltage, self.next_voltage)
            
            # Target voltage reached
            elif self.voltage == self.next_voltage:
                digital_2.value(1)  # Gate on slew reached target volatge

            # Set the current smooth / stepped voltage.
            analog_1.value(self.voltage)
            analog_2.value(self.next_voltage)

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

