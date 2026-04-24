"""
Analysis endpoints:
  POST /api/v1/analyze  — full 6-agent pipeline (rate-limited: 5/10min/IP)
  GET  /api/v1/calculate — headless math engine, no LLM (rate-limited: 30/min/IP)
"""
import logging
import os
import time
import traceback
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.agents.pipeline import run_analysis
from backend.calculations.benchmarks import get_maintenance_estimate, get_rental_yield, get_area_benchmark_result
from backend.calculations.financial import compute_all
from backend.models.input_models import AnalysisRequest
from backend.utils.rate_limit import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["analysis"])

DEMO_API_KEY: str | None = os.getenv("DEMO_API_KEY")


def _check_api_key(request: Request) -> None:
    """Enforce X-API-Key header when DEMO_API_KEY env var is set."""
    if DEMO_API_KEY and request.headers.get("X-API-Key") != DEMO_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header.")


@router.post("/analyze")
@limiter.limit("5/10 minutes")
async def analyze(request: Request, body: AnalysisRequest):
    """
    Run the full 6-agent analysis pipeline.

    Rate-limited to 5 requests per 10 minutes per IP. If DEMO_API_KEY env var is set,
    requires a matching X-API-Key header (disabled in local development).
    """
    _check_api_key(request)
    try:
        raw_input = {
            "financial": body.financial.model_dump(),
            "property": body.property.model_dump(),
            "output_language": body.output_language.value,
            "behavioral_checklist_responses": body.behavioral_checklist_responses,
        }
        raw_input["financial"]["employment_type"] = body.financial.employment_type.value
        raw_input["property"]["configuration"] = body.property.configuration.value
        raw_input["property"]["buyer_gender"] = body.property.buyer_gender.value
        return await run_analysis(raw_input)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {e}")
    except Exception as e:
        logger.error("Unexpected error: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Unexpected error. Please try again.")


class CalculateResponse(BaseModel):
    """Response model for the headless calculate endpoint."""
    loan_amount: float
    monthly_emi: float
    total_loan_payment: float
    total_interest_paid: float
    total_acquisition_cost: float
    stamp_duty: float
    registration: float
    gst: float
    monthly_ownership_cost: float
    monthly_maintenance: float
    emi_to_income_ratio: float
    total_housing_to_income_ratio: float
    down_payment_to_savings_ratio: float
    emergency_runway_months: float
    post_purchase_savings: float
    annual_tax_saving: float
    effective_monthly_cost_after_tax: float
    rent_vs_buy_premium_pct: float
    rent_vs_buy_break_even_years: float
    interiors_estimated_cost: float
    true_total_acquisition_cost: float
    down_payment_opportunity_cost_10yr: float
    annual_commute_cost_estimate: float
    maintenance_5yr_projected_cost: float
    true_monthly_cost_after_all_factors: float
    down_payment: float
    benchmark_available: bool
    response_time_ms: float


@router.get("/calculate", response_model=CalculateResponse)
@limiter.limit("30/minute")
async def calculate(
    request: Request,
    monthly_income: float,
    property_price: float,
    down_payment: float,
    carpet_area_sqft: float,
    location_area: str = "Mumbai",
    spouse_income: float = 0.0,
    existing_emis: float = 0.0,
    monthly_expenses: float = 0.0,
    liquid_savings: float = 0.0,
    dependents: int = 0,
    loan_tenure_years: int = 20,
    interest_rate: float = 8.5,
    buyer_gender: str = "male",
    is_ready_to_move: bool = True,
    commute_distance_km: float = 0.0,
):
    """
    Headless math engine — returns all computed financial metrics without running any LLM agents.

    Accepts all financial and property parameters as query parameters.
    Response time is typically under 100ms.

    Args:
        monthly_income: Primary earner's gross monthly income in INR.
        property_price: Total property price in INR.
        down_payment: Down payment amount in INR.
        carpet_area_sqft: Property carpet area in sqft.
        location_area: Mumbai area name for benchmark lookup.
        spouse_income: Co-borrower monthly income. Default 0.
        existing_emis: Sum of existing monthly EMIs. Default 0.
        monthly_expenses: Monthly household expenses. Default 0 (auto: 40% of income).
        liquid_savings: Total liquid savings in INR. Default 0.
        dependents: Number of financial dependents. Default 0.
        loan_tenure_years: Loan tenure in years. Default 20.
        interest_rate: Annual interest rate percentage. Default 8.5.
        buyer_gender: "male" or "female". Default "male".
        is_ready_to_move: True for ready-to-move property. Default True.
        commute_distance_km: One-way commute distance in km. Default 0.

    Returns:
        CalculateResponse with all computed metrics plus benchmark_available flag and response_time_ms.
    """
    t0 = time.perf_counter()

    if monthly_income <= 0:
        raise HTTPException(status_code=422, detail="monthly_income must be greater than 0")
    if property_price <= 100000:
        raise HTTPException(status_code=422, detail="property_price must be greater than 100,000")
    if down_payment >= property_price:
        raise HTTPException(status_code=422, detail="down_payment cannot exceed property_price")
    if buyer_gender not in ("male", "female"):
        raise HTTPException(status_code=422, detail="buyer_gender must be 'male' or 'female'")

    if monthly_expenses <= 0:
        monthly_expenses = round(monthly_income * 0.40, 2)

    bm = get_area_benchmark_result(location_area)
    maintenance = bm.data.maintenance_typical if bm.data else 5.5
    rental_yield = bm.data.rental_yield_pct if bm.data else 2.5
    benchmark_available = bm.coverage_level != "default"
    equivalent_rent = round(property_price * (rental_yield / 100) / 12, 2)

    computed = compute_all(
        monthly_income=monthly_income,
        spouse_income=spouse_income,
        existing_emis=existing_emis,
        monthly_expenses=monthly_expenses,
        liquid_savings=liquid_savings,
        dependents=dependents,
        property_price=property_price,
        down_payment=down_payment,
        loan_tenure_years=loan_tenure_years,
        interest_rate=interest_rate,
        carpet_area_sqft=carpet_area_sqft,
        buyer_gender=buyer_gender,
        is_ready_to_move=is_ready_to_move,
        maintenance_per_sqft=maintenance,
        equivalent_rent=equivalent_rent,
        commute_distance_km=commute_distance_km,
    )

    result = computed.to_dict()
    result["benchmark_available"] = benchmark_available
    result["response_time_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    return result
