"""The game engine is implemented here."""
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
# TODO should be settings on Simulation not globals
MAX_X = 64
MAX_Y = 64

# TODO these aren't used because the concept of a 'long range map' went away
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

    def grid_cell(self, scale=1.0):
        """Place this point into the nearest grid cell.

        Grid cells are assumed to be labelled with whole numbers.
        The grid may have a different resolution, so scale first.
        """
        # python's rounding is odd: https://docs.python.org/3/library/functions.html#round
        def round_sanely(v):
            floor = math.floor(v)
            return floor if v - floor < 0.5 else math.ceil(v)
        return self.__class__(x=round_sanely(self.x * scale), y=round_sanely(self.y * scale))

    def bearing_to(self, other):
        """In radians.

        0 is East, pi is West, 1.5 * pi is South.
        """
        delta = self - other
        # ensure angular range is 0 to 2*pi -----v
        return math.atan2(delta.y, delta.x) + math.pi

    def cardinal_direction_to(self, other, direction_count=8):
        """Returns 1-n where 1 is east, 2 is north of east, etc.

        East is assumed to be 0 degrees == 0 radians. Each direction
        is 360 degrees / `direction_count` wide. So if
        direction_count == 8, East is -22.5deg to +22.5deg.
        """
        angle = self.bearing_to(other)
        width = 2 * math.pi / direction_count
        offset = 0.5 * width
        for i in range(direction_count):
            end_angle = i * width + offset
            if angle < end_angle:
                return i
        return 0 # handle the case of the southern other half of the eastern wedge

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
        if self.x == self.y == 0.0:  # relative coords are sometimes (0, 0)
            return
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

def random_point(x_range=(1, MAX_X), y_range=(1, MAX_Y), rand_type=int):
    if rand_type != int: # implement floats later
        raise NotImplementedError()
    return point(random.randint(*x_range), random.randint(*y_range))

def zone(*args, **kwargs):
    """Factory for points that represent one zone."""
    p = Point(*args, **kwargs)
    p.validate_as_zone()
    return p


class SpaceborneObject(abc.ABC):
    """All vessels, planets, stations, and other objects."""

    def __init__(self, designation: str, point: Point, simulation=None):
        self.designation = designation
        self.point = point
        self.simulation = simulation

    def __hash__(self):
        return hash(self.designation)

    def __repr__(self):
        fq_name = self.__class__.__module__ + '.' + self.__class__.__qualname__
        return f"<{fq_name} {self.designation} {self.point}>"

    def distance(self, other):
        return self.point.distance(other.point)

    def message(self, message):
        """Send a message to the simulation."""
        if self.simulation is not None:
            self.simulation.message(message)

    # this is class Message but it's further down in the file and I can't be bothered
    #                           vvv
    def receive_message(self, message):
        """Receive a Message, acting on it if needed."""
        pass # no action in SpaceborneObject

    def initialize(self, simulation):
        self.simulation = simulation


class Side(enum.Enum):
    """When it comes to fights and other interactions, what side is this object on?"""
    FRIENDLY = 'friendly'
    ENEMY = 'enemy'
    NEUTRAL = 'neutral'

    def is_hostile_to(self, other):
        return {self, other} == {self.FRIENDLY, self.ENEMY}


class Controller(enum.Enum):
    """When it comes to fights and other interactions, what side is this object on?"""
    PLAYER = 'player'
    ENEMY_AI = 'enemy_ai'


# TODO validate order params (consider changing to a conventional class to carry the payload)
class Order(enum.Enum):
    """Controllable objects in the simulation need to be given orders."""
    MOVE = 'move'
    ATTACK = 'attack'
    IDLE = 'idle'

    def is_movement_order(self):
        # have to delay evaluating eg self.MOVE to give time for Enum magic
        # to change the strings into Order instances:
        return self in (self.MOVE, self.ATTACK)


