"""
Clock Divider
author: awonak
version: 1.1

Provide 4 divisions of the master clock set by knob 1.

Master clock set by knob 1 will emit a trigger pulse once every quarter note
for the current tempo. Use button 2 to cycle through each digital out enabling
it to set a division from a list of division choices chosen by knob 2.

knob_1: master clock tempo
knob_2: choose the division for the current selected index.
button_2: cycle through the digital
digital_1: first division, default master clock
digital_2: second division, default /2
digital_3: third division, default /4
digital_4: fourth division, default /8

"""
import uasyncio as asyncio

from lib.europi import knob_1
from lib.europi import knob_2
from lib.europi import button_2
from lib.europi import digital_outputs
from lib.clock import Clock
from lib.helpers import trigger


DEBUG = False

# Useful divisions to choose from.
DIVISION_CHOICES = [1, 2, 3, 4, 5, 6, 7, 8, 12, 16]
MAX_DIVISION = max(DIVISION_CHOICES)


class ClockDivider:

    def __init__(self, clock: Clock):
        self.selected_output = -1
        self.previous_choice = int(knob_2.percent() * len(DIVISION_CHOICES) - 0.0001)
        self.counter = 1
        self.clock = clock

        # Divisions corresponding to each digital output.
        self.divisions = [1, 2, 4, 8]

    async def start(self):
        # Register button handlers.
        @button_2.handler
        def config_divisions():
            self.selected_output = (self.selected_output + 1) % len(self.divisions)
            
        # Start the main loop.
        while True:
            # Trigger the digital pin if it's divisible by the counter.
            for i, pin in enumerate(digital_outputs):
                if self.counter % self.divisions[i] == 0:
                    trigger(pin)

            # Set the currently selected digital out's clock division to the value
            # selected by knob 2.
            choice = int((knob_2.percent() - 0.001) * len(DIVISION_CHOICES))
            if self.selected_output >= 0 and choice != self.previous_choice:
                self.divisions[self.selected_output] = DIVISION_CHOICES[choice]
                self.previous_choice = choice

            # Wrap the counter if we've reached the largest division.
            self.counter = (self.counter + 1) % MAX_DIVISION

            if DEBUG:
                msg = "DJ: {}  || config:{} tempo:{} wait: {}"
                print(msg.format(self.divisions, self.selected_output, self.clock.tempo, self.clock.wait_ms()))
            
            await asyncio.sleep_ms(self.clock.wait_ms())


# Run the script if called directly.
if __name__ == '__main__':
    clock = Clock(knob_1)
    clock_divider = ClockDivider(clock)
    
    # Main script function
    async def main():
        loop = asyncio.get_event_loop()
        loop.create_task(clock_divider.start())
        loop.run_forever()

    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()
