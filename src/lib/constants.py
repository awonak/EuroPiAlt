"""
Common constant value definitions.

"""

# Maximum unsigned 16 bit integer value.
UINT_16 = 65535

# One chromatic step given 16 bit over 3.3v output. 
CHROMATIC_STEP = UINT_16 / (11.75 * 3.3)
