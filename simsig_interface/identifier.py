"""identifier.py

Provides unique identifiers for entities the SSIG can communicate about.

(possible issue: where signals, points etc exist in one era of a sim and not
another - may need a "sim era" parameter alongside "sim name".)
"""
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar, Tuple, Union


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
    MANUAL_CROSSING = auto()
    AUTOMATIC_CROSSING = auto()
    FLAG = auto()

    TRAIN_LOCATION = auto()
    TRAIN_DELAY = auto()

    OTHER = auto()


SimName = str
LocalId = str
PrefixLetter = str
PwayId = Tuple[Entity, SimName, LocalId]

TrainDescription = str  # aka headcode
SsigUid = str
TrainSsigId = Tuple[TrainDescription, SimName, SsigUid]
FullId = Union[PwayId, TrainSsigId]

class Identifier():
    """Base class for identity of any SimSig Interface Gateway entity"""
    @property
    @abstractmethod
    def full_id(self) -> FullId:
        """Returns ID unique to SimSig Interface Gateway"""

    @property
    @abstractmethod
    def str(self) -> str:
        """Represent ID in human-readable string"""

@dataclass
class PwayIdentifier(Identifier):
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
    def full_id(self) -> PwayId:
        """sim + type + id needed to uniquely identify any entity"""
        return (self.entity_type, self.sim, self.local_id)

    @property
    def str(self) -> str:
        """Present ID as full string"""
        type_name_words = self.entity_type.name.split("_")
        type_name = " ".join([word.title() for word in type_name_words])
        return f"{self.sim.title()} {type_name} {self.id_prefix}{self.local_id}"


# pylint: disable=missing-class-docstring


@dataclass
class TrackCircuitIdentifier(PwayIdentifier):
    id_prefix: ClassVar[PrefixLetter] = "T"
    entity_type: ClassVar[Entity] = Entity.TRACK_CIRCUIT


@dataclass
class BerthIdentifier(PwayIdentifier):
    id_prefix: ClassVar[PrefixLetter] = ""
    entity_type: ClassVar[Entity] = Entity.TD_BERTH


@dataclass
class PointsIdentifier(PwayIdentifier):
    id_prefix: ClassVar[PrefixLetter] = "P"
    entity_type: ClassVar[Entity] = Entity.POINTS


@dataclass
class SignalIdentifier(PwayIdentifier):
    id_prefix: ClassVar[PrefixLetter] = "S"
    entity_type: ClassVar[Entity] = Entity.SIGNAL


@dataclass
class FlagIdentifier(PwayIdentifier):
    id_prefix: ClassVar[PrefixLetter] = "L"
    entity_type: ClassVar[Entity] = Entity.FLAG


@dataclass
class RouteIdentifier(PwayIdentifier):
    id_prefix: ClassVar[PrefixLetter] = "R"
    entity_type: ClassVar[Entity] = Entity.ROUTE


@dataclass
class SubrouteIdentifier(PwayIdentifier):
    id_prefix: ClassVar[PrefixLetter] = "U"
    entity_type: ClassVar[Entity] = Entity.SUBROUTE


@dataclass
class GroundFrameIdentifier(PwayIdentifier):
    id_prefix: ClassVar[PrefixLetter] = "F"
    entity_type: ClassVar[Entity] = Entity.GROUND_FRAME


@dataclass
class ManualCrossingIdentifier(PwayIdentifier):
    id_prefix: ClassVar[PrefixLetter] = "G"
    entity_type: ClassVar[Entity] = Entity.MANUAL_CROSSING


@dataclass
class AutomaticCrossingIdentifier(PwayIdentifier):
    id_prefix: ClassVar[PrefixLetter] = "H"
    entity_type: ClassVar[Entity] = Entity.AUTOMATIC_CROSSING


@dataclass
class TrainIdentifier(Identifier):
    """Identifier for train in SSIG context"""

    train_description: TrainDescription  # aka headcode
    ssig_uid: str
    sim: SimName  # context for ssig_uid

    @property
    def full_id(self) -> TrainSsigId:
        return (self.train_description, self.sim, self.ssig_uid)

    @property
    def str(self) -> str:
        return f"{self.sim.title()}:{self.ssig_uid} {self.train_description}"
