"""
Euclidean Rhythms
author: awonak
version: 1.0

A rhythm sequence of evenly distributed pulses over a number of steps.

Inspired by:
https://www.computermusicdesign.com/simplest-euclidean-rhythm-algorithm-explained/

Tempo Edit Mode
knob_1: master clock speed

Pattern Edit Mode
knob_1: adjust the number of steps from 1 to 16
knob_2: adjust the number of pulses from 0 to steps
button_1: toggle tempo / pattern edit mode
button_2: cycle through patterns
digital_1: pattern 1
digital_2: pattern 2
digital_3: pattern 3
digital_4: pattern 4

"""
import uasyncio as asyncio

from lib.button import Pushbutton
from lib.clock import Clock
from lib.constants import UINT_16
from lib.europi import DigitalOut
from lib.europi import knob_1
from lib.europi import knob_2
from lib.europi import button_1
from lib.europi import button_2
from lib.europi import digital_1
from lib.europi import digital_2
from lib.europi import digital_3
from lib.europi import digital_4
from lib.helpers import trigger


DEBUG = False

class Pattern:
    """A Euclidean rhythm pattern bound to a DigitalOut pin."""

    def __init__(self, out: DigitalOut, steps: int, pulses: int) -> None:
        self.out = out
        self.steps = steps
        self.pulses = pulses
        self.step = 0
        self._pattern = [0] * steps
        self.build()

    def __repr__(self):
        """String representation of the pattern."""
        return self._pattern

    def __len__(self):
        """Length of the pattern."""
        return self.steps

    def __getitem__(self, index: int):
        """Pattern step getter."""
        return self._pattern[index]

    def build(self):
        """Construct the pattern given the given steps and pulses."""
        step = 0
        for i in range(self.steps):
            step += self.pulses
            if step >= self.steps:
                step -= self.steps
                self._pattern[i] = 1

    def play_step(self):
        """Trigger the current step if high and advance to next step."""
        if self._pattern[self.step] == 1:
            trigger(self.out)
        self.step = (self.step + 1) % self.steps


class EuclideanRhythm:
    MAX_STEPS = 16

    def __init__(self, clock: Clock):
        self.clock = clock
        self.patterns = [
            Pattern(digital_1, 8, 5),
            Pattern(digital_2, 1, 0),
            Pattern(digital_3, 1, 0),
            Pattern(digital_4, 1, 0),
        ]
        self._selected_pattern = 0
        self._pattern_mode = False

    def _short1(self):
        """Toggle between tempo/pattern edit modes."""
        self.clock.toggle_edit()
        self._pattern_mode = not self._pattern_mode

    def _short2(self):
        """Cycle through patterns for editing."""
        self._selected_pattern = (self._selected_pattern + 1) % len(self.patterns)

    def debug(self):
        if DEBUG:
            p = self.patterns[self._selected_pattern]
            print("{:>2}-{}: steps: {:>2}  pulses: {:>2}  >>  {}".format(
                p.step, self._selected_pattern, p.steps, p.pulses, p))

    def update(self):
        """Check knobs for a change and update pattern accordingly."""
        if self._pattern_mode:
            _steps = knob_1.choice(self.MAX_STEPS) + 1
            _pulses = knob_2.choice(_steps) + 1
            p = self.patterns[self._selected_pattern]
            if _steps != p.steps or _pulses != p.pulses:
                self.patterns[self._selected_pattern] = Pattern(p.out, _steps, _pulses)

    async def start(self):
        # Register button handlers.
        Pushbutton(button_1.pin)\
            .press_func(self._short1)

        Pushbutton(button_2.pin)\
            .press_func(self._short2)

        # Start the main loop.
        while True:
            # Check knob state and update the current pattern.
            self.update()

            # Trigger each pattern on high step.
            for pattern in self.patterns:
                pattern.play_step()

            self.debug()
            await asyncio.sleep_ms(self.clock.wait_ms())


if __name__ == '__main__':
    clock = Clock(knob_1)
    euclid = EuclideanRhythm(clock)

    async def main():
        loop = asyncio.get_event_loop()
        loop.create_task(euclid.start())
        loop.run_forever()

    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()
