import pytest
import trek

@pytest.fixture(params=[
    ((0, 0), (3, 4), 5),
    ((2, 0), (5, 4), 5),
    ((0, 0), (8, 15), 17),
    ((8, 15), (0, 0), 17),
    ((0, 0), (0, 4), 4),
    ((0, 0), (4, 0), 4),
])
def distances(request):
    a, b, d = request.param
    return a, b, d, trek.distance(a, b)

def test_distance(distances):
    _, _, expected_distance, actual_distance = distances
    assert expected_distance == actual_distance
