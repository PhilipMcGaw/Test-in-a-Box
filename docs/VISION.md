# Vision

Test in a Box exists to reduce the amount of bespoke software engineers have
to write when automating electrical and environmental validation tests.

The project is aimed first at R&D work: one-off and evolving tests where an
engineer needs to get from a specification to useful data quickly, without
first building a large test framework.

The software should help an engineer configure laboratory hardware, build a
clear visual test procedure, run it across one or more DUTs or EUTs, monitor
progress and estimated finish time, and record useful results.

The goal is not to replace engineering judgement. Test in a Box automates the
repetitive implementation work that follows good engineering decisions.

> Tests should express what the engineer wants to happen, while drivers decide
> how to communicate with the equipment.

A test step should say **set the coil supply to 12 V**, not **send `VOLT 12`
to COM7**.

The initial focus includes voltage sweeps, power cycling, temperature soak and
cycling, relay and contactor characterisation, repeated multi-DUT tests, and
informational measurements where no pass/fail criterion exists.

Production and end-of-line testing may be explored later, but are not the
immediate goal.
