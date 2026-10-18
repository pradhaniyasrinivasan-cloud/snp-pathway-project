"""
Pathway endpoints. GET /api/pathway/{pathway_id} returns the graph shape
(nodes + edges) that the frontend's React Flow visualization (Step 7)
will render directly.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models import models
from app.models.schemas import PathwayOut, PathwayNodeOut, PathwayEdgeOut

router = APIRouter(prefix="/api/pathway", tags=["pathway"])


@router.get("/{pathway_id}", response_model=PathwayOut)
def get_pathway(pathway_id: str, db: Session = Depends(get_db)):
    pathway = db.query(models.Pathway).filter_by(pathway_key=pathway_id).first()
    if pathway is None:
        raise HTTPException(status_code=404, detail=f"No pathway found with id '{pathway_id}'.")

    return PathwayOut(
        pathway_id=pathway.pathway_key,
        name=pathway.name,
        description=pathway.description,
        terminal_node=pathway.terminal_node_key,
        nodes=[
            PathwayNodeOut(
                node_key=n.node_key,
                label=n.label,
                baseline_activity=n.baseline_activity,
                position_x=n.position_x,
                position_y=n.position_y,
            )
            for n in pathway.nodes
        ],
        edges=[
            PathwayEdgeOut(
                source=e.source_node_key,
                target=e.target_node_key,
                weight=e.weight,
                interaction_type=e.interaction_type,
            )
            for e in pathway.edges
        ],
    )
