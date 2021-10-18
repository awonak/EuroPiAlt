"""
Scales
author: awonak
version: 1.0

Common musical scales for quantized pitch output.

This library provides a class to construct a musical scale given the steps in
that musical scale. The class also provides convenience methods for playing
the scale in several ways.

"""
from lib.constants import CHROMATIC_STEP


class Scale:
    """A series of notes in a scale and its sequence state."""

    OCTAVE_RANGE = 3

    notes: list(int)
    include_octave: bool

    def __init__(self, notes: tuple(int), include_octave: bool = False) -> None:
        if include_octave:
            self.notes = create_scale(notes, max_steps=37)
        else:
            self.notes = create_scale(notes)
        self.include_octave = include_octave

    # Scale length for the given octave range.
    def step_count(self, octave_range) -> int:
        length = int((len(self.notes) / self.OCTAVE_RANGE) * octave_range)
        if self.include_octave:
            length += 1
        return min(length, len(self.notes))


def create_scale(notes: tuple(int), max_steps: int = 36):
    if max_steps > 37:
        raise ValueError("More than 37 steps will exceed pico's 3.3V output")
    scale = []
    note = 0
    step = 1
    while note < (CHROMATIC_STEP * max_steps):
        if step in notes:
            scale.append(int(note))
        note += CHROMATIC_STEP
        step += 1
        if step == 13:
            step = 1
    return scale


# Create a full 3 octave chromatic scale for sequencer pitch.
chromatic_scale = create_scale(range(1,13), max_steps=37)


# Define the scales available.
scales = [
    Scale([1, 3, 5, 6, 8, 10, 12], include_octave=True),  # Major scale
    Scale([1, 3, 4, 6, 8, 9, 11], include_octave=True),  # Minor scale
    Scale([1, 5, 8]),  # Major triad
    Scale([1, 4, 8]),  # Minor triad
    Scale([1, 3, 5, 6, 8]),  # Major pentatonic
    Scale([1, 4, 5, 6, 9]),  # Minor pentatonic
    Scale(range(1, 13), include_octave=True),  # Chromatic scale
    Scale([1], include_octave=True),  # Octave
    Scale([1, 12]),  # Octave + 7th
]
