import json
from simsig_interface.identifier import BerthId, PointsId
from tests.util import arg_or_kwarg

# pylint: disable=all


def should_send_snapshot_request(default_connection, inner_connection):

    conn = default_connection

    conn.request_snapshot()

    call = inner_connection.send.call_args
    sent_dest = arg_or_kwarg(call, 0, "destination")
    sent_body = arg_or_kwarg(call, 1, "body")

    assert sent_dest == "/topic/TD_ALL_SIG_AREA"
    assert sent_body == """{"snapshot": {}}"""


def should_send_berth_interpose(default_connection, inner_connection):

    conn = default_connection
    berth = BerthId("waterloo", "0149")

    conn.berth_interpose(berth=berth, train_description="1A01")

    call = inner_connection.send.call_args
    sent_dest = arg_or_kwarg(call, 0, "destination")
    sent_body = arg_or_kwarg(call, 1, "body")

    assert sent_dest == "/topic/TD_ALL_SIG_AREA"
    assert json.loads(sent_body) == {"cc_msg": {"to": "0149", "descr": "1A01"}}


def should_send_berth_cancel(default_connection, inner_connection):

    conn = default_connection
    berth = BerthId("waterloo", "0149")

    conn.berth_cancel(berth=berth)

    call = inner_connection.send.call_args
    sent_dest = arg_or_kwarg(call, 0, "destination")
    sent_body = arg_or_kwarg(call, 1, "body")

    assert sent_dest == "/topic/TD_ALL_SIG_AREA"
    assert json.loads(sent_body) == {"cb_msg": {"from": "0149"}}


def should_send_berth_step(default_connection, inner_connection):

    conn = default_connection
    from_berth = BerthId("waterloo", "0149")
    to_berth = BerthId("waterloo", "0151")

    conn.berth_step(from_berth=from_berth, to_berth=to_berth, train_description="0Z99")

    call = inner_connection.send.call_args
    sent_dest = arg_or_kwarg(call, 0, "destination")
    sent_body = arg_or_kwarg(call, 1, "body")

    assert sent_dest == "/topic/TD_ALL_SIG_AREA"
    assert json.loads(sent_body) == {
        "ca_msg": {"from": "0149", "to": "0151", "descr": "0Z99"}
    }


