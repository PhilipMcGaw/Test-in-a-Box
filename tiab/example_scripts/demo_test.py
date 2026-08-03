"""
Hand-written stand-in for what a Blockly-generated script will look like.
Run with:  python -m tiab.example_scripts.demo_test

Scenario: two DUTs multiplexed in one run.
  - psu1 powers DUT-0001, psu2 powers DUT-0002
  - relay1 (relay channel 1) switches a load on DUT-0001, relay2 on DUT-0002
Loop steps through a voltage sweep on both DUTs, logging + asserting each step.
"""

from tiab.run.mapping import DutMapping
from tiab.run.runner import TestRunner

# ensure mock drivers get registered
import tiab.drivers.mock  # noqa: F401


def main():
    mapping = DutMapping()
    mapping.assign("psu1", "voltage", "DUT-0001")
    mapping.assign("relay1", "relay1", "DUT-0001")
    mapping.assign("psu2", "voltage", "DUT-0002")
    mapping.assign("relay1", "relay2", "DUT-0002")

    with TestRunner(run_id="demo_run_001", mapping=mapping, output_dir="./runs") as runner:
        runner.add_device("mock_psu", "psu1")
        runner.add_device("mock_psu", "psu2")
        runner.add_device("mock_relay", "relay1", num_channels=8)
        runner.lock_mapping()

        for dut_psu, dut_relay_ch in [("psu1", "relay1"), ("psu2", "relay2")]:
            runner.set("relay1", dut_relay_ch, True)
            runner.log(f"load switched on for {dut_psu}", device_id="relay1", position_id=dut_relay_ch)

            for voltage in [5.0, 8.0, 11.0]:
                runner.set(dut_psu, "output", True)
                runner.set(dut_psu, "voltage", voltage)
                runner.wait(0.05)
                measured = runner.get(dut_psu, "voltage")
                runner.assert_that(
                    abs(measured - voltage) < 0.1,
                    f"{dut_psu} voltage within tolerance at {voltage}V (measured {measured:.3f}V)",
                    device_id=dut_psu, position_id="voltage",
                )

            runner.set(dut_psu, "output", False)
            runner.set("relay1", dut_relay_ch, False)


if __name__ == "__main__":
    main()