class ArtificialObject(SpaceborneObject):
    """Any vessel, whether mobile like a ship, or not, like a space station.

    Thus it has a hull, a combat value, and optionally, shields.  They may be
    manned or automated.  For now, such objects can't be given orders; they
    just sit there and defend themselves if needed.
    """
    max_hull = 1
    max_shields = 0
    _combat_value = 1
    side = Side.NEUTRAL
    controller = None
    # TODO move away from Ship.Order.FOO and just reference Order.FOO
    Order = Order
    valid_orders = {Order.IDLE}
    repair_rate = 0.0 # no capacity for fixing itself

    # TODO ArtificialObject does not yet exist so can't use it as a type
    #   annotation in Component, and can't use typing.Self because that refers to the wrong class
    @dataclasses.dataclass
    class Component:
        """Parts or Systems on the vessel that can be damaged individually."""
        _health: float=1.0 # clamped to [0, 1].
        random: typing.Callable[[float], float]=random.random

        @property
        def health(self):
            return self._health

        @health.setter
        def health(self, new_value: float):
            self._health = 1.0 if new_value > 1.0 else (0.0 if new_value < 0.0 else new_value)

        def is_damaged(self):
            return self.health < 1.0

        def damage_check(self, hull_damage: float, hull_fraction: float, vessel) -> float | None:
            """Check for damage to the given component if there has been hull damage.

            The chance of component damage is up to 50%. The amount of
            component damage is up to 100%. Both values are scaled by the
            hull damage fraction.
            """
            if hull_damage <= 0.0 or self.random() > hull_fraction / 2.0:
                return None
            dmg_fraction = self.random() * (1 - hull_fraction)
            self.health -= dmg_fraction
            self.apply_to(vessel)
            return dmg_fraction

        def apply_to(self, vessel):
            """Immediate effects of component damage, if any."""
            pass

    class Shields(Component):
        def apply_to(self, vessel):
            vessel.current_shields = min(vessel.current_shields, vessel.max_shields * self.health)

    def __init__(self, designation: str, point: Point, simulation=None):
        super().__init__(designation, point, simulation)
        self.fought_this_tick = False
        self.current_shields = self.max_shields
        self.current_hull = self.max_hull
        self.planned_move = None
        self.current_order = None # start out with no orders
        self.current_order_params = None
        self.speed = 0
        # start with neutral morale, worst and best is [-1, 1]
        self._morale = 0.0
        # TODO why does it default to having shields when max_shields == 0?
        self.components = dict(shields=self.Shields(), tactical=self.Component())

    def has_orders(self):
        return self.current_order is not None

    def order(self, order: Order, **kwargs):
        if order not in self.valid_orders:
            raise ValueError(f"'{order}' is not in the set of valid orders: {self.valid_orders}")
        self.current_order = order
        self.current_order_params = kwargs

    def reset_order(self):
        self.current_order = None
        self.current_order_params = None

    def displacement(self, ticks=1):
        return self.point # ain't goin nowhere

    def destination(self):
        return self.point # still ain't goin nowhere

    def recharge_shields(self):
        if self.fought_this_tick:
            return
        else:
            self.current_shields = self.max_shields
            self.components['shields'].apply_to(self)

    @property
    def morale(self):
        """A property representing the crew's morale."""
        return self._morale

    @morale.setter
    def morale(self, new_value: float):
        """Raise or lower morale, capped in the range [-1, 1]."""
        # it'd be better to have a curve that has horizontal asymptotes at [-1, 1]:
        # The further from neutral it is, the less it is altered by a given quantity.
        # self.morale += (1 - abs(self.morale)) * quantity
        self._morale = 1.0 if new_value > 1.0 else -1.0 if new_value < -1.0 else new_value

    MORALE_HULL_DMG_FACTOR = 0.25 # hull damage reduces morale
    # linearly scale CV and retreat chance by as much as these factors:
    MORALE_CV_FACTOR = 0.25
    MORALE_RETREAT_FACTOR = 0.5

    def hull_damage_morale_change(self, hull_dmg):
        self.morale -= self.MORALE_HULL_DMG_FACTOR * (hull_dmg / self.max_hull)

    def combat_participation_morale_change(self, report):
        self.morale -= 0.05 # being in battle at all is bad for morale
        # but a retreating opponent is good for morale
        opposing_retreaters = {Side.FRIENDLY: report.enemy_side.retreaters,
                               Side.ENEMY: report.friendly_side.retreaters,
                               }[self.side]
        self.morale += len(opposing_retreaters) * 0.05

    def destroyed_object_morale_change(self, obj):
        if obj.side == self.side:
            self.morale -= 0.2
        elif self.side.is_hostile_to(obj.side):
            # if witnessing destruction close at hand (say in battle), bonus morale
            self.morale += 0.2 if self.point.isclose(obj.point) else 0.1

    def combat_value(self):
        # TODO other factors possibly
        return (self._combat_value * (1.0 + self.morale * self.MORALE_CV_FACTOR)
                * self.components['tactical'].health)

    def shields_status(self):
        """Ships's shields as a ratio; 0.8 = shields are at 80%."""
        # some vessels may not have shields so catch div-by-zero case:
        return 0.0 if self.max_shields == 0.0 else self.current_shields / self.max_shields

    def hull_status(self):
        """as shields_status but for hull"""
        return self.current_hull / self.max_hull

    def retreats_from(self, side_cv_ratio):
        return False # only mobile objects can retreat

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
            # crew doesn't like getting shot at
            self.hull_damage_morale_change(hull_dmg)

        self.current_shields -= shield_dmg
        # intentionally let it go negative, for how busted up the hulk is I guess
        self.current_hull -= hull_dmg

        sys_dmg = self.system_damage(hull_dmg)

        # can send message now that changes to self are applied
        if self.current_hull <= 0.0 < self.current_hull + hull_dmg:
            self.message(DestroyedObjectMessage(self))

        return (self.is_destroyed(), shield_dmg, hull_dmg, sys_dmg)

    # TODO Hulk instance for wreckage? maybe raiders scavenge it
    def is_destroyed(self):
        return self.current_hull <= 0.0

    def system_damage(self, hull_dmg: float):
        damage_report = dict()
        hull_fraction = self.hull_status()
        for name, component in self.components.items():
            damage_report[name] = component.damage_check(hull_dmg, hull_fraction, self)
        return damage_report

    def combat_notification(self, report):
        """Notify the ship that it has fought this tick."""
        self.fought_this_tick = True
        self.combat_participation_morale_change(report)

    # TODO it's odd to have boilerplate like this
    def compute_move(self, ticks=None):
        return self.point

    def plan_move(self):
        pass

    def move(self):
        pass

    def repair(self):
        """Repair damaged components."""
        damaged_components = {n: c for (n, c) in self.components.items()
                              if c.is_damaged()}
        dc_cnt = len(damaged_components)

        # often, no repairs needed, or else can't due to combat
        if self.fought_this_tick or dc_cnt == 0:
            return

        if self.planned_move is not None:
            modifier = 1.0 # FTL
        else:
            modifier = 1.5 # waiting alone
            locals = self.simulation.colocate_objects()[self.point]
            friendly_locals, _ = CombatSide.sort_into_sides(*locals)
            if len(friendly_locals) > 1:
                modifier = 2.0 # waiting with friends

        for c in damaged_components.values():
            # TODO affect by morale?
            c.health += modifier * self.repair_rate / dc_cnt

        if not any(c.is_damaged() for c in damaged_components.values()):
            self.message(CompletedRepairsMessage(self))

    def post_action(self):
        self.recharge_shields()
        self.repair()

    def finish_tick(self):
        self.fought_this_tick = False


