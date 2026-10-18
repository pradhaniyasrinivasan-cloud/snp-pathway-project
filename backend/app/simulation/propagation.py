"""
The core computational contribution of this project (project spec Section 10).

Represents pathway activity propagation over a directed acyclic graph.
Deliberately kept as a small, pure function with no database or API
dependency, so the model itself is easy to read, unit-test, and later
swap out for something more sophisticated (ODE-based, Bayesian, etc.)
without touching anything else in the app.

--------------------------------------------------------------------------
THE MODEL (documented in full -- see also README "Mathematical Model"):

For each node, in topological order:

  - If the node has no predecessors (a "source" node, e.g. Growth Factor):
        activity = baseline_activity

  - If the node has one or more predecessors:
        for each predecessor p with edge weight w:
            contribution_p = activity[p] * w              (if activation)
            contribution_p = activity[p] * (1 - w)         (if inhibition)
        activity = average(all contributions)

    Using the average when a node has multiple parents is a deliberate
    simplification for the MVP (real pathways often integrate multiple
    inputs non-linearly). It's documented here and in the README's
    "Limitations" section rather than presented as biological fact.

  - A PERTURBATION is applied by multiplying a specific node's computed
    activity by a `perturbation_factor`:
        activity[node] *= perturbation_factor

    This happens AFTER the node's normal contribution from its
    predecessors is computed, so the effect still respects upstream
    pathway state, and then propagates forward through every downstream
    node exactly as normal from that point on.

  - The "normal" run is simply this same computation with no
    perturbation applied (every factor = 1.0).
--------------------------------------------------------------------------
"""
from dataclasses import dataclass, field
from typing import Optional
import networkx as nx


@dataclass
class PropagationResult:
    node_activities: dict[str, float]
    pathway_output: float          # activity at the terminal node
    terminal_node: str


def propagate(
    graph: nx.DiGraph,
    terminal_node: str,
    perturbations: Optional[dict[str, float]] = None,
) -> PropagationResult:
    """
    Runs one propagation pass over the graph.

    `perturbations`: optional dict of {node_key: factor}. Omit or pass {}
    for a normal (unperturbed) run. Pass e.g. {"RAF": 1.8} to simulate a
    variant that boosts RAF's activity by 80%.
    """
    perturbations = perturbations or {}

    if terminal_node not in graph.nodes:
        raise ValueError(f"Terminal node '{terminal_node}' is not in the graph.")
    for node_key in perturbations:
        if node_key not in graph.nodes:
            raise ValueError(f"Perturbed node '{node_key}' is not in the graph.")

    activities: dict[str, float] = {}

    for node in nx.topological_sort(graph):
        predecessors = list(graph.predecessors(node))

        if not predecessors:
            base_activity = graph.nodes[node]["baseline_activity"]
        else:
            contributions = []
            for pred in predecessors:
                edge = graph.edges[pred, node]
                weight = edge["weight"]
                if edge.get("interaction_type") == "inhibition":
                    contributions.append(activities[pred] * (1 - weight))
                else:  # "activation" (default)
                    contributions.append(activities[pred] * weight)
            base_activity = sum(contributions) / len(contributions)

        factor = perturbations.get(node, 1.0)
        activities[node] = base_activity * factor

    return PropagationResult(
        node_activities=activities,
        pathway_output=activities[terminal_node],
        terminal_node=terminal_node,
    )


def run_normal_vs_variant(
    graph: nx.DiGraph,
    terminal_node: str,
    affected_node: Optional[str],
    perturbation_factor: float,
) -> tuple[PropagationResult, PropagationResult]:
    """
    Convenience wrapper: runs both the normal pass and the variant pass
    and returns (normal_result, variant_result).

    If `affected_node` is None (e.g. we couldn't map the variant's gene
    onto any node in this pathway), the variant pass is identical to the
    normal pass -- there's simply nothing for this variant to perturb in
    this particular pathway, which is a valid and meaningful result, not
    an error.
    """
    normal_result = propagate(graph, terminal_node, perturbations={})

    variant_perturbations = {}
    if affected_node is not None:
        variant_perturbations = {affected_node: perturbation_factor}

    variant_result = propagate(graph, terminal_node, perturbations=variant_perturbations)

    return normal_result, variant_result


def percent_change(normal_output: float, variant_output: float) -> float:
    if normal_output == 0:
        return 0.0
    return round((variant_output - normal_output) / normal_output * 100, 2)
