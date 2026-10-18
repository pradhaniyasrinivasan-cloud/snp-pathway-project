"""
FunctionalEffectService — turns raw database/prediction fields into two
things the rest of the app actually needs:

  1. impact_level:        LOW | MODERATE | HIGH | UNKNOWN   (for display)
  2. perturbation_factor: a float multiplier applied to the affected
                           pathway node's activity in the simulation
                           (this is the number that actually drives
                           Step 5/6's normal-vs-variant comparison)

This is the single place in the whole app where that interpretation
happens. Two important design decisions, both called out explicitly
here so nothing is quietly guessed elsewhere in the codebase:

DECISION 1 — Real evidence takes priority, missing evidence falls back
to a documented heuristic.
    If we have a real ClinVar significance, or real SIFT/PolyPhen scores,
    those drive the result and `is_modelled` is set to False (well,
    "not fabricated" -- see note below). If none of that is available
    (as will often happen for live lookups, since not every variant has
    been run through VEP), we fall back to a simple rule based on the
    *consequence type* (missense / nonsense / synonymous / etc.), and
    `is_modelled` is explicitly set to True with a note explaining why.
    This satisfies project spec Section 6: "Do NOT fabricate biological
    predictions... If real prediction data is unavailable, clearly
    label the result as Demo/Modelled Prediction."

DECISION 2 — perturbation_factor is a SIMPLIFIED linear model, not a
    biological measurement.
    Even when it's derived from real SIFT/PolyPhen/ClinVar values, the
    *mapping* from "ClinVar says Pathogenic" to "multiply activity by
    0.4" is our own modelling choice, not something the database tells
    us directly. So `is_modelled` reflects whether the underlying
    evidence is real; the numeric conversion itself is always a
    documented simplification (see PERTURBATION_RULES below) regardless.
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class FunctionalEffectResult:
    impact_level: str                    # LOW | MODERATE | HIGH | UNKNOWN
    perturbation_factor: float
    perturbation_direction: str          # "loss_of_function" | "activating" | "neutral"
    is_modelled: bool
    note: str
    basis: str                           # what evidence drove this result, for transparency


# ---------------------------------------------------------------------
# Consequence-type heuristic (used ONLY when no real prediction scores
# are available). These numbers are a documented simplification, not a
# citation-backed biological fact -- exactly the kind of thing that
# belongs in the README's "Limitations" section.
# ---------------------------------------------------------------------
CONSEQUENCE_HEURISTIC = {
    "stop_gained":              (0.15, "HIGH",     "loss_of_function"),
    "frameshift_variant":       (0.15, "HIGH",     "loss_of_function"),
    "splice_donor_variant":     (0.25, "HIGH",     "loss_of_function"),
    "splice_acceptor_variant":  (0.25, "HIGH",     "loss_of_function"),
    "missense_variant":         (0.65, "MODERATE", "loss_of_function"),
    "inframe_deletion":         (0.70, "MODERATE", "loss_of_function"),
    "inframe_insertion":        (0.70, "MODERATE", "loss_of_function"),
    "synonymous_variant":       (0.97, "LOW",       "neutral"),
    "intron_variant":           (0.98, "LOW",       "neutral"),
    "5_prime_UTR_variant":      (0.95, "LOW",       "neutral"),
    "3_prime_UTR_variant":      (0.95, "LOW",       "neutral"),
}
DEFAULT_UNKNOWN_CONSEQUENCE = (1.0, "UNKNOWN", "neutral")


# dbNSFP (via MyVariant.info) reports predictions as single-letter codes
# (SIFT: D/T, PolyPhen-2: D/P/B), while curated/demo data uses full words.
# Previously the codes were not recognised, so a live variant that BOTH tools
# call damaging was labelled LOW impact. Normalise both to full words.
_SIFT_CODES = {"d": "deleterious", "t": "tolerated"}
_POLYPHEN_CODES = {"d": "probably_damaging", "p": "possibly_damaging", "b": "benign"}


def normalize_sift(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = str(value).strip().lower().replace(" ", "_")
    return _SIFT_CODES.get(v, v)


def normalize_polyphen(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = str(value).strip().lower().replace(" ", "_")
    return _POLYPHEN_CODES.get(v, v)


# ---------------------------------------------------------------------
# Known ACTIVATING (gain-of-function) hotspots.
# Databases report these as "Pathogenic"/"damaging" but cannot say that the
# protein becomes MORE active. Without this list, the live BRAF V600E rsID
# (rs113488022) was simulated as a ~60% DECREASE in pathway output -- the
# opposite of well-established biology. Deliberately small and limited to
# textbook MAPK oncogene hotspots; this is a documented modelling judgment.
# ---------------------------------------------------------------------
KNOWN_ACTIVATING_HOTSPOTS = {
    "BRAF": {600},
    "HRAS": {12, 13, 61},
    "KRAS": {12, 13, 61},
    "NRAS": {12, 13, 61},
}

_AA_CHANGE_RE = re.compile(r"^(?:p\.)?([A-Za-z]{1,3})(\d+)([A-Za-z]{1,3}|\*)$")


def known_direction_for(gene_symbol: Optional[str], amino_acid_change: Optional[str]) -> Optional[str]:
    """Return "activating" for a missense change at a known oncogenic hotspot
    (accepts "V600E" and "p.Val600Glu" styles), otherwise None."""
    if not gene_symbol or not amino_acid_change:
        return None
    hotspots = KNOWN_ACTIVATING_HOTSPOTS.get(gene_symbol.upper())
    if not hotspots:
        return None
    m = _AA_CHANGE_RE.match(amino_acid_change.strip())
    if not m:
        return None
    ref, pos, alt = m.group(1).lower(), int(m.group(2)), m.group(3).lower()
    if pos not in hotspots or ref == alt or alt in ("*", "ter"):
        return None  # synonymous or nonsense changes are not activating
    return "activating"


def _from_clinvar(clinvar_significance: Optional[str]) -> Optional[FunctionalEffectResult]:
    """ClinVar is the strongest single signal we get, when present."""
    if not clinvar_significance:
        return None

    sig = clinvar_significance.lower().strip()

    # "Conflicting interpretations of pathogenicity" contains the word
    # "pathogenic" but means submitters DISAGREE -- treat it like
    # "uncertain", never as a confident Pathogenic call.
    if "conflicting" in sig:
        return FunctionalEffectResult(
            impact_level="MODERATE",
            perturbation_factor=0.8,
            perturbation_direction="loss_of_function",
            is_modelled=True,
            note="ClinVar submitters disagree about this variant ('Conflicting interpretations "
                 "of pathogenicity'), so we apply a cautious moderate perturbation rather "
                 "than treating it as Pathogenic or Benign.",
            basis="clinvar",
        )

    # Values like "not provided", "association", "risk factor", "drug response"
    # say nothing about damage to the protein -- fall through to SIFT/PolyPhen.
    if not any(k in sig for k in ("pathogenic", "benign", "uncertain")):
        return None

    if "pathogenic" in sig and "likely" not in sig:
        return FunctionalEffectResult(
            impact_level="HIGH",
            perturbation_factor=0.4,
            perturbation_direction="loss_of_function",
            is_modelled=False,
            note="Based on a real ClinVar 'Pathogenic' classification. The 0.4 multiplier "
                 "is our own simplified mapping from that classification to a pathway "
                 "activity factor, not a value reported by ClinVar itself.",
            basis="clinvar",
        )
    if "likely pathogenic" in sig or "pathogenic/likely pathogenic" in sig:
        return FunctionalEffectResult(
            impact_level="HIGH",
            perturbation_factor=0.5,
            perturbation_direction="loss_of_function",
            is_modelled=False,
            note="Based on a real ClinVar 'Likely pathogenic' classification, mapped to a "
                 "pathway activity factor using our own simplified scale.",
            basis="clinvar",
        )
    if "benign" in sig:
        return FunctionalEffectResult(
            impact_level="LOW",
            perturbation_factor=0.97,
            perturbation_direction="neutral",
            is_modelled=False,
            note="Based on a real ClinVar 'Benign' classification.",
            basis="clinvar",
        )
    if "uncertain significance" in sig:
        return FunctionalEffectResult(
            impact_level="MODERATE",
            perturbation_factor=0.8,
            perturbation_direction="loss_of_function",
            is_modelled=True,
            note="ClinVar reports this variant as 'Uncertain significance' -- real evidence "
                 "exists but does not point to a clear effect, so we apply a cautious "
                 "moderate perturbation as a placeholder rather than assuming no effect.",
            basis="clinvar",
        )
    return None


def _from_sift_polyphen(
    sift_prediction: Optional[str],
    polyphen_prediction: Optional[str],
) -> Optional[FunctionalEffectResult]:
    """Used when ClinVar has nothing, but SIFT and/or PolyPhen do."""
    # Accept both dbNSFP single-letter codes (live data) and full words (demo data).
    sift = normalize_sift(sift_prediction) or ""
    polyphen = normalize_polyphen(polyphen_prediction) or ""

    sift_bad = sift in ("deleterious", "damaging")
    polyphen_bad = polyphen in ("probably_damaging", "possibly_damaging")

    if not sift and not polyphen:
        return None

    if sift_bad and polyphen_bad:
        return FunctionalEffectResult(
            impact_level="HIGH",
            perturbation_factor=0.45,
            perturbation_direction="loss_of_function",
            is_modelled=False,
            note="Both SIFT and PolyPhen predict a damaging effect on protein function.",
            basis="sift_polyphen",
        )
    if sift_bad or polyphen_bad:
        return FunctionalEffectResult(
            impact_level="MODERATE",
            perturbation_factor=0.7,
            perturbation_direction="loss_of_function",
            is_modelled=False,
            note="One of SIFT/PolyPhen predicts a damaging effect; the other disagrees or "
                 "is unavailable, so we treat this as a moderate (not high) effect.",
            basis="sift_polyphen",
        )
    return FunctionalEffectResult(
        impact_level="LOW",
        perturbation_factor=0.95,
        perturbation_direction="neutral",
        is_modelled=False,
        note="SIFT and/or PolyPhen predict this variant is tolerated/benign.",
        basis="sift_polyphen",
    )


def _from_consequence(consequence: Optional[str]) -> FunctionalEffectResult:
    """Last-resort fallback: derive an estimate purely from the consequence
    type (missense, nonsense, synonymous, etc.). Always modelled."""
    factor, level, direction = CONSEQUENCE_HEURISTIC.get(
        (consequence or "").lower(), DEFAULT_UNKNOWN_CONSEQUENCE
    )
    return FunctionalEffectResult(
        impact_level=level,
        perturbation_factor=factor,
        perturbation_direction=direction,
        is_modelled=True,
        note=(
            f"No real SIFT/PolyPhen/ClinVar prediction was available for this variant. "
            f"This is a Demo/Modelled Prediction estimated only from its consequence type "
            f"('{consequence or 'unknown'}'), using a fixed heuristic table, not a "
            f"database-reported prediction."
        ),
        basis="consequence_heuristic",
    )


class FunctionalEffectService:
    """
    Entry point: `interpret()` takes whatever raw fields we have for a
    variant (which may be partial or entirely absent) and returns a
    single, documented FunctionalEffectResult.

    Priority order (highest-confidence evidence wins):
        1. ClinVar clinical significance
        2. SIFT / PolyPhen predictions
        3. Consequence-type heuristic (always modelled/demo)
    """

    def interpret(
        self,
        *,
        clinvar_significance: Optional[str] = None,
        sift_prediction: Optional[str] = None,
        polyphen_prediction: Optional[str] = None,
        consequence: Optional[str] = None,
        # Some variants (like activating oncogene mutations, e.g. BRAF V600E)
        # increase rather than decrease downstream signalling. Real databases
        # don't encode "direction of pathway effect" in a structured field,
        # so for known special cases we allow an explicit override; this is
        # itself a modelled judgment call and is always labelled as such.
        known_direction_override: Optional[str] = None,
    ) -> FunctionalEffectResult:

        result = _from_clinvar(clinvar_significance)
        if result is None:
            result = _from_sift_polyphen(sift_prediction, polyphen_prediction)
        if result is None:
            result = _from_consequence(consequence)

        if known_direction_override == "activating" and result.perturbation_direction == "loss_of_function":
            # Flip a loss-of-function-style factor (e.g. 0.4) into an
            # activating one (e.g. 1 + (1 - 0.4) = 1.6) using a simple,
            # symmetric transform. This keeps the "how damaging" magnitude
            # from the evidence above, just applied in the other direction.
            flipped_factor = round(1 + (1 - result.perturbation_factor), 2)
            result = FunctionalEffectResult(
                impact_level=result.impact_level,
                perturbation_factor=flipped_factor,
                perturbation_direction="activating",
                is_modelled=True,
                note=result.note + " Direction flipped to 'activating' based on known "
                     "oncogene biology for this specific variant (a modelled judgment call, "
                     "not something ClinVar/SIFT/PolyPhen encode).",
                basis=result.basis + "+direction_override",
            )

        return result


functional_effect_service = FunctionalEffectService()
