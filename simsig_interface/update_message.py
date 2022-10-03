"""Representation of each type of update message SSIG can send.

Exception being clock messages which are digested upstream.
"""

from dataclasses import dataclass
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


@dataclass(frozen=True)
class TrackCircuitUpdate(TrackCircuitIdentifier, BaseUpdate):

    is_clear: bool


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


@dataclass(frozen=True)
class SignalUpdate(SignalIdentifier, BaseUpdate):
    aspect: SignalAspect
    bpull: bool
    route_set: bool
    approach_locked: bool
    lamp_proven: bool
    auto_mode: bool
    train_ready_to_start: bool
    stack_n: bool
    stack_x: bool


@dataclass(frozen=True)
class FlagUpdate(FlagIdentifier, BaseUpdate):
    """The meaning of the flag state is up to the user to determine"""

    state: int


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
    reminder_lower: bool
    reminder_raise: bool
    reminder_clear: bool
    reminder_auto: bool
    auto_raise: bool  # note: field in message is mislabelled "auto_lower"
    requested_lower: bool
    requested_raise: bool
    crossing_obstructed: bool  # = state == "2" and blocked == "2"


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
    telephone_message: Any  # Meaning TBC
    reminder: bool
    failed: bool
    fail_acknowledged: bool


@dataclass(frozen=True)
class TrainLocationUpdate(TrainIdentifier, BaseUpdate):
    entity_type: ClassVar[Entity] = Entity.TRAIN_LOCATION

    class Action(Enum):
        ARRIVE = auto()
        DEPART = auto()
        PASS = auto()

    action: Action
    location: Union[Tiploc, PwayId]
    platform: str
    aspect_approaching: Optional[SignalAspect]
    aspect_passing: Optional[SignalAspect]


@dataclass(frozen=True)
class TrainDelayUpdate(TrainIdentifier, BaseUpdate):
    """Note: these messages uniquely do not convey the sim time. For
    consistency, these messages will include the sim time from the most recent
    message."""

    entity_type: ClassVar[Entity] = Entity.TRAIN_DELAY
    delay: Seconds
