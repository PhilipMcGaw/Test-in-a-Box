# LAB-DCH 30-665 Output Enable Characterisation

Bench testing showed that a single `SB,R` can make `SB` report `SB,R`
without energising the output stage.

The reliable sequence observed on physical hardware was:

```text
MODE,UI
SB,S
delay
SB,R
delay
SB,R
delay
SB
```

After this sequence the red output indicator illuminated and `MU` reported
the programmed voltage.

The driver now applies this sequence automatically when its `output`
position is set to `True`.

Configure Devices exposes:

- **Output Transition Delay (s)** — default `0.25`;
- **Output Enable Commands** — default `2`.

These settings allow adjustment if another firmware revision requires a
longer transition or a different number of enable commands.
