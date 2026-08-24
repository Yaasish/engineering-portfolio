# Arduino ultrasonic strain-measurement prototype

## Project at a glance

| | |
|---|---|
| Role | Individual university prototype and report |
| Hardware | Arduino Uno R3 and HY-SRF05 ultrasonic sensor |
| Specimen | Latex sample under staged tensile loading |
| Loading | Four 160 g increments, separated by approximately 10 seconds |
| Output | Specimen length and Green-Lagrange strain |

## Objective

The goal was to create a low-cost educational setup for observing finite deformation. An ultrasonic sensor measured the changing position of the loaded end of a latex specimen. The measured length was then converted to Green-Lagrange strain.

<img src="../../assets/ultrasonic-strain/system-architecture.svg" alt="Ultrasonic strain measurement workflow" width="800">

For reference length \(L_0\) and current length \(L\):

\[
\lambda = \frac{L}{L_0}, \qquad E = \frac{1}{2}(\lambda^2 - 1)
\]

The finite-strain measure was selected because the specimen experienced visible geometric change during loading.

## Public reconstruction

The public version separates acquisition from analysis:

- [Arduino firmware](firmware/ultrasonic_strain_monitor.ino) emits timestamped distance measurements in millimetres.
- [Python analysis](analysis/strain.py) calculates stretch ratio, engineering strain, and Green-Lagrange strain.
- [Unit tests](tests/test_strain.py) verify the strain calculation for undeformed, tensile, and compressive cases.

The original prototype code and photographs are not published directly. The firmware was reconstructed for clarity, uses a timeout, reports explicit units, and applies a median filter to five ultrasonic readings.

## Experimental limitations

This was an educational prototype rather than a calibrated metrology system. The main uncertainty sources were:

- Ultrasonic beam alignment and reflections from nearby surfaces.
- Fixture motion and compliance.
- Manual load placement and timing.
- No simultaneous calibrated force measurement.
- Sensor resolution relative to small length changes.

A stronger next iteration would combine the distance sensor with a calibrated load cell, log both channels at a fixed sample rate, and quantify repeatability over multiple loading cycles.

## Run the analysis tests

```bash
python -m unittest discover -s tests -v
```

[Back to portfolio](../../README.md)

