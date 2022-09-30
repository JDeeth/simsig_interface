class Connection:
    def __init__(self, address, port):
        pass


def should_connect_to_specified_location(mocker):
    MockConnection = mocker.patch("stomp.Connection")

    connection = Connection("123.45.6.78", 24601)

    MockConnection.assert_called()
