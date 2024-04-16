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

def test_simulation_objects():
    simulation = trek.default_scenario()
    objects = list(simulation.objects())
    # import pdb; pdb.set_trace()
    assert len(objects) == 5
