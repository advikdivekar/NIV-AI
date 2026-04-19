"""
Agent Pipeline — orchestrates all 6 agents sequentially.
Single entry point: run_analysis(raw_input) -> report dict.
"""
from __future__ import annotations
import logging
import time
from backend.agents import context_synthesizer, financial_analyst, risk_simulator
from backend.agents import property_analyst, assumption_challenger, decision_composer
from backend.calculations.benchmarks import get_maintenance_estimate, get_rental_yield
from backend.calculations.financial import compute_all
from backend.llm.client import LLMClient

logger = logging.getLogger(__name__)


async def run_analysis(raw_input: dict) -> dict:
    start = time.perf_counter()
    llm = LLMClient()
    fin = raw_input["financial"]
    prop = raw_input["property"]

    maintenance = get_maintenance_estimate(prop["location_area"])
    rental_yield = get_rental_yield(prop["location_area"])
    equivalent_rent = round(prop["property_price"] * (rental_yield / 100) / 12, 2)

    computed = compute_all(
        monthly_income=fin["monthly_income"], spouse_income=fin["spouse_income"],
        existing_emis=fin["existing_emis"], monthly_expenses=fin["monthly_expenses"],
        liquid_savings=fin["liquid_savings"], dependents=fin["dependents"],
        property_price=prop["property_price"], down_payment=prop["down_payment_available"],
        loan_tenure_years=prop["loan_tenure_years"], interest_rate=prop["expected_interest_rate"],
        carpet_area_sqft=prop["carpet_area_sqft"], buyer_gender=prop["buyer_gender"],
        is_ready_to_move=prop["is_ready_to_move"], maintenance_per_sqft=maintenance,
        equivalent_rent=equivalent_rent)
    computed_dict = computed.to_dict()

    context = await context_synthesizer.run(llm, raw_input, computed_dict)
    financial = await financial_analyst.run(llm, context, computed_dict, raw_input)
    stress_data = [{"name": s.name, "description": s.description, "can_survive": s.can_survive,
                    "months_before_default": s.months_before_default, "key_number": s.key_number,
                    "new_emi": s.new_emi, "new_ratio": s.new_ratio} for s in computed.stress_scenarios]
    risk = await risk_simulator.run(llm, context, financial, computed_dict, stress_data, raw_input)
    property_result = await property_analyst.run(llm, context, computed_dict, raw_input)
    assumptions = await assumption_challenger.run(llm, context, financial, risk, property_result, computed_dict, raw_input)
    verdict = await decision_composer.run(llm, context, financial, risk, property_result, assumptions, computed_dict, raw_input)

    rvb = property_result.get("rent_vs_buy", {})
    return {
        "verdict": verdict.get("verdict", "risky"),
        "confidence_score": verdict.get("confidence_score", 5),
        "verdict_reason": verdict.get("verdict_reason", ""),
        "top_reasons": verdict.get("top_reasons", []),
        "financial_summary": financial,
        "stress_scenarios": risk.get("scenarios", []),
        "property_assessment": property_result,
        "assumptions_challenged": assumptions.get("challenges", []),
        "blind_spots": assumptions.get("blind_spots", []),
        "emotional_flags": assumptions.get("emotional_flags", []),
        "conditions_for_safety": verdict.get("conditions_for_safety", []),
        "recommended_actions": verdict.get("recommended_actions", []),
        "rent_vs_buy": {"equivalent_monthly_rent": rvb.get("equivalent_monthly_rent", equivalent_rent),
                        "buying_monthly_cost": rvb.get("buying_monthly_cost", computed.monthly_ownership.total),
                        "premium_for_ownership_pct": rvb.get("premium_for_ownership_pct", computed.rent_vs_buy.premium_pct),
                        "break_even_years": rvb.get("break_even_years", computed.rent_vs_buy.break_even_years)},
        "computed_numbers": computed_dict,
        "full_reasoning": verdict.get("full_reasoning", ""),
        "data_sources": ["Mumbai benchmark data Q4 2025", "Indian income tax rules (80C, 24b)",
                         "Maharashtra stamp duty rates", "RBI home loan guidelines"],
        "limitations": ["Legal title not verified", "Builder financials not assessed",
                        "Physical inspection not done", "Bank eligibility may differ",
                        "Benchmark data may lag market by 1-2 quarters"],
        "disclaimer": "This analysis is for informational purposes only. Not financial advice.",
        "_meta": {"pipeline_time_seconds": round(time.perf_counter() - start, 2)}
    }
