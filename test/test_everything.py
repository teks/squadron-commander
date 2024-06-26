import string
import random
import math

import pytest

import squadcom.cli
import squadcom

@pytest.mark.parametrize('a, b, expected_distance', [
    ((2, 1), (5, 5), 5),
    ((1, 1), (9, 16), 17),
    ((9, 16), (1, 1), 17),
    ((1, 1), (1, 5), 4),
    ((1, 1), (5, 1), 4),
])
def test_point_distance(a, b, expected_distance):
    assert expected_distance == squadcom.point(*a).distance(squadcom.point(*b))

@pytest.fixture(params=[
    [(5, 4), (2, 6), (-3, 2)],
    [(3, 7), (5, 6), (2, -1)],
    [(10, 10), (10, 10), (0, 0)],
])
def point_deltas(request):
    a, b, d_expected = request.param
    return a, b, d_expected, squadcom.point(*a).delta_to(squadcom.point(*b))

def test_point_delta_to(point_deltas):
    a, b, d_expected, d_actual = point_deltas
    assert d_expected == d_actual

def test_point_validate_low():
    with pytest.raises(AttributeError):
        squadcom.point(0, 5)

def test_point_validate_high():
    with pytest.raises(AttributeError):
        squadcom.point(65, 5)

@pytest.mark.parametrize('target, expected_bearing', [
    [(37, 6), 0.031239833430],
    [(37, 4), 6.251945473749],
    [(3,  3), 3.926990816987],
])
def test_point_bearing_to(target, expected_bearing):
    self = squadcom.point(5, 5)
    assert math.isclose(expected_bearing, self.bearing_to(squadcom.Point(*target)))

@pytest.mark.parametrize('target, expected_direction', [
    [(37, 6), 0],
    [(37, 4), 0],
    [(3,  3), 5],
])
def test_cardinal_direction_to(target, expected_direction):
    self = squadcom.point(5, 5)
    assert expected_direction == self.cardinal_direction_to(squadcom.Point(*target))

@pytest.mark.parametrize('raw_p, expected_z', [
    [( 3.5, 5.5), (1, 1)],
    [( 8.7, 4.0), (2, 1)],
    [(15.8, 16.3), (2, 2)],
])
def test_point_zone(raw_p, expected_z):
    """Confirm Point.zone() correctly assigns a zone to a Point."""
    p = squadcom.Point(*raw_p)
    assert expected_z == p.zone()

@pytest.mark.parametrize('expected_object_cnt, side, controller', [
    (8, None, None),
    (5, squadcom.Side.FRIENDLY, None),
    (3, squadcom.Side.ENEMY, None),
    (4, None, squadcom.Controller.PLAYER),
    (3, None, squadcom.Controller.ENEMY_AI),
    (4, squadcom.Side.FRIENDLY, squadcom.Controller.PLAYER),
])
def test_simulation_get_objects(side, controller, expected_object_cnt):
    simulation = squadcom.default_scenario(enemies=True)
    # so not all friendlies are player-controlled:
    simulation.get_object(squadcom.Side.FRIENDLY, 'charlie').controller = None
    objects = list(simulation.get_objects(side=side, controller=controller))
    assert expected_object_cnt == len(objects)

def test_simulation_run_not_ready():
    """Confirm simulation won't run if ships have no orders."""
    simulation = squadcom.default_scenario()
    with pytest.raises(squadcom.Simulation.NotReadyToRun):
        simulation.run()

@pytest.fixture
def ready_simulation():
    simulation = squadcom.default_scenario()
    for s in simulation.get_objects(squadcom.Side.FRIENDLY):
        # everyone meet in the middle
        s.order(squadcom.Order.MOVE, destination=squadcom.point(32, 32))
    return simulation

# TODO writing the algorithm a second time does not a good test make
def one_tick_dest(start, dest, speed=1):
    """Return new location for the given parameters:

    From the start position, make progress towards the given
    destination, assuming 1 tick of time has passed.
    """
    relative_dest = dest - start
    distance = start.distance(dest)
    travel_dist = min(distance, speed)
    travel_fraction = travel_dist / distance
    return start + squadcom.Point(relative_dest.x * travel_fraction,
                                  relative_dest.y * travel_fraction)

def test_simulation_run(ready_simulation):
    """Confirm ships fly around as they should and time is kept."""
    ready_simulation.initialize()
    ready_simulation.run(1)
    point = squadcom.point
    dest = point(32, 32)
    expected_positions = {
        'abel': one_tick_dest(point(x=5, y=5), dest),
        'alice': one_tick_dest(point(x=7, y=7), dest),
        'baker': one_tick_dest(point(x=35, y=30), dest),
        'charlie': one_tick_dest(point(x=60, y=60), dest),
        'doug': one_tick_dest(point(x=4, y=58), dest),
    }
    actual_positions = {s.designation: s.point for s in ready_simulation.get_objects()}
    assert expected_positions == actual_positions

def friendly_squadron():
    return [squadcom.FriendlyShip(d, squadcom.point(1, 1)) for d in ('a', 'b', 'c')]

