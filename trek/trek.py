"""Probably the whole dang game engine is gonna go in here.

"""

import typing
import dataclasses
import abc

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
            raise AttributeError(f"{self} is outside the map bounds")


def point(*args, **kwargs):
    """Factory for Points.

    Because NamedTuple doesn't let you override the constructor.
    """
    p = Point(*args, **kwargs)
    p.validate()
    return p


@dataclasses.dataclass
class SpaceborneObject(abc.ABC):
    """All vessels, planets, stations, and other objects."""
    designation: str
    position: Point


@dataclasses.dataclass
class Ship(SpaceborneObject):
    pass


class Map:
    """Area of operations for a specific playthrough.

    Spaceborne objects may stack, because it's space.
    """
    def __init__(self, contents=None):
        if contents is None:
            contents = dict()
        self.contents = contents # set or list most likely


class UserInterface:
    pass


@dataclasses.dataclass
class Simulation:
    """Holds all the information necessary for the simulation.

    Also can access most of the semantics too.
    """
    map: Map
    # left None here for bootstrapping porpoises
    user_interface: UserInterface = None
    clock: int = 0 # game clock; starts at 0. User will be shown stardate


def default_scenario():
    ships = [
        Ship('abel', point(x=5, y=5)),
        Ship('baker', point(35, 30)),
        Ship('charlie', point(60, 60)),
        Ship('doug', point(4, 58)),
    ]
    map = Map(contents=ships)
    sim = Simulation(map)
    return sim