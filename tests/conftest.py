import pytest

from simsig_interface.connection import Connection


@pytest.fixture
def MockConnection(mocker):
    return mocker.patch("stomp.Connection")


@pytest.fixture
def default_connection(MockConnection):
    connection = Connection()
    connection.connect()
    return connection


@pytest.fixture
def inner_connection(MockConnection):
    return MockConnection.return_value
