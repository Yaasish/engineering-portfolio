package portfolio.hydrogel;

import java.util.List;
import java.util.Map;

/**
 * Public, solver-independent manifest of a COMSOL hydrogel model.
 *
 * <p>This file was curated from a private COMSOL Java export. It records the
 * model architecture, final parameter snapshot, and constitutive expressions
 * without publishing the .mph file, solver history, solution data, local file
 * paths, or generated COMSOL boilerplate. It is documentation, not a runnable
 * COMSOL model and not evidence that the archived results have been reproduced.
 */
public final class HydrogelModelDefinition {

    public record Definition(String name, String expression, String purpose) {}

    public static final Map<String, String> SNAPSHOT_PARAMETERS = Map.ofEntries(
        Map.entry("geometry", "10 mm x 10 mm square; 2D plane stress"),
        Map.entry("A1", "1.0e4 J/m^3"),
        Map.entry("solventVolume", "1.0e-28 m^3"),
        Map.entry("floryHugginsChi", "0.1"),
        Map.entry("acidSensitiveMonomerFraction", "0.05"),
        Map.entry("initialSwellingStretch", "3.4"),
        Map.entry("initialVolumeRatio", "initialSwellingStretch^3"),
        Map.entry("temperature", "290 K"),
        Map.entry("relativePermittivity", "80"),
        Map.entry("bathSaltConcentration", "0.001 mol/L"),
        Map.entry("pKa", "4.3"),
        Map.entry("polymerVolumeFraction", "1.0"),
        Map.entry("osmoticExcludedFraction", "0"),
        Map.entry("fixedChargeReference", "500 mol/m^3"),
        Map.entry("dissociationConstant", "0.01 mol/m^3"),
        Map.entry("diffusivityH", "5.0e-7 m^2/s"),
        Map.entry("diffusivityPositiveIon", "5.0e-7 m^2/s"),
        Map.entry("diffusivityNegativeIon", "5.0e-7 m^2/s"),
        Map.entry("studyTime", "0 to 400 s; requested output every 10 s"),
        Map.entry("studyPH", "5 and 9 in the study node; see review gates")
    );

    public static final List<Definition> KINEMATICS = List.of(
        new Definition("C", "transpose(F) * F", "Right Cauchy-Green tensor"),
        new Definition("C_inv", "inverse(C)", "Inverse right Cauchy-Green tensor"),
        new Definition("I1", "trace(C)", "First invariant"),
        new Definition("I2", "0.5 * (I1^2 - trace(C*C))", "Second invariant"),
        new Definition("I3", "det(C)", "Third invariant"),
        new Definition("J", "solid.J * J0", "Total volume ratio including initial swelling"),
        new Definition("J0", "initialSwellingStretch^3", "Initial free-swelling volume ratio")
    );

    public static final List<Definition> MECHANICS = List.of(
        new Definition("dW_dI1", "A1", "Network-energy derivative"),
        new Definition("dW_dI2", "0", "Network-energy derivative"),
        new Definition("dW_dI3", "-A1 / I3", "Network-energy derivative"),
        new Definition(
            "S_mechanical",
            "2 * sum(dW_dIi * dIi_dC)",
            "Second Piola-Kirchhoff stress from the invariant derivatives"
        ),
        new Definition(
            "sigma_mechanical",
            "(1/J) * F * S_mechanical * transpose(F)",
            "Push-forward to Cauchy stress"
        )
    );

    public static final List<Definition> CHEMISTRY_AND_SWELLING = List.of(
        new Definition(
            "c_H_bath",
            "10^(-pH) * 1000 mol/m^3",
            "Hydrogen-ion concentration imposed at the bath boundary"
        ),
        new Definition(
            "c_minus_bath",
            "c_H_bath + c_plus_bath",
            "Bath electroneutrality"
        ),
        new Definition(
            "c_fixed",
            "polymerFraction * c_fixed_reference * Kd * J / (Kd*J + c_H)",
            "pH-dependent fixed charge concentration"
        ),
        new Definition(
            "osmoticStress",
            "(kB*T/vs)*(ln(1-(1-Xi_p)/J)+(1-Xi_p)/J+chi*(1-Xi_p)^2/J^2)"
                + " - kB*NA*T*((c_H+c_plus+c_minus)-(c_H_bath+c_plus_bath+c_minus_bath))",
            "Flory-Huggins mixing contribution plus ionic osmotic contribution"
        ),
        new Definition(
            "S_swelling",
            "J * osmoticStress * C_inv",
            "Isotropic swelling contribution in the material description"
        )
    );

    public static final List<Definition> TRANSPORT_AND_ELECTROSTATICS = List.of(
        new Definition(
            "weakNernstPlanck(species)",
            "(D*C_inv*Grad_X(c) + D*z*q_e*c*C_inv*Grad_X(phi)/(kB*T))"
                + " . Grad_X(test(c)) + d(c)/dt*test(c)",
            "Weak diffusion, electromigration, and transient storage term"
        ),
        new Definition(
            "weakPoissonCore",
            "-(eps0*epsr*J*C_inv*Grad_X(phi)).Grad_X(test(phi))"
                + " + Faraday*(z_fixed*c_fixed+z_H*c_H+z_plus*c_plus+z_minus*c_minus)*test(phi)",
            "Material-frame electrostatic balance before any numerical scaling"
        ),
        new Definition(
            "D_electric",
            "eps0 * epsr * J * C_inv * E",
            "Pulled-back electric displacement"
        ),
        new Definition(
            "S_electric",
            "outer(D_electric,D_electric)/(eps0*epsr*J) - 0.5*(E.D_electric)*C_inv",
            "Electrical second Piola-Kirchhoff stress"
        ),
        new Definition(
            "S_total",
            "S_mechanical + S_swelling + S_electric",
            "Stress supplied to the user-defined hyperelastic material"
        )
    );

    public static final List<String> ARCHIVED_REVIEW_GATES = List.of(
        "Use one explicitly derived coordinate frame for all three species and electric potential; "
            + "the archived snapshot switched only the hydrogen-ion field to the spatial frame.",
        "Remove or physically justify the isolated 3e12 multiplier on the electrostatic gradient term.",
        "Synchronize the pH list stored in the study node (5, 9) with the batch node (5 through 9).",
        "Repeat mesh and time-step convergence checks and regenerate the literature benchmark; "
            + "the export retained mesh level 9 and did not contain solution fields."
    );

    private HydrogelModelDefinition() {}

    public static void main(String[] args) {
        int equationCount = KINEMATICS.size()
            + MECHANICS.size()
            + CHEMISTRY_AND_SWELLING.size()
            + TRANSPORT_AND_ELECTROSTATICS.size();
        System.out.printf(
            "Hydrogel model manifest: %d parameters, %d definitions, %d review gates.%n",
            SNAPSHOT_PARAMETERS.size(),
            equationCount,
            ARCHIVED_REVIEW_GATES.size()
        );
    }
}
