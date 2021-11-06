"""
Sequencer
author: awonak
version: 3.0

4 channels sequencer with 8 programmable steps of quantized pitch.

Long press button_1 to change between play and edit modes.
Long press button_2 to cycle through analog outs for editing.


Edit Mode:
knob_1: adjust pitch for current output
knob_2: adjust octave for current output
button_1: trigger current step / toggle between play and edit mode
button_2: cycle to next step / cycle to next output
analog_1: pattern 1 output
analog_2: pattern 2 output
analog_3: pattern 3 output
analog_4: pattern 4 output
digital_1: step trigger
digital_2: (state display) step change
digital_3: (state display) note value change
digital_4: (state display) output change

Play Mode:
knob_1: master tempo
button_1: play/pause / change to Edit mode
analog_1: pattern 1 output
analog_2: pattern 2 output
analog_3: pattern 3 output
analog_4: pattern 4 output
digital_1: step trigger

"""
import uasyncio as asyncio

# User libraries
from lib.button import Pushbutton
from lib.clock import Clock
from lib.europi import Knob, knob_1
from lib.europi import knob_2
from lib.europi import button_1
from lib.europi import button_2
from lib.europi import digital_outputs
from lib.europi import analog_outputs
from lib.helpers import trigger
from lib.scales import chromatic_scale


DEBUG = True


class Sequencer:
    # State variables
    run = False
    edit = True
    counter = 0
    selected_output = 0
    _previous_pitch = 0

    def __init__(self, clock: Clock, seq_len: int = 8):
        # Initialize instance variables
        self.clock = clock
        self.clock.toggle_edit(False)  # Disable clock edit
        self.seq_len = seq_len
        self.pitch = [
            [0] * self.seq_len,
            [0] * self.seq_len,
            [0] * self.seq_len,
            [0] * self.seq_len,
        ]

    def _short1(self):
        if self.edit:
            self.play_step()
        else:
            self.toggle_run()

    def _long1(self):
        self.toggle_edit()

    def _short2(self):
        if self.edit:
            self.next_step()

    def _long2(self):
        if self.edit:
            self.toggle_output()

    def toggle_run(self):
        """Toggle between sequence play/pause state."""
        self.run = not self.run

    def toggle_output(self):
        """Toggle between editing analogue outs."""
        self.selected_output = (self.selected_output + 1) % 4
        trigger(digital_outputs[3])

    def toggle_edit(self):
        """Toggle between playback and edit mode."""
        if self.edit == True:
            self.clock.toggle_edit(True)
            self.edit = False
            self.run = True
        else:
            self.clock.toggle_edit(False)
            self.edit = True
            self.run = False
            self.counter = 0

    def get_pitch(self) -> int:
        """Get the pitch cv value for the given knob position."""
        # TODO: allow user selected scales
        p = knob_1.choice(13)
        o = knob_2.choice(3) * 12
        return chromatic_scale[p + o]

    def adjust_step(self):
        """Set the pitch for the current output."""
        pitch = self.get_pitch()
        if pitch != self._previous_pitch:
            self.pitch[self.selected_output][self.counter] = pitch
            self._previous_pitch = pitch
            self.play_step()
            trigger(digital_outputs[2])


    def play_step(self):
        # Play pitch/velocity
        analog_outputs[0].value(self.pitch[0][self.counter])
        analog_outputs[1].value(self.pitch[1][self.counter])
        analog_outputs[2].value(self.pitch[2][self.counter])
        analog_outputs[3].value(self.pitch[3][self.counter])
        # Trigger digital 1
        trigger(digital_outputs[0])
        self.debug()

    def next_step(self):
        self.counter = (self.counter + 1) % self.seq_len
        # In edit mode blink d1 to show editing position.
        if self.edit:
            if self.counter == 0:
                # Longer blink to indicate pattern start.
                trigger(digital_outputs[1], 500)
            else:
                trigger(digital_outputs[1])
        self.debug()

    def debug(self):
        if DEBUG:
            print("S:{} R{} \tA1: {} \tA2: {} \tA3: {} \tA4: {}".format(
                self.counter, self.selected_output,
                self.pitch[0][self.counter], self.pitch[1][self.counter],
                self.pitch[2][self.counter], self.pitch[3][self.counter]))

    def register_buttons(self):
        # Set up the buttons
        Pushbutton(button_1.pin)\
            .press_func(self._short1)\
            .long_func(self._long1)

        Pushbutton(button_2.pin)\
            .press_func(self._short2)\
            .long_func(self._long2)

    def reset_state(self):
        self.run = False
        self.edit = True
        self.counter = 0
        self.selected_output = 0

    async def start(self):
        # Register the button handlers and module state.
        self.register_buttons()
        self.reset_state()

        # Main loop.
        while True:
            # Play sequence
            if self.run:
                self.play_step()
                self.next_step()
            # Edit sequence
            elif self.edit:
                self.adjust_step()

            await asyncio.sleep_ms(self.clock.wait_ms())


if __name__ == '__main__':
    clock = Clock(knob_1)
    seq = Sequencer(clock)

    # Main script function
    async def main():
        loop = asyncio.get_event_loop()
        loop.create_task(seq.start())
        loop.run_forever()

    try:
        asyncio.run(main())
    finally:
        asyncio.new_event_loop()
