from datetime import time
import pytest
from simsig_interface import Connection
from simsig_interface.exception import MalformedStompMessage
from simsig_interface.update_message import (
    AutomaticCrossingUpdate,
    BerthUpdate,
    Entity,
    ManualCrossingUpdate,
    SignalAspect,
)
from simsig_interface.parser import SimpleSubscriber

# pylint: disable=all

BERTH_INTERPOSE_MSG = """
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

BERTH_STEP_MSG = """
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

BERTH_CANCEL_MSG = """
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
    connection, test_subscriber = conn_and_subsc(BERTH_INTERPOSE_MSG)

    berth_0110 = test_subscriber.get_entity((Entity.TD_BERTH, "waterloo", "0110"))
    assert berth_0110.train_description == "2K22"
    assert berth_0110.action == BerthUpdate.Action.INTERPOSE
    assert berth_0110.sim_time.time() == time(4, 30, 57)

    connection.simulate_receive_message(BERTH_STEP_MSG)

    berth_0110 = test_subscriber.get_entity((Entity.TD_BERTH, "waterloo", "0110"))
    assert berth_0110.train_description == ""
    assert berth_0110.action == BerthUpdate.Action.CANCEL
    assert berth_0110.sim_time.time() == time(4, 31, 20)

    berth_0094 = test_subscriber.get_entity((Entity.TD_BERTH, "waterloo", "0094"))
    assert berth_0094.train_description == "2K22"
    assert berth_0094.action == BerthUpdate.Action.INTERPOSE
    assert berth_0094.sim_time.time() == time(4, 31, 20)

    connection.simulate_receive_message(BERTH_CANCEL_MSG)

    berth_0094 = test_subscriber.get_entity((Entity.TD_BERTH, "waterloo", "0094"))
    assert berth_0094.train_description == ""
    assert berth_0094.action == BerthUpdate.Action.CANCEL
    assert berth_0094.sim_time.time() == time(4, 31, 50)


TRACK_BLOCKED_MSG = """
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

TRACK_CLEAR_MSG = """
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
    connection, test_subscriber = conn_and_subsc(TRACK_BLOCKED_MSG)

    tc_1371 = test_subscriber.get_entity((Entity.TRACK_CIRCUIT, "waterloo", "1371"))
    assert tc_1371.is_clear == False
    assert tc_1371.sim_time.time() == time(4, 31, 20)

    connection.simulate_receive_message(TRACK_CLEAR_MSG)

    tc_1371 = test_subscriber.get_entity((Entity.TRACK_CIRCUIT, "waterloo", "1371"))
    assert tc_1371.is_clear == True
    assert tc_1371.sim_time.time() == time(4, 31, 30)


POINTS_MSG = """
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
    _, test_subscriber = conn_and_subsc(POINTS_MSG)

    p721b = test_subscriber.get_entity((Entity.POINTS, "waterloo", "721B"))

    assert p721b.detected_normal == True
    assert p721b.detected_reverse == False
    assert p721b.called_normal == True
    assert p721b.called_reverse == False
    assert p721b.keyed_normal == False
    assert p721b.keyed_reverse == False
    assert p721b.locked == False
    assert p721b.sim_time.time() == time(4, 36, 17)


