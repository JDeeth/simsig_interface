from datetime import time
from simsig_interface import Connection
from simsig_interface.entity import BerthUpdate, Entity
from simsig_interface.parser import SimpleSubscriber

# pylint: disable=all


def should_parse_berth_messages() -> None:
    connection = Connection()
    test_subscriber = SimpleSubscriber()
    connection.set_subscriber("test", test_subscriber)

    connection.simulate_receive_message(
        """
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
    )

    berth_0110 = test_subscriber.entities[(Entity.TD_BERTH, "waterloo", "0110")]
    assert berth_0110.train_description == "2K22"
    assert berth_0110.action == BerthUpdate.Action.INTERPOSE
    assert berth_0110.sim_time.time() == time(4,30,57)

    connection.simulate_receive_message(
        """
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
    )

    berth_0110 = test_subscriber.entities[(Entity.TD_BERTH, "waterloo", "0110")]
    assert berth_0110.train_description == ""
    assert berth_0110.action == BerthUpdate.Action.CANCEL
    assert berth_0110.sim_time.time() == time(4,31,20)

    berth_0094 = test_subscriber.entities[(Entity.TD_BERTH, "waterloo", "0094")]
    assert berth_0094.train_description == "2K22"
    assert berth_0094.action == BerthUpdate.Action.INTERPOSE
    assert berth_0094.sim_time.time() == time(4,31,20)

    connection.simulate_receive_message(
        """
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
    )

    berth_0094 = test_subscriber.entities[(Entity.TD_BERTH, "waterloo", "0094")]
    assert berth_0094.train_description == ""
    assert berth_0094.action == BerthUpdate.Action.CANCEL
    assert berth_0094.sim_time.time() == time(4,31,50)
