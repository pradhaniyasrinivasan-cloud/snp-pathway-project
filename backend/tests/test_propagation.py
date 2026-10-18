"""
Tests for app.simulation.propagation — the core math, with no DB dependency.
"""
import pytest
import networkx as nx

from app.simulation.propagation import propagate, run_normal_vs_variant, percent_change


def make_mapk_like_graph():
    """A small linear chain matching the real MAPK pathway's shape and weights."""
    g = nx.DiGraph()
    for node in ["GrowthFactor", "Receptor", "RAS", "RAF", "MEK", "ERK", "CellularResponse"]:
        g.add_node(node, baseline_activity=1.0)
    edges = [
        ("GrowthFactor", "Receptor", 0.95),
        ("Receptor", "RAS", 0.90),
        ("RAS", "RAF", 0.90),
        ("RAF", "MEK", 0.90),
        ("MEK", "ERK", 0.90),
        ("ERK", "CellularResponse", 0.90),
    ]
    for s, t, w in edges:
        g.add_edge(s, t, weight=w, interaction_type="activation")
    return g


class TestPropagate:
    def test_normal_run_matches_hand_calculation(self):
        g = make_mapk_like_graph()
        result = propagate(g, "CellularResponse")
        # 1.0 * 0.95 * 0.90 * 0.90 * 0.90 * 0.90 * 0.90
        expected = 1.0 * 0.95 * (0.90 ** 5)
        assert result.pathway_output == pytest.approx(expected, rel=1e-6)

    def test_activating_perturbation_increases_downstream(self):
        g = make_mapk_like_graph()
        normal = propagate(g, "CellularResponse")
        variant = propagate(g, "CellularResponse", perturbations={"RAF": 1.8})
        assert variant.pathway_output > normal.pathway_output
        assert variant.node_activities["RAS"] == normal.node_activities["RAS"]  # upstream unaffected

    def test_loss_of_function_perturbation_decreases_downstream(self):
        g = make_mapk_like_graph()
        normal = propagate(g, "CellularResponse")
        variant = propagate(g, "CellularResponse", perturbations={"Receptor": 0.15})
        assert variant.pathway_output < normal.pathway_output

    def test_no_perturbation_equals_normal(self):
        g = make_mapk_like_graph()
        normal = propagate(g, "CellularResponse")
        no_op = propagate(g, "CellularResponse", perturbations={})
        assert normal.pathway_output == no_op.pathway_output

    def test_invalid_terminal_node_raises(self):
        g = make_mapk_like_graph()
        with pytest.raises(ValueError):
            propagate(g, "NotARealNode")

    def test_invalid_perturbed_node_raises(self):
        g = make_mapk_like_graph()
        with pytest.raises(ValueError):
            propagate(g, "CellularResponse", perturbations={"NotARealNode": 0.5})

    def test_cyclic_graph_raises(self):
        g = nx.DiGraph()
        g.add_node("A", baseline_activity=1.0)
        g.add_node("B", baseline_activity=1.0)
        g.add_edge("A", "B", weight=1.0, interaction_type="activation")
        g.add_edge("B", "A", weight=1.0, interaction_type="activation")
        with pytest.raises(nx.NetworkXUnfeasible):
            propagate(g, "B")

    def test_inhibition_edge_reduces_contribution(self):
        g = nx.DiGraph()
        g.add_node("A", baseline_activity=1.0)
        g.add_node("B", baseline_activity=1.0)
        g.add_edge("A", "B", weight=0.3, interaction_type="inhibition")
        result = propagate(g, "B")
        # inhibition: activity = activity[A] * (1 - weight) = 1.0 * 0.7
        assert result.node_activities["B"] == pytest.approx(0.7)

    def test_multiple_parents_averaged(self):
        g = nx.DiGraph()
        g.add_node("A", baseline_activity=1.0)
        g.add_node("B", baseline_activity=0.5)
        g.add_node("C", baseline_activity=1.0)
        g.add_edge("A", "C", weight=1.0, interaction_type="activation")
        g.add_edge("B", "C", weight=1.0, interaction_type="activation")
        result = propagate(g, "C")
        # average of (1.0*1.0) and (0.5*1.0) = 0.75
        assert result.node_activities["C"] == pytest.approx(0.75)


class TestRunNormalVsVariant:
    def test_no_affected_node_gives_identical_results(self):
        g = make_mapk_like_graph()
        normal, variant = run_normal_vs_variant(g, "CellularResponse", affected_node=None, perturbation_factor=0.5)
        assert normal.pathway_output == variant.pathway_output


class TestPercentChange:
    def test_increase(self):
        assert percent_change(0.5, 1.0) == 100.0

    def test_decrease(self):
        assert percent_change(1.0, 0.5) == -50.0

    def test_zero_normal_output_does_not_divide_by_zero(self):
        assert percent_change(0.0, 1.0) == 0.0
