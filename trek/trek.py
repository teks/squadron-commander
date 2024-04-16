"""Probably the whole dang game engine is gonna go in here.

"""

import math
import typing
import dataclasses
import abc
import enum

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
    def __init__(self, designation: str, point: Point, ftl_max_velocity: int=1):
        super().__init__(designation, point)
        self.ftl_max_velocity = ftl_max_velocity
        self.current_order = None # start out with no orders

    class Order(enum.Enum):
        MOVE = 'move'

    def has_orders(self):
        return self.current_order is not None

    def order(self, order: Order, **kwargs):
        if order not in self.Order:
            raise ValueError(f"'{order}' is not a valid order")
        self.current_order = order, kwargs


class UserInterface:
    pass


@dataclasses.dataclass
class Simulation:
    """Holds all the information necessary for the simulation.

    Also can access most of the semantics too.
    """
    squadron: set = dataclasses.field(default_factory=set)
    # left None here for bootstrapping porpoises
    user_interface: UserInterface = None
    clock: int = 0 # game clock; starts at 0. User will be shown stardate
    # player's ships:

    class Message(enum.Enum):
        ARRIVE = 'arrive'

    def __post_init__(self):
        for o in self.squadron:
            o.simulation = self

    def objects(self):
        """Generator for all the objects in the simulation."""
        for o in self.squadron:
            yield o

    def message(self, type, text, **details):
        """Cause the simulation to emit a message to the user interface."""
        self.user_interface.message(type, text, **details)

    def ready_to_run(self):
        return all(s.has_orders() for s in self.squadron)

    def should_pause(self):
        if not self.ready_to_run():
            return True

        # there will be more checks here for other events
        # (likely these events will be detected by message()
        # and saved, and should be cleared here)

        return False

    class NotReadyToRun(ValueError):
        pass

    def run(self, force=False):
        if not force and not self.ready_to_run():
            raise self.NotReadyToRun()
        while True:
            self.clock += 1
            for s in self.squadron:
                s.act()
            if self.should_pause():
                break


def default_scenario():
    ships = {
        Ship('abel', point(x=5, y=5)),
        Ship('baker', point(35, 30)),
        Ship('charlie', point(60, 60)),
        Ship('doug', point(4, 58)),
        Ship('alice', point(7, 7)),
    }
    sim = Simulation(ships)
    return sim