class SpaceColony(ArtificialObject):
    """Orbital and deep-space habitats."""
    side = Side.FRIENDLY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_order = Order.IDLE


class Ship(ArtificialObject):
    """Mobile spaceborne object. Issue orders to have it move and take other actions."""
    cruising_speed = 1 # warp, not newtonian, in ly/hour
    side = Side.NEUTRAL
    valid_orders = set(Order) # can do anything
    # this is a gross violation of separation of concerns (mixing UX with engine)
    # but it was the easiest way:
    retreat_text = 'RETREATED'

    class Drive(ArtificialObject.Component):
        def apply_to(self, vessel):
            # TODO this is a bit funny because maximum speed was never established
            vessel.speed = min(vessel.speed, vessel.cruising_speed * self.health)

    def __init__(self, designation: str, point: Point, simulation=None):
        """Cruising speed is in light year per hour."""
        super().__init__(designation, point, simulation)
        self.speed = self.cruising_speed
        self.components['drive'] = self.Drive()

    def displacement(self, destination: Point=None, ticks=1):
        """Where will self be at a future time?

        Returns a relative point giving the displacement after the given number
        of ticks.
        """
        d = self.destination() if destination is None else destination
        if self.point == d:
            return point(0.0, 0.0) # we're here! everybody remember where we parked
        distance_to_dest = self.point.distance(d)
        travel_distance = min(ticks * self.speed, distance_to_dest)
        relative_dest = self.point.delta_to(d)
        distance_ratio = travel_distance / distance_to_dest
        return Point(x=(relative_dest.x * distance_ratio),
                     y=(relative_dest.y * distance_ratio))

    def destination(self):
        match self.current_order:
            case None | Order.IDLE:
                return self.point
            case Order.MOVE:
                return self.current_order_params['destination']
            case Order.ATTACK:
                t = self.current_order_params['target']
                return self.intercept_point(t)[1]
        raise ValueError(f"Can't find the destination for {self}")

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
        t_pos = target.point
        t_travel_dist = 0

        ### walk along the target's travel path, trying to find an intercept point
        while True:
            elapsed_time += 1
            # TODO stop using obj.speed; instead call obj.velocity() which respects the current Order:
            # if the target is IDLE and thus not moving, it's odd to add speed here.
            # but t_max_travel_dist would be 0 in that case, and save us.
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

        # worse off the ship is, more likely to retreat
        if self.morale < 0.0: # poor morale
            p -= self.MORALE_RETREAT_FACTOR * self.morale
        # TODO
        # p += msf_factor * self.missing_shields_fraction()
        # p += hdf_factor * self.hull_damage_fraction()
        # if self is a formidable ship, reduced chance of retreat:
        #   ie greater self.combat_value() --> reduced chance of retreat
        return p

    def retreats_from(self, side_cv_ratio):
        """Randomly determines if a ship retreats from battle.

        Examples of probability of retreat (most of this isn't implemented):
            * medium: badly outnumbered
            * medium: shields low
            * high: both --^
            * high: shields down
            * high: significant hull damage
        """
        # garaunteed: 0.0 <= random.random() < 1.0
        retreats = self.retreat_chance(side_cv_ratio) > random.random()
        return retreats

    # this is class Message but it's further down in the file and I can't be bothered
    #                           vvv
    def receive_message(self, message):
        """Receive a Message, acting on it if needed."""
        if isinstance(message, DestroyedObjectMessage):
            self.destroyed_object_morale_change(message.obj)

    def compute_move(self, ticks=1):
        if self.current_order == self.Order.MOVE:
            return self.point + self.displacement(ticks=ticks)
        elif self.current_order == self.Order.ATTACK:
            (intercepted_before_destination, intercept_point, ticks_to_intercept
                )= self.intercept_point(self.current_order_params['target'])
            return self.point + self.displacement(intercept_point, ticks=1)
        return None

    def plan_move(self):
        self.planned_move = self.compute_move()

    def move(self):
        """Perform one tick of movement."""
        if self.planned_move is not None:
            self.point = self.planned_move

    def post_action(self):
        super().post_action()
        self.planned_move = None
        match self.current_order:
            case self.Order.MOVE:
                if self.point == self.destination():
                    self.reset_order()
                    self.message(ArriveMessage(self))
            case self.Order.ATTACK:
                t = self.current_order_params['target']
                if t.is_destroyed():
                    self.reset_order()
            case self.Order.IDLE:
                pass
            case None:
                pass
            case _:
                raise ValueError(f"Invalid order {self.current_order}")


