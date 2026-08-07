# LAB-DCH Validation + Repository Cleanup

## Validation change

LAB-DCH output-disable validation now polls measured voltage rather than
assuming the output must be below 0.3 V after a fixed 0.5 second wait.

The procedure now allows up to 5 seconds:

- initial measured-voltage read;
- poll every 250 ms;
- pass once voltage is <= 0.3 V;
- fail only if voltage remains above 0.3 V after 20 polls.

This preserves a meaningful safe-discharge check while allowing for output
capacitance.

## Repository cleanup

This was a targeted release-cleanup pass, not an architectural refactor.

Removed/generated items:

- No additional removable generated files were present.

## Validation workspaces updated

- `examples/validation/labdch_smoke_test.json`
- `examples/validation/labdch_driver_validation.json`
- `webapp/sequences/LAB-DCH Smoke Test.json`
- `webapp/sequences/LAB-DCH Driver Validation.json`
