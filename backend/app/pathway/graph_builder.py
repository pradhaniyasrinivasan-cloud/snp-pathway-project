"""
Turns the DB-stored pathway definition (Pathway / PathwayNode / PathwayEdge
rows) into a networkx DiGraph that the propagation engine can run on.

Keeping this as its own module (rather than inlining it into the
simulation service) means the graph representation could later be swapped
out or extended (e.g. loading from Reactome/KEGG format) without touching
the propagation math at all -- this is the "modular so it can be replaced
with a more sophisticated model" requirement from the project spec.
"""
from typing import Optional
import networkx as nx
from sqlalchemy.orm import Session

from app.models import models


class PathwayNotFoundError(Exception):
    pass


def build_graph(pathway_key: str, db: Session) -> tuple[nx.DiGraph, models.Pathway]:
    """
    Returns (graph, pathway_row).

    Each node carries a `baseline_activity` attribute (default 1.0).
    Each edge carries `weight` and `interaction_type` ("activation" | "inhibition").
    """
    pathway = db.query(models.Pathway).filter_by(pathway_key=pathway_key).first()
    if pathway is None:
        raise PathwayNotFoundError(f"No pathway found with key '{pathway_key}'")

    graph = nx.DiGraph()

    for node in pathway.nodes:
        graph.add_node(
            node.node_key,
            label=node.label,
            baseline_activity=node.baseline_activity,
            protein_id=node.protein_id,
            position_x=node.position_x,
            position_y=node.position_y,
        )

    for edge in pathway.edges:
        graph.add_edge(
            edge.source_node_key,
            edge.target_node_key,
            weight=edge.weight,
            interaction_type=edge.interaction_type,
        )

    if not nx.is_directed_acyclic_graph(graph):
        # The propagation engine relies on a topological order. If someone
        # later adds a pathway with a feedback loop (common in real
        # biology!), this is exactly where it needs to fail loudly rather
        # than silently produce nonsense numbers -- handling cyclic
        # pathways is explicitly future work, not an MVP requirement.
        raise ValueError(
            f"Pathway '{pathway_key}' contains a cycle. The current propagation "
            f"model only supports acyclic (DAG) pathways."
        )

    return graph, pathway


# Each MAPK node stands for a protein FAMILY, but the database links each node
# to only one representative protein (e.g. RAS -> HRAS). Without this table a
# live KRAS or NRAS variant would not map to the RAS node, and ERK (no linked
# protein at all) could never be hit. Gene symbols are HGNC names.
GENE_FAMILY_TO_NODE = {
    "mapk": {
        "Receptor": {"PDGFRA", "PDGFRB", "EGFR"},
        "RAS": {"HRAS", "KRAS", "NRAS"},
        "RAF": {"BRAF", "RAF1", "ARAF"},
        "MEK": {"MAP2K1", "MAP2K2"},
        "ERK": {"MAPK1", "MAPK3"},
    },
}


def resolve_affected_node(pathway_key: str, gene_symbol: Optional[str], db: Session) -> Optional[str]:
    """
    Given a gene symbol (e.g. "BRAF"), find which node in the given pathway
    represents that gene's protein, by following PathwayNode -> Protein ->
    gene_symbol.

    This is needed for variants that arrive from the live provider, which
    doesn't know about pathway topology at all (see MyVariantProvider's
    module docstring) -- only the demo dataset has affected_node pre-filled.

    Returns None if the gene isn't part of this pathway (a perfectly valid
    outcome -- not every gene participates in every pathway).
    """
    if not gene_symbol:
        return None

    pathway = db.query(models.Pathway).filter_by(pathway_key=pathway_key).first()
    if pathway is None:
        return None

    for node in pathway.nodes:
        if node.protein and node.protein.gene_symbol:
            if node.protein.gene_symbol.upper() == gene_symbol.upper():
                return node.node_key

    # Fall back to the documented gene-family table (only for nodes that
    # really exist in this pathway).
    node_keys = {node.node_key for node in pathway.nodes}
    for node_key, genes in GENE_FAMILY_TO_NODE.get(pathway_key, {}).items():
        if node_key in node_keys and gene_symbol.upper() in genes:
            return node_key

    return None


def list_pathways(db: Session) -> list[models.Pathway]:
    return db.query(models.Pathway).all()
