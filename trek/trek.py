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

    def __init__(self, designation: str, point: Point, simulation=None):
        self.designation = designation
        self.point = point
        self.simulation = simulation

    def __hash__(self):
        return hash(self.designation)

    def __repr__(self):
        fq_name = self.__class__.__module__ + '.' + self.__class__.__qualname__
        return f"<{fq_name} {self.designation} {self.point}>"


class Ship(SpaceborneObject):
    """Mobile spaceborne object. Issue orders to have it move and take other actions."""
    cruising_speed = 1
    max_hull = 1
    max_shields = 0
    _combat_value = 1

    def __init__(self, designation: str, point: Point, simulation=None):
        """Cruising speed is in light year per hour."""
        super().__init__(designation, point, simulation)
        self.speed = self.cruising_speed
        self.current_order = None # start out with no orders
        self.fought_last_tick = False
        self.current_shields = self.max_shields
        self.current_hull = self.max_hull

    class Order(enum.Enum):
        MOVE = 'move'
        ATTACK = 'attack'

    def has_orders(self):
        return self.current_order is not None

    def order(self, order: Order, **kwargs):
        if order not in self.Order:
            raise ValueError(f"'{order}' is not a valid order")
        self.current_order = order, kwargs

    def reset_order(self):
        self.current_order = None

    def message(self, message):
        if self.simulation is not None:
            self.simulation.message(message)

    def move(self, destination):
        """Perform 1 tick of movement."""
        self.point = self.future_position(destination, ticks=1)
        if self.point == destination:
            self.reset_order()
            self.message(ArriveMessage(self))

    def future_position(self, destination: Point, ticks):
        if self.point == destination:
            return self.point
        distance_to_dest = self.point.distance(destination)
        travel_distance = min(ticks * self.speed, distance_to_dest)
        relative_dest = self.point.delta_to(destination)
        distance_ratio = travel_distance / distance_to_dest
        return self.point + Point(x=(relative_dest.x * distance_ratio),
                                  y=(relative_dest.y * distance_ratio))

    def recharge_shields(self):
        if self.fought_last_tick:
            self.fought_last_tick = False
        else:
            self.current_shields = self.max_shields

    def combat_value(self):
        # TODO add in morale and possibly other factors
        return self._combat_value

    def shields_status(self):
        """Ships's shields as a ratio; 0.8 = shields are at 80%."""
        # some vessels may not have shields so catch div-by-zero case:
        return 0.0 if self.max_shields == 0.0 else self.current_shields / self.max_shields

    def hull_status(self):
        """as shields_status but for hull"""
        return self.current_hull / self.max_hull

    def retreat_chance(self, side_cv_ratio):
        """What is the chance of the ship choosing to retreat?"""
        p = 0.0 # start with no chance of retreat
        if side_cv_ratio > 1: # if the other side has the upper hand,
            # ratio P(retreat)
            #   1     0.0
            #   2     0.35 <-- TODO seems low
            #   3     0.7
            m, b = 0.35, -0.35
            p = m * side_cv_ratio + b

        # TODO:
        # worse off the ship is, more likely to retreat
        # p += msf_factor * self.missing_shields_fraction()
        # p += hdf_factor * self.hull_damage_fraction()
        # worse morale -> greater chance of retreat
        # p += morale_factor * self.morale
        # if self is a formidable ship, reduced chance of retreat:
        #   ie greater self.combat_value() --> reduced chance of retreat
        return p

    def retreats_from(self, side_cv_ratio):
        """Randomly determines if a ship retreats from battle.

        Examples of probability of retreat:
            * medium: badly outnumbered
            * medium: shields low
            * high: both --^
            * high: shields down
            * high: significant hull damage
        """
        # garaunteed: 0.0 <= random.random() < 1.0
        retreats = self.retreat_chance(side_cv_ratio) > random.random()
        return retreats

    def receive_damage(self, quantity: float):
        """Damage shields the given amount, applying overflow to hull.

        If damage is dealt to the hull, it may result in system damage.

        Returns a tuple:
        (destroyed: bool, shield damage, hull damage, system damage)
        """
        assert quantity >= 0.0, "Damage value should not be negative"
        if self.current_shields >= quantity:
            shield_dmg = quantity
            hull_dmg = 0.0
        else: # overflow damage to hull
            shield_dmg = self.current_shields
            hull_dmg = quantity - shield_dmg

        self.current_shields -= shield_dmg
        # intentionally let it go negative, for how busted up the hulk is I guess
        self.current_hull -= hull_dmg

        sys_dmg = self.system_damage(hull_dmg)

        # TODO do ships need a 'destroyed' flag or do they get replaced by a Hulk instance?
        return (self.current_hull <= 0.0, shield_dmg, hull_dmg, sys_dmg)

    def system_damage(self, hull_dmg):
        if hull_dmg <= 0.0:
            return None
        # TODO system damage; I got some ideas written down somewhere I think
        # hdf = self.hull_damage_fraction()
        return None

    def combat(self):
        """Notify the ship that it has fought this tick."""
        self.fought_last_tick = True

    def act(self, simulation):
        """Perform one tick of simulation."""
        self.recharge_shields()
        order, params = self.current_order
        # TODO set this up so there's no need to add to it with every new order
        match order:
            case self.Order.MOVE:
                self.move(**params)
            case self.Order.ATTACK:
                self.attack(**params)
            case _:
                raise ValueError(f"Invalid order {self.current_order}")


