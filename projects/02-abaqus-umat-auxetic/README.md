# Hyperelastic ABS UMAT with a collaborative auxetic application

## Project at a glance

| | |
|---|---|
| Role | Individual UMAT implementation; auxetic application completed in a two-person university project |
| Tools | Abaqus/Standard 2022, Fortran UMAT, nonlinear finite elements |
| Material model | Second-order polynomial hyperelastic strain-energy function |
| Verification | Published tensile data and Abaqus native hyperelastic model |
| Collaborative application | Auxetic structure; shared geometry, design parameters, and results withheld |

## Engineering objective

The work had two connected goals with different attribution boundaries:

1. Implement a finite-deformation hyperelastic material law for ABS as an Abaqus UMAT.
2. Apply the verified material model to an auxetic structure in a two-person university project.

## Constitutive implementation

The UMAT evaluates the right Cauchy-Green tensor, its invariants, a second-order polynomial strain-energy function, second Piola-Kirchhoff stress, Cauchy stress, and the material Jacobian supplied to Abaqus.

Near-incompressibility was handled using a penalty parameter. The project explicitly explored the numerical trade-off: too small a penalty allowed volume drift, while too large a value harmed convergence.

The public file is a sanitized coursework implementation:

- [View the Fortran UMAT](code/umat_abs_sanitized.for)
- Solver databases, journals, and institution-specific input files are omitted.
- An externally credited general matrix-inversion helper from the coursework copy was removed and replaced with a local analytical 3x3 inverse.
- The sanitized file has not been recompiled here because an Abaqus-compatible Fortran toolchain is unavailable in this environment.

## Verification

The tensile model was compared with published ABS data and with Abaqus' native polynomial hyperelastic implementation. The project report found close agreement among the experimental curve, the native model, and the UMAT response.

| Sanitized UMAT result | Abaqus native model |
|---|---|
| <img src="../../assets/umat-auxetic/umat-stress.png" alt="Stress contour from the ABS UMAT model" width="440"> | <img src="../../assets/umat-auxetic/abaqus-native-stress.png" alt="Stress contour from Abaqus native hyperelastic model" width="440"> |

The element-volume study was used to select a penalty magnitude that preserved near-incompressibility without causing solver failure.

<img src="../../assets/umat-auxetic/volume-stability.png" alt="Element-volume histories for different incompressibility penalties" width="760">

## Collaborative auxetic application

The verified material model was later used in a two-person university project involving an auxetic structure. Because this was shared work, the geometry, design parameters, meshes, and simulation results are not published here. No claim of sole authorship is made for that application.

## Related work

Separate coursework implemented Total and Updated Lagrangian user elements for nonlinear cantilever bending. That study compared both formulations and identified a small discrepancy caused by using the same elastic-property tensor representation in the current and reference configurations.

## Material-data reference

The ABS parameters and comparison data were drawn from S. Kouchakzadeh and K. Narooei, "Simulation of piezoresistance and deformation behavior of a flexible 3D printed sensor considering the nonlinear mechanical behavior of materials," *Sensors and Actuators A: Physical* 332 (2021), [doi:10.1016/j.sna.2021.113214](https://doi.org/10.1016/j.sna.2021.113214).

[Back to portfolio](../../README.md)
