"""Probably the whole dang game engine is gonna go in here.

"""

import typing

MAX_X = 64
MAX_Y = 64


class Point(typing.NamedTuple):
    """Bounds are from (1, 1) to (MAX_X, MAX_Y), inclusive."""
    x: int
    y: int

    def distance(self, other):
        """Computes the distance between a and b."""
        # recall the distance formula doesn't care which way is up:
        ax, ay = self
        bx, by = other
        d = ((ax - bx)**2 + (ay - by)**2)**0.5
        return d

    def validate(self):
        """Perform safety checks on self."""
        if not (0 < self.x <= MAX_X) or not (0 < self.y <= MAX_Y):
            raise AttributeError("{} is outside the map bounds".format(self))


def point(*args, **kwargs):
    """Factory for Points.

    Because NamedTuple doesn't let you override the constructor.
    """
    p = Point(*args, **kwargs)
    p.validate()
    return p

class Map:
    """Area of operations for a playthrough.

    Spaceborne objects may stack, because it's space.
    """
    def __init__(self):
        self.contents = dict() # tuple location -> spaceborne object
