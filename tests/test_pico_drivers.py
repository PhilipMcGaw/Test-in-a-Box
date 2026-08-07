"""Hardware-independent tests for Pico driver capability models."""

import unittest

from tiab.drivers.pico_adc import PicoAdcDriver, decode_digital_inputs
from tiab.drivers.pico_tc08 import PicoTC08Driver


class PicoAdcCapabilityTests(unittest.TestCase):
    def test_adc20_exposes_eight_analogue_positions(self):
        positions = PicoAdcDriver("adc20", model="adc20").capabilities().positions

        self.assertEqual([position.id for position in positions], [
            "ch1", "ch2", "ch3", "ch4",
            "ch5", "ch6", "ch7", "ch8",
        ])

    def test_adc24_exposes_sixteen_analogue_and_four_digital_positions(self):
        positions = PicoAdcDriver(
            "adc24",
            model="adc24",
            num_channels=16,
        ).capabilities().positions

        self.assertEqual(len(positions), 20)
        self.assertEqual(
            [position.id for position in positions[-4:]],
            ["d1", "d2", "d3", "d4"],
        )

    def test_digital_mask_is_decoded_low_bit_first(self):
        self.assertEqual(
            decode_digital_inputs(0b0101),
            {"d1": True, "d2": False, "d3": True, "d4": False},
        )


class PicoTc08CapabilityTests(unittest.TestCase):
    def test_tc08_exposes_internal_temperature_before_external_channels(self):
        positions = PicoTC08Driver("tc08").capabilities().positions

        self.assertEqual(positions[0].id, "internal_temperature")
        self.assertEqual(
            [position.id for position in positions[1:]],
            ["ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "ch7", "ch8"],
        )


if __name__ == "__main__":
    unittest.main()