class FriendlyShip(Ship):
    side = Side.FRIENDLY
    controller = Controller.PLAYER
    max_shields = 1
    repair_rate = 0.01


class EnemyShip(Ship):
    side = Side.ENEMY
    controller = Controller.ENEMY_AI
    max_shields = 1

    def choose_closest(self, targets):
        min_distance = MAX_X + MAX_Y
        candidates = set()
        for o in targets:
            d = self.distance(o)
            if d < min_distance:
                min_distance, candidates = d, {o}
            elif d == min_distance:
                candidates.add(o)
        if not candidates:
            return None
        return random.choice(list(candidates)) # sets aren't sequences

    def choose_target(self):
        """Chose a target based on priority.

        Priorities are:
            1) the nearest FRIENDLY SpaceColony or settlement
            TODO 2) the nearest FRIENDLY Starbase
        """
        if self.current_order is None:
            self.order(Order.IDLE)
            priority_targets, targets = set(), set()
            for o in self.simulation.get_objects(Side.FRIENDLY):
                (priority_targets if isinstance(o, SpaceColony) and not o.is_destroyed()
                 else targets).add(o)
            # unsolved circular pursuit case:
            # target = self.choose_closest(priority_targets if priority_targets else targets)
            target = self.choose_closest(priority_targets)
            if target is not None:
                self.order(Order.ATTACK, target=target)
                self.message(ChosenNewTarget(self, target))

    def post_action(self):
        super().post_action()
        self.choose_target()

    def initialize(self, simulation):
        super().initialize(simulation)
        self.choose_target()
        self.plan_move()


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
            {Side.FRIENDLY: friendly_side.members,
             Side.ENEMY: enemy_side.members}[p.side].add(p)
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
        return self.retreaters

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
    tick = None

