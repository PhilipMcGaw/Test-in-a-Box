# Results and Traceability

## Formats

Version 0.1 uses CSV for machine-readable results and Markdown for the
human-readable run summary.

## Informational and evaluated measurements

An informational measurement is recorded without a verdict. Evaluated
measurements may later support pass, warning and fail outcomes; the richer
evaluation engine is not required for the first v0.1 milestone.

## Suggested layout

```text
runs/
  <run_id>/
    run_metadata.csv
    summary.md
    DUT_<identifier>.csv
```

## Run metadata

Record the run ID, project, DUT set, test case and name, timestamps, operator
where supplied, software version, parameters and units, hardware mappings, and
`*IDN?` or equivalent responses.

## Suggested measurement schema

```text
timestamp,run_id,project,dut_id,test_case,device_role,device_id,position,channel,value,unit,event_type,result_level
```

The exact schema may evolve, but units and DUT identity must not be implicit.

## Markdown summary

Include project, DUT and test name, start and finish, duration, result files,
measurement count, warning/failure counts where applicable, instrument identity,
and a clear note when the test was for information only.
