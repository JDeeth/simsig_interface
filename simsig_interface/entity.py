from dataclasses import dataclass
import datetime
from enum import Enum, auto
from typing import ClassVar, Tuple


class Entity(Enum):
    """Types of object or event SimSig can send messages about"""

    SIM = auto()

    TRACK_CIRCUIT = auto()
    ROUTE = auto()
    SUBROUTE = auto()
    POINTS = auto()
    SIGNAL = auto()
    TD_BERTH = auto()
    GROUND_FRAME = auto()
    CONTROLLED_CROSSING = auto()
    AUTOMATIC_CROSSING = auto()
    FLAG = auto()

    TRAIN_MOVEMENT = auto()
    TRAIN_DELAY = auto()

    OTHER = auto()


SimName = str
LocalId = str
PrefixLetter = str
FullId = Tuple[Entity, SimName, LocalId]


@dataclass
class Identifier:
    """Unique identifier for an infrastructure entity

    Properties:
    sim: the name of the simulation e.g. "exeter"
    entity_type: is this a signal, track circuit, ground frame etc
    id_prefix: letter prefix on identifier in STOMP messages e.g. L for Flag IDs
    local_id: the ID of the entity within this sim _without_ the prefix letter
    """

    sim: SimName
    entity_type: ClassVar[Entity]
    id_prefix: ClassVar[PrefixLetter] = ""
    local_id: LocalId

    @property
    def full_id(self) -> FullId:
        """sim + type + id needed to uniquely identify any entity"""
        return (self.entity_type, self.sim, self.local_id)


@dataclass
class BaseUpdate(Identifier):
    """Fields shared by all infrastructure update messages"""

    real_time: datetime.datetime
    sim_time: datetime.datetime


@dataclass
class TrackCircuitUpdate(BaseUpdate):
    """Track circuit update message"""

    id_prefix: ClassVar[PrefixLetter] = "T"
    entity_type: ClassVar[Entity] = Entity.TRACK_CIRCUIT

    is_clear: bool


@dataclass
class BerthUpdate(BaseUpdate):
    """Train description berth update message"""

    entity_type: ClassVar[Entity] = Entity.TD_BERTH

    class Action(Enum):
        """Actions available for TD berth"""

        INTERPOSE = auto()
        CANCEL = auto()

    action: Action
    train_description: str


@dataclass
class PointsUpdate(BaseUpdate):
    """Points update message"""

    id_prefix: ClassVar[PrefixLetter] = "P"
    entity_type: ClassVar[Entity] = Entity.POINTS

    detected_normal: bool
    detected_reverse: bool
    called_normal: bool
    called_reverse: bool
    keyed_normal: bool
    keyed_reverse: bool
    locked: bool


@dataclass
class SignalUpdate(BaseUpdate):  # pylint: disable=too-many-instance-attributes
    """Signal update message"""

    id_prefix: ClassVar[PrefixLetter] = "S"
    entity_type: ClassVar[Entity] = Entity.SIGNAL

    class Aspect(Enum):
        """Signal aspects modelled by SimSig"""

        RED = 0
        SHUNT = 1
        YELLOW = 2
        FLASHING_YELLOW = 3
        DOUBLE_YELLOW = 4
        FLASHING_DOUBLE_YELLOW = 5
        GREEN = 6

    aspect: Aspect
    bpull: bool
    route_set: bool
    approach_locked: bool
    lamp_proven: bool
    auto_mode: bool
    train_ready_to_start: bool
    stack_n: bool
    stack_x: bool
