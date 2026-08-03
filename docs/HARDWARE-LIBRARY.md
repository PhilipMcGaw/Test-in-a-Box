# Hardware Library

## New hardware

When an instrument is not yet stored:

1. Create a hardware definition.
2. Select its type.
3. Describe its capabilities.
4. Select its communication method.
5. Enter or import its command map or driver details.
6. Verify it using the mimic panel.
7. Save it to the library.

## Existing hardware

Later projects select the saved make/model definition, configure the current
connection and assign it to a logical role.

Typical roles include coil power supply, environmental chamber,
contact-state monitor and temperature logger.

## Identity capture

At run start, each driver returns identity information. For SCPI instruments
this normally includes the full `*IDN?` response. Non-SCPI drivers return the
closest equivalent.

Where available, record logical role, driver, manufacturer, model, serial
number, firmware, full identity response and connection details used for the run.
