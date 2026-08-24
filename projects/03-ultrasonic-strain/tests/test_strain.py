from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path


ANALYSIS_DIR = Path(__file__).resolve().parents[1] / "analysis"
sys.path.insert(0, str(ANALYSIS_DIR))

from strain import calculate_strain  # noqa: E402


class CalculateStrainTests(unittest.TestCase):
    def test_undeformed_specimen_has_zero_strain(self) -> None:
        result = calculate_strain(100.0, 100.0)
        self.assertEqual(result.stretch_ratio, 1.0)
        self.assertEqual(result.engineering_strain, 0.0)
        self.assertEqual(result.green_lagrange_strain, 0.0)

    def test_ten_percent_extension(self) -> None:
        result = calculate_strain(100.0, 110.0)
        self.assertAlmostEqual(result.stretch_ratio, 1.1)
        self.assertAlmostEqual(result.engineering_strain, 0.1)
        self.assertAlmostEqual(result.green_lagrange_strain, 0.105)

    def test_ten_percent_compression(self) -> None:
        result = calculate_strain(100.0, 90.0)
        self.assertAlmostEqual(result.engineering_strain, -0.1)
        self.assertAlmostEqual(result.green_lagrange_strain, -0.095)

    def test_rejects_nonpositive_or_nonfinite_lengths(self) -> None:
        invalid_cases = [
            (0.0, 100.0),
            (-1.0, 100.0),
            (100.0, 0.0),
            (math.inf, 100.0),
            (100.0, math.nan),
        ]
        for reference, current in invalid_cases:
            with self.subTest(reference=reference, current=current):
                with self.assertRaises(ValueError):
                    calculate_strain(reference, current)


if __name__ == "__main__":
    unittest.main()

