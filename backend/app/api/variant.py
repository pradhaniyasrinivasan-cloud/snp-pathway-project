"""
Variant endpoints.

GET /api/variant/{variant_id}
    Accepts either an rsID ("rs113488022") or a demo key ("demo-001").
    Tries the live provider chain first, falls back to demo data
    automatically -- the caller has no idea (and doesn't need to know)
    which one actually answered; that information is only visible in
    the `source` field of the response.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services.variant_service import variant_service
from app.models.schemas import VariantOut, FunctionalEffectOut

router = APIRouter(prefix="/api/variant", tags=["variant"])


@router.get("/{variant_id}", response_model=VariantOut)
def get_variant(variant_id: str, db: Session = Depends(get_db)):
    result = variant_service.get_variant(variant_id, db)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No variant data found for '{variant_id}'. "
                "It wasn't found via the live lookup, and it isn't one of the demo variants "
                "(try GET /api/demo/variants for a list of working demo IDs)."
            ),
        )

    return VariantOut(
        rsid=result["rsid"],
        chromosome=result.get("chromosome"),
        position=result.get("position"),
        ref_allele=result.get("ref_allele"),
        alt_allele=result.get("alt_allele"),
        gene_symbol=result.get("gene_symbol"),
        consequence=result.get("consequence"),
        amino_acid_change=result.get("amino_acid_change"),
        source=result.get("source", "unknown"),
        has_functional_effect_data=result.get("functional_effect") is not None,
        protein_name=(result.get("protein") or {}).get("name"),
        protein_description=(result.get("protein") or {}).get("simple_description"),
    )


@router.get("/{variant_id}/functional-effect", response_model=FunctionalEffectOut)
def get_functional_effect(variant_id: str, db: Session = Depends(get_db)):
    result = variant_service.get_variant(variant_id, db)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No variant data found for '{variant_id}'.",
        )

    fe = result.get("functional_effect")
    if fe is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Variant '{variant_id}' was found, but no functional-effect data "
                "(SIFT/PolyPhen/ClinVar or a modelled estimate) is available for it."
            ),
        )

    return FunctionalEffectOut(
        rsid=result["rsid"],
        sift_prediction=fe.get("sift_prediction"),
        sift_score=fe.get("sift_score"),
        polyphen_prediction=fe.get("polyphen_prediction"),
        polyphen_score=fe.get("polyphen_score"),
        clinvar_significance=fe.get("clinvar_significance"),
        impact_level=fe.get("impact_level", "UNKNOWN"),
        perturbation_factor=fe.get("perturbation_factor", 1.0),
        perturbation_direction=fe.get("perturbation_direction"),
        affected_node=fe.get("affected_node"),
        is_modelled=fe.get("is_modelled", True),
        note=fe.get("note", ""),
        source=result.get("source", "unknown"),
    )
