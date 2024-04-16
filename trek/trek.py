"""Probably the whole dang game engine is gonna go in here.

TYPING: 2D points are just 2-tuples. Most other things (spaceborne objects,
cartographic entities like 'quadrants') are instances of classes.
"""

import typing

class Point(typing.NamedTuple):
    horiz: int
    vert: int

    def distance(self, other):
        """Computes the distance between a and b."""
        ax, ay = self
        bx, by = other
        d = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
        return d


class Map:
    """Area of operations for a playthrough.

    Spaceborne objects may stack, because it's space.
    """
    def __init__(self):
        self.contents = dict() # tuple location -> spaceborne object