SIGNAL_MSG = """
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


def should_parse_signal_message():
    _, test_subscriber = conn_and_subsc(SIGNAL_MSG)

    k980 = test_subscriber.get_entity((Entity.SIGNAL, "royston", "K980"))

    assert k980.aspect == SignalAspect.GREEN
    assert k980.bpull == False
    assert k980.route_set == True
    assert k980.approach_locked == False
    assert k980.lamp_proven == True
    assert k980.auto_mode == False
    assert k980.train_ready_to_start == False
    assert k980.stack_n == False
    assert k980.stack_x == False
    assert k980.sim_time.time() == time(0, 10, 17)


FLAG_MSG = """
{
    "SG_MSG": {
        "area_id": "royston",
        "obj_id": "LSTOPSIGNU",
        "obj_type": "flag",
        "state": "0",
        "msg_type": "SG",
        "time": "617"
    }
}
""".strip()


def should_parse_flag_message():
    _, test_subscriber = conn_and_subsc(FLAG_MSG)
    flag = test_subscriber.get_entity((Entity.FLAG, "royston", "STOPSIGNU"))

    assert flag.state == 0
    assert flag.sim_time.time() == time(0, 10, 17)


ROUTE_MSG = """
{
    "SG_MSG": {
        "area_id": "royston",
        "obj_id": "RK984AM",
        "obj_type": "route",
        "is_set": "True",
        "msg_type": "SG",
        "time": "1828"
    }
}
""".strip()


def should_parse_route_message():
    _, test_subscriber = conn_and_subsc(ROUTE_MSG)

    route = test_subscriber.get_entity((Entity.ROUTE, "royston", "K984AM"))

    assert route.is_set == True
    assert route.sim_time.time() == time(0, 30, 28)


SUBROUTE_MSG = """
{
    "SG_MSG": {
        "area_id": "waterloo",
        "obj_id": "U1027-AB",
        "obj_type": "ulc",
        "locked": "True",
        "overlap": "False",
        "msg_type": "SG",
        "time": "19308"
    }
}
""".strip()


def should_parse_subroute_message():
    _, test_subscriber = conn_and_subsc(SUBROUTE_MSG)

    subroute = test_subscriber.get_entity((Entity.SUBROUTE, "waterloo", "1027-AB"))

    assert subroute.locked == True
    assert subroute.overlap == False


GROUND_FRAME_MSG = """
{
    "SG_MSG": {
        "area_id": "kingsx",
        "obj_id": "F2261",
        "obj_type": "frame",
        "release_given": "True",
        "release_taken": "False",
        "reminder": "False",
        "msg_type": "SG",
        "time": "22"
    }
}
""".strip()


def should_parse_groundframe_message():
    _, test_subscriber = conn_and_subsc(GROUND_FRAME_MSG)

    frame = test_subscriber.get_entity((Entity.GROUND_FRAME, "kingsx", "2261"))

    assert frame.release_given == True
    assert frame.release_taken == False
    assert frame.reminder == False


MANUAL_CROSSING_MSG = """
{
    "SG_MSG": {
        "area_id": "exeter",
        "obj_id": "GPINX",
        "obj_type": "crossing",
        "state": "0",
        "lower_reminder": "False",
        "raise_reminder": "False",
        "clear_reminder": "False",
        "auto_reminder": "False",
        "auto_lower": "True",
        "request_lower": "True",
        "request_raise": "False",
        "blocked": "0",
        "msg_type": "SG",
        "time": "0"
    }
}
""".strip()


def should_parse_manual_crossing_message():
    _, test_subscriber = conn_and_subsc(MANUAL_CROSSING_MSG)

    mcb = test_subscriber.get_entity((Entity.MANUAL_CROSSING, "exeter", "PINX"))

    assert mcb.state == ManualCrossingUpdate.State.UP

    assert mcb.reminder_lower == False
    assert mcb.reminder_raise == False
    assert mcb.reminder_clear == False
    assert mcb.reminder_auto == False

    assert mcb.auto_raise == True
    assert mcb.requested_lower == True
    assert mcb.requested_raise == False
    assert mcb.crossing_obstructed == False


AUTOMATIC_CROSSING_MSG = """
{
    "SG_MSG": {
        "area_id": "exeter",
        "obj_id": "HVIC",
        "obj_type": "ahb",
        "state": "3",
        "user_state": "0",
        "tel_message": "23",
        "reminder": "False",
        "failed": "False",
        "failed_ack": "False",
        "msg_type": "SG",
        "time": "699"
    }
}
""".strip()


def should_parse_automatic_crossing_message():
    _, test_subscriber = conn_and_subsc(AUTOMATIC_CROSSING_MSG)

    ahb = test_subscriber.get_entity((Entity.AUTOMATIC_CROSSING, "exeter", "VIC"))

    assert ahb.state == AutomaticCrossingUpdate.State.RED_LIGHTS

    # user_state and tel_message should not be converted to int
    # pending an understanding of what these fields mean
    assert ahb.user_state == "0"
    assert ahb.telephone_message == "23"
    assert ahb.reminder == False
    assert ahb.failed == False
    assert ahb.fail_acknowledged == False


TRAIN_LOCATION_TIPLOC = """
{
    "train_location": {
        "headcode": "5M01",
        "uid": "4",
        "action": "pass",
        "location": "INTJN",
        "platform": "5",
        "time": 15445
    }
}
""".strip()


@pytest.mark.xfail
def should_parse_train_location_tiploc_message():
    raise NotImplemented


TRAIN_LOCATION_SIGNAL = """
{
    "train_location": {
        "headcode": "1O28",
        "uid": "5",
        "action": "pass",
        "location": "SVC92",
        "platform": "",
        "time": 15310,
        "aspPass": 6,
        "aspAppr": 2
    }
}
""".strip()


@pytest.mark.xfail
def should_parse_train_location_signal_message():
    raise NotImplemented


TRAIN_DELAY = """
{
    "train_delay": {
        "headcode": "5M01",
        "uid": "",
        "delay": -240
    }
}
""".strip()


@pytest.mark.xfail
def should_parse_train_delay_message():
    raise NotImplemented


SURPRISE_JSON_BOOLEAN_MSG = """
{
    "SG_MSG": {
        "area_id": "waterloo",
        "obj_id": "T1371",
        "obj_type": "track",
        "clear": true,
        "msg_type": "SG",
        "time": "16280"
    }
}
""".strip()


def should_parse_json_boolean():
    _, test_subscriber = conn_and_subsc(SURPRISE_JSON_BOOLEAN_MSG)

    tc_1371 = test_subscriber.get_entity((Entity.TRACK_CIRCUIT, "waterloo", "1371"))

    assert tc_1371.is_clear == True


GARBLED_BOOL_MSG = """
{
    "SG_MSG": {
        "area_id": "waterloo",
        "obj_id": "T1371",
        "obj_type": "track",
        "clear": "Probably",
        "msg_type": "SG",
        "time": "16280"
    }
}
""".strip()

UNEXPECTED_OBJ_TYPE_MSG = """
{
    "SG_MSG": {
        "area_id": "waterloo",
        "obj_id": "T1371",
        "obj_type": "vacuum_tube",
        "clear": "True",
        "msg_type": "SG",
        "time": "16280"
    }
}
""".strip()


@pytest.mark.parametrize("message", [GARBLED_BOOL_MSG, UNEXPECTED_OBJ_TYPE_MSG])
def should_throw_malformedstompmessage_on_bad_data(message):
    with pytest.raises(MalformedStompMessage):
        conn_and_subsc(message)
