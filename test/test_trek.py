import pytest
import trek

@pytest.fixture(params=[
    ((2, 1), (5, 5), 5),
    ((1, 1), (9, 16), 17),
    ((9, 16), (1, 1), 17),
    ((1, 1), (1, 5), 4),
    ((1, 1), (5, 1), 4),
])
def distances(request):
    a, b, d = request.param
    return a, b, d, trek.point(*a).distance(trek.point(*b))

def test_point_distance(distances):
    _, _, expected_distance, actual_distance = distances
    assert expected_distance == actual_distance

@pytest.fixture(params=[
    [(5, 4), (2, 6), (-3, 2)],
    [(3, 7), (5, 6), (2, -1)],
    [(10, 10), (10, 10), (0, 0)],
])
def point_deltas(request):
    a, b, d_expected = request.param
    return a, b, d_expected, trek.point(*a).delta_to(trek.point(*b))

def test_point_delta_to(point_deltas):
    a, b, d_expected, d_actual = point_deltas
    assert d_expected == d_actual

def test_point_validate_low():
    with pytest.raises(AttributeError):
        trek.point(0, 5)

def test_point_validate_high():
    with pytest.raises(AttributeError):
        trek.point(65, 5)

@pytest.fixture(params=[
    [( 3.5, 5.5), (1, 1)],
    [( 8.7, 4.0), (2, 1)],
    [(15.8, 16.3), (2, 2)],
])
def points_and_zones(request):
    return request.param

def test_point_zone(points_and_zones):
    """Confirm Point.zone() correctly assigns a zone to a Point."""
    raw_p, expected_z = points_and_zones
    p = trek.Point(*raw_p)
    assert expected_z == p.zone()

def test_simulation_objects():
    simulation = trek.default_scenario()
    objects = list(simulation.get_objects())
    assert len(objects) == 5

def test_simulation_run_not_ready():
    """Confirm simulation won't run if ships have no orders."""
    simulation = trek.default_scenario()
    with pytest.raises(trek.Simulation.NotReadyToRun):
        simulation.run()

@pytest.fixture
def ready_simulation():
    simulation = trek.default_scenario()
    for s in simulation.get_objects(trek.FriendlyShip.type):
        # everyone meet in the middle
        s.order(trek.FriendlyShip.Order.MOVE, destination=trek.point(32, 32))
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
    return start + trek.Point(relative_dest.x * travel_fraction,
                              relative_dest.y * travel_fraction)

def test_simulation_run(ready_simulation):
    """Confirm ships fly around as they should and time is kept."""
    ready_simulation.run(1)
    from trek import point
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
