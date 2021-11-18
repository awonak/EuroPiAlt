"""
Helper functions.

"""
from random import random, randint
from time import sleep

import uasyncio as asyncio

from lib.constants import UINT_16
from lib.europi import DigitalOut, digital_outputs


def random_chance(percentage: float) -> bool:
    return random() < percentage


def randint16() -> int:
    return randint(0, UINT_16)

def volts(percentage: float) -> float:
    """Converts a float between 0 and 1 into an equivalent 3.3v value."""
    if percentage > 1:
        raise ValueError("volts expects a percentage between 0 and 1.")
    return percentage * 3.3

def trigger(digital: DigitalOut, delay: int = 10) -> None:
    """Trigger a digital jack in a thread to avoid affecting tempo."""
    loop = asyncio.get_event_loop()
    loop.create_task(_trigger(digital, delay))


async def _trigger(digital: DigitalOut, delay: int) -> None:
    digital.value(1)
    await asyncio.sleep_ms(delay)
    digital.value(0)
