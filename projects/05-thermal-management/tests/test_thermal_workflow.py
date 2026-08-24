from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from thermal_workflow import (  # noqa: E402
    analyze_mesh_convergence,
    fan_pressure,
    run_study,
    solve_operating_point,
    synthetic_mesh_levels,
    system_pressure,
)


class ThermalWorkflowTests(unittest.TestCase):
    def test_operating_point_balances_fan_and_system_curves(self) -> None:
        point = solve_operating_point(1.6)

        self.assertAlmostEqual(
            fan_pressure(point.flow_normalized),
            system_pressure(point.flow_normalized, 1.6),
            places=10,
        )
        self.assertLessEqual(point.balance_residual, 1.0e-9)

    def test_higher_restriction_reduces_flow_and_increases_temperature_rise(self) -> None:
        lower_restriction = solve_operating_point(0.35)
        higher_restriction = solve_operating_point(3.2)

        self.assertGreater(
            lower_restriction.flow_normalized,
            higher_restriction.flow_normalized,
        )
        self.assertLess(
            lower_restriction.temperature_rise_normalized,
            higher_restriction.temperature_rise_normalized,
        )

    def test_mesh_analysis_recovers_known_second_order_sequence(self) -> None:
        result = analyze_mesh_convergence(synthetic_mesh_levels())

        self.assertAlmostEqual(2.0, result["observed_order"], places=10)
        self.assertAlmostEqual(
            0.82,
            result["richardson_extrapolated_value"],
            places=10,
        )
        self.assertLess(result["fine_grid_gci_percent"], 1.0)

    def test_invalid_restriction_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            solve_operating_point(0.0)

    def test_end_to_end_outputs_are_explicitly_synthetic(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            summary = run_study(root / "data", root / "assets")

            self.assertTrue(all(summary["checks"].values()))
            self.assertIn("synthetic", summary["dataset"].casefold())

            summary_path = root / "data" / "summary.synthetic.json"
            self.assertEqual(
                summary,
                json.loads(summary_path.read_text(encoding="utf-8")),
            )

            with (root / "data" / "restriction_sweep.synthetic.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(6, len(rows))
            self.assertTrue(
                all("synthetic" in row["dataset_notice"].casefold() for row in rows)
            )

            for filename in ("fan-system-curves.svg", "restriction-sweep.svg"):
                svg = (root / "assets" / filename).read_text(encoding="utf-8")
                self.assertIn("Synthetic dimensionless demonstration", svg)
                self.assertNotIn("C:\\", svg)


if __name__ == "__main__":
    unittest.main()
