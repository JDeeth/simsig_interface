from datetime import time
import pytest
from simsig_interface import Connection
from simsig_interface.entity import BerthUpdate, Entity
from simsig_interface.parser import SimpleSubscriber

# pylint: disable=all

CC_BERTH_INTERPOSE = """
{
    "CC_MSG": {
        "area_id": "waterloo",
        "to": "0110",
        "descr": "2K22",
        "msg_type": "CC",
        "time": "16257"
    }
}
""".strip()

CA_BERTH_STEP = """
{
    "CA_MSG": {
        "area_id": "waterloo",
        "from": "0110",
        "to": "0094",
        "descr": "2K22",
        "msg_type": "CA",
        "time": "16280"
    }
}
""".strip()

CB_BERTH_CANCEL = """
{
    "CB_MSG": {
        "area_id": "waterloo",
        "from": "0094",
        "descr": "",
        "msg_type": "CB",
        "time": "16310"
    }
}
""".strip()


def conn_and_subsc(message):
    connection = Connection()
    test_subscriber = SimpleSubscriber()
    connection.set_subscriber("test", test_subscriber)
    connection.simulate_receive_message(message)
    return connection, test_subscriber


def should_parse_berth_messages() -> None:
    connection, test_subscriber = conn_and_subsc(CC_BERTH_INTERPOSE)

    berth_0110 = test_subscriber.get_entity((Entity.TD_BERTH, "waterloo", "0110"))
    assert berth_0110.train_description == "2K22"
    assert berth_0110.action == BerthUpdate.Action.INTERPOSE
    assert berth_0110.sim_time.time() == time(4, 30, 57)

    connection.simulate_receive_message(CA_BERTH_STEP)

    berth_0110 = test_subscriber.get_entity((Entity.TD_BERTH, "waterloo", "0110"))
    assert berth_0110.train_description == ""
    assert berth_0110.action == BerthUpdate.Action.CANCEL
    assert berth_0110.sim_time.time() == time(4, 31, 20)

    berth_0094 = test_subscriber.get_entity((Entity.TD_BERTH, "waterloo", "0094"))
    assert berth_0094.train_description == "2K22"
    assert berth_0094.action == BerthUpdate.Action.INTERPOSE
    assert berth_0094.sim_time.time() == time(4, 31, 20)

    connection.simulate_receive_message(CB_BERTH_CANCEL)

    berth_0094 = test_subscriber.get_entity((Entity.TD_BERTH, "waterloo", "0094"))
    assert berth_0094.train_description == ""
    assert berth_0094.action == BerthUpdate.Action.CANCEL
    assert berth_0094.sim_time.time() == time(4, 31, 50)


TRACK_NOT_CLEAR = """
{
    "SG_MSG": {
        "area_id": "waterloo",
        "obj_id": "T1371",
        "obj_type": "track",
        "clear": "False",
        "msg_type": "SG",
        "time": "16280"
    }
}
""".strip()

TRACK_CLEAR = """
{
    "SG_MSG": {
        "area_id": "waterloo",
        "obj_id": "T1371",
        "obj_type": "track",
        "clear": "True",
        "msg_type": "SG",
        "time": "16290"
    }
}
""".strip()


def should_parse_track_circuit_messages():
    connection, test_subscriber = conn_and_subsc(TRACK_NOT_CLEAR)

    tc_1371 = test_subscriber.get_entity((Entity.TRACK_CIRCUIT, "waterloo", "1371"))
    assert tc_1371.is_clear == False
    assert tc_1371.sim_time.time() == time(4, 31, 20)

    connection.simulate_receive_message(TRACK_CLEAR)

    tc_1371 = test_subscriber.get_entity((Entity.TRACK_CIRCUIT, "waterloo", "1371"))
    assert tc_1371.is_clear == True
    assert tc_1371.sim_time.time() == time(4, 31, 30)


POINTS = """
{
    "SG_MSG": {
        "area_id": "waterloo",
        "obj_id": "P721B",
        "obj_type": "point",
        "dn": "True",
        "dr": "False",
        "cn": "True",
        "cr": "False",
        "kn": "False",
        "kr": "False",
        "locked": "False",
        "msg_type": "SG",
        "time": "16577"
    }
}
""".strip()


def should_parse_points_message():
    connection, test_subscriber = conn_and_subsc(POINTS)

    p721b = test_subscriber.get_entity((Entity.POINTS, "waterloo", "721B"))

    assert p721b.detected_normal
    assert not p721b.detected_reverse
    assert p721b.called_normal
    assert not p721b.called_reverse
    assert not p721b.keyed_normal
    assert not p721b.keyed_reverse
    assert not p721b.locked
    assert p721b.sim_time.time() == time(4, 36, 17)


SIGNAL = """
{
    "SG_MSG":
        {"area_id": "royston",
        "obj_id": "SK980",
        "obj_type": "signal",
        "aspect": "6",
        "bpull": "False",
        "rset": "True",
        "appr_lock": "False",
        "lp": "True",
        "auto": "False",
        "trts": "False",
        "stackN": "False",
        "stackX": "False",
        "msg_type": "SG",
        "time": "617"
    }
}
""".strip()

from simsig_interface.entity import SignalUpdate


def should_parse_signal_message():
    connection, test_subscriber = conn_and_subsc(SIGNAL)

    k980 = test_subscriber.get_entity((Entity.SIGNAL, "royston", "K980"))

    assert k980.aspect == SignalUpdate.Aspect.GREEN
    assert not k980.bpull
    assert k980.route_set
    assert not k980.approach_locked
    assert k980.lamp_proven
    assert not k980.auto_mode
    assert not k980.train_ready_to_start
    assert not k980.stack_n
    assert not k980.stack_x
