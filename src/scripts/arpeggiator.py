"""
Arpeggiator
author: awonak
version: 2.1



Master tempo is set by knob 1, each analog output has a diffent cycle pattern
and each digital output triggers a different rhythmic pattern based off the
master clock. Knob 2 will adjust the octave range from 1 to 3 octaves.

knob_1: adjust the master clock tempo
knob_2: adjust the octave range; 1, 2 or 3 octaves
button_1: reset arpeggio order back to first note in pattern and change scale
analog_1: play notes in ascending order: 1 > 2 > 3
analog_2: play notes in descending order: 3 > 2 > 1
analog_3: play notes in asc & desc order: 1 > 2 > 3 > 3 > 2 > 1
analog_4: play notes in scale will be played randomly
digital_1: master clock trigger
digital_2: trigger at cycle start
digital_3: trigger at sequence step divided by 3
digital_4: trigger at sequence step divided by 4
"""

from random import choice

import uasyncio as asyncio
from utime import sleep_ms

from lib.clock import Clock
from lib.europi import knob_1
from lib.europi import knob_2
from lib.europi import button_1
from lib.europi import analog_outputs
from lib.europi import digital_outputs
from lib.helpers import trigger
from lib.scales import scales


DEBUG = False


class Arpeggiator:
    """Cycle through a sequence of notes in a scale."""
    OCTAVE_RANGE = 3  # EuroPi outputs max 3.3v so we only have a 3 octave range

    def __init__(self, clock: Clock):
        self.scale = scales[0]
        self.clock = clock
        self.prev_octave_range = 1

        self.step = 0
        self.bi_forward = True
        self.octave_range = 1

    def get_octave_range(self) -> int:
        """Get the current selected octave range."""
        return knob_2.choice(self.OCTAVE_RANGE) + 1

    def restart(self, octave_range: int) -> None:
        """Restart the scale sequence."""
        self.octave_range = octave_range
        self.step = 0
        self.bi_forward = True

    def next_step(self) -> bool:
        """Proceed to the next step in the scale sequence."""
        if self.step + 1 == self.scale_len():
            self.step = 0
            self.bi_forward = not self.bi_forward
        else:
            self.step += 1
        return True
    
    def scale_len(self) -> int:
        """Returns the step count of the current scale."""
        return self.scale.step_count(self.octave_range)

    def play(self) -> tuple(int):
        """Calculate the current note for each arpeggio pattern."""
        fwd = self.scale.notes[self.step]
        bwd = self.scale.notes[0 : self.scale_len()][0 - self.step - 1]
        bi = fwd if self.bi_forward else bwd
        rnd = choice(self.scale.notes[0 : self.scale_len()])
        return fwd, bwd, bi, rnd

    async def start(self):
        """Start the script execution."""
        # Handler function for button 1 to cycle to the next scale sequence.
        @button_1.handler
        def next_scale():
            self.scale = scales[(scales.index(self.scale) + 1) % len(scales)]
            self.restart(self.get_octave_range())

        # Increment sequence step, or cycle back to the beginning.
        while self.next_step():
            # Set the octave range
            octave_range = self.get_octave_range()
            if octave_range != self.prev_octave_range:
                self.prev_octave_range = octave_range
                self.restart(octave_range)

            # Choose the frequency for each arp direction.
            fwd, bwd, bi, rnd = self.play()
            analog_outputs[0].value(fwd)
            analog_outputs[1].value(bwd)
            analog_outputs[2].value(bi)
            analog_outputs[3].value(rnd)

            # Activate triggers for this scale sequence step.
            trigger(digital_outputs[0])
            if self.step == 0:
                trigger(digital_outputs[1])
            if self.step % 3 == 0:
                trigger(digital_outputs[2])
            if self.step % 4 == 0:
                trigger(digital_outputs[3])

            if DEBUG:
                msg = "{:>2}) A[1:{:>6} 2:{:>6} 3:{:>6} 4:{:>6}] scale:{:>2} octaves:{:>2} tempo: {}".format(
                    self.step, fwd, bwd, bi, rnd, scales.index(self.scale), octave_range, self.clock.tempo
                )
                print(msg)

            await asyncio.sleep_ms(self.clock.wait_ms())


if __name__ == '__main__':
    clock = Clock(knob_1)
    arp = Arpeggiator(clock)

    # Main script function
    async def main():
        loop = asyncio.get_event_loop()
        loop.create_task(arp.start())
        loop.run_forever()

    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()
