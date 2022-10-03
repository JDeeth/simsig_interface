from typing import Dict, Optional
import datetime
from enum import Enum, auto
import json
import logging
import stomp

from simsig_interface.entity import Update, BerthUpdate

class BaseSubscriber:
    """SimSig update message subscriber"""

    def on_update(self, update_message: Update):
        """For child classes to override"""


class SimpleSubscriber(BaseSubscriber):
    """Keeps a record of the most recent update for each entity"""
    def __init__(self):
        self.entities = {}

    def on_update(self, update_message: Update):
        """Records the update by full ID"""
        self.entities[update_message.full_id] = update_message


class Parser(stomp.ConnectionListener):
    """Data about the current SimSig session"""

    def __init__(self, start_date: datetime.date = datetime.date(1970, 1, 1)):
        self._start_date = datetime.datetime.fromordinal(start_date.toordinal())
        self._name = None
        self._timestamp = 0
        self._interval = 500
        self.subscribers: Dict[str, BaseSubscriber] = {}

    class PauseState(Enum):
        """Possible simulation pause states"""

        UNKNOWN = auto()
        PAUSED = auto()
        RUNNING = auto()

    @property
    def name(self) -> Optional[str]:
        """SimSig .exe name"""
        return self._name

    @property
    def latest_time(self) -> datetime.datetime:
        """Most recent time from sim"""
        timedelta = datetime.timedelta(seconds=self._timestamp)
        return self._start_date + timedelta

    @property
    def speed_ratio(self) -> float:
        """Current approximate speed setting"""
        return 500.0 / self._interval

    @property
    def pause_state(self) -> PauseState:
        """Shows sim's reported pause state"""
        # pending SimSig update
        return Parser.PauseState.UNKNOWN

    def on_message(self, frame: stomp.utils.Frame) -> None:
        """Update sim data"""
        try:
            payload = json.loads(frame.body)
            for msg_type, message in payload.items():
                self.parse_message(msg_type, message)
        except json.JSONDecodeError:
            logging.warning("SimSig message assumed to be JSON but could not parse: %s", frame.body)
            return

    def parse_message(self, msg_type: str, message: Dict) -> None:
        """Digest SimSig message and pass on to subscribers"""

        # update sim data
        if "area_id" in message:
            self._name = message["area_id"]
        new_time = int(message.get("time", 0) or message.get("clock", 0))
        if new_time > self._timestamp:
            self._timestamp = new_time
        if "interval" in message:
            self._interval = message["interval"]

        # berth cancel
        if msg_type in ["CA_MSG", "CC_MSG"]:
            self._send_update(BerthUpdate(
                real_time=datetime.datetime.now(),
                sim_time=self.latest_time,
                sim=message["area_id"],
                local_id=message["to"],
                action=BerthUpdate.Action.INTERPOSE,
                train_description=message["descr"],
            ))

        # berth interpose
        if msg_type in ["CA_MSG", "CB_MSG"]:
            self._send_update(BerthUpdate(
                real_time=datetime.datetime.now(),
                sim_time=self.latest_time,
                sim=message["area_id"],
                local_id=message["from"],
                action=BerthUpdate.Action.CANCEL,
                train_description="",
            ))

    def _send_update(self, update):
        """send update to subscribers"""
        for subscriber in self.subscribers.values():
            subscriber.on_update(update)
