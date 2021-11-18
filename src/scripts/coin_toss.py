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
from lib.europi import knob_1
from lib.europi import knob_2
from lib.europi import button_1
from lib.europi import digital_1
from lib.europi import digital_2
from lib.europi import digital_3
from lib.europi import digital_4
from lib.helpers import volts


DEBUG = False
NORMAL = MAX_BPM
TURBO = 10000
TOGGLE_SPEED = NORMAL ^ TURBO


class CoinToss:

    def __init__(self, clock: Clock):
        self.clock = clock
    
    def get_next_deadline(self):
        """Get the deadline for next clock tick whole note."""
        return ticks_ms() + (self.clock.wait_ms() * 4)

    def debug(self, c1, c2, t):
        if DEBUG:
            print("COIN1: {:>.2f}  COIN2: {:>.2f}  THRESH: {:>.2f}".format(
                volts(c1), volts(c2), volts(t)))
    
    async def start(self):
        # Register button handlers
        @button_1.handler
        def toggle_speed():
            self.clock.max_bpm ^= TOGGLE_SPEED
            
        # Start the main loop.
        deadline = self.get_next_deadline()
        coin1 = random()
        while True:
            if ticks_ms() > deadline:
                coin1 = random()
                deadline = self.get_next_deadline()
                
            coin2 = random()
            threshold = knob_2.percent()
            
            digital_1.value(coin1 > threshold)
            digital_2.value(coin1 < threshold)
            digital_3.value(coin2 > threshold)
            digital_4.value(coin2 < threshold)

            self.debug(coin1, coin2, threshold)
            await asyncio.sleep_ms(self.clock.wait_ms())


if __name__ == '__main__':
    clock = Clock(knob_1)
    coin_toss = CoinToss(clock)
    loop = asyncio.new_event_loop()
    loop.create_task(coin_toss.start())
    loop.run_forever()

