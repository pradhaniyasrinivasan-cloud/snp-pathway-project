"""
SimulationService: the glue between everything built in Steps 3-5.

Given a variant_id (and optionally a pathway_id), this:
  1. Looks up the variant + its functional effect (Step 3/4's VariantService)
  2. Resolves which pathway node it affects (demo data has this pre-filled;
     live variants get resolved via gene_symbol -> Protein -> PathwayNode)
  3. Builds the pathway graph (Step 5's graph_builder)
  4. Runs normal vs variant propagation (Step 5's propagation engine)
  5. Generates a plain-language interpretation sentence
  6. Persists the run for history/caching

This is the one place that produces the exact payload the frontend's
Simulation page (Step 8) will render.
"""
import json
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.services.variant_service import variant_service
from app.pathway.graph_builder import build_graph, resolve_affected_node, PathwayNotFoundError
from app.simulation.propagation import run_normal_vs_variant, percent_change
from app.models import models

DEFAULT_PATHWAY_KEY = "mapk"  # only pathway available in the MVP; see README limitations


class VariantNotFoundError(Exception):
    pass


class NoFunctionalEffectError(Exception):
    pass


@dataclass
class SimulationResult:
    variant_id: str
    pathway_id: str
    normal_activities: dict[str, float]
    variant_activities: dict[str, float]
    affected_node: Optional[str]
    pathway_output_normal: float
    pathway_output_variant: float
    percent_change: float
    interpretation: str
    is_modelled: bool


def _build_interpretation(
    gene_symbol: Optional[str],
    protein_name: Optional[str],
    affected_node: Optional[str],
    direction: Optional[str],
    pathway_name: str,
    pct_change: float,
    is_modelled: bool,
) -> str:
    """
    Generates the plain-language summary required by project spec Section 12.
    Always phrased as a computational prediction, never a claim of biological
    fact (Section 20's scientific-safety requirement).
    """
    subject = gene_symbol or "The affected gene"
    protein_part = f" ({protein_name})" if protein_name else ""

    if affected_node is None:
        return (
            f"The selected variant is in {subject}{protein_part}, which does not map to any "
            f"node in the {pathway_name}. No perturbation was applied, so the model predicts "
            f"no change to this particular pathway's output. This does not mean the variant "
            f"has no effect elsewhere in the cell -- only that this pathway model doesn't "
            f"represent it."
        )

    if abs(pct_change) < 1:
        direction_phrase = "a negligible change in"
    elif pct_change > 0:
        direction_phrase = f"an estimated {pct_change}% increase in"
    else:
        direction_phrase = f"an estimated {abs(pct_change)}% decrease in"

    effect_verb = {
        "activating": "increased functional activity of",
        "loss_of_function": "reduced functional activity of",
        "neutral": "minimal change to the functional activity of",
    }.get(direction, "a change in the functional activity of")

    modelled_clause = (
        " This estimate uses a Demo/Modelled Prediction rather than a real database-reported "
        "functional score, since real prediction data was not available for this variant."
        if is_modelled else ""
    )

    return (
        f"The selected variant in {subject}{protein_part} is predicted to cause {effect_verb} "
        f"the {affected_node} protein. {affected_node} participates in the {pathway_name}. "
        f"When this perturbation is introduced into the pathway model, it produces {direction_phrase} "
        f"downstream pathway activity compared with the normal model.{modelled_clause} "
        f"This is a computational prediction based on a simplified pathway model, not experimental proof."
    )


class SimulationService:

    def simulate(self, variant_id: str, db: Session, pathway_id: Optional[str] = None) -> SimulationResult:
        variant = variant_service.get_variant(variant_id, db)
        if variant is None:
            raise VariantNotFoundError(f"No variant data found for '{variant_id}'.")

        fe = variant.get("functional_effect")
        if fe is None:
            raise NoFunctionalEffectError(
                f"Variant '{variant_id}' has no functional-effect data to simulate with."
            )

        pathway_key = pathway_id or variant.get("pathway_id") or DEFAULT_PATHWAY_KEY

        try:
            graph, pathway_row = build_graph(pathway_key, db)
        except PathwayNotFoundError as exc:
            raise

        affected_node = fe.get("affected_node")
        if affected_node is None:
            affected_node = resolve_affected_node(pathway_key, variant.get("gene_symbol"), db)
        elif affected_node not in graph.nodes:
            # Defensive: demo data says a node that doesn't exist in this
            # particular pathway's graph (e.g. simulating against a
            # different pathway than the one the demo data was written for).
            affected_node = None

        terminal_node = pathway_row.terminal_node_key
        normal_result, variant_result = run_normal_vs_variant(
            graph,
            terminal_node=terminal_node,
            affected_node=affected_node,
            perturbation_factor=fe.get("perturbation_factor", 1.0),
        )

        pct_change = percent_change(normal_result.pathway_output, variant_result.pathway_output)

        interpretation = _build_interpretation(
            gene_symbol=variant.get("gene_symbol"),
            protein_name=(variant.get("protein") or {}).get("name") if variant.get("protein") else None,
            affected_node=affected_node,
            direction=fe.get("perturbation_direction"),
            pathway_name=pathway_row.name,
            pct_change=pct_change,
            is_modelled=fe.get("is_modelled", True),
        )

        result = SimulationResult(
            variant_id=variant["rsid"],
            pathway_id=pathway_key,
            normal_activities=normal_result.node_activities,
            variant_activities=variant_result.node_activities,
            affected_node=affected_node,
            pathway_output_normal=round(normal_result.pathway_output, 4),
            pathway_output_variant=round(variant_result.pathway_output, 4),
            percent_change=pct_change,
            interpretation=interpretation,
            is_modelled=fe.get("is_modelled", True),
        )

        self._persist(result, variant, pathway_row, db)
        return result

    def _persist(self, result: SimulationResult, variant: dict, pathway_row: models.Pathway, db: Session) -> None:
        variant_row = db.query(models.Variant).filter_by(rsid=result.variant_id).first()
        if variant_row is None:
            return  # shouldn't happen since VariantService just persisted it, but don't crash a simulation over history logging

        db.add(models.SimulationRun(
            variant_id=variant_row.id,
            pathway_id=pathway_row.id,
            normal_result_json=json.dumps(result.normal_activities),
            variant_result_json=json.dumps(result.variant_activities),
            pathway_output_normal=result.pathway_output_normal,
            pathway_output_variant=result.pathway_output_variant,
            percent_change=result.percent_change,
            interpretation=result.interpretation,
        ))
        db.commit()


simulation_service = SimulationService()
