# Seeit USB-RELAY08

## Status

Driver support is present but remains unverified against the physical board
until bench testing is complete.

## Interface

The USB-RELAY08 is an eight-channel relay controller connected through a
virtual serial COM port.

The board communicates at:

```text
9600 baud
```

## Windows driver installation

The board uses a **Prolific PL2303 USB-to-serial converter**.

Windows may require the PL2303 driver before the board appears as a COM port.
The driver and supporting downloads are available from the manufacturer page:

https://seeit.fr/produits.php?produit_ref=USB-RELAY08

Installing the driver normally requires **administrator rights**.

After installation:

1. Disconnect the relay board.
2. Reconnect it using a USB-A to Micro-USB cable.
3. Open Windows Device Manager.
4. Find the new COM port under **Ports (COM & LPT)**.
5. Enter that COM port on the Test in a Box **Configure Devices** page.
6. Press **Save & Reconnect**.

## Test in a Box configuration

Add:

```text
Seeit USB-RELAY08
```

Then set:

```text
COM Port: the port shown by Windows Device Manager
```

## Channel numbering

Test in a Box exposes the eight relays as:

```text
relay1
relay2
relay3
relay4
relay5
relay6
relay7
relay8
```

Confirm the physical terminal numbering during the first bench test before
connecting a DUT.

## Enclosure and breakout recommendation

For regular engineering use, and particularly for education or shared
laboratories, the bare relay board should preferably be fitted inside a
suitable enclosure.

Bring the relay contacts out to clearly labelled, touch-safe connectors such
as jacks or terminal sockets. The enclosure should identify:

- relay number;
- common contact;
- normally-open contact;
- normally-closed contact;
- any voltage or current limits imposed by the local installation.

This reduces wiring errors, protects the electronics and provides a repeatable
fixture interface.

Document the enclosure wiring separately because Test in a Box controls logical
relay numbers; it cannot determine how those contacts have been wired
externally.

## Safety

The relay-board contact rating is not, by itself, a complete statement of what
is safe in a particular enclosure or fixture.

Use appropriate fusing, insulation, creepage and clearance, touch-safe
connectors, cable ratings, strain relief and protective-earth arrangements
where applicable.

Do not use a bare relay board for hazardous-voltage teaching or unattended
testing.
