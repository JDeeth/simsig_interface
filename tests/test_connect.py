import pytest
import stomp.exception
import stomp.listener
import stomp.utils

from simsig_interface.connection import Connection
from simsig_interface.exception import InvalidLogin, ConnectionTimeout

from tests.util import arg_or_kwarg

# pylint: disable=all

"""
Connection times out:
stomp.py emits ConnectionFailedException
no call to listener

Connection rejected due to username/password:
Simsig returns error message which listener can pick up
Stomp emits ConnectionFailedException
Simsig sends disconnect message
"""


def should_connect_to_localhost_51515_by_default(MockConnection, default_connection):
    MockConnection.assert_called_once_with([("localhost", 51515)])


def should_connect_to_specified_addr_and_port(MockConnection, inner_connection):
    connection = Connection("123.45.6.78", 24601)
    MockConnection.assert_called_once_with([("123.45.6.78", 24601)])


def should_use_connect_command(default_connection, inner_connection):
    # 3.7 compatibility: call_args[1] == call_args.kwargs
    assert inner_connection.connect.call_args[1]["with_connect_command"] == True


def should_subscribe_to_simsig_topics(default_connection, inner_connection):
    subscribe_calls = inner_connection.subscribe.call_args_list
    subscribed_topics = {
        arg_or_kwarg(call, 0, "destination") for call in subscribe_calls
    }
    assert subscribed_topics == {
        "/topic/SimSig",
        "/topic/TD_ALL_SIG_AREA",
        "/topic/TRAIN_MVT_ALL_TOC",
        "/topic/TRAIN_MVT_SUMMARY",
    }


def should_raise_timeout_exception(inner_connection):
    attrs = {"connect.side_effect": stomp.exception.ConnectFailedException}
    inner_connection.configure_mock(**attrs)

    connection = Connection()

    with pytest.raises(ConnectionTimeout):
        connection.connect()


def should_send_username_and_password(inner_connection):
    connection = Connection()

    connection.connect(username="alice", password="swordfish")

    connect_call = inner_connection.connect.call_args
    assert connect_call[1]["username"] == "alice"
    assert connect_call[1]["passcode"] == "swordfish"


def should_handle_password_rejection(MockConnection):
    """When connecting to a payware sim without valid username/password,
    SimSig sends a STOMP frame like this:

        {cmd=ERROR,headers=[{'content-length': '22'}],body=Invalid login/passcode}

    Then Stomp raises stomp.exception.ConnectFailedException

    Then SimSig/Stomp disconnect (and call listener.on_disconnect())
    """

    connection = Connection()
    inner_connection = MockConnection.return_value

    error_frame = stomp.utils.Frame(
        cmd="ERROR", headers=None, body="Invalid login/passcode"
    )

    def connect_side_effect(*args, **kwargs):
        calls = inner_connection.set_listener.call_args_list
        listeners = [arg_or_kwarg(call, 1, "listener") for call in calls]

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


def should_disconnect(default_connection, inner_connection):
    inner_connection.disconnect.assert_not_called()

    default_connection.disconnect()

    inner_connection.disconnect.assert_called()


def should_set_get_remove_stomp_listener():
    # NOT mocking stomp.Connect - do not call connect()
    connection = Connection()

    assert connection.get_stomp_listener("test_listener") is None

    class TestListener(stomp.listener.ConnectionListener):
        def __init__(self):
            self.messages = []

        def on_message(self, frame):
            self.messages.append(frame)

    test_listener = TestListener()

    connection.set_stomp_listener("test_listener", test_listener)

    assert connection.get_stomp_listener("test_listener") is test_listener

    connection.simulate_receive_message("First message")
    connection.remove_stomp_listener("test_listener")
    connection.simulate_receive_message("Second message")

    assert len(test_listener.messages) == 1
    assert test_listener.messages[0].body == "First message"
    assert connection.get_stomp_listener("test_listener") is None
