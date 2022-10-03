from dataclasses import dataclass
import datetime
from enum import Enum, auto
from typing import ClassVar, Tuple

# pylint: disable=missing-class-docstring

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
    def full_id(self) -> Tuple[Entity, SimName, LocalId]:
        """sim + type + id needed to uniquely identify any entity"""
        return (self.entity_type, self.sim, self.local_id)


@dataclass
class Update(Identifier):
    """Fields shared by all infrastructure update messages"""

    real_time: datetime.datetime
    sim_time: datetime.datetime


@dataclass
class BerthUpdate(Update):
    class Action(Enum):
        INTERPOSE = auto()
        CANCEL = auto()

    entity_type: ClassVar[Entity] = Entity.TD_BERTH
    action: Action
    train_description: str
