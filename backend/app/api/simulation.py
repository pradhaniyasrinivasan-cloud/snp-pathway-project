"""
The core endpoint of the whole project: POST /api/simulate.

Takes a variant_id (and optionally a pathway_id) and returns the full
normal-vs-variant comparison, ready for the frontend's Simulation page
(Step 8) to render directly -- node activities for both conditions,
the headline pathway_output numbers, percent change, and the generated
plain-language interpretation.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.simulation.simulation_service import (
    simulation_service, VariantNotFoundError, NoFunctionalEffectError
)
from app.pathway.graph_builder import PathwayNotFoundError
from app.models.schemas import SimulateRequest, SimulateResponse

router = APIRouter(prefix="/api", tags=["simulation"])


@router.post("/simulate", response_model=SimulateResponse)
def simulate(request: SimulateRequest, db: Session = Depends(get_db)):
    try:
        result = simulation_service.simulate(
            variant_id=request.variant_id,
            db=db,
            pathway_id=request.pathway_id,
        )
    except VariantNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except NoFunctionalEffectError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except PathwayNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        # e.g. cyclic pathway graph -- see graph_builder.build_graph
        raise HTTPException(status_code=500, detail=str(exc))

    return SimulateResponse(
        variant_id=result.variant_id,
        pathway_id=result.pathway_id,
        normal=result.normal_activities,
        variant=result.variant_activities,
        affected_node=result.affected_node,
        pathway_output_normal=result.pathway_output_normal,
        pathway_output_variant=result.pathway_output_variant,
        percent_change=result.percent_change,
        interpretation=result.interpretation,
        is_modelled=result.is_modelled,
    )
