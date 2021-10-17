"""
Helper functions for dispalying state and animations using the digital LEDs on
the EuroPi.

NOTE: Animations should not use async because they can be used by the
      main/bootloader scripts outside of an event loop.

"""
from random import choice, randint

from utime import sleep_ms

from src.lib.europi import DigitalOut, digital_outputs


def display_choice(choice: int) -> str:
    """Display given choice as binary using the digital LEDs.
    
    Convert the input choice (0..15) to a 4 bit binary and display that on the
    digital out LEDs. Returns the 4 bit binary string.
    """
    if choice > 15:
        raise ValueError("choice must be between 0 and 15")
    # Convert the choice into 4 bit binary used to show choice in the 4
    # digital out LEDs.
    b = bin(choice).replace('0b', '')
    while len(b) < 4:
        b = "0" + b
    # Convert each positional binary value into corresponding digital output
    # LED value.
    for i, output in enumerate(digital_outputs):
        output.value(int(b[i]))
    return b


def loading_animation() -> None:
    """Cycle the lights of the digital LEDs in a back and forth snake pattern 
    for 3 iterations."""
    sleep_ms(500)
    [_blink(d) for d in digital_outputs + digital_outputs[::-1] * 3]
    sleep_ms(500)


def sparkle_animation(count: int = 30) -> None:
    """Randomly blink the digital LEDs for the given number of iterations."""
    for _ in range(count):
        _blink(choice(digital_outputs), randint(10, 50))
        sleep_ms(randint(30, 70))


def _blink(d: DigitalOut, ms: int):
    d.value(1)
    sleep_ms(ms)
    d.value(0)
