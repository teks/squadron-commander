"""Probably the whole dang game engine is gonna go in here.

"""

import math
import typing
import dataclasses
import abc

# min x & y are both 1, not 0, for both spaces and zones
MAX_X = 64
MAX_Y = 64
# size of a zone (a sort of grid laid over the individual spaces).
# Zones are represented as Point instances.
ZONE_SIZE_X = 8
ZONE_SIZE_Y = 8
MAX_ZONE_X = math.ceil(MAX_X / ZONE_SIZE_X)
MAX_ZONE_Y = math.ceil(MAX_Y / ZONE_SIZE_Y)


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

    # TODO use this  ----vvvvvvvvv
    def validate(self, is_zone=False):
        """Perform safety checks on self."""
        max_x, max_y = MAX_X, MAX_Y
        if is_zone:
            max_x, max_y = MAX_ZONE_X, MAX_ZONE_Y
        if not (0 < self.x <= max_x) or not (0 < self.y <= max_y):
            raise AttributeError(f"{self} is outside the map bounds")

    def zone(self):
        """Determine which zone the current point is in."""
        return self.__class__(x=1 + (self.x - 1) // ZONE_SIZE_X,
                              y=1 + (self.y - 1) // ZONE_SIZE_Y)


def point(*args, **kwargs):
    """Factory for Points.

    Needed for validating at instantiation time,
    but NamedTuple doesn't let you override the constructor.
    """
    p = Point(*args, **kwargs)
    p.validate()
    return p


def zone(*args, **kwargs):
    """Factor for zones, which are points with different validation."""
    p = Point(*args, **kwargs)
    p.validate_zone()
    return p


class SpaceborneObject(abc.ABC):
    """All vessels, planets, stations, and other objects."""
    # TODO may want to scope this by Simulation
    designations = set()

    def __init__(self, designation: str, point: Point):
        if designation in self.designations:
            raise ValueError(f"SpaceborneObject designated '{designation}' already exists")
        self.designations.add(designation)
        self.designation = designation
        self.point = point

    def __hash__(self):
        return hash(self.designation)

    def __repr__(self):
        fq_name = self.__class__.__module__ + '.' + self.__class__.__qualname__
        return f"<{fq_name} {self.designation} {self.point}>"


# TODO are Ships friendly or is this the superclass for friendly and enemy ships?
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
    ships = {
        Ship('abel', point(x=5, y=5)),
        Ship('baker', point(35, 30)),
        Ship('charlie', point(60, 60)),
        Ship('doug', point(4, 58)),
        Ship('alice', point(7, 7)),
    }
    map = Map(contents=ships)
    sim = Simulation(map)
    return sim