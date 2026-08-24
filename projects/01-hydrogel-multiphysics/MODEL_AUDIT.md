# Public model audit and sanitization record

## Purpose

This note documents how the public hydrogel source was prepared from a private COMSOL model export. The goal is to make the independently implemented equations inspectable without publishing a proprietary solver database, private working paths, thousands of model-history operations, or unverified solution data.

The public artifact is [HydrogelModelDefinition.java](code/HydrogelModelDefinition.java). It is a solver-independent equation manifest, not a runnable COMSOL model.

## What the source inspection confirmed

The archived model contains an independently assembled finite-strain electro-chemo-mechanical formulation:

1. The deformation gradient, right Cauchy-Green tensor, its inverse, and three invariants are exposed as model variables.
2. A user-defined hyperelastic law constructs second Piola-Kirchhoff stress from derivatives of the strain-energy function and pushes it forward to Cauchy stress.
3. Flory-Huggins mixing and ionic osmotic terms form an additional swelling stress.
4. Three weak-form Nernst-Planck equations represent hydrogen, positive-ion, and negative-ion transport.
5. A weak-form Poisson equation couples electric potential to mobile and fixed charge.
6. Electric displacement, Maxwell-type electrical stress, and boundary traction couple electrostatics back to mechanics.

The final archived stress expression combines mechanical, swelling, and electrical contributions. Magnetic terms explored earlier in the model history were removed from the final state.

## Audited snapshot

| Item | Value retained in the export |
|---|---|
| Geometry | 10 mm square |
| Mechanical assumption | 2D plane stress |
| Initial swelling stretch | 3.4 |
| Hyperelastic coefficient | 10 kPa |
| Temperature | 290 K |
| Bath salt concentration | 0.001 mol/L |
| Fixed-charge reference concentration | 500 mol/m^3 |
| Species diffusivities | 5e-7 m^2/s |
| Study time | 0-400 s, requested output every 10 s |
| Study pH list | 5 and 9; batch-node list requires synchronization |

This is one implementation snapshot. It is not presented as the exact input file that generated every figure in the wider graduate-study case study.

## Review gates before a reproducibility release

- **Coordinate frames:** the archived final history places the hydrogen-ion weak-form field in the spatial frame while the other ion fields and electric potential remain in the material frame. The transport terms should be re-derived in one declared frame and rerun.
- **Electrostatic scaling:** an isolated factor of `3e12` multiplies the electric-potential gradient term but not its charge source. It must be removed or supported by a documented nondimensionalization or regularization argument.
- **Parameter sweep:** the study node stores pH 5 and 9, while the batch node retains pH 5-9. The sweep definition must be normalized before another solve.
- **Convergence evidence:** the source ends at automatic mesh level 9 and clears solution data. A fresh mesh/time-step study and benchmark table are required before claiming numerical reproduction from this public artifact.

## Public and private boundaries

Published:

- Solver-independent parameters and equation structure.
- Selected figures from the documented graduate study.
- Literature references and explicit validation limitations.

Not published:

- COMSOL `.mph` files and the raw Java history export.
- Solver databases, cached solutions, and machine-specific paths.
- Full manuscripts, personal records, or third-party working files.
- Employer models, product information, or confidential work.

## Defensible project description

> Independently implemented a custom finite-strain electro-chemo-mechanical hydrogel model in COMSOL, coupling a user-defined hyperelastic network, Flory-Huggins and ionic swelling stresses, three-species Nernst-Planck transport, and Poisson electrostatics through weak-form PDEs; benchmarked computational behaviour against published literature.

The benchmark was literature-based. No experimental validation is claimed.