@dataclasses.dataclass
class PausedSimulation(Message):
    pass

@dataclasses.dataclass
class ArriveMessage(Message):
    ship: Ship

@dataclasses.dataclass
class SpawnMessage(Message):
    obj: SpaceborneObject

@dataclasses.dataclass
class DestroyedObjectMessage(Message):
    obj: SpaceborneObject

@dataclasses.dataclass
class ChosenNewTarget(Message):
    obj: Ship
    target: ArtificialObject

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


@dataclasses.dataclass
class CompletedRepairsMessage(Message):
    obj: ArtificialObject


@dataclasses.dataclass
class ScenarioWinMessage(Message):
    pass


@dataclasses.dataclass
class ScenarioLossMessage(Message):
    pass


class UserInterface:
    pass


@dataclasses.dataclass
class Scenario(abc.ABC):
    """Define a custom scenario to play."""
    simulation: 'Simulation' = None

    def __post_init__(self):
        if self.simulation is None:
            # this kind of double-linking feels awkward
            self.simulation = Simulation(scenario=self)

    def setup(self, initialize_simulation=True):
        """Called once to add content to self.simulation.

        It should populate self.simulation with units then conditionally
        call self.simulation.initialize().
        """
        raise NotImplementedError()

    def finish_tick(self) -> bool:
        """Called once a tick by its Simulation.

        Concrete implementations should do two things:
        1) Mutate self.simulation as needed, eg, spawning reinforcements, and
        2) return True if the scenario has reached an end state, False otherwise.
        """
        raise NotImplementedError()


class EndlessScenario(Scenario):
    """A scenario that doesn't end; useful for development."""
    def finish_tick(self) -> bool:
        return False


