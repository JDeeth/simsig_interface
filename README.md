# SimSig Interface

[![Tests](https://github.com/JDeeth/simsig_interface/actions/workflows/run_tests.yaml/badge.svg)](https://github.com/JDeeth/simsig_interface/actions/workflows/run_tests.yaml)

`simsig_interface` is an unofficial Python wrapper for the [SimSig](https://www.simsig.co.uk) Interface Gateway. Supports Pythons 3.7-3.10 and the current version of SimSig, which is v5.21.

## Features

 - Manages STOMP connections to SimSig game instances
 - Translates SimSig messages into Python dataclasses
 - TODO: Interface for sending commands back to SimSig
 - TODO: Message collation
 - TODO: Loading additional data e.g. where to find specific signals
 - TODO: Timetable loader / integration

## Installation

This will be deployed to PyPI at some point.

```bash
git clone https://github.com/JDeeth/simsig_interface
cd simsig_interface
python -m venv venv
venv/Scripts/activate
# for Windows, or for Linux
. venv/bin/activate
python -m pip install -e .[dev,examples]
```

## Quick start

```python
from simsig_interface import Connection, BaseSubscriber

class SimplePrinter(BaseSubscriber):
    def on_update(self, message):
        print(message)
        print()

def main():
    connection = Connection("localhost", 51515)
    connection.set_subscriber("simple_printer", SimplePrinter())

    input("Press Enter to begin, then Ctrl-C to quit")

    # SimSig username and password required for payware sims
    connection.connect(username="alice", password="swordfish")
    try:
        while True:
            input()
    except KeyboardInterrupt:
        print()

```

## Exceptions

`simsig_interface` raises a few of its own exceptions:

`InvalidLogin`: on attempting to connect to a payware sim without valid user credentials

`ConnectionTimeout`: if the connection times out on initial attempt to connect

`MalformedStompMessage`: if the parser can't make sense of a STOMP message
