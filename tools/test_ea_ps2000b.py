#!/usr/bin/env python3
"""
Read-first bench tester for an EA PS 2000 B (2020 TFT).

The default run performs identification and read-only checks only.

Use --control-test to perform a cautious write test. The control test:
1. records the existing voltage/current setpoints and output state;
2. acquires remote control;
3. confirms output OFF;
4. applies low setpoints supplied on the command line;
5. reads the values back;
6. keeps the output OFF;
7. restores the original setpoints;
8. leaves remote control.

No control test should be run with a DUT connected unless the operator has
confirmed the requested values are safe.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback

from tiab.drivers.serial.ea_ps2000b import EaPs2000bDriver


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM9")
    parser.add_argument(
        "--control-test",
        action="store_true",
        help="perform a cautious remote/setpoint test with output kept OFF",
    )
    parser.add_argument("--test-voltage", type=float, default=1.0)
    parser.add_argument("--test-current", type=float, default=0.1)
    args = parser.parse_args()

    driver = EaPs2000bDriver(
        device_id="ea_ps2000b_test",
        serial_port=args.port,
    )

    original_voltage = None
    original_current = None

    try:
        print(f"Connecting to {args.port}...")
        driver.connect()

        print("Identity:")
        print(json.dumps(driver.identify(), indent=2))

        print("\nRead-only checks:")
        print("Remote owner:", driver.get_remote_owner())
        print("Output:", driver.get_output())
        print("Voltage setpoint:", driver.get_voltage(), "V")
        print("Current setpoint:", driver.get_current(), "A")
        print("Actual values:", driver.get_actual_values())
        print("Nominal voltage:", driver.get_nominal_voltage(), "V")
        print("Nominal current:", driver.get_nominal_current(), "A")
        print("Nominal power:", driver.get_nominal_power(), "W")
        print("Error queue:", driver.get_all_errors())

        if not args.control_test:
            print("\nRead-only test completed.")
            return 0

        print("\nCONTROL TEST REQUESTED")
        print(
            f"Target setpoints: {args.test_voltage} V, "
            f"{args.test_current} A"
        )
        print("The output will remain OFF throughout the test.")

        original_voltage = driver.get_voltage()
        original_current = driver.get_current()

        driver.enter_remote()
        driver.set_output(False)
        driver.set_voltage(args.test_voltage)
        driver.set_current(args.test_current)

        print("Read-back voltage:", driver.get_voltage(), "V")
        print("Read-back current:", driver.get_current(), "A")
        print("Output state:", driver.get_output())
        print("Errors:", driver.get_all_errors())

        driver.set_output(False)
        driver.set_voltage(original_voltage)
        driver.set_current(original_current)
        driver.leave_remote()

        print("\nControl test completed and original setpoints restored.")
        return 0

    except Exception as exc:
        print(f"\nTEST FAILED: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

    finally:
        try:
            if driver.connected:
                driver.set_output(False)
                if original_voltage is not None:
                    driver.set_voltage(original_voltage)
                if original_current is not None:
                    driver.set_current(original_current)
        except Exception:
            traceback.print_exc()

        try:
            driver.close()
        except Exception:
            traceback.print_exc()


if __name__ == "__main__":
    raise SystemExit(main())
