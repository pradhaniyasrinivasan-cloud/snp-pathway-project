"""
Tests for app.services.functional_effect_service — the model that turns
raw SIFT/PolyPhen/ClinVar (or, failing that, consequence type) into
impact_level + perturbation_factor.
"""
from app.services.functional_effect_service import functional_effect_service as svc


class TestClinVarPriority:
    def test_pathogenic(self):
        result = svc.interpret(clinvar_significance="Pathogenic")
        assert result.impact_level == "HIGH"
        assert result.is_modelled is False
        assert result.basis == "clinvar"

    def test_likely_pathogenic(self):
        result = svc.interpret(clinvar_significance="Likely pathogenic")
        assert result.impact_level == "HIGH"
        assert result.is_modelled is False

    def test_benign(self):
        result = svc.interpret(clinvar_significance="Benign")
        assert result.impact_level == "LOW"
        assert result.is_modelled is False

    def test_uncertain_significance_is_modelled(self):
        result = svc.interpret(clinvar_significance="Uncertain significance")
        assert result.is_modelled is True


class TestSiftPolyphenFallback:
    def test_both_damaging_is_high(self):
        result = svc.interpret(sift_prediction="deleterious", polyphen_prediction="probably_damaging")
        assert result.impact_level == "HIGH"
        assert result.is_modelled is False

    def test_one_damaging_is_moderate(self):
        result = svc.interpret(sift_prediction="deleterious", polyphen_prediction="benign")
        assert result.impact_level == "MODERATE"

    def test_both_tolerated_is_low(self):
        result = svc.interpret(sift_prediction="tolerated", polyphen_prediction="benign")
        assert result.impact_level == "LOW"

    def test_clinvar_takes_priority_over_sift_polyphen(self):
        result = svc.interpret(
            clinvar_significance="Benign",
            sift_prediction="deleterious",
            polyphen_prediction="probably_damaging",
        )
        assert result.impact_level == "LOW"
        assert result.basis == "clinvar"


class TestConsequenceHeuristicFallback:
    def test_no_evidence_at_all_falls_back_to_consequence(self):
        result = svc.interpret(consequence="stop_gained")
        assert result.is_modelled is True
        assert result.impact_level == "HIGH"
        assert result.perturbation_factor < 0.3

    def test_synonymous_is_low_impact(self):
        result = svc.interpret(consequence="synonymous_variant")
        assert result.impact_level == "LOW"
        assert result.is_modelled is True

    def test_totally_unknown_consequence_is_unknown(self):
        result = svc.interpret(consequence="some_never_seen_consequence")
        assert result.impact_level == "UNKNOWN"
        assert result.perturbation_factor == 1.0

    def test_no_data_at_all_is_unknown(self):
        result = svc.interpret()
        assert result.impact_level == "UNKNOWN"
        assert result.is_modelled is True


class TestDirectionOverride:
    def test_activating_override_flips_direction_and_factor(self):
        base = svc.interpret(sift_prediction="deleterious", polyphen_prediction="probably_damaging")
        assert base.perturbation_direction == "loss_of_function"

        flipped = svc.interpret(
            sift_prediction="deleterious",
            polyphen_prediction="probably_damaging",
            known_direction_override="activating",
        )
        assert flipped.perturbation_direction == "activating"
        assert flipped.perturbation_factor > 1.0
        assert flipped.is_modelled is True  # direction override is always a modelled judgment call
