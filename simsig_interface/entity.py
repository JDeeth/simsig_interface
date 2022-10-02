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
    POINT = auto()
    SIGNAL = auto()
    TD_BERTH = auto()
    GROUND_FRAME = auto()
    CONTROLLED_CROSSING = auto()
    AUTOMATIC_CROSSING = auto()
    FLAG = auto()

    TRAIN_MOVEMENT = auto()
    TRAIN_DELAY = auto()

    OTHER = auto()


@dataclass
class Identifier:
    """Unique identifier for an infrastructure entity"""

    sim: str
    id: str  # pylint: disable=invalid-name
    id_prefix: ClassVar[str] = ""
    entity_type: ClassVar[Entity]

    @property
    def full_id(self) -> Tuple[Entity, str, str]:
        """sim + type + id needed to uniquely identify any entity"""
        return (self.entity_type, self.sim, self.id)


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
