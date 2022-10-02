from typing import Optional
import datetime
from enum import Enum, auto
import json
import stomp


class SimListener(stomp.ConnectionListener):
    """Data about the current SimSig session"""

    def __init__(self, start_date: datetime.date = datetime.date(1970, 1, 1)):
        self._start_date = datetime.datetime.fromordinal(start_date.toordinal())
        self._name = None
        self._timestamp = 0
        self._interval = 500

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
        return SimListener.PauseState.UNKNOWN

    def on_message(self, frame: stomp.utils.Frame) -> None:
        """Update sim data"""
        try:
            payload = json.loads(frame.body)
            for message in payload.values():
                if "area_id" in message:
                    self._name = message["area_id"]
                if "clock" in message:
                    new_time = int(message["clock"])
                    if new_time > self._timestamp:
                        self._timestamp = new_time
                if "time" in message:
                    new_time = int(message["time"])
                    if new_time > self._timestamp:
                        self._timestamp = new_time
                if "interval" in message:
                    self._interval = message["interval"]
        except json.JSONDecodeError:
            pass
