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

def test_point_validate_low():
    with pytest.raises(AttributeError):
        trek.point(0, 5)

def test_point_validate_high():
    with pytest.raises(AttributeError):
        trek.point(65, 5)
