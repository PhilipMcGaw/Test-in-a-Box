# Seeit USB and USBB Relay Controllers

Test in a Box supports two different Seeit relay-board interfaces. They expose
the same logical relay positions but use different transports.

## Driver status

Both implementations remain unverified against the physical boards until bench
testing is complete.

## USB-RELAY08 using a virtual COM port

Select:

```text
Seeit USB-RELAY08 (Serial)
```

This board uses a Prolific PL2303 USB-to-serial converter and communicates at:

```text
9600 baud
```

After the Windows PL2303 driver is installed, find the assigned COM port in
Device Manager and enter it on the **Configure Devices** page.

The serial command set was adapted from a community implementation because a
public vendor protocol document was not available. Confirm all channel and
state behaviour during the first bench test.

## USBB relay using the native USB DLL

Select:

```text
Seeit USBB Relay (Native USB)
```

This version uses the vendor-supplied:

```text
usb_relay_device.dll
```

It does not use a COM port.

The recommended no-admin installation is:

```text
Test-in-a-Box/
  vendor/
    seeit/
      usb_relay_device.dll
```

Configure:

- **Vendor DLL Path** — normally leave this as `usb_relay_device.dll` when the
  DLL is in `vendor/seeit/`. An absolute path can also be used.
- **Device Serial Number** — required when more than one compatible relay board
  is attached.
- **Safe State** — `open_all` or `close_all`.

Python and the DLL must have matching architectures. A 64-bit Python
installation requires a 64-bit DLL.

The DLL is vendor software and is not included in the Test in a Box repository.
Obtain it from the hardware supplier and confirm that its licence permits your
intended use and redistribution arrangements.

## Relay positions

Both drivers expose channels as:

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

Native USB devices with fewer channels expose only the channels reported by the
vendor DLL.

## Important state terminology

The serial implementation uses logical **ON** and **OFF** states.

The current native DLL SDK uses the vendor terms **open** and **close**:

- `open` means relay ON;
- `close` means relay OFF;
- a status bit of `1` means ON;
- a status bit of `0` means OFF.

Test in a Box maps a truthy write value to relay ON and a false value to relay
OFF. Confirm the resulting NO/NC contact behaviour, external wiring and intended
safe condition before relying on automated shutdown.

## Enclosure and breakout recommendation

For regular engineering use, fit bare relay boards inside a suitable enclosure
and bring the relay contacts out to clearly labelled, touch-safe connectors.

The enclosure should identify:

- relay number;
- common contact;
- normally-open contact;
- normally-closed contact;
- local voltage and current limits.

Document the enclosure wiring separately. Test in a Box controls logical relay
numbers; it cannot determine how contacts are wired externally.

## Safety

A relay-board contact rating is not, by itself, a complete statement of what is
safe in a fixture.

Use appropriate fusing, insulation, creepage and clearance, touch-safe
connectors, cable ratings, strain relief and protective-earth arrangements
where applicable.

Do not rely on an unverified driver or unconfirmed `open`/`close` interpretation
for hazardous-voltage or unattended testing.
