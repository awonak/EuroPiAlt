"""
Sequencer
author: awonak
version: 2.1

4 channels sequencer with 8 programmable steps of quantized pitch.

Long press button_1 to toggle between row (A1, A2) and (A3, A4).
Long press button_2 to change between play and edit modes.


Edit Mode:
knob_1: adjust pitch for current step & row
knob_2: adjust velocity for current step & row
button_1: trigger current step / toggle row
button_2: cycle to next step / change to Play mode
analog_1: row 1 left pitch output
analog_2: row 1 right pitch output
analog_3: row 2 left pitch output
analog_4: row 2 right pitch output
digital_1: step trigger
digital_2: (state display) step change
digital_3: (state display) row 1 active (A1, A2)
digital_4: (state display) row 2 active (A3, A4)

Play Mode:
knob_1: master tempo
button_1: play/pause
button_2: _ / change to Edit mode
analog_1: row 1 left pitch output
analog_2: row 1 right pitch output
analog_3: row 2 left pitch output
analog_4: row 2 right pitch output
digital_1: step trigger

"""
import uasyncio as asyncio

# User libraries
from src.lib.button import Pushbutton
from src.lib.clock import Clock
from src.lib.europi import Knob, knob_1
from src.lib.europi import knob_2
from src.lib.europi import button_1
from src.lib.europi import button_2
from src.lib.europi import digital_outputs
from src.lib.europi import analog_outputs
from src.lib.helpers import blink
from src.lib.scales import chromatic_scale


DEBUG = False


class Sequencer:
    # State variables
    run = False
    edit = True
    counter = 0
    row = 0
    _previous_pitch_left = 0
    _previous_pitch_right = 0
    
    def __init__(self, clock: Clock, seq_len: int = 8):
        # Initialize instance variables
        self.clock = clock
        self.seq_len = seq_len
        self.pitch = [
            [0] * self.seq_len, [0] * self.seq_len,
            [0] * self.seq_len, [0] * self.seq_len,
        ]
    
    def _short1(self):
        if self.edit:
            self.play_step()
        else:
            self.toggle_run()
    
    def _long1(self):
        if self.edit:
            self.toggle_row()
            
    def _short2(self):
        if self.edit:
            self.next_step()

    def _long2(self):
        self.toggle_edit()

    def toggle_run(self):
        """Toggle between sequence play/pause state."""
        self.run = not self.run
    
    def toggle_row(self):
        """Toggle between editing analogue rows."""
        self.row = (self.row + 1) % 2
        digital_outputs[2].value(1 if self.row == 0 else 0)
        digital_outputs[3].value(1 if self.row == 1 else 0)
    
    def toggle_edit(self):
        """Toggle between playback and edit mode."""
        if self.edit == True:
            self.edit = False
            self.run = True
            digital_outputs[1].value(0)
            digital_outputs[2].value(0)
            digital_outputs[3].value(0)
        else:
            self.edit = True
            self.run = False
            self.counter = 0
            digital_outputs[2].value(1 if self.row == 0 else 0)
            digital_outputs[3].value(1 if self.row == 1 else 0)

    def get_pitch(self, knob: Knob) -> int:
        """Get the pitch cv value for the given knob position."""
        i = knob.choice(len(chromatic_scale))
        return chromatic_scale[i]
    
    def adjust_step(self):
        """Set the left and right pitch for the current step and row."""
        # Adjust row left pitch
        pitch = self.get_pitch(knob_1)
        if pitch != self._previous_pitch_left:
            self.pitch[self.row][self.counter] = pitch
            self._previous_pitch = pitch
        # Adjust row right pitch
        pitch = self.get_pitch(knob_2)
        if pitch != self._previous_pitch_right:
            self.pitch[self.row + 2][self.counter] = pitch
            self._previous_pitch = pitch
        
    def play_step(self):
        # Play pitch/velocity
        analog_outputs[0].value(self.pitch[0][self.counter])
        analog_outputs[1].value(self.pitch[2][self.counter])
        analog_outputs[2].value(self.pitch[1][self.counter])
        analog_outputs[3].value(self.pitch[3][self.counter])
        # Trigger digital 1
        blink(digital_outputs[0], 10)
        self.debug()

    def next_step(self):
        self.counter = (self.counter + 1) % self.seq_len
        # In edit mode blink d1 to show editing position.
        if self.edit:           
            if self.counter == 0:
                # Longer blink to indicate pattern start.
                blink(digital_outputs[1], 500)
            else:
                blink(digital_outputs[1], 10)
        self.debug()
    
    def debug(self):
        if DEBUG:
            print("S:{} R{} \tA1: {} \tA2: {} \tA3: {} \tA4: {}".format(
                self.counter, self.row,
                self.pitch[0][self.counter], self.pitch[2][self.counter],
                self.pitch[1][self.counter], self.pitch[3][self.counter]))

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
        self.row = 0
        # Set initial display state.
        # Default state is edit mode with top row selected.
        digital_outputs[2].value(1)
        digital_outputs[3].value(0)


    async def start(self):
        # Register the button handlers and module state.
        self.register_buttons()
        self.reset_state()
        
        # Main loop.
        while True:
            # Play sequence
            if self.run:
                self.clock.wait()
                self.play_step()
                self.next_step()
            # Edit sequence
            elif self.edit:
                self.adjust_step()

            await asyncio.sleep_ms(0)


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
