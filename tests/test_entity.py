import pytest
from simsig_interface.identifier import (
    RouteClass,
    RouteIdentifier,
    TrackCircuitIdentifier,
    TrainIdentifier,
)

# pylint: disable=all


def test_pway_identifier_string():
    tc = TrackCircuitIdentifier("waterloo", 4269)

    assert tc.str == "Waterloo Track Circuit T4269"


def test_train_identifier_no_uid():
    train = TrainIdentifier(train_description="2B10", uid="")

    assert train.str == "2B10"
    assert train.full_id == "2B10"


def test_train_identifier_with_uid():
    train = TrainIdentifier(train_description="1A80", uid="W24601")

    assert train.str == "1A80:W24601"
    assert train.full_id == "W24601"


@pytest.mark.parametrize(
    "local_id,signal,position,class_",
    [
        ("K984AM", "K984", "A", RouteClass.MAIN),
        ("123BS", "123", "B", RouteClass.SHUNT),
        ("123CC", "123", "C", RouteClass.CALL_ON),
        ("123DV", "123", "D", RouteClass.VIRTUAL),
        ("123M", None, None, None),
        ("", None, None, None),
    ],
)
def test_route_identifier_categories_self(local_id, signal, position, class_):
    route = RouteIdentifier("royston", local_id)

    assert route.signal == signal
    assert route.position == position
    assert route.class_ == class_
