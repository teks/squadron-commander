"""Probably the whole dang game engine is gonna go in here.

"""
import collections
import itertools
import sys
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

    def isclose(self, other):
        """math.isclose for points"""
        # math.isclose defaults a relative tolerance, so the tolerance varies
        # around the map as x & y values grow and shrink.  Set it to an
        # effectively fixed tolerance for consistency.
        kw = dict(rel_tol=1e-100, abs_tol=1e-9)
        return math.isclose(self.x, other.x, **kw) and math.isclose(self.y, other.y, **kw)

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
        self.current_order_params = None
        self.fought_last_tick = False
        self.current_shields = self.max_shields
        self.current_hull = self.max_hull

    # not sure python enums are worth it, but here it is:
    class Order(enum.Enum):
        MOVE = 'move'
        ATTACK = 'attack'
        IDLE = 'idle'

        def is_movement_order(self):
            # have to delay evaluating eg self.MOVE to give time for Enum magic
            # to change the strings into Order instances:
            return self in (self.MOVE, self.ATTACK)

    def has_orders(self):
        return self.current_order is not None

    def order(self, order: Order, **kwargs):
        if order not in self.Order:
            raise ValueError(f"'{order}' is not a valid order")
        self.current_order = order
        self.current_order_params = kwargs

    def reset_order(self):
        self.current_order = None
        self.current_order_params = None

    def message(self, message):
        if self.simulation is not None:
            self.simulation.message(message)

    def displacement(self, destination: Point=None, ticks=1):
        """Where will self be at a future time?

        Returns a relative point giving the displacement after the given number
        of ticks.
        """
        d = self.destination() if destination is None else destination
        if self.point == d:
            return self.point
        distance_to_dest = self.point.distance(d)
        travel_distance = min(ticks * self.speed, distance_to_dest)
        relative_dest = self.point.delta_to(d)
        distance_ratio = travel_distance / distance_to_dest
        return Point(x=(relative_dest.x * distance_ratio),
                     y=(relative_dest.y * distance_ratio))

    def destination(self, pos_if_none=True):
        if self.has_orders() and self.current_order.is_movement_order():
            return self.current_order_params['destination']
        return self.point if pos_if_none else None

    def intercept_point(self, target) -> (bool, Point, int):
        """Return the earliest time & place at which self can intercept the target.

        It's an estimatd solution, but should always be accurate enough given
        quantization of time into ticks.  Returns a tuple:
            (intercepted_before_destination, intercept_point, ticks_to_intercept)
        """
        # I figured out an equation for this but I couldn't solve it, hence estimation
        ### set constants
        t_one_tick_disp = target.displacement(ticks=1)
        # helps detect meet-at-destination case
        t_dest = target.destination()
        t_max_travel_dist = target.point.distance(t_dest)

        ### initial values
        d_last = sys.float_info.max # helps check for impossible interception
        elapsed_time = 0
        t_pos  = target.point
        t_travel_dist = 0

        ### walk along the target's travel path, trying to find an intercept point
        while True:
            elapsed_time += 1
            t_travel_dist += target.speed

            if t_travel_dist >= t_max_travel_dist:
                t_pos = t_dest # lastly, check destination
            else:
                t_pos += t_one_tick_disp

            d = self.point.distance(t_pos)
            if d <= elapsed_time * self.speed:
                return True, t_pos, elapsed_time # found intercept point

            # distance to target should shrink each tick;
            # if it stalls or starts growing, give up and meet at the destination
            if d >= d_last:
                return False, t_dest, self.point.distance(t_dest) / self.speed
            d_last = d

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

        return (self.is_destroyed(), shield_dmg, hull_dmg, sys_dmg)

    # TODO Hulk instance for trashed ships?
    def is_destroyed(self):
        return self.current_hull <= 0.0

    def system_damage(self, hull_dmg):
        if hull_dmg <= 0.0:
            return None
        # TODO system damage; I got some ideas written down somewhere I think
        # hdf = self.hull_damage_fraction()
        return None

    def combat(self):
        """Notify the ship that it has fought this tick."""
        self.fought_last_tick = True

    def plan_move(self): # currently simulation param isn't needed
        if not self.has_orders():
            self.planned_move = None
        elif self.current_order == self.Order.MOVE:
            self.planned_move = self.point + self.displacement()
        elif self.current_order == self.Order.ATTACK:
            (intercepted_before_destination, intercept_point, ticks_to_intercept
                )= self.intercept_point(self.current_order_params['target'])
            self.planned_move = self.point + self.displacement(intercept_point)

    def move(self):
        """Perform one tick of movement."""
        if self.planned_move is not None:
            self.point = self.planned_move

    def post_action(self):
        # TODO any AI ships with no orders should choose an order
        self.planned_move = None
        self.recharge_shields()
        match self.current_order:
            case self.Order.MOVE:
                if self.point == self.destination():
                    self.reset_order()
                    self.message(ArriveMessage(self))
            case self.Order.ATTACK:
                t = self.current_order_params['target']
                if t.is_destroyed():
                    self.reset_order()
                    self.message(TargetDestroyed(self, t))
            case None | self.Order.IDLE:
                pass
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

    def __len__(self):
        return len(self.members)

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
class TargetDestroyed(Message):
    attacker: Ship
    defender: SpaceborneObject

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
            k = (o.type, o.designation)
            if k in self.objects:
                raise ValueError(f"Object with duplicate key {k} detected.")
            o.simulation = self
            self.objects[k] = o

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

    @staticmethod
    def validate_colocations(group):
        # transitive property of spatial colocation should be preserved.
        # but it may not be, so this check will at least make sure I know
        for o, p in itertools.combinations(group, 2):
            if not o.point.isclose(p.point):
                raise ValueError(f"Objects are not colocated: {o}, {p}")

    def colocate_objects(self, validate=True):
        groups = collections.defaultdict(set) # keyed by position
        for o in self.get_objects():
            generator = (p for p in groups.keys() if o.point.isclose(p)) # <3 python <3
            p = next(generator, o.point)
            groups[p].add(o)

        if validate:
            for group in groups.values():
                self.validate_colocations(group)

        return groups

    def combat(self, participants):
        """Compute and apply 1 tick of combat effects.

        Returns a CombatReport, or else None if there was no battle due to
        no co-belligerents among the participants.
        """
        # TODO should this method be a class method in CombatSide()?
        # import pdb; pdb.set_trace()
        participant_list = list(participants) # might be an iterator so save its contents
        # split participants into sides
        friendly_side, enemy_side = CombatSide.sort_into_sides(*participant_list)
        # if either side is empty, just give up
        if any(len(s) == 0 for s in (friendly_side, enemy_side)):
            return

        for p in participant_list:
            p.combat() # notify that they're participating in combat
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
            # because there's no initiative, keep events effectively simultaneous
            for s in self.get_objects():
                s.plan_move()

            for s in self.get_objects():
                s.move()

            # combat step
            for place, participants in self.colocate_objects().items():
                report = self.combat(participants)

            for s in self.get_objects():
                s.post_action()

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
