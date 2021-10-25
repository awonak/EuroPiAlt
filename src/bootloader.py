"""
Bootloader

Main entrypoint script used to select a script from a list of registered scripts.

Hold both buttons for >1 second to stop script and return to the bootloader.
"""
from utime import sleep_ms
import uasyncio as asyncio

from lib.europi import knob_1
from lib.europi import button_1
from lib.europi import button_2
from lib.europi import digital_outputs
from lib.clock import Clock
from lib.button import Pushbutton
from lib.ui import display_choice
from lib.ui import digital_off
from lib.ui import loading_animation

from scripts.arpeggiator import Arpeggiator
from scripts.clock_divider import ClockDivider
from scripts.sequencer import Sequencer
from scripts.turing_machine import TuringMachine
from scripts.smooth_random_voltages import SmoothRandomVoltages

# Initialize a Clock for the sequencer.
#clock = Clock(tempo_knob = knob_1,
#              clock_bus = digital_in,
#              clock_switch = digital_sw)  # Use this with external clock source.
# Use this clock config when no external EuroPi clock present.
clock = Clock(knob_1)


# Register each script individually in the scripts list.
scripts = [
    Arpeggiator(clock),
    ClockDivider(clock),
    Sequencer(clock),
    TuringMachine(clock),
    SmoothRandomVoltages(clock),
]
SCRIPT_COUNT = len(scripts)


# When both button 1 and 2 are long pressed, return to the bootloader.
def add_reset_handler():
    def _reset_check(b2):
        # If long press detected on button_1, check if button_2 is also pressed.
        if b2.value() == 0:
            loop = asyncio.get_event_loop()
            loop.stop()
            loading_animation()
            loop.close()

    Pushbutton(button_1.pin)\
            .long_func(_reset_check, (button_2,))


async def main(script: any):
    # Display the selected script.
    digital_off()
    add_reset_handler()
    sleep_ms(500)
    # Execute script in main async loop.
    loop = asyncio.get_event_loop()
    loop.create_task(script.start())
    loop.run_forever()


def bootloader():

    # Boot animation.
    loading_animation()

    # Bootloader script selection.
    while True:
        choice = knob_1.choice(SCRIPT_COUNT)
        b = display_choice(choice)

        # Debug logging.
        print("choice: {} display: {} button: {} script: {}".format(
            choice, b, button_1.value(), scripts[choice].__qualname__))

        # If button 1 is pressed, execute the currently selected script.
        if button_1.value() == 0:
            try:
                # Execute the main loop with the currently selected script.
                asyncio.run(main(scripts[choice]))
            finally:
                # This line will stop previous run() method.
                asyncio.new_event_loop()
                # Reset button handlers
                button_1.reset_handler()
                button_2.reset_handler()

        sleep_ms(100)
