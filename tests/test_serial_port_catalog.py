"""Tests for platform-neutral serial-port configuration metadata."""

import unittest

from tiab.drivers.catalog import DEVICE_CATALOG


class SerialPortCatalogTests(unittest.TestCase):
    def test_serial_port_fields_are_platform_neutral(self):
        serial_fields = [
            field
            for device in DEVICE_CATALOG.values()
            for field in device.get("fields", [])
            if field.get("type") == "serial_port"
        ]

        self.assertTrue(serial_fields)

        for field in serial_fields:
            self.assertEqual(field["label"], "Serial Port")
            self.assertEqual(field["default"], "")


if __name__ == "__main__":
    unittest.main()
