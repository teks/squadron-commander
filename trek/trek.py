"""Probably the whole dang game engine is gonna go in here.

"""

import math
import typing
import dataclasses
import abc
import enum
import operator

# min x & y are both 1, not 0, for both spaces and zones
MAX_X = 64
MAX_Y = 64
# size of a zone (a sort of grid laid over the individual spaces).
# Zones are represented as Point instances.
ZONE_SIZE_X = 8
ZONE_SIZE_Y = 8
MAX_ZONE_X = math.ceil(MAX_X / ZONE_SIZE_X)
MAX_ZONE_Y = math.ceil(MAX_Y / ZONE_SIZE_Y)


# TODO point validation vs. the map is not appropriate in all cases:
#   what if it's a relative point ie (+7, -5)?
class Point(typing.NamedTuple):
    """Bounds are from (1, 1) to (MAX_X, MAX_Y), inclusive."""
    x: float
    y: float

    def distance(self, other):
        """Computes the distance between a and b."""
        # recall the distance formula doesn't care which way is up:
        ax, ay = self
        bx, by = other
        d = ((ax - bx)**2 + (ay - by)**2)**0.5
        return d

    def binary_operator(self, other, operator):
        """Implement generic binary operator for Points."""
        return self.__class__(
            *(operator(a, b) for (a, b) in zip(self, other))
        )

    def __add__(self, other):
        return self.binary_operator(other, operator.add)

    def __sub__(self, other):
        return self.binary_operator(other, operator.sub)

    def delta_to(self, other):
        """Return the relative position of other wrt self.

        eg Point(1, 3).delta_to(Point(4, 5)) == Point(3, 2)
        """
        return other - self

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
        return self.__class__(x=1 + (self.x - 0.5) // ZONE_SIZE_X,
                              y=1 + (self.y - 0.5) // ZONE_SIZE_Y)


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


# TODO this is acting like a friendly ship class as it responds to Orders;
#   enemy vessels need a separate class, and this class needs to be renamed
class Ship(SpaceborneObject):
    def __init__(self, designation: str, point: Point, cruising_speed: float=1.0):
        """Cruising speed is in light year per hour."""
        # TODO did I discover that a dataclass doesn't inherit right?
        super().__init__(designation, point)
        self.cruising_speed = cruising_speed
        self.speed = self.cruising_speed
        self.current_order = None # start out with no orders

    class Order(enum.Enum):
        MOVE = 'move'

    def has_orders(self):
        return self.current_order is not None

    def order(self, order: Order, **kwargs):
        if order not in self.Order:
            raise ValueError(f"'{order}' is not a valid order")
        self.current_order = order, kwargs

    def reset_order(self):
        self.current_order = None

    def move(self, destination):
        """Perform 1 tick of movement."""
        # print(f"{self} is MOVIN to {destination}")
        distance_to_dest = self.point.distance(destination)
        travel_distance = min(self.speed, distance_to_dest)
        assert travel_distance > 0, "Unexpectedly arrived at destination"

        relative_dest = self.point.delta_to(destination)
        distance_ratio = travel_distance / distance_to_dest
        self.point += Point(x=(relative_dest.x * distance_ratio),
                            y=(relative_dest.y * distance_ratio))

        if distance_to_dest - travel_distance <= 0.0:
            self.reset_order()
            self.simulation.message(ArriveMessage(self))
            return

    def act(self):
        order, params = self.current_order
        match order:
            case self.Order.MOVE:
                self.move(params['destination'])
            case _:
                raise ValueError(f"Invalid order {self.current_order}")


class Message:
    """Used for sending and receiving signals resulting from game events."""

@dataclasses.dataclass
class ArriveMessage(Message):
    ship: Ship

@dataclasses.dataclass
class SpawnMessage(Message):
    obj: SpaceborneObject

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

    def __post_init__(self):
        for o in self.squadron:
            o.simulation = self

    def objects(self):
        """Generator for all the objects in the simulation."""
        for o in self.squadron:
            yield o

    def message(self, message):
        """Send a message to the simulation and the user interface."""
        self.user_interface.message(message)

    def ready_to_run(self):
        return all(s.has_orders() for s in self.squadron)

    def idle_ships(self):
        """Returns a set of idle friendly vessels."""
        return set(s for s in self.squadron if not s.has_orders())

    def should_pause(self):
        if not self.ready_to_run():
            return True

        # there will be more checks here for other events
        # (likely these events will be detected by message()
        # and saved, and should be cleared here)

        return False

    class NotReadyToRun(ValueError):
        pass

    def run(self, duration=24):
        if not self.ready_to_run():
            raise self.NotReadyToRun()
        stop_time = self.clock + duration
        while self.clock < stop_time:
            self.clock += 1
            for s in self.squadron:
                # TODO receive messages here instead of SpaceborneObject.simulation?
                #   can self.simulation be removed?
                s.act()
            if self.should_pause():
                break


def default_scenario():
    SpaceborneObject.designations = set()
    ships = {
        Ship('abel', point(x=5, y=5)),
        Ship('baker', point(35, 30)),
        Ship('charlie', point(60, 60)),
        Ship('doug', point(4, 58)),
        Ship('alice', point(7, 7)),
    }
    sim = Simulation(ships)
    return sim