"""
Integration tests hitting the actual FastAPI endpoints, using a seeded
in-memory-equivalent test database (see conftest.py's api_client fixture).
"""
import pytest


class TestVariantEndpoint:
    def test_get_demo_variant(self, api_client):
        response = api_client.get("/api/variant/demo-001")
        assert response.status_code == 200
        body = response.json()
        assert body["gene_symbol"] == "BRAF"
        assert body["source"] == "demo"
        assert body["has_functional_effect_data"] is True

    def test_get_unknown_variant_returns_404(self, api_client):
        response = api_client.get("/api/variant/rs00000000000")
        assert response.status_code == 404
        assert "detail" in response.json()

    def test_functional_effect_endpoint(self, api_client):
        response = api_client.get("/api/variant/demo-003/functional-effect")
        assert response.status_code == 200
        body = response.json()
        assert body["impact_level"] == "HIGH"
        assert body["is_modelled"] is True

    def test_functional_effect_unknown_variant_404(self, api_client):
        response = api_client.get("/api/variant/rs00000000000/functional-effect")
        assert response.status_code == 404


class TestPathwayEndpoint:
    def test_get_mapk_pathway(self, api_client):
        response = api_client.get("/api/pathway/mapk")
        assert response.status_code == 200
        body = response.json()
        assert body["pathway_id"] == "mapk"
        assert len(body["nodes"]) == 7
        assert len(body["edges"]) == 6

    def test_get_unknown_pathway_404(self, api_client):
        response = api_client.get("/api/pathway/nonexistent")
        assert response.status_code == 404


class TestDemoEndpoints:
    def test_list_demo_variants(self, api_client):
        response = api_client.get("/api/demo/variants")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 4
        assert {v["variant_id"] for v in body} == {"demo-001", "demo-002", "demo-003", "demo-004"}

    def test_list_demo_pathways(self, api_client):
        response = api_client.get("/api/demo/pathways")
        assert response.status_code == 200
        body = response.json()
        assert any(p["pathway_id"] == "mapk" for p in body)


class TestSimulateEndpoint:
    def test_simulate_activating_variant_increases_output(self, api_client):
        response = api_client.post("/api/simulate", json={"variant_id": "demo-001"})
        assert response.status_code == 200
        body = response.json()
        assert body["affected_node"] == "RAF"
        assert body["percent_change"] > 0
        assert body["pathway_output_variant"] > body["pathway_output_normal"]
        assert "computational prediction" in body["interpretation"].lower()

    def test_simulate_loss_of_function_variant_decreases_output(self, api_client):
        response = api_client.post("/api/simulate", json={"variant_id": "demo-003"})
        assert response.status_code == 200
        body = response.json()
        assert body["percent_change"] < 0
        assert body["pathway_output_variant"] < body["pathway_output_normal"]

    def test_simulate_unknown_variant_404(self, api_client):
        response = api_client.post("/api/simulate", json={"variant_id": "rs00000000000"})
        assert response.status_code == 404

    def test_simulate_missing_variant_id_is_422(self, api_client):
        response = api_client.post("/api/simulate", json={})
        assert response.status_code == 422

    def test_simulate_response_matches_manual_calculation(self, api_client):
        # This is the same BRAF V600E scenario hand-verified in Step 5:
        # normal output ~0.561, variant output ~1.0097, +80% change.
        response = api_client.post("/api/simulate", json={"variant_id": "demo-001"})
        body = response.json()
        assert body["pathway_output_normal"] == pytest.approx(0.561, abs=0.001)
        assert body["pathway_output_variant"] == pytest.approx(1.0097, abs=0.001)
        assert body["percent_change"] == pytest.approx(80.0, abs=0.1)
