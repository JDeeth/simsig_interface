from simsig_interface.identifier import TrackCircuitIdentifier, TrainIdentifier

# pylint: disable=all


def test_pway_identifier_string():
    tc = TrackCircuitIdentifier("waterloo", 4269)

    assert tc.str == "Waterloo Track Circuit T4269"

def test_train_identifier_string():
    train = TrainIdentifier("1A80", "42", "exeter")

    assert train.str == "Exeter:42 1A80"