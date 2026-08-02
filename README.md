<p align="center">
  <img src="docs/images/TestinaBox.png"
       width="192"
       alt="Test in a Box logo">
</p>

<h1 align="center">Test in a Box</h1>

<p align="center">
An open-source engineering test automation platform for automated validation,
laboratory instrumentation, and hardware testing.
</p>

<p align="center">

[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/License-PolyForm%20Noncommercial%201.0.0-purple.svg)](https://polyformproject.org/licenses/noncommercial/1.0.0)

</p>

## Project Website

For more information about the motivation, architecture, and future roadmap:

https://philipmcgaw.com/projects/test-in-a-box/

---

# What is Test in a Box?

**Test in a Box** is an open-source engineering test automation platform designed
to simplify the creation and execution of repeatable validation procedures for
**Devices Under Test (DUTs)** and **Equipment Under Test (EUTs)**.

The project is focused initially on **research and development (R&D) testing**,
where engineers need to repeatedly evaluate multiple devices against defined
test procedures, collect measurements, and record pass/fail results.

Test in a Box provides a flexible framework for building automated test
sequences that can control laboratory equipment, apply defined test conditions,
capture data, and provide consistent results across multiple test samples.

The long-term vision is to provide a scalable test automation platform that can
support the engineering lifecycle from early prototype validation through to
more structured automated testing environments.

---

# Why was Test in a Box created?

Engineering test systems are often built as one-off solutions, combining custom
scripts, instrument drivers, spreadsheets, and manual procedures.

While these approaches can work, they can become difficult to maintain,
reproduce, and expand as test requirements grow.

Test in a Box aims to provide a common framework for:

- Creating repeatable automated test procedures.
- Testing multiple DUTs using the same defined sequence.
- Controlling different types of laboratory equipment.
- Capturing measurements and test results.
- Improving test traceability and repeatability.
- Reducing the amount of custom software required for each test system.

---

# Key Features

## Hardware abstraction

Test in a Box separates test procedures from hardware implementation through a
driver-based architecture.

This allows different instruments and equipment to be integrated through a
common interface rather than requiring custom code for every test setup.

Supported and planned integrations include:

- SCPI-controlled laboratory instruments.
- Programmable power supplies.
- Relay switching hardware.
- Temperature measurement equipment.
- Data acquisition hardware.
- Custom engineering hardware.

---

## Visual test sequence development

The project includes a Blockly-based interface allowing engineers to create
test sequences visually.

The aim is to allow test procedures to be created and modified without every
change requiring software development.

Current capabilities include:

- Hardware control blocks.
- Measurement acquisition.
- Wait and timing functions.
- Loop execution.
- Operator prompts.
- Logging.
- Assertions and pass/fail checks.

---

# Current Architecture

```

Test Sequence
|
v
Blockly Interface
|
v
Generated Test Procedure
|
v
Test Runner
|
+----------------+
|                |
v                v
Hardware Drivers    Result Logger
|
+----------------+
|
v
Laboratory Equipment

```

The core components are:

```

hwapp/
drivers/
base.py             Driver interface and common data structures
registry.py         Driver registration system
scpi_generic.py     Generic SCPI instrument driver
scpi_command_map.example.json
seeit_relay.py      Relay controller driver
pico_tc08.py        Pico TC-08 temperature logger
pico_adc.py         Pico ADC-20/24 driver
mock.py             Simulation drivers for development

run/
mapping.py          DUT position mapping
csv_logger.py       Test result logging
runner.py           Test execution engine

webapp/
server.py             FastAPI web application
static/
index.html          Blockly workspace
app.js              User interface logic
custom_blocks.js    Hardware test blocks
generators.js       Python code generation

```

---

# Running on Windows without administrator rights

Test in a Box is designed to operate in restricted engineering environments
where users may not have permission to install software globally.

See:

```

SETUP_INSTRUCTIONS.md

```

for detailed instructions.

The short version:

1. Install the included portable Python environment.
2. Run the startup batch file.
3. Open the local web application.

The application runs locally:

```

http://127.0.0.1:8765

````

No system-wide installation is required.

---

# Running the demonstration

The demonstration can be run without any physical hardware.

Install dependencies:

```bash
pip install -r requirements.txt
````

Run:

```bash
python3 -m hwapp.example_scripts.demo_test
```

The demonstration performs a simulated multi-DUT test sequence using mock
hardware drivers and generates test result files.

Example output:

```
runs/demo_run_001/

run_demo_run_001_DUT_DUT-0001.csv
run_demo_run_001_DUT_DUT-0002.csv
run_demo_run_001_DUT_unassigned.csv
```

The logged data uses a consistent format:

```
timestamp,
device_id,
position,
channel,
value,
unit,
event_type
```

Where `event_type` can represent:

* Measurement results.
* Commanded states.
* Log messages.
* Test assertions.

---

# Adding new hardware

## SCPI instruments

Many SCPI instruments can be added without writing new Python code.

Create a command map:

```
scpi_command_map.example.json
```

Define:

* VISA resource.
* SCPI commands.
* Instrument functions.

Then add the device:

```python
runner.add_device(
    "scpi",
    "my_instrument",
    command_map_path="my_instrument.json"
)
```

---

## Custom hardware drivers

For non-SCPI equipment:

1. Create a new driver under:

```
hwapp/drivers/
```

2. Subclass:

```
Driver
```

3. Implement:

* connect()
* close()
* capabilities()
* write()
* read()
* query()

4. Register the driver:

```python
@register_driver("your_type_name")
```

---

# Roadmap

Future development areas include:

* Additional instrument drivers.
* Improved test report generation.
* Automated PDF reporting.
* Test limits and specification management.
* Improved result database storage.
* Test sequence version control.
* Operator workflows.
* Integration with manufacturing test environments.

The long-term goal is to create a flexible engineering test platform that can
grow from R&D validation into more structured automated test applications.

---

# Author

**Philip McGaw MIET**

Lead EMC Test Engineer specialising in:

* Automotive battery testing.
* EMC testing.
* SCPI automation.
* Laboratory test systems.
* Embedded electronics.

## Contact

Website:
https://philipmcgaw.com

GitHub:
https://github.com/PhilipMcGaw

LinkedIn:
https://linkedin.com/in/philipmcgaw

Email:
[philip@mcgaw.eu](mailto:philip@mcgaw.eu)

Questions, collaboration enquiries, and feature suggestions are welcome.

---

# Commercial Licensing

Test in a Box is available for non-commercial use under the
**PolyForm Noncommercial License 1.0.0**.

If you would like to use Test in a Box commercially, please contact the
copyright holder to discuss licensing options.

---

# License

This project ("Test in a Box") is licensed under the:

**PolyForm Noncommercial License 1.0.0**

Full license text:

https://polyformproject.org/licenses/noncommercial/1.0.0