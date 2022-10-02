from simsig_interface import Connection

import datetime
import json
from simsig_interface.entity import Update, Entity

# pylint: disable=all


class Listener:
    def update(self, update_message: Update):
        pass


def should_have_sensible_app_structure():
    class TestListener(Listener):
        def __init__(self):
            self.entities = {}

        def update(self, update_message: Update):
            self.entities[update_message.full_id] = update_message

    connection = Connection()
    test_listener = TestListener()
    connection.set_listener("test", test_listener)

    connection.simulate_receive_message(
        """
        {
            "CC_MSG": {
                "area_id": "waterloo",
                "to": "0149",
                "descr": "1A30",
                "msg_type": "CC",
                "time": "16257"
            }
        }
        """.strip()
    )

    berth_0149 = test_listener.entities[(Entity.TD_BERTH, "waterloo", "0149")]
    assert berth_0149.train_description == "1A30"
