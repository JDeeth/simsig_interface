from typing import Optional, Dict
import stomp  # type: ignore
import stomp.exception  # type: ignore
import stomp.utils  # type: ignore

from simsig_interface.exception import ConnectionTimeout, InvalidLogin
from simsig_interface.parser import Parser


class Connection:  # pylint: disable=too-few-public-methods
    """Wraps Stomp connection to SimSig gateway"""

    def __init__(self, address: str = "localhost", port: int = 51515) -> None:
        self._connection = stomp.Connection([(address, port)])
        self.sim = Parser()
        self._connection.set_listener("sim_data", self.sim)

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
            for i, topic in enumerate(
                [
                    "SimSig",
                    "TD_ALL_SIG_AREA",
                    "TRAIN_MVT_ALL_TOC",
                    "TRAIN_MVT_SUMMARY",
                ]
            ):
                self._connection.subscribe(destination=f"/topic/{topic}", id=i + 1)
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
