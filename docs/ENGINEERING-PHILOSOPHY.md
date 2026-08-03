# Engineering Philosophy

## Automate good engineering

The normal workflow remains:

1. Read the specification.
2. Ask for missing information.
3. Clarify data requirements, including resolution.
4. Suggest changes that may provide more useful answers.
5. Select instruments.
6. Draw the wiring diagram outside Test in a Box.
7. Write the procedure.
8. Automate its execution.

Test in a Box does not replace the first seven steps.

## Express intent, not protocol

A procedure should say set the chamber to 40 °C, wait for DUT soak, apply 9 V
to the coil and log contact resistance. It should not expose SCPI or vendor APIs
outside diagnostics.

## Units first

Parameters and measurements carry explicit units: `40 °C`, `3600 s`,
`0.2 V/s`, `0.373 mΩ`. Units reduce ambiguity and allow invalid combinations to
be rejected.

## Preserve intent, not bench wiring

Reproducibility means preserving the procedure, parameters, logical hardware
requirements, DUT metadata and result interpretation. The physical equipment is
mapped again when the test is run.

## Capture evidence

Some R&D tests are for information or characterisation. They must not be forced
into artificial pass/fail outcomes.

## Keep the operator informed

The execution screen should answer: Is it running? How far through is it? Which
DUT and step are active? When is it likely to finish? Is intervention required?
Protocol details belong in diagnostics.