class Simulation:
    """Holds all the information necessary for the simulation.

    Also can access most of the semantics too.
    """
    def __init__(self, objects=None, scenario: Scenario=None):
        self.user_interface = None
        self.need_to_pause = False
        self.clock = 0
        self.objects = {}
        self.destroyed_objects = {}
        if objects is not None:
            self.populate(*objects)
        self.scenario = EndlessScenario(self) if scenario is None else scenario
        self.scenario.simulation = self

    def get_objects(self, side=None, controller=None):
        """Yield objects, with optional filtering."""
        i = self.objects.values()
        if side is not None:
            i = (o for o in i if o.side == side)
        if controller is not None:
            i = (o for o in i if o.controller == controller)
        yield from i

    def get_object(self, side, designation):
        """Get a single object by side and object's designation."""
        return self.objects[(side, designation)]

    def add_object_helper(self, obj: SpaceborneObject):
        k = (obj.side, obj.designation)
        if k in self.objects:
            raise ValueError(f"Object with key {k} already found: {self.objects[k]}")
        self.objects[k] = obj

    def add_object(self, obj: SpaceborneObject):
        """Add the given object to the simulation and initialize it.

        This is intended to be used while the simulation is running.
        """
        self.add_object_helper(obj)
        obj.initialize(self)
        self.message(SpawnMessage(obj))

    def populate(self, *objects):
        """Add the given objects to the simulation, but don't initialize them.

        Suitable for setting up a new simulation.
        """
        [self.add_object_helper(o) for o in objects]

    def destroy_object(self, obj):
        if not obj.is_destroyed(): # destroy it if it's not already
            obj.current_hull = 0.0
        k = (obj.side, obj.designation)
        self.objects.pop(k)
        self.destroyed_objects[k] = obj

    @staticmethod
    def validate_colocations(group):
        # transitive property of spatial colocation should be preserved.
        # but it may not be, so this check will at least make sure I know
        for o, p in itertools.combinations(group, 2):
            if not o.point.isclose(p.point):
                raise ValueError(f"Objects are not colocated: {o}, {p}")

    def colocate_objects(self, validate=True):
        """Determine which objects are presently 'in the same place'."""
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
        participant_list = list(p for p in participants if not p.is_destroyed())
        # split participants into sides
        friendly_side, enemy_side = CombatSide.sort_into_sides(*participant_list)
        # if either side is empty, just give up
        if any(len(s) == 0 for s in (friendly_side, enemy_side)):
            return

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

        for p in participant_list:
            p.combat_notification(report)  # notify that they were in a fight

        return report

    def message(self, message):
        """Send a message to the simulation and the user interface.

        The message is also propagated to the simulated objects.
        """
        message.tick = self.clock
        match message:
            case DestroyedObjectMessage():
                self.destroy_object(message.obj)
            case SpawnMessage():
                self.need_to_pause = True
        for o in self.get_objects():
            o.receive_message(message)
        if self.user_interface is not None:
            self.user_interface.message(message)

    def initialize(self):
        """Perform setup actions.

        Best not do this until the user's finished adding objects.
        """
        for o in self.get_objects():
            o.initialize(self)
        for o in self.get_objects(controller=Controller.ENEMY_AI):
            o.choose_target()
        for o in self.get_objects():
            o.plan_move()

    # TODO this method isn't really needed; pull out the inner owo call
    def ready_to_run(self, raise_exception=False):
        """Report whether the simulation is ready to run.

        Any idle friendly ships prevent the simulation from running.
        """
        owo = self.objects_without_orders()
        if raise_exception and owo:
            raise self.NotReadyToRun(owo)
        return not owo

    def objects_without_orders(self, side=None, controller=None):
        """Returns a set of idle vessels, optionally filtered per get_objects."""
        return set(s for s in self.get_objects(side=side, controller=controller)
                   if not s.has_orders())

    class NotReadyToRun(Exception):
        pass

    def run(self, duration=24):
        self.ready_to_run(raise_exception=True)
        self.need_to_pause = False # keep going unless something causes a stop
        stop_time = self.clock + duration
        while self.clock < stop_time:
            self.clock += 1
            # because there's no initiative, keep events effectively simultaneous:
            # first, everybody moves
            for s in self.get_objects():
                s.move()

            # second, combat (based on present locations)
            post_combat_pause = False
            for place, participants in self.colocate_objects().items():
                report = self.combat(participants)
                post_combat_pause = post_combat_pause or report is not None

            # third, post-combat activity
            for s in self.get_objects():
                s.post_action()
            for o in self.get_objects():
                o.plan_move()

            for o in self.get_objects():
                o.finish_tick()

            scenario_finished = self.scenario.finish_tick()

            # TODO can this be simplified? tracking three different booleans that do the same thing
            if self.need_to_pause or scenario_finished or post_combat_pause or not self.ready_to_run():
                self.message(PausedSimulation())
                break


def default_scenario(enemies=False, space_colonies=False):
    from . import scenarios
    scenario = scenarios.DefaultScenario(include_enemies=enemies, include_colonies=space_colonies)
    scenario.setup()
    return scenario.simulation