def enemy_squadron():
    return [squadcom.EnemyShip(d, squadcom.point(1, 1)) for d in ('x', 'y', 'z')]

def simple_simulation():
    s = squadcom.Simulation(friendly_squadron() + enemy_squadron())
    s.initialize()
    return s

def combat_sides():
    fs = friendly_squadron()
    es = enemy_squadron()
    return squadcom.CombatSide.sort_into_sides(*fs, *es)

def test_CombatSide_sort_into_sides():
    friendly_side, enemy_side = combat_sides()
    assert (all(m.side == squadcom.Side.FRIENDLY for m in friendly_side.members)
            and all(m.side == squadcom.Side.ENEMY for m in enemy_side.members))

def setup_sides():
    sides = combat_sides()
    for s in sides:
        s.cv_modifier = 1
    return sides

def test_CombatSide_retreat_chance__even_fight():
    """should not retreat when odds are even"""
    s = squadcom.FriendlyShip('name-here', squadcom.point(1, 1))
    assert 0.0 == s.retreat_chance(1.0)

def test_CombatSide_retreat_chance__1v2():
    """Sometimes retreat when it's 1 to 2."""
    s = squadcom.FriendlyShip('name-here', squadcom.point(1, 1))
    assert 0.35 == s.retreat_chance(2.0)

def test_CombatSide_retreat_chance__2v1():
    """Never retreat when it's 2 to 1"""
    s = squadcom.FriendlyShip('name-here', squadcom.point(1, 1))
    assert 0.0 == s.retreat_chance(0.5)

def test_CombatSide_retreat_check__even_fight():
    """Shouldn't retreat if the fight is even."""
    fs, es = setup_sides()
    ratio = es.combat_value() / fs.combat_value()
    # unused var retreated = fs.retreat_check(ratio)
    fs.retreat_check(ratio)
    assert len(fs.retreaters) == 0

def test_CombatSide_retreat_check__hopeless_case():
    """Should always retreat when the fight is hopeless."""
    fs, es = setup_sides()
    for s in es.members:
        s._combat_value = 9001
    ratio = es.combat_value() / fs.combat_value()
    fs.retreat_check(ratio)
    assert len(fs.retreaters) == 3

def test_Simulation_combat():
    """Run through the method once."""
    fsq, esq = friendly_squadron(), enemy_squadron()
    sim = squadcom.Simulation(fsq + esq)
    sim.combat(sim.get_objects())
    assert all(0.0 <= o.shields_status() < 1.0 for o in fsq + esq
               ), "No ship should escape unscathed."

def test_Simulation_combat__hull_damage():
    """Confirm hull damage is present when damage is high."""
    fsq, esq = friendly_squadron(), enemy_squadron()
    for s in fsq + esq:
        s._combat_value = 10
    sim = squadcom.Simulation(fsq + esq)
    sim.combat(sim.get_objects())
    assert all(o.shields_status() == 0.0 and o.hull_status() <= 0.0 for o in fsq + esq
               ), "total annihilation case"

@pytest.mark.parametrize(
    'retreat, advantage, fs, fh,  es,  eh', [
    [1.0, (1.00, 1.00), 0.4, 1.0, 0.0, 1/3], # no retreat, no advantage
    [0.0, (1.00, 1.00), 0.7, 1.0, 1/6, 1.0], # enemy retreats, no advantage
    [1.0, (1.25, 0.75), 0.55, 1.0, 0.0, 2 - 25 / 12], # no retreat, friendly advantage
])
def test_Simulation_combat__damage(mocker, retreat, advantage, fs, fh, es, eh):
    # TODO this will need revision as well when package is renamed
    mocker.patch('squadcom.engine.random.random', return_value=retreat)
    mocker.patch('squadcom.engine.random.choice', return_value=advantage)
    simulation = squadcom.default_scenario(enemies=True)
    report = simulation.combat(simulation.get_objects())
    # crs = trek.cli.combat_report_string(report)
    # print(crs)
    fm = report.friendly_side.members
    em = report.enemy_side.members
    assert (all(math.isclose(fs, u.current_shields) for u in fm)
        and all(math.isclose(fh, u.current_hull   ) for u in fm)
        and all(math.isclose(es, u.current_shields) for u in em)
        and all(math.isclose(eh, u.current_hull   ) for u in em)
    )

@pytest.mark.parametrize(
    'i_coord, i_speed, e_early, e_time, e_coord', [ # <-- e is for expectations
    [(20.0, 40.0), 1.0, True,  15, (30.606601718, 30.606601718)], # base case, easy intercept
    [(20.0, 40.0), 1.5, True,  10, (27.071067812, 27.071067812)], # fast interceptor case
    [(20.0, 40.0), 0.5, False, 40, (40.0, 40.0)], # kinda slow interceptor case
    [(19.0, 20.0), 1.0, False, 29, (40.0, 40.0)], # chase case
    [(19.0, 20.0), 1.5, True,   2, (21.414213562, 21.414213562)], # chase + fast interceptor case
])
def test_Ship_intercept_point(i_coord, i_speed, e_early, e_time, e_coord):
    """Go through various scenarios and confirm interception works"""
    target = squadcom.Ship('target', squadcom.point(20.0, 20.0))
    target.order(squadcom.Order.MOVE, destination=squadcom.point(40.0, 40.0))
    interceptor = squadcom.Ship('interceptor', squadcom.point(*i_coord))
    interceptor.speed = i_speed

    early, point, time = interceptor.intercept_point(target)

    assert (e_early, e_time) == (early, time) and squadcom.point(*e_coord).isclose(point)

