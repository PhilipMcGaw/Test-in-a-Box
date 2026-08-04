# Expected Results

Representative generated Python:

```python
set("aimtti_psu_1", "v1", 10)
set("aimtti_psu_1", "i1", 3)
set("aimtti_psu_1", "output1", 1)
wait(1)
measured_voltage = get("aimtti_psu_1", "v1_meas")
log("Measured voltage", measured_voltage)
assert_that(
    abs(measured_voltage - 10) <= 0.2,
    "Measured voltage outside 10 V ± 0.2 V",
)
set("aimtti_psu_1", "output1", 0)
```

The CSV should include a labelled log row whose value is the measured voltage,
followed by an assertion row.
