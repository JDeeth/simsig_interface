# SimSig Interface Client

[![Tests](https://github.com/JDeeth/simsig_interface/actions/workflows/run_tests.yaml/badge.svg)](https://github.com/JDeeth/simsig_interface/actions/workflows/run_tests.yaml)

This will be a wrapper for the SimSig Interface Gateway, aimed at support of other client apps.

- [x] Set up project, test framework, etc
- [x] `Connection` class wrapping [`stomp.py`](https://jasonrbriggs.github.io/stomp.py/quickstart.html#command-line-client)
- [ ] Parse messages from SimSig
- [ ] Send commands to SimSig

## SimSig Interface Gateway

As of SimSig v5.21, Sep 2022:

The SimSig Interface Gateway is a [STOMP](https://stomp.github.io/index.html) interface for SimSig. A client can subscribe to receive notification of in-game events, and send some commands back to the game.

### Messages sent

SimSig sends messages about the following entities and events:

 - Train describer berths
 - Track circuits
 - Points
 - Signals
 - "Flags" (A kind of general-purpose state-indicating mechanism)
 - Routes
 - Subroutes
 - Ground frames
 - Level crossings
 - Trains passing timing points
 - Train delay
 - Game clock

## Quick start

For Python, [`stomp.py`](https://jasonrbriggs.github.io/stomp.py/quickstart.html#command-line-client) is a good client library which also has an interactive command-line functionality, which is a good way to test interactions with SimSig.

On a PC with Python installed:

    pip install stomp.py
    # launch SimSig, start Brighton with Interface Gateway enabled
    stomp -H localhost -P 51515
    subscribe /topic/TD_ALL_SIG_AREA

This will connect to SimSig and subscribe to messages relating to the interlocking.

Set a route and you'll see a flurry of messages, as the route and its subroutes are locked, points move, signal aspects change...

Send a command to interpose a train description:

    send /topic/TD_ALL_SIG_AREA {"cc_msg":{"to": "0663", "descr": "2A80"}}

You should see `2A80` appear at platform 1 at Brighton.

## Technicalities

### Payware sims
To connect to payware sims, you must have a licence for the sim, and authenticate yourself with your SimSig username and password when connecting.

For example with the `stomp.py` command line client:

    stomp -H localhost -P 51515 -U Bobby -P swordfish

There will be a delay while SimSig authenticates you.

### True/false and numbers as strings

SimSig communicates using JSON messages, but often represents boolean and integer values as strings, rather than as JSON `true`, `false`, and integers.

```json
{
    "locked": "True",
    "time": "1523"
}
```
vs
```json
{
    "locked": true,
    "time": 1523
}
```

### Error message

If a client sends an invalid command e.g. malformed JSON, SimSig shows an error message to the host:

> Internal error: Stomp JSON message badly formed

This appears to only happen once - any subsequent errors are ignored, and subsequent valid messages are processed.

### Game time

SimSig communicates time as a number of seconds after midnight on the day the sim started.

### Game speed

SimSig communicates game speed indirectly. It reports an `interval`, where 500 is normal speed and smaller = faster. To obtain a speed ratio, divide 500 by the interval.

## Topics

Interaction is organised into four topics (STOMP destinations):

 * `/topic/TD_ALL_SIG_AREA`
   - Train describers
   - Track circuits
   - Points
   - Signals
   - Flags
   - Routes
   - Reserved tracks (subroutes)
   - Ground frames
   - Level crossings
 * `/topic/TRAIN_MVT_ALL_TOC`
   - Train passing location
   - Train delay
 * `/topic/TRAIN_MVT_SUMMARY`
   - (TBC)
 * `/topic/SimSig`
   - Game clock

---

### /topic/TD_ALL_SIG_AREA

#### Train describer

There are three kinds of train describer message / commands:

Type | Description
-----|------------
CA   | Step (advance) train description from one berth to the next
CB   | Cancel train description from a berth
CC   | Interpose train description to a berth

Berths are often but not always associated with signals.

##### Messages sent

```json
{
    "CA_MSG": {
        "area_id": "waterloo",
        "from": "0243",
        "to": "0235",
        "descr": "2R02",
        "msg_type": "CA",
        "time": "16250"
    }
}
{
    "CB_MSG": {
        "area_id": "waterloo",
        "from": "0130",
        "descr": "",
        "msg_type": "CB",
        "time": "16249"
    }
}
{
    "CC_MSG": {
        "area_id": "waterloo",
        "to": "0149",
        "descr": "1A30",
        "msg_type": "CC",
        "time": "16257"
    }
}
```
Field      | Description
-----------|------------
`area_id`  | Name of simulation
`from`     | Berth to remove TD from
`to`       | Berth to interpose TD into
`descr`    | TD to interpose
`msg_type` | `CA`, `CB`, or `CC` as described above
`time`     | Game time in seconds after midnight **as string**

##### Commands accepted

This topic accepts commands to advance, cancel, and interpose train descriptions:

```json
{"ca_msg": {"from": "HJ9", "to": "HJ13", "descr": "2B42"}}

{"cb_msg": {"from": "HJ10"}}

{"cc_msg": {"to": "HJ6", "descr": "1A69"}}
```

Field   | Description
--------|------------
`from`  | ID of berth to remove train description from
`to`    | ID of berth to interpose train description into
`descr` | Train description to interpose

#### Track circuits

These messages are sent when a track circuit status changes.

```json
{
    "SG_MSG": {
        "area_id": "waterloo",
        "obj_id": "T1371",
        "obj_type": "track",
        "clear": "False",
        "msg_type": "SG",
        "time": "16280"
    }
}
```

Field      | Description
-----------|------------
`area_id`  | Name of simulation
`obj_id`   | Track circuit ID, prefixed with `T`
`obj_type` | `"track"`
`clear`    | `"True"` or `"False"` **as string**
`msg_type` | `"SG"`
`time`     | Game time in seconds after midnight **as string**

#### Points

##### Messages sent

These messages are sent when the status of a set of points changes.

```json
{
    "SG_MSG": {
        "area_id": "waterloo",
        "obj_id": "P721B",
        "obj_type": "point",
        "dn": "True",
        "dr": "False",
        "cn": "True",
        "cr": "False",
        "kn": "False",
        "kr": "False",
        "locked": "False",
        "msg_type": "SG",
        "time": "16577"
    }
}
```

Field      | Description
-----------|------------
`area_id`  | Name of simulation
`obj_id`   | Point ID, prefixed with `P`
`obj_type` | `"point"`
`dn`       | Detected normal
`dr`       | Detected reverse
`cn`       | Called normal
`cr`       | Called reverse
`kn`       | Keyed normal
`kr`       | Keyed reverse
`locked`   | Locked (by interlocking - unable to move)
`msg_type` | `"SG"`
`time`     | Game time in seconds after midnight **as string**

Note that `"True"` and `"False"` values here are strings.

##### Commands accepted

Points can be keyed normal and reverse with these commands:

```json
{"sigobjstate": {"object": "P2377B", "keyN": "0"}}

{"sigobjstate": {"object": "PHJ33B", "keyR": "1"}}
```

Note that `"0"` and `"1"` here are strings.

#### Signals

##### Messages sent

```json
{
    "SG_MSG":
        {"area_id": "royston",
        "obj_id": "SK980",
        "obj_type": "signal",
        "aspect": "6",
        "bpull": "False",
        "rset": "True",
        "appr_lock": "False",
        "lp": "True",
        "auto": "False",
        "trts": "False",
        "stackN": "False",
        "stackX": "False",
        "msg_type": "SG",
        "time": "617"
    }
}
```

Field       | Description
------------|------------
`area_id`   | Name of simulation
`obj_id`    | Signal ID, prefixed with `S`
`obj_type`  | `"signal"`
`aspect`    | Aspect displayed by signal - see chart below
`bpull`     | Has a signaller cancelled this signal?
`rset`      | Is a route set from this signal?
`appr_lock` | Is the signal approach-locked?
`lp`        | Is the signal lamp proved?
`auto`      | Is the auto button set (or the emergency replacement button **not** set)?
`trts`      | Is the Train Ready To Start indication active?
`stackN`    | (Relates to stacked routes)
`stackX`    | (Relates to stacked routes)
`msg_type`  | `"SG"`
`time`      | Game time in seconds after midnight **as string**

Value | Aspect
------|-------
`"0"` | Red
`"1"` | Position light
`"2"` | Yellow
`"3"` | Flashing yellow
`"4"` | Double yellow
`"5"` | Flashing double yellow
`"6"` | Green

Note the use of strings for `"True"`, `"False"`, and the aspect numbers.

##### Commands accepted

Signals can be set to danger with this command:

```json
{"bpull": {"signal": "SHJ10"}}
```

#### Flags

Flags are used for various purposes from simulation to simulation, often to simulate status lights not represented by other simulator features.

##### Messages sent

```json
{
    "SG_MSG": {
        "area_id": "royston",
        "obj_id": "LSTOPSIGNU",
        "obj_type": "flag",
        "state": "0",
        "msg_type": "SG",
        "time": "617"
    }
}
```

Field       | Description
------------|------------
`area_id`   | Name of simulation
`obj_id`    | Flag ID, prefixed with `L`
`obj_type`  | `"flag"`
`state`     | Integer as string, usually `"0"` or `"1"` but can be up to `"63"`
`msg_type`  | `"SG"`
`time`      | Game time in seconds after midnight **as string**

##### Commands accepted

Flags can be set with this command:

```json
{"sigobjstate": {"object": "LWHJINTCON", "state": "true"}}
```

Note `"true"` and `"false"` must be strings.

#### Routes

These are the defined routes between NX pairs.

##### Messages sent

```json
{
    "SG_MSG": {
        "area_id": "royston",
        "obj_id": "RK984AM",
        "obj_type": "route",
        "is_set": "True",
        "msg_type": "SG",
        "time": "1828"
    }
}
```

Field       | Description
------------|------------
`area_id`   | Name of simulation
`obj_id`    | Route ID, prefixed with `R`
`obj_type`  | `"route"`
`is_set`    | `"True"` or `"False"` **as string**
`msg_type`  | `"SG"`
`time`      | Game time in seconds after midnight **as string**

Route IDs are usually in this format:

    R{signal}{position}{class}

Element    | Description
-----------|------------
`signal`   | Identifier for the starting signal
`position` | `A` being the leftmost route, `B` the second leftmost, etc
`class`    | `M`: Main, `S`: Shunt, `C`: Call-on, `V`: Virtual

##### Commands accepted

SimSig allows routes to be requested in two ways:

```json
{"routerequest": {"route": "RHJ1AM"}}

{"routerequest": {"fromSignal": "SHJ3","toSignal": "SHJ5"}}
```

A route request can be cancelled with a `bpull` command.

#### Subroutes / reserved tracks

Broadly speaking, these are track circuit sections lit with white lights when setting a route, and cleared by the passage of a train or the cancelling of the route.

```json
{
    "SG_MSG": {
        "area_id": "waterloo",
        "obj_id": "U1027-AB",
        "obj_type": "ulc",
        "locked": "False",
        "overlap": "False",
        "msg_type": "SG",
        "time": "19308"
    }
}
```

Field       | Description
------------|------------
`area_id`   | Name of simulation
`obj_id`    | Subroute ID, prefixed with `U`
`obj_type`  | `"ulc"`
`locked`    | `"True"` or `"False"` **as string**
`overlap`   | `"True"` or `"False"` **as string**
`msg_type`  | `"SG"`
`time`      | Game time in seconds after midnight **as string**

#### Ground frames

##### Messages sent

```json
{
    "SG_MSG": {
        "area_id": "kingsx",
        "obj_id": "F2261",
        "obj_type": "frame",
        "release_given": "True",
        "release_taken": "False",
        "reminder": "False",
        "msg_type": "SG",
        "time": "22"
    }
}
```

Field           | Description
----------------|------------
`area_id`       | Name of simulation
`obj_id`        | Ground frame ID, prefixed with `F`
`obj_type`      | `"frame"`
`release_given` | Has the signaller released theframe
`release_taken` | Has the ground frame operator taken the release
`reminder`      | Has the signaller collared the release
`msg_type`      | `"SG"`
`time`          | Game time in seconds after midnight **as string**

Note `"True"` and `"False"` are strings.

##### Commands accepted

Frames can be released / unreleased with this command:

```json
{"framerelease": {"frame": "F2261", "release": "True"}}
```

There does not appear to be a command to take the release.

#### Controlled level crossings

##### Messages sent

```json
{
    "SG_MSG": {
        "area_id": "exeter",
        "obj_id": "GPINX",
        "obj_type": "crossing",
        "state": "0",
        "lower_reminder": "False",
        "raise_reminder": "False",
        "clear_reminder": "False",
        "auto_reminder": "False",
        "auto_lower": "True",
        "request_lower": "True",
        "request_raise": "False",
        "blocked": "0",
        "msg_type": "SG",
        "time": "0"
    }
}
```

Field            | Description
-----------------|------------
`area_id`        | Name of simulation
`obj_id`         | Crossing ID, prefixed with `G`
`obj_type`       | `"crossing"`
`state`          | `0`: Up, `1`: Lowering, `2`: Down, `3`: Clear, `4`: Raising
`lower_reminder` | Is a reminder device on the lower control
`raise_reminder` | Is a reminder device on the lower control
`clear_reminder` | Is a reminder device on the lower control
`auto_reminder`  | Is a reminder device on the lower control
`auto_lower`     | Is the crossing set to automatically **raise** - `"True"` means it will
`request_lower`  | Has the signaller requested lowering the barriers
`request_raise`  | Has the signaller requested raising the barriers
`blocked`        | `"0"` Barriers up, `"1"` Barriers down, `"2"` Barriers down and crossing obstructed
`msg_type`       | `"SG"`
`time`           | Game time in seconds after midnight **as string**


##### Commands accepted

To `raise`, `lower`, or `clear` a manual crossing, you can use this command:

```json
{"crossingrequest": {"crossing": "GPENCOED", "operation": "raise"}}
```

To set/unset the auto-raise control:

```json
{"crossingauto": {"crossing": "GPENCOED", "autoraise": "False"}}
```

#### Automatic level crossings

```json
{
    "SG_MSG": {
        "area_id": "exeter",
        "obj_id": "HVIC",
        "obj_type": "ahb",
        "state": "3",
        "user_state": "0",
        "tel_message": "23",
        "reminder": "False",
        "failed": "False",
        "failed_ack": "False",
        "msg_type": "SG",
        "time": "699"
    }
}
```

Field        | Description
-------------|------------
`area_id`    | Name of simulation
`obj_id`     | Crossing ID, prefixed with `H`
`obj_type`   | `"ahb"`
`state`      | `0`: Idle, `1`: Delayed lowering, `2`: Amber lights, `3`: Red lights, `4`: Barriers down
`user_state` | ?
`tel_msg`    | ?
`reminder`   | Is a reminder device on the controls
`failed`     | Has the crossing detected a failure
`failed_ack` | Has the signaller acknowledged the failure
`msg_type`   | `"SG"`
`time`       | Game time in seconds after midnight **as string**

#### Snapshot

You can request the state of all the entities in this topic with this command:

    {"snapshot":{}}

SimSig will send a message with this data, however, it is presented as a single JSON object with duplicate `SG_MSG` keys:

    {
        "SG_MSG": {"area_id": "royston", "obj_id": "HLITLINGTON", "obj_type": "ahb", ...},
        "SG_MSG": {"area_id": "royston", "obj_id": "HIVY", "obj_type": "ahb", ...},
        "SG_MSG": {"area_id": "royston", "obj_id": "L2368ARM", "obj_type": "flag", ...},
        ...
        "SG_MSG": {"area_id": "royston","obj_id": "U4861-BA","obj_type": "ulc", ...}
    }

This is technically valid - the JSON spec only says that you SHOULD always use distinct keys, not that you MUST, however in practice most languages' JSON libraries prohibit duplicate keys and won't parse this message correctly.

To work around this in Python:

```python
messages = list()

def collect_msg(msg_body):
    messages.append(msg_body)

json.loads(frame.body, object_hook=collect_msg)
```
This would transform this input:
```json
{
    "SG_MSG": {"obj_id": "SAN126", "aspect": 0},
    "SG_MSG": {"obj_id": "SAN128", "aspect": 6}
}
```
into a list of dictionaries:
```python
[
    {"obj_id": "SAN126", "aspect": 0},
    {"obj_id": "SAN128", "aspect": 6},
    {"SG_MSG": None}
]
 ```
The final `{"SG_MSG": None}` item can then be sliced or popped off.

### /topic/TRAIN_MVT_ALL_TOC

#### Train passing location

Train passing a timing point:

```json
{
    "train_location": {
        "headcode": "5M01",
        "uid": "4",
        "action": "pass",
        "location": "INTJN",
        "platform": "5",
        "time": 15445
    }
}
```

Train passing a signal:

```json
{
    "train_location": {
        "headcode": "1O28",
        "uid": "5",
        "action": "pass",
        "location": "SVC92",
        "platform": "",
        "time": 15310,
        "aspPass": 6,
        "aspAppr": 2
    }
}
```
Field        | Description
-------------|------------
`headcode`   | The train description
`uid`        | Unique identifier within sim - not the same as the timetable UID
`action`     | 'arrive', 'depart', or 'pass'
`location`   | TIPLOC of timing point, or ID of signal
`platform`   | Can indicate platform at a station, or line taken at a junction
`time`       | Game time in seconds after midnight **as `int`**
`aspPass`    | Aspect shown when passing the signal **as `int`**
`aspAppr`    | Aspect shown when approaching the signal **as `int`**

#### Train delay

```json
{
    "train_delay": {
        "headcode": "5M01",
        "uid": "",
        "delay": -240
    }
}
```

Field        | Description
-------------|------------
`headcode`   | The train description
`uid`        | Unique identifier within sim - not the same as the timetable UID
`delay`      | Current delay in seconds - negative is early.

Delays seem to be reported in multiples of 60 (i.e. to the nearest minute) when passing a timing point, and to the second when arriving/departing.

### /topic/TRAIN_MVT_SUMMARY

This topic is mentioned in the SimSig wiki but as of v5.21 does not appear to send any messages.

### /topic/SimSig

This topic sends one type of message and accepts one command.

#### Game clock

##### Messages sent

These are emitted:
 - when the game speed changes (including pause/unpause)
 - once per minute (when the minute changes)

```json
{
    "clock_msg": {
        "area_id": "waterloo",
        "clock": 15720,
        "interval": 500
    }
}

```
Field      | Description
-----------|------------
`area_id`  | Simulation name
`clock`    | Game time, seconds after midnight
`interval` | Game speed ratio = 500 / `interval` (so 500 is normal speed)
`paused`   | Coming soon!

Note that here the time and interval are transmitted as `int`, rather than as strings.

##### Commands accepted

This topic accepts one command:

```json
{"idrequest": {}}
```

This appears to cause the most recent `clock_msg` to be sent again, which would give you out-of-date `clock` data.
