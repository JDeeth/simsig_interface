import datetime
from enum import Enum
import json
from typing import Optional, Dict, Union
import stomp  # type: ignore
import stomp.exception  # type: ignore
import stomp.utils  # type: ignore

from simsig_interface.identifier import BerthId
from simsig_interface.exception import ConnectionTimeout, InvalidLogin
from simsig_interface.parser import Parser


class Connection:
    """Wraps Stomp connection to SimSig gateway"""

    def __init__(
        self,
        address: str = "localhost",
        port: int = 51515,
        sim_date: datetime.date = datetime.date(2000, 1, 1),
    ) -> None:
        self._sim_date = sim_date
        self._connection = stomp.Connection([(address, port)])
        self.sim = Parser(sim_date)
        self._connection.set_listener("sim_data", self.sim)

    class _Topic(Enum):
        """STOMP destinations used by SimSig"""

        SIMSIG = "/topic/SimSig"
        TD_ALL_SIG_AREA = "/topic/TD_ALL_SIG_AREA"
        TRAIN_MVT_ALL_TOC = "/topic/TRAIN_MVT_ALL_TOC"
        TRAIN_MVT_SUMMARY = "/topic/TRAIN_MVT_SUMMARY"

    def connect(
        self, username: Optional[str] = None, password: Optional[str] = None
    ) -> None:
        """Connects and subscribes to SimSig"""

        class InvalidLoginListener(stomp.listener.ConnectionListener):  # type: ignore
            """Catches credentials error when connecting to a payware sim"""

            def on_error(self, frame: stomp.utils.Frame) -> None:
                raise InvalidLogin(frame.body)

        # this listener only exists for the duration of the connection attempt,
        # to capture any ERROR frame sent in response to our CONNECT
        self._connection.set_listener("invalid_login", InvalidLoginListener())

        try:
            self._connection.connect(
                wait=True,
                with_connect_command=True,
                username=username,
                passcode=password,
            )
            for i, topic in enumerate(Connection._Topic):
                self._connection.subscribe(destination=topic.value, id=i + 1)
        except stomp.exception.ConnectFailedException as exc:
            raise ConnectionTimeout() from exc

        self._connection.remove_listener("invalid_login")

    def disconnect(self) -> None:
        """Disconnect from SimSig game"""
        self._connection.disconnect()

    def set_subscriber(self, name: str, listener) -> None:
        """Add subscriber to SimSig message parser"""
        self.sim.subscribers[name] = listener

    def set_stomp_listener(
        self, name: str, listener: stomp.listener.ConnectionListener
    ) -> None:
        """Attach listener to underlying STOMP connection"""
        self._connection.set_listener(name=name, listener=listener)

    def get_stomp_listener(
        self, name: str
    ) -> Optional[stomp.listener.ConnectionListener]:
        """Get listener from underlying STOMP connection by name
        If it doesn't exist, returns None
        """
        return self._connection.get_listener(name)

    def remove_stomp_listener(self, name: str) -> None:
        """Remove listener from underlying STOMP connection by name"""
        self._connection.remove_listener(name)

    def simulate_receive_message(
        self, message_body: str, headers: Optional[Dict[str, str]] = None
    ) -> None:
        """Construct MESSAGE frame and pass to underlying STOMP connection

        Simulates STOMP server sending a message. For testing."""
        frame = stomp.utils.Frame(cmd="MESSAGE", headers=headers, body=message_body)
        self._connection.transport.process_frame(frame, repr(frame))

    def _send_json(self, topic: _Topic, body: Union[Dict, str]) -> None:
        """Internal method to convert message to json and send to topic"""
        if isinstance(body, dict):
            body = json.dumps(body)
        self._connection.send(topic.value, body, content_type="application/json")

    def request_snapshot(self) -> None:
        """Request status of all signalling-related entities"""
        self._send_json(self._Topic.TD_ALL_SIG_AREA, {"snapshot": {}})

    def berth_interpose(self, berth: BerthId, train_description: str) -> None:
        """Interpose train description into berth"""
        body = {
            "cc_msg": {
                "to": berth.local_id,
                "descr": train_description,
            }
        }
        self._send_json(self._Topic.TD_ALL_SIG_AREA, body)

    def berth_cancel(self, berth: BerthId) -> None:
        """Clear train description from berth"""
        body = {
            "cb_msg": {
                "from": berth.local_id,
            }
        }
        self._send_json(self._Topic.TD_ALL_SIG_AREA, body)

    def berth_step(
        self,
        from_berth: BerthId,
        to_berth: BerthId,
        train_description: str,
    ) -> None:
        """Move train description between berths"""
        body = {
            "ca_msg": {
                "from": from_berth.local_id,
                "to": to_berth.local_id,
                "descr": train_description,
            }
        }
        self._send_json(self._Topic.TD_ALL_SIG_AREA, body)
