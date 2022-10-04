"""Representation of each type of update message SSIG can send.

Exception being clock messages which are digested upstream.
"""

from dataclasses import dataclass, fields
import datetime
from enum import Enum, auto
from typing import Any, ClassVar, Optional, Union

from simsig_interface.identifier import (
    Entity,
    PwayId,
    TrainDescription,
    TrackCircuitIdentifier,
    BerthIdentifier,
    PointsIdentifier,
    SignalIdentifier,
    FlagIdentifier,
    RouteIdentifier,
    SubrouteIdentifier,
    GroundFrameIdentifier,
    ManualCrossingIdentifier,
    AutomaticCrossingIdentifier,
    TrainIdentifier,
)

# pylint: disable=missing-class-docstring, too-many-instance-attributes


class SignalAspect(Enum):
    RED = 0
    SHUNT = 1
    YELLOW = 2
    FLASHING_YELLOW = 3
    DOUBLE_YELLOW = 4
    FLASHING_DOUBLE_YELLOW = 5
    GREEN = 6


Tiploc = str  # TIming Point LOCation
Seconds = int


@dataclass
class BaseUpdate:
    """Used by all update messages"""

    real_time: datetime.datetime
    sim_time: datetime.datetime

    @classmethod
    def from_gateway_message(cls, message: dict):
        """Convert gateway message dict to suitable for constructor"""
        return cls.from_dict(message)

    @classmethod
    def from_dict(cls, message: dict):
        """Converts "True"/"False" to boolean and discards keys not in class"""
        class_fields = {field.name for field in fields(cls)}
        message = {k: message[k] for k in message if k in class_fields}

        for key, value in message.items():
            if value == "True":
                message[key] = True
            if value == "False":
                message[key] = False

        return cls(**message)


@dataclass(frozen=True)
class TrackCircuitUpdate(TrackCircuitIdentifier, BaseUpdate):

    is_clear: bool

    @classmethod
    def from_gateway_message(cls, message: dict):
        message["is_clear"] = message.pop("clear")
        return cls.from_dict(message)


@dataclass(frozen=True)
class BerthUpdate(BerthIdentifier, BaseUpdate):
    class Action(Enum):
        INTERPOSE = auto()
        CANCEL = auto()

    action: Action
    train_description: TrainDescription


@dataclass(frozen=True)
class PointsUpdate(PointsIdentifier, BaseUpdate):
    detected_normal: bool
    detected_reverse: bool
    called_normal: bool
    called_reverse: bool
    keyed_normal: bool
    keyed_reverse: bool
    locked: bool

    @classmethod
    def from_gateway_message(cls, message: dict):
        message["detected_normal"] = message.pop("dn")
        message["detected_reverse"] = message.pop("dr")
        message["called_normal"] = message.pop("cn")
        message["called_reverse"] = message.pop("cr")
        message["keyed_normal"] = message.pop("kn")
        message["keyed_reverse"] = message.pop("kr")
        return cls.from_dict(message)


@dataclass(frozen=True)
class SignalUpdate(SignalIdentifier, BaseUpdate):
    aspect: SignalAspect
    bpull: bool
    route_set: bool
    appr_lock: bool
    lamp_proven: bool
    auto_mode: bool
    trts: bool
    stack_n: bool
    stack_x: bool

    @classmethod
    def from_gateway_message(cls, message: dict):
        message["aspect"] = SignalAspect(int(message["aspect"]))
        message["route_set"] = message.pop("rset")
        message["lamp_proven"] = message.pop("lp")
        message["auto_mode"] = message.pop("auto")
        message["stack_n"] = message.pop("stackN")
        message["stack_x"] = message.pop("stackX")

        return cls.from_dict(message)


@dataclass(frozen=True)
class FlagUpdate(FlagIdentifier, BaseUpdate):
    """The meaning of the flag state is up to the user to determine"""

    state: int

    @classmethod
    def from_gateway_message(cls, message: dict):
        message["state"] = int(message["state"])
        return cls.from_dict(message)


@dataclass(frozen=True)
class RouteUpdate(RouteIdentifier, BaseUpdate):
    is_set: Optional[bool] = None


@dataclass(frozen=True)
class SubrouteUpdate(SubrouteIdentifier, BaseUpdate):
    locked: bool
    overlap: bool


@dataclass(frozen=True)
class GroundFrameUpdate(GroundFrameIdentifier, BaseUpdate):
    release_given: bool
    release_taken: bool
    reminder: bool


@dataclass(frozen=True)
class ManualCrossingUpdate(
    ManualCrossingIdentifier, BaseUpdate
):  # pylint: disable=too-many-instance-attributes
    class State(Enum):
        UP = 0
        LOWERING = 1
        DOWN = 2
        CLEAR = 3
        RAISING = 4

    state: State
    lower_reminder: bool
    raise_reminder: bool
    clear_reminder: bool
    auto_reminder: bool
    auto_raise: bool  # note: field in message is mislabelled "auto_lower"
    request_lower: bool
    request_raise: bool
    crossing_obstructed: bool  # = state == "2" and blocked == "2"

    @classmethod
    def from_gateway_message(cls, message: dict):
        message["state"] = ManualCrossingUpdate.State(int(message["state"]))
        message["auto_raise"] = message["auto_lower"]
        message["crossing_obstructed"] = message["blocked"] == 2
        return cls.from_dict(message)


@dataclass(frozen=True)
class AutomaticCrossingUpdate(AutomaticCrossingIdentifier, BaseUpdate):
    class State(Enum):
        IDLE = 0
        DELAYED_LOWERING = 1
        AMBER_LIGHTS = 2
        RED_LIGHTS = 3
        BARRIERS_DOWN = 4

    state: State
    user_state: Any  # Meaning TBC
    tel_message: Any  # Meaning TBC
    reminder: bool
    failed: bool
    failed_ack: bool

    @classmethod
    def from_gateway_message(cls, message: dict):
        message["state"] = AutomaticCrossingUpdate.State(int(message["state"]))
        return cls.from_dict(message)


@dataclass(frozen=True)
class TrainLocationUpdate(TrainIdentifier, BaseUpdate):
    entity_type: ClassVar[Entity] = Entity.TRAIN_LOCATION

    class Action(Enum):
        ARRIVE = "arrive"
        DEPART = "depart"
        PASS = "pass"

    action: Action
    location: Union[Tiploc, PwayId]
    platform: str
    aspect_approaching: Optional[SignalAspect]
    aspect_passing: Optional[SignalAspect]

    @classmethod
    def from_gateway_message(cls, message):
        if "aspPass" in message and message["location"].startswith("S"):
            message["location"] = SignalIdentifier(
                sim=message["sim"], local_id=message["location"][1:]
            )
            message["aspect_approaching"] = SignalAspect(message["aspAppr"])
            message["aspect_passing"] = SignalAspect(message["aspPass"])
        else:
            message["aspect_approaching"] = None
            message["aspect_passing"] = None
        message["train_description"] = message["headcode"]
        message["action"] = TrainLocationUpdate.Action(message["action"])
        return cls.from_dict(message)


@dataclass(frozen=True)
class TrainDelayUpdate(TrainIdentifier, BaseUpdate):
    """Note: these messages uniquely do not convey the sim time. For
    consistency, these messages will include the sim time from the most recent
    message."""

    entity_type: ClassVar[Entity] = Entity.TRAIN_DELAY
    delay: Seconds

    @classmethod
    def from_gateway_message(cls, message):
        message["train_description"] = message.pop("headcode")
        return cls.from_dict(message)
