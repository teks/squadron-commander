"""Probably the whole dang game engine is gonna go in here."""

def distance(point_a, point_b):
    """Computes the distance between a and b."""
    ax, ay = point_a
    bx, by = point_b
    d = ((ax - bx)**2 + (ay - by)**2)**0.5
    return d


class Quadrant:
    """Represents one quadrant, an 8x8 grid of sectors.

    Each sector is in turn a single location for an object.
    Objects exclude each other; there is no stacking.
    """
    def __init__(self):
        self.contents = dict() # tuple location -> spaceborne object
