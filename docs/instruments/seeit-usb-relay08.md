# Seeit USB and USBB Relay Controllers

Test in a Box supports two different Seeit relay-board interfaces. They expose
the same logical relay positions but use different transports.

## Driver status

The native Windows USBB implementation has switched physical relay hardware
successfully. Selection of two duplicate-serial boards has been proven with
the vendor enumeration nodes; final confirmation through the main application
remains part of the current alpha validation. The serial implementation has
not yet been bench tested.

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

It does not use a COM port. This driver is Windows-only; the vendor DLL
does not run on Linux or macOS.

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
- **Physical Relay Board** — use **Scan for Devices** and select the required
  enumerated board.
- **Safe State** — `open_all` or `close_all`.

Python and the DLL must have matching architectures. A 64-bit Python
installation requires a 64-bit DLL.

The DLL is vendor software and is not included in the Test in a Box repository.
Obtain it from the hardware supplier and confirm that its licence permits your
intended use and redistribution arrangements.

## Discovering more than one native USB relay

The factory serial number is not guaranteed to be unique. When more than one
board is connected:

1. Open the instrument's cog menu.
2. Select **Scan for Devices**.
3. Choose the required board from the discovered list.
4. Give the instrument a meaningful Test in a Box name, such as
   `Relay bank 1`.
5. Toggle one channel manually to confirm the physical identity, then label the
   enclosure.

Test in a Box uses the best identifier exposed by the vendor DLL. Where the
DLL supplies no unique path, it stores an enumeration selector such as
`index:1` or `index:2`.

### Duplicate DLL identifiers

Some boards report the same factory serial number and the same device-path
value through the vendor DLL. When that happens, Test in a Box automatically
uses the board's enumeration index for selection.

The discovered list will show entries such as:

```text
enumerated device 1
enumerated device 2
```

Assign one to each Instrument Library entry, save and reconnect, then toggle a
relay to identify and label the physical boards.

Enumeration order may change after reconnecting hardware or rebooting Windows.
If a saved selection later controls the wrong board, scan and assign the boards
again.

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