class FriendlyShip(Ship):
    type = 'friendly'
    max_shields = 1


class EnemyShip(Ship):
    type = 'enemy'
    max_shields = 1

    def act(self, simulation):
        pass # stub for now

@dataclasses.dataclass
class CombatSide:
    """Represents one side of a combat encounter."""
    def __init__(self, *members):
        self.members = set(*members)
        self.retreaters = set()
        # compiled data on what happened to each ship; keyed by ship
        self.outcomes = {}

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

    def retreat_check(self, cv_ratio):
        """Find out who retreats on this side."""
        for m in self.members:
            retreats = m.retreats_from(cv_ratio)
            if retreats:
                self.retreaters.add(m)

    def receive_damage(self, damage):
        self.damage_received = damage
        unit_damage = damage / len(self.members)
        retreater_damage = self.RETREAT_MODIFIER * unit_damage
        for s in self.retreaters:
            self.outcomes[s] = s.receive_damage(retreater_damage)
        for s in self.members - self.retreaters:
            self.outcomes[s] = s.receive_damage(unit_damage)

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

@dataclasses.dataclass
class CombatReport(Message):
    """Report outcome of 1 tick of combat.

    Each CombatSide keeps a record of events for more information:
    * Who participated
    * Who retreated
    * Damage & Destruction:
        * each ship's damage to shields, hull, and systems
        * Which ships where destroyed
    """
    point: Point
    friendly_side: CombatSide
    enemy_side: CombatSide


class UserInterface:
    pass


class Simulation:
    """Holds all the information necessary for the simulation.

    Also can access most of the semantics too.
    """
    def __init__(self, objects, user_interface: UserInterface=None, clock: int=0):
        self.user_interface = user_interface
        self.clock = clock
        self.objects = {}
        for o in objects:
            o.simulation = self
            self.objects[(o.type, o.designation)] = o
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

    def combat(self, participants):
        """Compute and apply 1 tick of combat effects."""
        # TODO should this method be a class method in CombatSide()?
        participant_list = list(participants) # might be an iterator so save its contents
        for p in participant_list:
            p.combat() # notify that they're participating in combat
        # split participants into sides
        friendly_side, enemy_side = CombatSide.sort_into_sides(*participant_list)
        CombatSide.assign_cv_modifiers(friendly_side, enemy_side)

        # have to compute cv ratio ahead of time because retreat checking may alter ships' CV
        cv_ratio = enemy_side.combat_value() / friendly_side.combat_value()

        # TODO more intuitive if the ratio is us-to-them
        friendly_side.retreat_check(cv_ratio)
        enemy_side.retreat_check(1 / cv_ratio)

        # recompute combat values after retreat checks since retreating units do less damage
        friendly_side.receive_damage(enemy_side.combat_value())
        enemy_side.receive_damage(friendly_side.combat_value())

        # report outcomes for this tick of combat:
        report = CombatReport(next(iter(friendly_side.members)).point, friendly_side, enemy_side)
        self.message(report)

        # TODO here down:
        #   retreat movement; see combat.md
        return report

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


def default_scenario(enemies=False):
    ships = {
        FriendlyShip('abel', point(x=5, y=5)),
        FriendlyShip('baker', point(35, 30)),
        FriendlyShip('charlie', point(60, 60)),
        FriendlyShip('doug', point(4, 58)),
        FriendlyShip('alice', point(7, 7)),
    }
    s = Simulation(ships)
    if enemies:
        for (d, p) in (('ukliss', point(20, 23)),
                       ('klaybeq', point(32, 32)),
                       ('lowragh', point(60, 53))):
            s.add_object(EnemyShip(d, p))
    return s