def test_Ship_same_place_intercept():
    e = squadcom.EnemyShip('e', squadcom.point(40, 12))
    c = squadcom.SpaceColony('c', squadcom.point(40, 12))
    _, actual_ip, _ = e.intercept_point(c)
    assert (40, 12) == actual_ip

def test_Ship_morale():
    s = squadcom.FriendlyShip('Lollipop', squadcom.point(1, 1))
    initial = s.morale
    s.morale += 0.2
    first = s.morale
    s.morale += 0.2
    second = s.morale
    s.morale += 99
    third = s.morale
    assert (0.0, 0.2, 0.4, 1.0) == (initial, first, second, third)

def test_Ship_morale_cv_effect():
    s = squadcom.FriendlyShip('Lollipop', squadcom.point(1, 1))
    s.morale = 9
    high_cv = s.combat_value()
    s.morale = -9
    low_cv = s.combat_value()
    assert (0.75, 1.25) == (low_cv, high_cv)


class TestArtificialObject:
    @pytest.mark.parametrize('hull_fraction, random_vals, expected_dmg', [
        [0.7, [0.36], None],  # no damage case
        [0.7, [0.34, 0.60], 0.18],  # damage damage case
    ])
    def test_Component_damage_check(self, hull_fraction, random_vals, expected_dmg):
        fake_random = lambda: random_vals.pop(0)
        c = squadcom.ArtificialObject.Component(random=fake_random)
        a = squadcom.ArtificialObject('no name', squadcom.Point(1, 1))
        actual_dmg = c.damage_check(0.1, hull_fraction, a)
        assert {expected_dmg, actual_dmg} == {None} or math.isclose(expected_dmg, actual_dmg)

    @pytest.mark.parametrize('planned_move, local_friend, fought, expected_health', [
        (squadcom.Point(2, 2), False, False, (0.78, 1.00)),  # FTL case; small loss is expected
        (None,             False, True,  (0.73, 0.97)),  # no repair if fought this tick
        (None,             True,  False, (0.83, 1.00)),  # nearby friendly; small loss is expected
    ])
    def test_repair(self, planned_move, local_friend, fought, expected_health):
        simulation = simple_simulation()
        o = next(simulation.get_objects(side=squadcom.Side.FRIENDLY))
        if local_friend:
            simulation.add_object(squadcom.FriendlyShip('USS Helpful', o.point))
        o.repair_rate = 0.1
        o.planned_move = planned_move
        o.components['tactical'].health = 0.73
        o.components['shields'].health = 0.97
        o.fought_this_tick = fought
        o.repair()
        assert expected_health == (o.components['tactical'].health, o.components['shields'].health)


@pytest.mark.parametrize('group', [
    # for now one obvious test is enough
    [(10, 10), (10, 10)],
])
def test_Simulation_validate_colocations(group):
    squadcom.Simulation.validate_colocations(
        set(squadcom.Ship(str(p), squadcom.point(*p)) for p in group))

@pytest.mark.parametrize('group', [
    # for now one obvious test is enough
    [(10, 10), (5, 5)],
])
def test_Simulation_validate_colocations_raises(group):
    with pytest.raises(ValueError):
        squadcom.Simulation.validate_colocations(
            set(squadcom.Ship(str(p), squadcom.point(*p)) for p in group))

@pytest.mark.parametrize(
    'indiv_positions, group_count', [
        [ # simple case, two clearly separated objects => two groups
            [(10, 10), (11, 11)], 2
        ],
        [ # nearby objects
            [(10 - 1e-15, 10), (10 + 1e-15, 10)], 1
        ],
    ])
def test_Simulation_colocate_objects(indiv_positions, group_count):
    abc_iter = iter(string.ascii_lowercase)
    sim = squadcom.Simulation(squadcom.Ship(next(abc_iter), squadcom.point(*p))
                              for p in indiv_positions)
    groups = sim.colocate_objects()
    assert group_count == len(groups)

def test_ai_target_selection():
    s = squadcom.default_scenario(enemies=True, space_colonies=True)

    actual = {}
    for r in s.get_objects(controller=squadcom.Controller.ENEMY_AI):
        r.post_action()
        actual[r.designation] = (r.current_order, r.current_order_params)

    new_ceylon = s.get_object(squadcom.Side.FRIENDLY, 'New Ceylon')
    harmony = s.get_object(squadcom.Side.FRIENDLY, 'Harmony')

    A = squadcom.Order.ATTACK
    expected = {'klaybeq': (A, {'target': new_ceylon}),
                'ukliss':  (A, {'target': new_ceylon}),
                'lowragh': (A, {'target': harmony}),
                }

    assert expected == actual
