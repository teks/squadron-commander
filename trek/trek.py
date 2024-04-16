"""Probably the whole dang game engine is gonna go in here.

"""

import math
import typing
import dataclasses
import abc
import enum
import operator
import random

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
    _combat_value = 1

    def __init__(self, designation: str, point: Point, cruising_speed: float=1.0):
        """Cruising speed is in light year per hour."""
        super().__init__(designation, point)
        self.cruising_speed = cruising_speed
        self.speed = self.cruising_speed
        self.current_order = None # start out with no orders
        self.fought_last_tick = False
        self.current_shields = self.max_shields
        self.current_hull = self.max_hull

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

    def combat_value(self):
        # TODO add in morale and possibly other factors
        return self._combat_value

    def missing_shields_fraction(self):
        """Ships's shields as a ratio; 0.2 = 20% of the shields are gone."""
        return 1 - self.current_shields / self.max_shields

    def hull_damage_fraction(self):
        """Hull damage as a ratio; 0.3 = 30% of the hull is gone."""
        return 1 - self.current_hull / self.max_hull

    def retreats_from(self, own_side, other_side):
        """Randomly determines if a ship retreats from battle.

        Examples of probability of retreat:
            * medium: badly outnumbered
            * medium: shields low
            * high: both --^
            * high: shields down
            * high: significant hull damage
        """
        # TODO:
        # p = 0.0 # 0% chance of retreating as a base
        #
        # # if ratio == 2, then enemy is twice as scary as us
        # battle_cv_ratio = other_side.combat_value() / own_side.combat_value()
        # p += somehow(battle_cv_ratio)
        #
        # # worse off the ship is, more likely to retreat
        # p += msf_factor * self.missing_shields_fraction()
        # p += hdf_factor * self.hull_damage_fraction()
        # retreats = p < random.random()

        retreats = False # MAMA DIDN RAISE NO QUITTER
        if retreats:
            own_side.retreaters += self
        return retreats

    def receive_damage(self, damage_qty: float):
        """Damage shields the given amount, applying overflow to hull.

        If damage is dealt to the hull, it may result in system damage.
        """
        self.current_shields -= damage_qty
        if self.current_shields >= 0.0: # is there overflow damage?
            return
        # TODO message here about shields being down
        hull_damage = -1 * self.current_shields
        self.current_shields = 0.0
        self.current_hull -= hull_damage
        # TODO self.system_damage()
        # TODO check for destruction

    # TODO
    # def system_damage(self):
    #     hdf = self.hull_damage_fraction()

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

@dataclasses.dataclass
class CombatSide:
    """Represents one side of a combat encounter."""
    def __init__(self, *members):
        self.members = set(*members)
        self.retreaters = set()

    @classmethod
    def sort_into_sides(cls, *participants):
        friendly_side, enemy_side = CombatSide(), CombatSide()
        for p in participants:
            {FriendlyShip.type: friendly_side.members,
             EnemyShip.type: enemy_side.members}[p.type].add(p)
        return friendly_side, enemy_side

    RETREAT_MODIFIER = 0.5

    def combat_value(self):
        cv = self.cv_modifier * sum(s.combat_value()
                                    for s in self.members - self.retreaters)
        rcv = self.RETREAT_MODIFIER * sum(s.combat_value() for s in self.retreaters)
        return cv + rcv

    def retreat_chance(self, other_side):
        """What is the chance of this side retreating?"""
        ratio = other_side.combat_value() / self.combat_value()
        if ratio <= 1: # self never retreats if it has the upper hand
            return 0.0
        # set up so P(retreat) = 0 if ratio == 1, and P(retreat) = 0.7 if ratio == 3
        # TODO if ratio == 2 then P(retreat) = 0.35 which feels a bit low
        m, b = 0.35, -0.35
        return m * ratio + b

    # I don't want to open the mocking can of worms, just being lazy:
    #                                   vvvvvvvvvvvvvvv
    def retreats_from(self, other_side, rand_value=None):
        """Does this side choose to retreat?"""
        # garaunteed: 0.0 <= random.random() < 1.0
        retreats = self.retreat_chance(other_side) > (
            random.random() if rand_value is None else rand_value)
        if retreats:
            self.retreaters |= self.members
        return retreats

    def receive_damage(self, damage):
        damage_per_unit = damage / len(self.members)
        for s in self.retreaters:
            s.receive_damage(damage_per_unit * self.RETREAT_MODIFIER)
        for s in self.members - self.retreaters:
            s.receive_damage(damage_per_unit)

    CV_MODIFIERS = (
        (1.25, 0.75),
        (1.00, 1.00),
        (0.75, 1.25),
    )

    @classmethod
    def assign_cv_modifiers(cls, side_a, side_b):
        """Assigns a CV modifier to each side via `side.cv_modifier`."""
        side_a.cv_modifier, side_b.cv_modifier = random.choice(cls.CV_MODIFIERS)


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

    def combat(self, *participants):
        # split participants into sides
        for p in participants:
            p.combat() # notify that they're participating in combat
        friendly_side, enemy_side = CombatSide.sort_into_sides(*participants)
        CombatSide.assign_cv_modifiers(friendly_side, enemy_side)

        friendly_side.retreats_from(enemy_side)
        enemy_side.retreats_from(friendly_side)

        # TODO check each ship for retreat

        friendly_side.receive_damage(enemy_side.combat_value())
        enemy_side.receive_damage(friendly_side.combat_value())

        # TODO here down:
        #   add in notifications & messages
        #   retreat movement; see combat.md

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
