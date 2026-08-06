# Protocol Explorer v0.1

Open:

```text
http://127.0.0.1:8765/engineering-tools/protocol-explorer
```

Protocol Explorer can communicate through:

1. a connected Test in a Box driver that implements `query()`;
2. a direct serial-port connection.

Connected-driver mode is recommended for the LAB-DCH because the configured
driver already owns COM15. It sends raw commands through the driver's serial
lock without opening the COM port a second time.

## LAB-DCH commissioning sequence

Start with read-only commands:

```text
ID
*IDN?
*OPT?
MODE
STATUS
*STB?
UA
IA
SB
MU
MI
OVP
```

Then, with the bench setup confirmed safe:

```text
SB,S
GTR
MODE,UI
OVP,36
UA,12
IA,1
SB,R
SB
MU
MI
STATUS
*STB?
MODE
```

Commands that do not return a reply should be sent with **Read response**
unchecked to avoid waiting for the serial timeout.

The session can be copied or saved as a text log.
