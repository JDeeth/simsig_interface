import stomp
import stomp.exception

from exception import InvalidLogin


class Connection:  # pylint: disable=too-few-public-methods
    """Wraps Stomp connection to SimSig gateway"""

    def __init__(self, address: str = "localhost", port: int = 51515):
        self._connection = stomp.Connection([(address, port)])

    def connect(self) -> None:
        """Connects and subscribes to SimSig"""

        class InvalidLoginListener(stomp.listener.ConnectionListener):
            """Catches credentials error when connecting to a payware sim"""

            def on_error(self, frame):
                raise InvalidLogin(frame.body)

        self._connection.set_listener("invalid_login", InvalidLoginListener())
        try:
            self._connection.connect(wait=True, with_connect_command=True)
            for i, topic in enumerate(
                [
                    "SimSig",
                    "TD_ALL_SIG_AREA",
                    "TRAIN_MVT_ALL_TOC",
                    "TRAIN_MVT_SUMMARY",
                ]
            ):
                self._connection.subscribe(destination=f"/topic/{topic}", id=i + 1)
        except stomp.exception.ConnectFailedException:
            pass
        self._connection.remove_listener("invalid_login")
