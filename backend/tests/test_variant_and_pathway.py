"""
Tests for variant lookup (VariantService) and gene-to-pathway-node
resolution (graph_builder.resolve_affected_node).
"""
import pytest

from app.services.variant_service import variant_service
from app.pathway.graph_builder import build_graph, resolve_affected_node, PathwayNotFoundError


class TestVariantLookup:
    def test_lookup_by_demo_key(self, db_session):
        result = variant_service.get_variant("demo-001", db_session)
        assert result is not None
        assert result["gene_symbol"] == "BRAF"
        assert result["rsid"] == "rs113488022"

    def test_lookup_by_rsid_after_caching(self, db_session):
        # first lookup by demo key persists the rsid-keyed row
        variant_service.get_variant("demo-001", db_session)
        # second lookup by the rsid itself should hit the cache and succeed
        result = variant_service.get_variant("rs113488022", db_session)
        assert result is not None
        assert result["gene_symbol"] == "BRAF"

    def test_unknown_variant_returns_none(self, db_session):
        result = variant_service.get_variant("rs00000000000", db_session)
        assert result is None

    def test_demo_variant_has_functional_effect(self, db_session):
        result = variant_service.get_variant("demo-003", db_session)
        assert result["functional_effect"] is not None
        assert result["functional_effect"]["is_modelled"] is True  # PDGFRA nonsense, no real SIFT/PolyPhen


class TestPathwayMapping:
    def test_build_graph_for_known_pathway(self, db_session):
        graph, pathway_row = build_graph("mapk", db_session)
        assert pathway_row.pathway_key == "mapk"
        assert "RAF" in graph.nodes
        assert graph.has_edge("RAS", "RAF")

    def test_build_graph_unknown_pathway_raises(self, db_session):
        with pytest.raises(PathwayNotFoundError):
            build_graph("not_a_real_pathway", db_session)

    def test_resolve_affected_node_by_gene_symbol(self, db_session):
        node_key = resolve_affected_node("mapk", "BRAF", db_session)
        assert node_key == "RAF"

    def test_resolve_affected_node_gene_not_in_pathway(self, db_session):
        node_key = resolve_affected_node("mapk", "TP53", db_session)
        assert node_key is None

    def test_resolve_affected_node_no_gene_symbol(self, db_session):
        node_key = resolve_affected_node("mapk", None, db_session)
        assert node_key is None
