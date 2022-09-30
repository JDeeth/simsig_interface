from sqlite3 import connect
import pytest
import stomp.utils
import stomp.exception
from connection import Connection
from exception import InvalidLogin

"""
Connection times out:
stomp.py emits ConnectionFailedException
no call to listener

Connection rejected due to username/password:
Simsig returns error message which listener can pick up
Stomp emits ConnectionFailedException
Simsig sends disconnect message
"""


@pytest.fixture
def MockConnection(mocker):
    return mocker.patch("stomp.Connection")


@pytest.fixture
def inner_connection(MockConnection):
    return MockConnection.return_value


@pytest.fixture
def default_connection(MockConnection):
    connection = Connection()
    connection.connect()


def should_connect_to_localhost_51515_by_default(MockConnection, default_connection):
    MockConnection.assert_called_once_with([("localhost", 51515)])


def should_connect_to_specified_addr_and_port(MockConnection, inner_connection):
    connection = Connection("123.45.6.78", 24601)
    MockConnection.assert_called_once_with([("123.45.6.78", 24601)])


def should_use_connect_command(inner_connection, default_connection):
    assert inner_connection.connect.call_args.kwargs["with_connect_command"] == True


def should_subscribe_to_simsig_topics(inner_connection, default_connection):
    subscribed_topics = {
        c.kwargs["destination"] for c in inner_connection.subscribe.call_args_list
    }
    assert subscribed_topics == {
        "/topic/SimSig",
        "/topic/TD_ALL_SIG_AREA",
        "/topic/TRAIN_MVT_ALL_TOC",
        "/topic/TRAIN_MVT_SUMMARY",
    }


def should_handle_timeout_on_connect(inner_connection):
    attrs = {"connect.side_effect": stomp.exception.ConnectFailedException}
    inner_connection.configure_mock(**attrs)

    connection = Connection()

    connection.connect()


def should_handle_password_rejection(mocker):
    """When connecting to a payware sim without valid username/password,
    SimSig sends a STOMP frame like this:

        {cmd=ERROR,headers=[{'content-length': '22'}],body=Invalid login/passcode}

    Then Stomp raises stomp.exception.ConnectFailedException

    Then SimSig/Stomp disconnect (and call listener.on_disconnect())
    """

    # avoiding fixtures to ensure correct sequence
    MC = mocker.patch("stomp.Connection")
    connection = Connection()
    inner_connection = MC.return_value

    error_frame = stomp.utils.Frame(
        cmd="ERROR", headers=None, body="Invalid login/passcode"
    )

    def connect_side_effect(*args, **kwargs):
        # find all connection listeners
        listeners = []
        for call in inner_connection.set_listener.call_args_list:
            listener = call.kwargs.get("listener")
            if not listener:
                # then listener is 2nd positional argument
                listener = call.args[1]
            listeners.append(listener)

        for listener in listeners:
            listener.on_error(error_frame)
        for listener in listeners:
            listener.on_disconnected()
        assert listeners

    # configure stomp.Connection to respond to connect method by sending error
    # frame to its listeners
    attrs = {"connect.side_effect": connect_side_effect}
    inner_connection.configure_mock(**attrs)

    with pytest.raises(InvalidLogin):
        connection.connect()


# todo: disconnect
# todo: throw exception on timeout
# todo: interface for username+password
