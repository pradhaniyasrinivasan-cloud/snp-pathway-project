"""
Pydantic response models. Kept separate from the SQLAlchemy models
(models.py) on purpose: the DB shape and the API's public shape are
allowed to drift from each other (e.g. we deliberately do NOT expose
raw_response_json or internal row IDs to the frontend).
"""
from typing import Optional
from pydantic import BaseModel, Field


class VariantOut(BaseModel):
    """
    Response for GET /api/variant/{variant_id}.
    Corresponds to project spec Section 6.A (Variant Information).
    Deliberately does NOT include functional-effect predictions --
    those live at GET /api/variant/{variant_id}/functional-effect (Step 4).
    """
    rsid: str
    chromosome: Optional[str] = None
    position: Optional[int] = None
    ref_allele: Optional[str] = None
    alt_allele: Optional[str] = None
    gene_symbol: Optional[str] = None
    consequence: Optional[str] = None
    amino_acid_change: Optional[str] = None
    source: str = Field(..., description="Which provider answered this lookup: 'myvariant' or 'demo'")
    has_functional_effect_data: bool = Field(
        ..., description="Whether functional-effect data is available for this variant"
    )
    protein_name: Optional[str] = Field(None, description="Full protein name, when known")
    protein_description: Optional[str] = Field(
        None, description="Plain-language explanation of what this protein does"
    )


class DemoVariantSummary(BaseModel):
    """One row in the GET /api/demo/variants picker list."""
    variant_id: str
    rsid: str
    gene_symbol: Optional[str] = None
    amino_acid_change: Optional[str] = None
    impact_level: str


class FunctionalEffectOut(BaseModel):
    """
    Response for GET /api/variant/{variant_id}/functional-effect.
    Corresponds to project spec Section 6.B (Functional Effect).
    """
    rsid: str
    sift_prediction: Optional[str] = None
    sift_score: Optional[float] = None
    polyphen_prediction: Optional[str] = None
    polyphen_score: Optional[float] = None
    clinvar_significance: Optional[str] = None
    impact_level: str = Field(..., description="LOW | MODERATE | HIGH | UNKNOWN")
    perturbation_factor: float = Field(
        ..., description="Multiplier applied to the affected pathway node's activity in simulation"
    )
    perturbation_direction: Optional[str] = Field(
        None, description="'loss_of_function' | 'activating' | 'neutral'"
    )
    affected_node: Optional[str] = Field(
        None, description="Which pathway node this effect maps to (set once pathway mapping exists)"
    )
    is_modelled: bool = Field(
        ..., description="True if this is a Demo/Modelled Prediction rather than a real database value"
    )
    note: str
    source: str


class PathwayNodeOut(BaseModel):
    node_key: str
    label: str
    baseline_activity: float
    position_x: Optional[float] = None
    position_y: Optional[float] = None


class PathwayEdgeOut(BaseModel):
    source: str
    target: str
    weight: float
    interaction_type: str


class PathwayOut(BaseModel):
    """Response for GET /api/pathway/{pathway_id} — feeds the React Flow graph."""
    pathway_id: str
    name: str
    description: Optional[str] = None
    terminal_node: Optional[str] = None
    nodes: list[PathwayNodeOut]
    edges: list[PathwayEdgeOut]


class DemoPathwaySummary(BaseModel):
    pathway_id: str
    name: str
    description: Optional[str] = None
    node_count: int


class SimulateRequest(BaseModel):
    variant_id: str = Field(..., description="rsID (e.g. 'rs113488022') or demo key (e.g. 'demo-001')")
    pathway_id: Optional[str] = Field(
        None, description="Defaults to the variant's associated pathway, or 'mapk' if unknown"
    )


class SimulateResponse(BaseModel):
    variant_id: str
    pathway_id: str
    normal: dict[str, float] = Field(..., description="Node activities under normal (baseline) conditions")
    variant: dict[str, float] = Field(..., description="Node activities with the variant's effect applied")
    affected_node: Optional[str]
    pathway_output_normal: float
    pathway_output_variant: float
    percent_change: float
    interpretation: str
    is_modelled: bool = Field(
        ..., description="True if the underlying functional-effect estimate was modelled rather than a real prediction"
    )


class ErrorResponse(BaseModel):
    detail: str
