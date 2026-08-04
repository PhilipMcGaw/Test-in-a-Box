# Expected Results

The generated Python should be equivalent to:

```python
set("aimtti_psu_1", "v1", 10)
set("aimtti_psu_1", "i1", 3)
set("aimtti_psu_1", "output1", 1)
wait(5)
set("aimtti_psu_1", "output1", 0)
```

The console should show the set operations and the five-second wait. The PSU
output should be off when the procedure completes.
