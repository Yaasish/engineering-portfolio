"""Finite-strain calculations for the ultrasonic tensile-test prototype."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class StrainResult:
    reference_length: float
    current_length: float
    stretch_ratio: float
    engineering_strain: float
    green_lagrange_strain: float


def _positive_finite(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive finite number")
    return value


def calculate_strain(reference_length: float, current_length: float) -> StrainResult:
    """Calculate one-dimensional engineering and Green-Lagrange strain.

    Lengths may use any consistent unit. Green-Lagrange strain is
    E = 0.5 * (lambda**2 - 1), where lambda = L / L0.
    """

    reference = _positive_finite(reference_length, "reference_length")
    current = _positive_finite(current_length, "current_length")
    stretch = current / reference

    return StrainResult(
        reference_length=reference,
        current_length=current,
        stretch_ratio=stretch,
        engineering_strain=stretch - 1.0,
        green_lagrange_strain=0.5 * (stretch * stretch - 1.0),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate finite strain from ultrasonic length readings."
    )
    parser.add_argument("reference_length", type=float, help="Initial specimen length")
    parser.add_argument("current_length", type=float, help="Measured current length")
    parser.add_argument(
        "--unit",
        default="mm",
        help="Display unit shared by both lengths (default: mm)",
    )
    args = parser.parse_args()

    result = calculate_strain(args.reference_length, args.current_length)
    print(f"reference_length={result.reference_length:.6g} {args.unit}")
    print(f"current_length={result.current_length:.6g} {args.unit}")
    print(f"stretch_ratio={result.stretch_ratio:.8f}")
    print(f"engineering_strain={result.engineering_strain:.8f}")
    print(f"green_lagrange_strain={result.green_lagrange_strain:.8f}")


if __name__ == "__main__":
    main()

