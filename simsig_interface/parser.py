from typing import Dict, Optional
import datetime
from enum import Enum, auto
import json
import logging
import stomp

from simsig_interface.entity import (
    FullId,
    BaseUpdate,
    BerthUpdate,
    SignalUpdate,
    TrackCircuitUpdate,
    PointsUpdate,
)


class BaseSubscriber:  # pylint: disable=too-few-public-methods
    """SimSig update message subscriber"""

    def on_update(self, update_message: BaseUpdate):
        """For child classes to override"""


class SimpleSubscriber(BaseSubscriber):
    """Keeps a record of the most recent update for each entity"""

    def __init__(self):
        self._entities = {}

    def get_entity(self, entity: FullId) -> Optional[BaseUpdate]:
        """Retrieve latest update for specified entity"""
        return self._entities.get(entity, None)

    def on_update(self, update_message: BaseUpdate):
        """Records the update by full ID"""
        self._entities[update_message.full_id] = update_message


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
            logging.warning(
                "SimSig message assumed to be JSON but could not parse: %s", frame.body
            )
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

        generic = dict(
            real_time=datetime.datetime.now(), sim_time=self.latest_time, sim=self._name
        )

        if msg_type in ["CA_MSG", "CB_MSG", "CC_MSG"]:
            self._parse_berth(message, generic)
        elif msg_type == "SG_MSG":
            self._parse_sg_msg(message, generic)

    def _parse_berth(self, message, generic):
        """Parse berth messages (CA, CB, CC)"""

        if "to" in message:
            self._send_update(
                BerthUpdate(
                    **generic,
                    local_id=message["to"],
                    action=BerthUpdate.Action.INTERPOSE,
                    train_description=message["descr"],
                )
            )

        if "from" in message:
            self._send_update(
                BerthUpdate(
                    **generic,
                    local_id=message["from"],
                    action=BerthUpdate.Action.CANCEL,
                    train_description="",
                )
            )

    def _parse_sg_msg(self, message, generic):
        """Parse messages relating to interlocking (SG_MSG)"""
        obj_type = message.get("obj_type" or None)
        local_id = message["obj_id"][1:]
        if obj_type == "track":
            return self._send_update(
                TrackCircuitUpdate(
                    **generic, local_id=local_id, is_clear=self._true(message, "clear")
                )
            )
        if obj_type == "point":
            return self._send_update(
                PointsUpdate(
                    **generic,
                    local_id=local_id,
                    detected_normal=self._true(message, "dn"),
                    detected_reverse=self._true(message, "dr"),
                    called_normal=self._true(message, "cn"),
                    called_reverse=self._true(message, "cr"),
                    keyed_normal=self._true(message, "kn"),
                    keyed_reverse=self._true(message, "kr"),
                    locked=self._true(message, "locked"),
                )
            )
        if obj_type == "signal":
            aspect_num = int(message["aspect"])
            return self._send_update(
                SignalUpdate(
                    **generic,
                    local_id=local_id,
                    aspect=SignalUpdate.Aspect(aspect_num),
                    bpull=self._true(message, "bpull"),
                    route_set=self._true(message, "rset"),
                    approach_locked=self._true(message, "appr_lock"),
                    lamp_proven=self._true(message, "lp"),
                    auto_mode=self._true(message, "auto"),
                    train_ready_to_start=self._true(message, "trts"),
                    stack_n=self._true(message, "stackN"),
                    stack_x=self._true(message, "stackX"),
                )
            )

    def _true(self, message, key) -> bool:
        return message.get(key, "").lower() == "true"

    def _send_update(self, update):
        """send update to subscribers"""
        for subscriber in self.subscribers.values():
            subscriber.on_update(update)
