from typing import Dict, Optional, Type
import datetime
from enum import Enum, auto
import json
import logging
import stomp
from simsig_interface.exception import MalformedStompMessage

from simsig_interface.identifier import FullId
from simsig_interface.update_message import (
    AutomaticCrossingUpdate,
    BaseUpdate,
    BerthUpdate,
    FlagUpdate,
    GroundFrameUpdate,
    ManualCrossingUpdate,
    RouteUpdate,
    SignalUpdate,
    SubrouteUpdate,
    TrackCircuitUpdate,
    PointsUpdate,
    TrainDelayUpdate,
    TrainLocationUpdate,
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
        self._entities[update_message.full_id] = update_message  # type: ignore


class Parser(stomp.ConnectionListener):
    """Data about the current SimSig session"""

    def __init__(self, start_date: datetime.date = datetime.date(1970, 1, 1)):
        self._start_date: datetime.datetime = datetime.datetime.fromordinal(
            start_date.toordinal()
        )
        self._name: str = ""
        self._timestamp: int = 0
        self._interval: int = 500
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
            # Duplicate key workaround
            # input:  {"SG_MSG": {message_1}, "SG_MSG": {message_2}}
            # interim result: [{message_1}, {message_2}, {"SG_MSG": None}]
            msg_list = list()

            def collect_msg(obj):
                msg_list.append(obj)

            json.loads(frame.body, object_hook=collect_msg)

            msg_type_dict = msg_list.pop(-1)
            msg_type = list(msg_type_dict)[0]

            for message in msg_list:
                self._parse_message(msg_type, message)
        except json.JSONDecodeError:
            logging.warning(
                "SimSig message assumed to be JSON but could not parse: %s", frame.body
            )
            return

    def _parse_message(self, msg_type: str, message: Dict) -> None:
        """Digest SimSig message and pass on to subscribers"""

        if "area_id" in message:
            self._name = message["area_id"]

        new_time = int(message.get("time", 0) or message.get("clock", 0))
        if new_time > self._timestamp:
            self._timestamp = new_time

        message["sim"] = self._name
        message["sim_time"] = self.latest_time
        message["real_time"] = datetime.datetime.now()

        if msg_type == "clock_msg":
            self._interval = message["interval"]
            # Clock messages do not need propogated to parser subscribers

        elif msg_type in ["CA_MSG", "CB_MSG", "CC_MSG"]:
            if "to" in message:
                message["local_id"] = message.pop("to")
                message["train_description"] = message["descr"]
                message["action"] = BerthUpdate.Action.INTERPOSE
                self._send_update(BerthUpdate.from_gateway_message(message))

            if "from" in message:
                message["local_id"] = message.pop("from")
                message["train_description"] = ""
                message["action"] = BerthUpdate.Action.CANCEL
                self._send_update(BerthUpdate.from_gateway_message(message))

        elif msg_type == "SG_MSG":
            obj_type = message["obj_type"]
            update_type: Dict[str, Type[BaseUpdate]] = dict(
                track=TrackCircuitUpdate,
                point=PointsUpdate,
                signal=SignalUpdate,
                flag=FlagUpdate,
                route=RouteUpdate,
                ulc=SubrouteUpdate,
                frame=GroundFrameUpdate,
                crossing=ManualCrossingUpdate,
                ahb=AutomaticCrossingUpdate,
            )
            if obj_type not in update_type:
                raise MalformedStompMessage(f"Unexpected 'obj_type' in {message}")
            message["local_id"] = message["obj_id"][1:]
            update = update_type[obj_type].from_gateway_message(message)
            self._send_update(update)

        elif msg_type == "train_location":
            self._send_update(TrainLocationUpdate.from_gateway_message(message))
        elif msg_type == "train_delay":
            self._send_update(TrainDelayUpdate.from_gateway_message(message))
        else:
            raise MalformedStompMessage(
                f"Unexpected message type '{msg_type}': {message}"
            )

    def _send_update(self, update):
        """send update to subscribers"""
        for subscriber in self.subscribers.values():
            subscriber.on_update(update)
