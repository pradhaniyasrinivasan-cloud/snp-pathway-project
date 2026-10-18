"""
Regression tests for problems found when checking the app against live
MyVariant.info data (October 2026):

  1. dbNSFP single-letter SIFT/PolyPhen codes (D/T/P/B) were not recognised.
  2. "Conflicting interpretations of pathogenicity" was treated as Pathogenic.
  3. Live activating hotspots (e.g. BRAF V600E) were simulated as loss of function.
  4. KRAS/NRAS/ERK-family genes did not map onto any pathway node.
  5. The live provider must query by rsID and pick the clinically annotated allele.
"""
import sys
import types

import pytest

from app.services.functional_effect_service import (
    functional_effect_service,
    known_direction_for,
    normalize_polyphen,
    normalize_sift,
)
from app.pathway.graph_builder import resolve_affected_node


class TestPredictionCodes:
    def test_sift_codes_are_normalised(self):
        assert normalize_sift("D") == "deleterious"
        assert normalize_sift("T") == "tolerated"
        assert normalize_sift("deleterious") == "deleterious"
        assert normalize_sift(None) is None

    def test_polyphen_codes_are_normalised(self):
        assert normalize_polyphen("D") == "probably_damaging"
        assert normalize_polyphen("P") == "possibly_damaging"
        assert normalize_polyphen("B") == "benign"
        assert normalize_polyphen("probably damaging") == "probably_damaging"

    def test_live_codes_both_damaging_gives_high(self):
        result = functional_effect_service.interpret(sift_prediction="D", polyphen_prediction="D")
        assert result.impact_level == "HIGH"
        assert result.basis == "sift_polyphen"

    def test_live_codes_tolerated_gives_low(self):
        result = functional_effect_service.interpret(sift_prediction="T", polyphen_prediction="B")
        assert result.impact_level == "LOW"


class TestClinVarEdgeCases:
    def test_conflicting_is_not_pathogenic(self):
        result = functional_effect_service.interpret(
            clinvar_significance="Conflicting interpretations of pathogenicity"
        )
        assert result.impact_level == "MODERATE"
        assert result.perturbation_factor == 0.8

    @pytest.mark.parametrize("value", ["not provided", "association", "risk factor", "drug response"])
    def test_non_informative_clinvar_falls_through_to_sift_polyphen(self, value):
        result = functional_effect_service.interpret(
            clinvar_significance=value, sift_prediction="D", polyphen_prediction="D"
        )
        assert result.basis == "sift_polyphen"
        assert result.impact_level == "HIGH"


class TestActivatingHotspots:
    @pytest.mark.parametrize("gene,change", [
        ("BRAF", "V600E"), ("BRAF", "p.Val600Glu"), ("KRAS", "p.Gly12Asp"),
        ("HRAS", "G12S"), ("NRAS", "p.Gln61Arg"),
    ])
    def test_known_hotspots_are_activating(self, gene, change):
        assert known_direction_for(gene, change) == "activating"

    @pytest.mark.parametrize("gene,change", [
        ("BRAF", "p.Val600Val"),   # synonymous
        ("BRAF", "p.Arg600*"),     # nonsense
        ("BRAF", "p.Gly469Ala"),   # not in the hotspot list
        ("TP53", "p.Arg175His"),   # not an oncogene hotspot gene
        (None, "V600E"),
    ])
    def test_non_hotspots_are_not_activating(self, gene, change):
        assert known_direction_for(gene, change) is None

    def test_live_braf_v600e_increases_pathway_output(self):
        result = functional_effect_service.interpret(
            clinvar_significance="Pathogenic",
            known_direction_override=known_direction_for("BRAF", "p.Val600Glu"),
        )
        assert result.perturbation_direction == "activating"
        assert result.perturbation_factor > 1.0


class TestGeneFamilyMapping:
    @pytest.mark.parametrize("gene,node", [
        ("KRAS", "RAS"), ("NRAS", "RAS"), ("RAF1", "RAF"),
        ("MAP2K2", "MEK"), ("MAPK1", "ERK"), ("MAPK3", "ERK"), ("EGFR", "Receptor"),
    ])
    def test_family_members_map_to_node(self, db_session, gene, node):
        assert resolve_affected_node("mapk", gene, db_session) == node

    def test_unrelated_gene_still_unmapped(self, db_session):
        assert resolve_affected_node("mapk", "APOE", db_session) is None


class TestMyVariantProvider:
    """Uses a fake httpx module, so no network access is needed."""

    @pytest.fixture()
    def provider(self, monkeypatch):
        from app.services.variant_provider import myvariant_provider as mod
        calls = {}
        payload = {"hits": [
            {"_id": "chr7:g.140753336A>G",
             "dbsnp": {"rsid": "rs113488022", "chrom": "7", "ref": "A", "alt": "G",
                       "hg38": {"start": 140753336}, "gene": {"symbol": "BRAF"}},
             "dbnsfp": {"polyphen2": {"hdiv": {"pred": "B", "score": 0.2}}},
             "snpeff": {"ann": [{"gene_name": "BRAF", "effect": "missense_variant", "hgvs_p": "p.Val600Ala"}]}},
            {"_id": "chr7:g.140753336A>T",
             "dbsnp": {"rsid": "rs113488022", "chrom": "7", "ref": "A", "alt": "T",
                       "hg38": {"start": 140753336}, "gene": [{"symbol": "BRAF"}]},
             "clinvar": {"rcv": [{"clinical_significance": "not provided"},
                                 {"clinical_significance": "Pathogenic"},
                                 {"clinical_significance": "Pathogenic"},
                                 {"clinical_significance": "Uncertain significance"}]},
             "dbnsfp": {"polyphen2": {"hdiv": {"pred": "D", "score": 0.971}}},
             "snpeff": {"ann": [{"gene_name": "BRAF", "effect": "missense_variant", "hgvs_p": "p.Val600Glu"}]}},
        ]}

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return calls.get("payload", payload)

        def fake_get(url, params=None, **kwargs):
            calls["url"], calls["params"] = url, params
            return FakeResponse()

        monkeypatch.setattr(mod.httpx, "get", fake_get)
        return mod.MyVariantProvider(), calls

    def test_queries_by_rsid_on_hg38(self, provider):
        prov, calls = provider
        prov.fetch_variant("rs113488022")
        assert calls["url"].endswith("/v1/query")
        assert calls["params"]["q"] == "dbsnp.rsid:rs113488022"
        assert calls["params"]["assembly"] == "hg38"

    def test_picks_clinically_annotated_allele_and_normalises(self, provider):
        prov, _ = provider
        result = prov.fetch_variant("rs113488022")
        assert result["alt_allele"] == "T"
        assert result["amino_acid_change"] == "p.Val600Glu"
        assert result["gene_symbol"] == "BRAF"
        assert result["position"] == 140753336
        fe = result["functional_effect"]
        assert fe["clinvar_significance"] == "Pathogenic"   # majority, not first-listed
        assert fe["polyphen_prediction"] == "probably_damaging"

    def test_no_hits_returns_none(self, provider):
        prov, calls = provider
        calls["payload"] = {"hits": []}
        assert prov.fetch_variant("rs999999999999") is None

    def test_non_rsid_skips_network(self, provider):
        prov, calls = provider
        assert prov.fetch_variant("demo-001") is None
        assert "url" not in calls
