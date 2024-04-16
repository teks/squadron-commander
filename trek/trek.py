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


class Point(typing.NamedTuple):
    """Bounds are from (1, 1) to (MAX_X, MAX_Y), inclusive.

    Neither NamedTuple's __init__ nor __new__ can be overridden, so use
    the factory functions below for validation.
    """
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

    def validate(self, is_zone=False):
        """Perform safety checks on self."""
        max_x, max_y = MAX_X, MAX_Y
        if is_zone:
            max_x, max_y = MAX_ZONE_X, MAX_ZONE_Y
        if not (0 < self.x <= max_x) or not (0 < self.y <= max_y):
            raise AttributeError(f"{self} is outside the map bounds")

    def validate_as_zone(self):
        return self.validate(is_zone=True)

    def zone(self):
        """Determine which zone the current point is in."""
        return zone(x=1 + (self.x - 0.5) // ZONE_SIZE_X,
                    y=1 + (self.y - 0.5) // ZONE_SIZE_Y)


def point(*args, **kwargs):
    """Factory for Points that represent an aboslute map cell."""
    p = Point(*args, **kwargs)
    p.validate()
    return p


def zone(*args, **kwargs):
    """Factory for points that represent one zone."""
    p = Point(*args, **kwargs)
    p.validate_as_zone()
    return p


class SpaceborneObject(abc.ABC):
    """All vessels, planets, stations, and other objects."""
    type = None # for organizing spaceborne objects by category

    def __init__(self, designation: str, point: Point):
        self.designation = designation
        self.point = point

    def __hash__(self):
        return hash(self.designation)

    def __repr__(self):
        fq_name = self.__class__.__module__ + '.' + self.__class__.__qualname__
        return f"<{fq_name} {self.designation} {self.point}>"


class Ship(SpaceborneObject):
    """Mobile spaceborne object. Issue orders to have it move and take other actions."""
    max_hull = 1
    max_shields = 0
    combat_value = 1

    def __init__(self, designation: str, point: Point, cruising_speed: float=1.0):
        """Cruising speed is in light year per hour."""
        super().__init__(designation, point)
        self.cruising_speed = cruising_speed
        self.speed = self.cruising_speed
        self.current_order = None # start out with no orders
        self.fought_last_tick = False
        self.current_shields = self.max_shields

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

    def move(self, simulation, destination):
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
            simulation.message(ArriveMessage(self))
            return

    def recharge_shields(self):
        if self.fought_last_tick:
            self.fought_last_tick = False
        else:
            self.current_shields = self.max_shields

    def combat(self):
        """Notify the ship that it has fought this tick."""
        self.fought_last_tick = True

    def act(self, simulation):
        """Perform one tick of simulation."""
        self.recharge_shields()
        order, params = self.current_order
        match order:
            case self.Order.MOVE:
                self.move(simulation, params['destination'])
            case _:
                raise ValueError(f"Invalid order {self.current_order}")


class FriendlyShip(Ship):
    type = 'friendly'


class EnemyShip(Ship):
    type = 'enemy'

    def act(self, simulation):
        pass # stub for now


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


class Simulation:
    """Holds all the information necessary for the simulation.

    Also can access most of the semantics too.
    """
    def __init__(self, objects, user_interface: UserInterface=None, clock: int=0):
        self.user_interface = user_interface
        self.clock = clock
        self.objects = {(o.type, o.designation): o for o in objects}
        if len(objects) != len(self.objects):
            raise ValueError("Objects with duplicate keys detected.")

    def get_objects(self, type=None):
        """Yield objects, optionally by type."""
        yield from (self.objects.values() if type is None else
                    (o for (t, _), o in self.objects.items() if t == type))

    def get_object(self, type, designation):
        return self.objects[(type, designation)]

    def add_object(self, obj):
        k = (obj.type, obj.designation)
        if k in self.objects:
            raise ValueError(f"Object with key {k} already found: {self.objects[k]}")
        self.objects[k] = obj
        self.message(SpawnMessage(obj))

    def side_combat_value(self, side):
        return sum(s.combat_value for s in side)

    def combat(self, *participants):
        friendly_side, enemy_side = set(), set()
        for p in participants:
            p.combat()
            {FriendlyShip.type: friendly_side,
             EnemyShip.type:    enemy_side}[p.type].add(p)

        friendly_cv = self.side_combat_value(friendly_side)
        enemy_cv = self.side_combat_value(enemy_side)

        outnumbered = enemy_cv > friendly_cv
        cv_ratio = friendly_cv / enemy_cv

        # report outcomes; effectively each battle is exactly 1 tick
        # self.combat_outcome_message(self, friendly_side, enemy_side)

    def message(self, message):
        """Send a message to the simulation and the user interface."""
        if self.user_interface is not None:
            self.user_interface.message(message)

    def ready_to_run(self):
        """Report whether the simulation is ready to run.

        Any idle friendly ships prevent the simulation from running.
        """
        return len(self.idle_ships()) == 0

    def idle_ships(self):
        """Returns a set of idle friendly vessels."""
        return set(s for s in self.get_objects(FriendlyShip.type) if not s.has_orders())

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
            for s in self.get_objects():
                s.act(self)
            if self.should_pause():
                break


def default_scenario():
    ships = {
        FriendlyShip('abel', point(x=5, y=5)),
        FriendlyShip('baker', point(35, 30)),
        FriendlyShip('charlie', point(60, 60)),
        FriendlyShip('doug', point(4, 58)),
        FriendlyShip('alice', point(7, 7)),
    }
    sim = Simulation(ships)
    return sim
