# Instrument Discovery and Naming v1

## LAB-DCH discovery

The LAB-DCH 30-665 driver now owns its COM-port discovery logic. It scans
enumerated serial ports using the configured 9600 8-N-1 settings and the
driver's documented identification sequence:

1. `*IDN?`
2. `ID` as a fallback

Only responses identifying a LAB-DCH instrument are returned to **Find
Compatible Instrument**.

Keeping identification inside the driver prevents the web interface from
having to know model-specific commands.

## Friendly default instrument names

Dragging an instrument from the library now creates an engineer-readable
device name based on the catalogue label, for example:

```text
LAB-DCH 30-665 PSU 1
Aim-TTi PSU 1
Seeit USBB Relay (Native USB) 1
```

The internal driver key, such as `labdch_30_665`, remains separate and is
not used as the default visible name. Existing configured names are not
changed.
