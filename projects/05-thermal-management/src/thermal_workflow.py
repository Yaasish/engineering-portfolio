"""Synthetic forced-air thermal-management workflow.

This is an independent portfolio reconstruction. It contains no employer
geometry, operating values, model files, experimental data, or product details.
The equations and dimensionless data are deliberately generic and synthetic.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


SYNTHETIC_NOTICE = (
    "Independent synthetic portfolio reconstruction; no employer data or results"
)


@dataclass(frozen=True)
class OperatingPoint:
    restriction_coefficient: float
    flow_normalized: float
    pressure_normalized: float
    temperature_rise_normalized: float
    balance_residual: float


@dataclass(frozen=True)
class MeshLevel:
    label: str
    cell_count: int
    relative_cell_size: float
    monitored_temperature_normalized: float


@dataclass(frozen=True)
class ChartSeries:
    label: str
    color: str
    points: tuple[tuple[float, float], ...]
    draw_line: bool = True
    draw_markers: bool = False


def fan_pressure(flow_normalized: float) -> float:
    """Return a fictional dimensionless fan curve over 0 <= flow <= 1."""
    if not 0.0 <= flow_normalized <= 1.0:
        raise ValueError("normalized flow must be between 0 and 1")
    return max(
        0.0,
        1.0 - 0.20 * flow_normalized - 0.80 * flow_normalized**2,
    )


def system_pressure(flow_normalized: float, restriction_coefficient: float) -> float:
    """Return a generic quadratic system-pressure curve."""
    if not 0.0 <= flow_normalized <= 1.0:
        raise ValueError("normalized flow must be between 0 and 1")
    if restriction_coefficient <= 0.0:
        raise ValueError("restriction coefficient must be positive")
    return restriction_coefficient * flow_normalized**2


def synthetic_temperature_rise(flow_normalized: float) -> float:
    """Return a disclosed synthetic response, not a CFD prediction."""
    if not 0.0 <= flow_normalized <= 1.0:
        raise ValueError("normalized flow must be between 0 and 1")
    return 0.22 + 0.78 / (1.0 + 2.60 * flow_normalized)


def solve_operating_point(
    restriction_coefficient: float,
    tolerance: float = 1.0e-12,
    max_iterations: int = 200,
) -> OperatingPoint:
    """Solve the fan/system intersection with a bounded bisection method."""
    if restriction_coefficient <= 0.0:
        raise ValueError("restriction coefficient must be positive")
    if tolerance <= 0.0:
        raise ValueError("tolerance must be positive")

    def balance(flow: float) -> float:
        return fan_pressure(flow) - system_pressure(flow, restriction_coefficient)

    lower, upper = 0.0, 1.0
    lower_balance, upper_balance = balance(lower), balance(upper)
    if lower_balance * upper_balance > 0.0:
        raise RuntimeError("fan and system curves do not bracket an operating point")

    midpoint = 0.5
    for _ in range(max_iterations):
        midpoint = (lower + upper) / 2.0
        midpoint_balance = balance(midpoint)
        if abs(midpoint_balance) <= tolerance or (upper - lower) <= tolerance:
            break
        if lower_balance * midpoint_balance <= 0.0:
            upper = midpoint
        else:
            lower = midpoint
            lower_balance = midpoint_balance
    else:
        raise RuntimeError("operating-point solver did not converge")

    pressure = system_pressure(midpoint, restriction_coefficient)
    return OperatingPoint(
        restriction_coefficient=restriction_coefficient,
        flow_normalized=midpoint,
        pressure_normalized=pressure,
        temperature_rise_normalized=synthetic_temperature_rise(midpoint),
        balance_residual=abs(balance(midpoint)),
    )


def synthetic_mesh_levels() -> tuple[MeshLevel, MeshLevel, MeshLevel]:
    """Create a known second-order sequence for convergence-method QA."""
    exact_value = 0.82
    error_coefficient = 0.008
    specifications = (
        ("Coarse", 12_500, 2.0),
        ("Medium", 50_000, 1.0),
        ("Fine", 200_000, 0.5),
    )
    return tuple(
        MeshLevel(
            label=label,
            cell_count=cell_count,
            relative_cell_size=relative_size,
            monitored_temperature_normalized=(
                exact_value + error_coefficient * relative_size**2
            ),
        )
        for label, cell_count, relative_size in specifications
    )


def analyze_mesh_convergence(levels: Sequence[MeshLevel]) -> dict[str, float]:
    """Estimate observed order, Richardson limit, and fine-grid GCI."""
    if len(levels) != 3:
        raise ValueError("exactly three ordered mesh levels are required")
    coarse, medium, fine = levels
    if not (
        coarse.relative_cell_size
        > medium.relative_cell_size
        > fine.relative_cell_size
    ):
        raise ValueError("mesh levels must be ordered from coarse to fine")

    refinement_ratio_1 = coarse.relative_cell_size / medium.relative_cell_size
    refinement_ratio_2 = medium.relative_cell_size / fine.relative_cell_size
    if not math.isclose(refinement_ratio_1, refinement_ratio_2, rel_tol=1.0e-12):
        raise ValueError("a constant refinement ratio is required")

    coarse_difference = (
        coarse.monitored_temperature_normalized
        - medium.monitored_temperature_normalized
    )
    fine_difference = (
        medium.monitored_temperature_normalized
        - fine.monitored_temperature_normalized
    )
    if coarse_difference == 0.0 or fine_difference == 0.0:
        raise ValueError("mesh values must differ to estimate convergence")

    refinement_ratio = refinement_ratio_1
    observed_order = math.log(abs(coarse_difference / fine_difference)) / math.log(
        refinement_ratio
    )
    extrapolated_value = fine.monitored_temperature_normalized + (
        fine.monitored_temperature_normalized
        - medium.monitored_temperature_normalized
    ) / (refinement_ratio**observed_order - 1.0)
    fine_grid_gci_percent = (
        1.25
        * abs(
            (fine.monitored_temperature_normalized - extrapolated_value)
            / fine.monitored_temperature_normalized
        )
        * 100.0
    )
    fine_to_medium_change_percent = (
        abs(
            (fine.monitored_temperature_normalized
            - medium.monitored_temperature_normalized)
            / fine.monitored_temperature_normalized
        )
        * 100.0
    )
    return {
        "refinement_ratio": refinement_ratio,
        "observed_order": observed_order,
        "richardson_extrapolated_value": extrapolated_value,
        "fine_grid_gci_percent": fine_grid_gci_percent,
        "fine_to_medium_change_percent": fine_to_medium_change_percent,
    }


def _write_csv(path: Path, rows: Sequence[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("cannot write an empty synthetic dataset")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _line_chart(
    path: Path,
    *,
    title: str,
    x_label: str,
    y_label: str,
    series: Sequence[ChartSeries],
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    x_ticks: Sequence[float],
    y_ticks: Sequence[float],
) -> None:
    width, height = 900, 520
    left, right, top, bottom = 95, 35, 115, 75
    plot_width = width - left - right
    plot_height = height - top - bottom
    x_min, x_max = x_range
    y_min, y_max = y_range

    def x_position(value: float) -> float:
        return left + (value - x_min) / (x_max - x_min) * plot_width

    def y_position(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * plot_height

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{html.escape(title)}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{left}" y="36" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#172033">{html.escape(title)}</text>',
        f'<text x="{left}" y="62" font-family="Arial, sans-serif" font-size="14" fill="#5b6475">Synthetic dimensionless demonstration — no employer data or results</text>',
    ]

    for value in x_ticks:
        x = x_position(value)
        parts.extend(
            [
                f'<line x1="{x:.2f}" y1="{top}" x2="{x:.2f}" y2="{top + plot_height}" stroke="#e3e7ee" stroke-width="1"/>',
                f'<text x="{x:.2f}" y="{top + plot_height + 25}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#4a5365">{value:g}</text>',
            ]
        )
    for value in y_ticks:
        y = y_position(value)
        parts.extend(
            [
                f'<line x1="{left}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#e3e7ee" stroke-width="1"/>',
                f'<text x="{left - 13}" y="{y + 4:.2f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#4a5365">{value:g}</text>',
            ]
        )

    parts.extend(
        [
            f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#263248" stroke-width="1.5"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#263248" stroke-width="1.5"/>',
        ]
    )

    legend_x = left
    for item in series:
        if item.draw_line:
            parts.append(
                f'<line x1="{legend_x}" y1="88" x2="{legend_x + 24}" y2="88" stroke="{item.color}" stroke-width="3"/>'
            )
        if item.draw_markers:
            parts.append(
                f'<circle cx="{legend_x + 12}" cy="88" r="4.5" fill="{item.color}" stroke="#ffffff" stroke-width="1.5"/>'
            )
        parts.append(
            f'<text x="{legend_x + 31}" y="92" font-family="Arial, sans-serif" font-size="12" fill="#263248">{html.escape(item.label)}</text>'
        )
        legend_x += 48 + 7 * len(item.label)

        coordinates = " ".join(
            f"{x_position(x):.2f},{y_position(y):.2f}" for x, y in item.points
        )
        if item.draw_line:
            parts.append(
                f'<polyline points="{coordinates}" fill="none" stroke="{item.color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>'
            )
        if item.draw_markers:
            parts.extend(
                f'<circle cx="{x_position(x):.2f}" cy="{y_position(y):.2f}" r="5" fill="{item.color}" stroke="#ffffff" stroke-width="1.5"/>'
                for x, y in item.points
            )

    parts.extend(
        [
            f'<text x="{left + plot_width / 2:.2f}" y="{height - 18}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#263248">{html.escape(x_label)}</text>',
            f'<text x="22" y="{top + plot_height / 2:.2f}" text-anchor="middle" transform="rotate(-90 22 {top + plot_height / 2:.2f})" font-family="Arial, sans-serif" font-size="14" fill="#263248">{html.escape(y_label)}</text>',
            "</svg>",
        ]
    )
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def _write_figures(asset_dir: Path, points: Sequence[OperatingPoint]) -> None:
    sample_flows = tuple(index / 40.0 for index in range(41))
    low_restriction = points[0]
    high_restriction = points[-1]
    _line_chart(
        asset_dir / "fan-system-curves.svg",
        title="Fan and system operating-point method",
        x_label="Normalized airflow",
        y_label="Normalized pressure",
        series=(
            ChartSeries(
                "Synthetic fan curve",
                "#2563eb",
                tuple((flow, fan_pressure(flow)) for flow in sample_flows),
            ),
            ChartSeries(
                "Lower restriction",
                "#16a34a",
                tuple(
                    (
                        flow,
                        system_pressure(flow, low_restriction.restriction_coefficient),
                    )
                    for flow in sample_flows
                ),
            ),
            ChartSeries(
                "Higher restriction",
                "#dc2626",
                tuple(
                    (
                        flow,
                        system_pressure(flow, high_restriction.restriction_coefficient),
                    )
                    for flow in sample_flows
                    if system_pressure(
                        flow, high_restriction.restriction_coefficient
                    )
                    <= 1.0
                ),
            ),
            ChartSeries(
                "Solved intersections",
                "#7c3aed",
                (
                    (
                        low_restriction.flow_normalized,
                        low_restriction.pressure_normalized,
                    ),
                    (
                        high_restriction.flow_normalized,
                        high_restriction.pressure_normalized,
                    ),
                ),
                draw_line=False,
                draw_markers=True,
            ),
        ),
        x_range=(0.0, 1.0),
        y_range=(0.0, 1.0),
        x_ticks=(0.0, 0.25, 0.5, 0.75, 1.0),
        y_ticks=(0.0, 0.25, 0.5, 0.75, 1.0),
    )

    _line_chart(
        asset_dir / "restriction-sweep.svg",
        title="Restriction sweep and synthetic thermal response",
        x_label="System restriction coefficient",
        y_label="Normalized response",
        series=(
            ChartSeries(
                "Operating airflow",
                "#2563eb",
                tuple(
                    (point.restriction_coefficient, point.flow_normalized)
                    for point in points
                ),
                draw_markers=True,
            ),
            ChartSeries(
                "Temperature rise",
                "#dc2626",
                tuple(
                    (
                        point.restriction_coefficient,
                        point.temperature_rise_normalized,
                    )
                    for point in points
                ),
                draw_markers=True,
            ),
        ),
        x_range=(0.0, 3.5),
        y_range=(0.4, 0.9),
        x_ticks=(0.0, 0.7, 1.4, 2.1, 2.8, 3.5),
        y_ticks=(0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
    )


def run_study(output_dir: Path | str, asset_dir: Path | str) -> dict[str, object]:
    """Generate deterministic synthetic data, QA evidence, and SVG figures."""
    output = Path(output_dir)
    assets = Path(asset_dir)
    output.mkdir(parents=True, exist_ok=True)
    assets.mkdir(parents=True, exist_ok=True)

    restrictions = (0.35, 0.65, 1.0, 1.6, 2.4, 3.2)
    operating_points = tuple(solve_operating_point(value) for value in restrictions)
    mesh_levels = synthetic_mesh_levels()
    convergence = analyze_mesh_convergence(mesh_levels)

    point_rows = [
        {
            "dataset_notice": SYNTHETIC_NOTICE,
            "restriction_coefficient": f"{point.restriction_coefficient:.6f}",
            "operating_flow_normalized": f"{point.flow_normalized:.8f}",
            "operating_pressure_normalized": f"{point.pressure_normalized:.8f}",
            "temperature_rise_normalized": (
                f"{point.temperature_rise_normalized:.8f}"
            ),
            "balance_residual": f"{point.balance_residual:.3e}",
        }
        for point in operating_points
    ]
    mesh_rows = [
        {
            "dataset_notice": SYNTHETIC_NOTICE,
            "grid": level.label,
            "cell_count": level.cell_count,
            "relative_cell_size": f"{level.relative_cell_size:.6f}",
            "monitored_temperature_normalized": (
                f"{level.monitored_temperature_normalized:.8f}"
            ),
        }
        for level in mesh_levels
    ]
    _write_csv(output / "restriction_sweep.synthetic.csv", point_rows)
    _write_csv(output / "mesh_convergence.synthetic.csv", mesh_rows)
    _write_figures(assets, operating_points)

    checks = {
        "fan_system_balance": all(
            point.balance_residual <= 1.0e-9 for point in operating_points
        ),
        "flow_decreases_with_restriction": all(
            left.flow_normalized > right.flow_normalized
            for left, right in zip(operating_points, operating_points[1:])
        ),
        "temperature_rise_increases_as_flow_falls": all(
            left.temperature_rise_normalized
            < right.temperature_rise_normalized
            for left, right in zip(operating_points, operating_points[1:])
        ),
        "known_second_order_mesh_sequence_recovered": math.isclose(
            convergence["observed_order"], 2.0, rel_tol=1.0e-10
        ),
        "fine_grid_gci_below_one_percent": (
            convergence["fine_grid_gci_percent"] < 1.0
        ),
    }
    summary: dict[str, object] = {
        "dataset": SYNTHETIC_NOTICE,
        "scope": (
            "Dimensionless workflow demonstration; not a CFD solve or an "
            "experimental-validation package"
        ),
        "equations": {
            "fan_pressure": "1 - 0.20 q - 0.80 q^2",
            "system_pressure": "K q^2",
            "synthetic_temperature_rise": "0.22 + 0.78 / (1 + 2.60 q)",
        },
        "restriction_sweep": [asdict(point) for point in operating_points],
        "mesh_convergence": {
            "levels": [asdict(level) for level in mesh_levels],
            **convergence,
        },
        "checks": checks,
    }
    (output / "summary.synthetic.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the synthetic thermal-management reconstruction."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--asset-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = run_study(args.output_dir, args.asset_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all(summary["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
