import datetime
import json
import stomp

from simsig_interface.entity import BerthUpdate


class Parser(stomp.ConnectionListener):
    """Converts Stomp messages into SimSig updates"""

    def __init__(self):
        self.listeners = {}

    def on_message(self, frame):
        try:
            body = json.loads(frame.body)
        except json.JSONDecodeError:
            return
        for msg_type, msg in body.items():
            if "time" in msg:
                time_delta = datetime.timedelta(seconds=int(msg["time"]))
                sim_time = datetime.datetime(1970, 1, 1) + time_delta
            if msg_type == "CC_MSG":
                update = BerthUpdate(
                    real_time=datetime.datetime.now(),
                    sim_time=sim_time,
                    sim=msg["area_id"],
                    id=msg["to"],
                    action=BerthUpdate.Action.INTERPOSE,
                    train_description=msg["descr"],
                )
                for listener in self.listeners.values():
                    listener.update(update)
