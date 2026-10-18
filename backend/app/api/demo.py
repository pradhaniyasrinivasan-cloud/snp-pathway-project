"""
Demo listing endpoints — power the "pick a demo variant/pathway" UI so the
app works even with zero network access (project spec Section 14).
"""
from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services.variant_service import variant_service
from app.pathway.graph_builder import list_pathways
from app.models.schemas import DemoVariantSummary, DemoPathwaySummary

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/variants", response_model=List[DemoVariantSummary])
def list_demo_variants():
    return variant_service.demo_provider.list_demo_variants()


@router.get("/pathways", response_model=List[DemoPathwaySummary])
def list_demo_pathways(db: Session = Depends(get_db)):
    return [
        DemoPathwaySummary(
            pathway_id=p.pathway_key,
            name=p.name,
            description=p.description,
            node_count=len(p.nodes),
        )
        for p in list_pathways(db)
    ]
