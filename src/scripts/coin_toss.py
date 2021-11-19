"""
Coin Toss
author: awonak
version: 1.1

Two pairs of clocked probability gates.

Knob 1 adjusts the master clock speed of gate change probability. Knob 2 moves
the probability thresholed between A and B with a 50% chance at noon. Digital
Out 1 and 2 run at 1x speed and Digital 3 and 4 run at 4x speed for
interesting rhythmic patterns. Push button 1 to toggle turbo mode which brings
the clock speed into audio rate.


knob_1: master clock speed, rate of voltage change
knob_2: probability threshold
button_1: toggle speed normal/turbo
button_2: toggle gate/trigger mode
digital_1: Coin 1 gate on when voltage above threshold
digital_2: Coin 2 gate on when voltage below threshold
digital_3: Coin 2 gate on when voltage above threshold
digital_4: Coin 2 gate on when voltage below threshold
"""
from random import random

import uasyncio as asyncio
from utime import ticks_ms

from lib.clock import Clock
from lib.clock import MAX_BPM
from lib.europi import DigitalOut, knob_1
from lib.europi import knob_2
from lib.europi import button_1
from lib.europi import button_2
from lib.europi import digital_1
from lib.europi import digital_2
from lib.europi import digital_3
from lib.europi import digital_4
from lib.helpers import trigger
from lib.helpers import volts
from lib.ui import digital_off


DEBUG = False
NORMAL = MAX_BPM
TURBO = 10000
TOGGLE_SPEED = NORMAL ^ TURBO


class CoinToss:

    def __init__(self, clock: Clock):
        self.clock = clock
        self.gate_mode = True
    
    def get_next_deadline(self):
        """Get the deadline for next clock tick whole note."""
        return ticks_ms() + (self.clock.wait_ms() * 4)
    
    def toss(self, a: DigitalOut, b: DigitalOut) -> float:
        coin = random()
        threshold = knob_2.percent()
        if self.gate_mode:
            a.value(coin > threshold)
            b.value(coin < threshold)
        else:
            trigger(a if coin > threshold else b)
        return coin

    def debug(self, c1, c2):
        if DEBUG:
            print("COIN1: {:>.2f}  COIN2: {:>.2f}  THRESH: {:>.2f}".format(
                volts(c1), volts(c2), volts(knob_2.percent())))
    
    async def start(self):
        # Register button handlers
        @button_1.handler
        def toggle_speed():
            self.clock.max_bpm ^= TOGGLE_SPEED
        
        @button_2.handler
        def toggle_gate():
            self.gate_mode = not self.gate_mode
            digital_off()
        
        # Start the main loop.
        deadline = self.get_next_deadline()
        coin1 = self.toss(digital_1, digital_2)
        while True:
            # D1/2 pair coin toss on the whole note.
            if ticks_ms() > deadline:
                deadline = self.get_next_deadline()
                coin1 = self.toss(digital_1, digital_2)

            # D3/4 pair coin toss on the quarter note.
            coin2 = self.toss(digital_3, digital_4)

            self.debug(coin1, coin2)
            await asyncio.sleep_ms(self.clock.wait_ms())


if __name__ == '__main__':
    clock = Clock(knob_1)
    coin_toss = CoinToss(clock)
    loop = asyncio.new_event_loop()
    loop.create_task(coin_toss.start())
    loop.run_forever()

