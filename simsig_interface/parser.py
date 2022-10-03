from typing import Dict, Optional
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
    SignalAspect,
    SignalUpdate,
    SubrouteUpdate,
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
        self._entities[update_message.full_id] = update_message  # type: ignore


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
                self._parse_message(msg_type, message)
        except json.JSONDecodeError:
            logging.warning(
                "SimSig message assumed to be JSON but could not parse: %s", frame.body
            )
            return

    def _parse_message(self, msg_type: str, message: Dict) -> None:
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

        def is_true(key: str) -> bool:
            """Converts `"True"` and `"False"` strings to boolean"""
            value = message.get(key, "")
            if isinstance(value, bool):
                return value
            if value.lower() not in {"true", "false"}:
                raise MalformedStompMessage(
                    f"Expected boolean/'True'/'False' for '{key}' in {message}"
                )
            return value.lower() == "true"

        obj_type = message.get("obj_type" or None)
        generic["local_id"] = message["obj_id"][1:]
        if obj_type == "track":
            self._send_update(
                TrackCircuitUpdate(
                    **generic,
                    is_clear=is_true("clear"),
                )
            )
        elif obj_type == "point":
            self._send_update(
                PointsUpdate(
                    **generic,
                    detected_normal=is_true("dn"),
                    detected_reverse=is_true("dr"),
                    called_normal=is_true("cn"),
                    called_reverse=is_true("cr"),
                    keyed_normal=is_true("kn"),
                    keyed_reverse=is_true("kr"),
                    locked=is_true("locked"),
                )
            )
        elif obj_type == "signal":
            aspect_num = int(message["aspect"])
            self._send_update(
                SignalUpdate(
                    **generic,
                    aspect=SignalAspect(aspect_num),
                    bpull=is_true("bpull"),
                    route_set=is_true("rset"),
                    approach_locked=is_true("appr_lock"),
                    lamp_proven=is_true("lp"),
                    auto_mode=is_true("auto"),
                    train_ready_to_start=is_true("trts"),
                    stack_n=is_true("stackN"),
                    stack_x=is_true("stackX"),
                )
            )
        elif obj_type == "flag":
            self._send_update(
                FlagUpdate(
                    **generic,
                    state=int(message["state"]),
                )
            )
        elif obj_type == "route":
            self._send_update(
                RouteUpdate(
                    **generic,
                    is_set=is_true("is_set"),
                )
            )
        elif obj_type == "ulc":
            self._send_update(
                SubrouteUpdate(
                    **generic,
                    locked=is_true("locked"),
                    overlap=is_true("overlap"),
                )
            )
        elif obj_type == "frame":
            self._send_update(
                GroundFrameUpdate(
                    **generic,
                    release_given=is_true("release_given"),
                    release_taken=is_true("release_taken"),
                    reminder=is_true("reminder"),
                )
            )
        elif obj_type == "crossing":
            state = int(message["state"])
            self._send_update(
                ManualCrossingUpdate(
                    **generic,
                    state=ManualCrossingUpdate.State(state),
                    reminder_lower=is_true("lower_reminder"),
                    reminder_raise=is_true("raise_reminder"),
                    reminder_clear=is_true("clear_reminder"),
                    reminder_auto=is_true("auto_reminder"),
                    auto_raise=is_true("auto_lower"),  # sic
                    requested_lower=is_true("request_lower"),
                    requested_raise=is_true("request_raise"),
                    # blocked: 0=barriers up, 1:barriers down, 2: down and obstructed
                    crossing_obstructed=message["blocked"] == 2,
                )
            )
        elif obj_type == "ahb":
            state = int(message["state"])
            self._send_update(
                AutomaticCrossingUpdate(
                    **generic,
                    state=AutomaticCrossingUpdate.State(state),
                    user_state=message["user_state"],
                    telephone_message=message["tel_message"],
                    reminder=is_true("reminder"),
                    failed=is_true("failed"),
                    fail_acknowledged=is_true("failed_ack"),
                )
            )
        else:
            raise MalformedStompMessage(f"Unexpected 'obj_type' in {message}")

    def _send_update(self, update):
        """send update to subscribers"""
        for subscriber in self.subscribers.values():
            subscriber.on_update(update)
