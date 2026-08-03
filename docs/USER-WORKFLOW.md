# User Workflow

## 1. Understand the test

Read the specification, clarify missing requirements and confirm the required
data and resolution.

## 2. Select and design

Select suitable instruments, draw the wiring diagram and write the procedure
outside Test in a Box.

## 3. Configure hardware

Select a saved hardware definition or add a new one, set its current connection,
assign it to a logical role, verify communication and commission it using the
mimic panel.

## 4. Define project metadata

Example:

- Project: `TO-1800`
- DUT: `C`
- Test case: `TC2`
- Test name: `Pickup and Hold Voltage`

Suggested display name:

`TO-1800.C — TC2 Pickup and Hold Voltage`

## 5. Define parameters

Examples include `40 °C`, `110 °C`, `10 °C`, `3600 s`, `9 V`, `16 V` and
`1 V`. Parameters are defined once and referenced throughout the procedure.

## 6. Author and run

Build the sequence in Blockly using logical hardware roles. The Execute view
shows status, percentage, estimated finish time, current DUT, current step and
result counts where applicable.

## 7. Review

Each run produces CSV data and a Markdown summary, including instrument identity.
