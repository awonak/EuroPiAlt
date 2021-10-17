"""
Turing Machine
author: roryjamesallen
version: 1.1

Play a sequence that changes notes within a scale according to the probability set by knob 2.

Use knob 1 to adjust the master clock tempo. The second knob increases the
probability that a note within the sequence will get changed on each step.
The first two analogue jacks play a quantized pitch while the last two
analogue jacks will play a random cv value. Digital 1 will trigger each step,
while digital 2 plays a gate for the duration of the step. Digital 3 will
trigger if a note is changed in the current step and digital 4 will trigger
when the sequence restarts.

knob_1: set master clock tempo
knob_2: set new note chance
button_1: introduce a new note
button_2: lock sequence
analogue_1: 1V/Oct pitch or timbre control
analogue_2: 1V/Oct pitch or timbre control
analogue_3: random cv
analogue_4: random cv
digital_1: trigger
digital_2: gate
digital_3: note changed
digital_4: sequence reset
"""
from random import choice

import uasyncio as asyncio

from src.lib.clock import Clock
from src.lib.europi import button_1
from src.lib.europi import button_2
from src.lib.europi import knob_1
from src.lib.europi import knob_2
from src.lib.europi import digital_outputs
from src.lib.europi import analog_outputs
from src.lib.helpers import blink
from src.lib.helpers import randint16
from src.lib.helpers import random_chance
from src.lib.scales import Scale, scales


class TuringStep:
    pitch1: int
    pitch2: int

    def __init__(self, scale: Scale):
        self.pitch_1 = choice(scale)
        self.pitch_2 = choice(scale)
    
    def play(self, step_duration: int):
        # Play quantized pitch on Analog 1 & 2.
        analog_outputs[0].value(self.pitch_1)
        analog_outputs[1].value(self.pitch_2)

        # Play random notes on Analog 3 & 4.
        analog_outputs[2].value(randint16())
        analog_outputs[3].value(randint16())
        
        #The gate is turned on as this is 'open' the whole time the note is active
        blink(digital_outputs[0], 50)
        blink(digital_outputs[1], step_duration - 10)


class TuringMachine:
    sequence: list(TuringStep)

    def __init__(self, clock: Clock):
        self.clock = clock
        self.sequence =  []
        self.sequence_length = 8
        self.scale = scales[0]
        self.step = 0
        self.lock = False

    async def start(self):
        # Register button handlers.
        @button_1.handler
        def push_new_note(self):
            self.sequence[self.step] = new_note
            digital_outputs[2].value(1)

        @button_2.handler
        def push_lock(self):
            self.lock = not self.lock

        while True:
            # The sequence has started again, so the reset indicator is turned off.
            digital_outputs[3].value(0)
            new_note = TuringStep(self.scale)

            # The new note can only be swapped out if the sequence has reached its final length, so not for the first x steps.
            if len(self.sequence) == self.sequence_length: 
                # The note is then dependent on the random chance controlled by knob 2
                if random_chance(knob_2.percent()): 
                    if self.lock == False:
                        self.sequence[self.step] = new_note
                        # The jack to indicate a new note has been added is turned on
                        digital_outputs[2].value(1)
            # If the sequence hasn't yet reached its full length, the note is added to the end.
            else:
                self.sequence.append(new_note)
            
            # Play the current step.
            self.sequence[self.step].play(self.clock.wait_ms)
            
            # The jack to indicate a new note is turned off as the note is over
            digital_outputs[2].value(0)
            
            self.step += 1
            if self.step == self.sequence_length:
                self.step = 0
                digital_outputs[3].value(1)

            self.clock.wait()



# Run the script if called directly.
if __name__ == '__main__':
    clock = Clock(knob_1)
    turing = TuringMachine(clock)
    
    # Main script function
    async def main():
        loop = asyncio.get_event_loop()
        loop.create_task(turing.start())
        loop.run_forever()

    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()
