# Custom finite-strain modelling of a pH-sensitive hydrogel sensor

## Project at a glance

| | |
|---|---|
| Role | Individual graduate research; model implemented independently; first author of a submitted conference manuscript |
| Tools | COMSOL Multiphysics, weak-form PDEs, nonlinear solid mechanics |
| Physics | Ion transport, electric potential, osmotic swelling, hyperelastic large deformation |
| Validation | Literature benchmark only; no experimental validation |
| Public source | [Sanitized equation manifest](code/HydrogelModelDefinition.java) and [model audit](MODEL_AUDIT.md) |

## Engineering question

How does a pH-sensitive polyelectrolyte hydrogel respond over time when its surrounding solution changes, and how do external tensile or compressive loads affect its deformation and electrical response?

I treated the hydrogel as a finite-strain hyperelastic solid immersed in an ionic solution. Instead of relying only on preconfigured interfaces, I implemented the electrochemical fields with custom weak-form equations and coupled them to user-defined constitutive and stress expressions.

## What I implemented

- Constructed the deformation gradient, right Cauchy-Green tensor, tensor inverse, invariants, and energy derivatives used by the constitutive law.
- Formed second Piola-Kirchhoff and Cauchy mechanical stresses for a user-defined hyperelastic network.
- Added Flory-Huggins mixing and ionic osmotic terms to represent swelling stress.
- Implemented three transient Nernst-Planck weak forms for hydrogen, positive-ion, and negative-ion transport.
- Coupled mobile and fixed charge to a weak-form Poisson equation, electric displacement, electrical stress, and boundary traction.
- Added pH-dependent fixed-charge dissociation and an initial free-swelling volume ratio.

The public [Java manifest](code/HydrogelModelDefinition.java) presents this architecture in a compact, solver-independent form. It excludes the private `.mph` model, raw COMSOL history, local paths, and solution data.

## Wider graduate-study configuration

The archived project report documents the broader investigation represented by the figures below:

- Initial stationary equilibrium in a pH 4 solution.
- Transient transfer to solutions at pH 5, 6, 7, and 8.
- Positive and negative bath-ion concentration of 150 mM.
- An 800-second transient window.
- Compression from 0 to 4 kPa.
- Tension from 0 to 20 kPa at pH 8.

The sanitized source was extracted from one later 10 mm implementation snapshot with different stored study settings. It demonstrates the equation structure and is not presented as the exact reproduction file for every plotted result. The settings and remaining verification gates are recorded in the [model audit](MODEL_AUDIT.md).

## Selected results

The wider study predicted greater swelling and a larger gel-solution electric-potential difference as pH increased.

<img src="../../assets/hydrogel/electric-potential-by-ph.png" alt="Electric-potential profiles across the hydrogel at pH 5 to 8" width="760">

The transient vertical-displacement response approached a plateau over the reported 800-second window. The separation between pH 5 and the higher-pH cases was larger than the separation among pH 6-8.

<img src="../../assets/hydrogel/transient-displacement-by-ph.png" alt="Transient vertical displacement for pH 5 to 8" width="760">

The report recorded the following volume ratios:

- 2.60 after equilibrium at pH 4.
- 2.83 after equilibrium at pH 8.
- 2.84 at pH 8 with 20 kPa tensile loading.

For this parameter set, the tensile-load result suggested that the chemical swelling response dominated the small change in total volume caused by the applied load.

<img src="../../assets/hydrogel/positive-ion-concentration.png" alt="Positive-ion concentration contour in the hydrogel model" width="700">

## Validation and limitations

The computational trends were benchmarked against published hydrogel theories and numerical studies. This was not an experimental validation, and I do not claim physical hydrogel synthesis or laboratory sensor testing.

The model was sensitive to constitutive parameters and nonlinear convergence. A source audit also identified coordinate-frame consistency, electrostatic equation scaling, parameter-sweep synchronization, and mesh/time-step convergence as explicit review gates before releasing a rerunnable model. These findings are retained publicly in the [audit record](MODEL_AUDIT.md) rather than hidden behind stronger claims.

## Research output

A first-author Persian-language manuscript based on this model was submitted to an IMAT conference. Submission is confirmed; acceptance and publication are not claimed until documentary evidence is found.

## Literature used for benchmarking

1. Marcombe et al., "A theory of constrained swelling of a pH-sensitive hydrogel," *Soft Matter* 6 (2010), [doi:10.1039/B917211D](https://doi.org/10.1039/B917211D).
2. Liu et al., "Multiphysics modeling of responsive deformation of dual magnetic-pH-sensitive hydrogel," *International Journal of Solids and Structures* 190 (2020), [doi:10.1016/j.ijsolstr.2019.11.002](https://doi.org/10.1016/j.ijsolstr.2019.11.002).
3. Liu et al., "Transient modeling of magneto-chemo-electro-mechanical behavior of magnetic polyelectrolyte hydrogel," *Mechanics of Materials* 155 (2021), [doi:10.1016/j.mechmat.2021.103783](https://doi.org/10.1016/j.mechmat.2021.103783).
4. Narayan and Anand, "A coupled electro-chemo-mechanical theory for polyelectrolyte gels," *Journal of the Mechanics and Physics of Solids* 159 (2022), [doi:10.1016/j.jmps.2021.104734](https://doi.org/10.1016/j.jmps.2021.104734).

[Back to portfolio](../../README.md)
