"""Analysis endpoint — runs the 6-agent pipeline."""
from __future__ import annotations
import logging, traceback
from fastapi import APIRouter, HTTPException
from backend.models.input_models import AnalysisRequest
from backend.agents.pipeline import run_analysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/analyze")
async def analyze(request: AnalysisRequest):
    try:
        raw_input = {"financial": request.financial.model_dump(), "property": request.property.model_dump()}
        raw_input["financial"]["employment_type"] = request.financial.employment_type.value
        raw_input["property"]["configuration"] = request.property.configuration.value
        raw_input["property"]["buyer_gender"] = request.property.buyer_gender.value
        return await run_analysis(raw_input)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")
    except Exception as e:
        logger.error("Unexpected error: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Unexpected error. Please try again.")
