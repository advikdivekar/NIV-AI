"""Agent 1: Context Synthesizer — structures raw input, finds assumptions."""
from __future__ import annotations
import logging
from backend.llm.client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Context Synthesizer agent in a home-buying decision system for Indian buyers.
Transform raw user input into a structured decision context. Do NOT evaluate — only prepare data.

Classify:
- employment_stability: "high" (salaried 3+ yrs), "medium" (salaried <3yrs or stable freelance), "low" (new job, irregular)
- risk_capacity: "high" (large buffer, low obligations), "moderate" (decent buffer), "low" (thin buffer, high obligations)
- property_type_risk: "low" (ready-to-move RERA), "medium" (ready unverified), "high" (under-construction or unknown)

Respond ONLY with JSON:
{
  "user_profile": {
    "monthly_take_home": <number>,
    "household_income": <number>,
    "employment_stability": "<high|medium|low>",
    "total_monthly_obligations": <number>,
    "liquid_savings": <number>,
    "dependents": <number>,
    "risk_capacity": "<high|moderate|low>"
  },
  "property_profile": {
    "total_acquisition_cost": <number>,
    "monthly_ownership_cost": <number>,
    "property_type_risk": "<low|medium|high>",
    "location_tier": "<string>"
  },
  "implicit_assumptions": ["<assumption>"],
  "missing_data": ["<gap>"],
  "notes_interpretation": "<string>"
}"""


async def run(llm: LLMClient, raw_input: dict, computed_numbers: dict) -> dict:
    fin = raw_input["financial"]
    prop = raw_input["property"]
    rera = {True: "Yes", False: "No"}.get(prop.get("is_rera_registered"), "Unknown")
    msg = f"""Analyze this situation:
FINANCIAL: Income Rs.{fin["monthly_income"]:,.0f}, Spouse Rs.{fin["spouse_income"]:,.0f}, Type: {fin["employment_type"]}, Yrs: {fin["years_in_current_job"]}, EMIs: Rs.{fin["existing_emis"]:,.0f}, Expenses: Rs.{fin["monthly_expenses"]:,.0f}, Savings: Rs.{fin["liquid_savings"]:,.0f}, Dependents: {fin["dependents"]}, Notes: {fin["financial_notes"] or "None"}
PROPERTY: Price Rs.{prop["property_price"]:,.0f}, Location: {prop["location_area"]}, Config: {prop["configuration"]}, Area: {prop["carpet_area_sqft"]}sqft, Ready: {prop["is_ready_to_move"]}, RERA: {rera}, Builder: {prop["builder_name"] or "Unknown"}, Notes: {prop["property_notes"] or "None"}
COMPUTED (use exactly): EMI Rs.{computed_numbers["monthly_emi"]:,.0f}, Total cost Rs.{computed_numbers["total_acquisition_cost"]:,.0f}, Monthly ownership Rs.{computed_numbers["monthly_ownership_cost"]:,.0f}, Post-purchase savings Rs.{computed_numbers["post_purchase_savings"]:,.0f}, EMI/income {computed_numbers["emi_to_income_ratio"]:.1%}, Runway {computed_numbers["emergency_runway_months"]:.1f}mo"""
    raw = await llm.run_agent(SYSTEM_PROMPT, msg)
    result = llm.parse_json(raw)
    logger.info("Context synthesizer complete")
    return result
