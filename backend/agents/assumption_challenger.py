"""Agent 5: Assumption Challenger — adversarial agent that finds holes in the decision."""
from __future__ import annotations
import logging
from backend.llm.client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Assumption Challenger — a financial devil's advocate for Indian home purchases.
Find EVERY way this decision could go wrong. Be specific with rupee amounts.

BAD: "Salary growth might be lower"
GOOD: "You assumed 10% growth. IT sector median has been 6-8% since 2022. At 7%, EMI/income stays above 40% for 5 years."

severity: "critical" (alone causes distress), "high" (materially changes decision), "medium" (plan for it), "low" (minor)
Generate at least 3 challenges and 2 blind spots.

Respond ONLY with JSON:
{
  "challenges": [{"assumption": "<what was assumed>", "challenge": "<why wrong, with data>", "impact": "<rupee impact>", "severity": "<level>"}],
  "blind_spots": ["<unconsidered factor>"],
  "emotional_flags": ["<bias detected>"],
  "reasoning": "<2-3 paragraphs>"
}"""


async def run(llm: LLMClient, context: dict, financial_analysis: dict, risk_analysis: dict,
              property_analysis: dict, computed_numbers: dict, raw_input: dict) -> dict:
    fin = raw_input["financial"]
    prop = raw_input["property"]
    challenges = [f"{c.get('assumption','?')} → {c.get('severity','?')}" for c in property_analysis.get("property_flags", [])]
    survived = sum(1 for s in risk_analysis.get("scenarios", []) if s.get("can_survive", False))
    msg = f"""Challenge every assumption in this decision:
Income Rs.{fin["monthly_income"]:,.0f} ({fin["employment_type"]}, {fin["years_in_current_job"]}yrs), Growth assumption: {fin["expected_annual_growth_pct"]}%, Dependents: {fin["dependents"]}, Savings: Rs.{fin["liquid_savings"]:,.0f}
Down payment: Rs.{prop["down_payment_available"]:,.0f}, Notes: {fin["financial_notes"] or "None"} | {prop["property_notes"] or "None"}
Implicit assumptions found: {context.get("implicit_assumptions", [])}
Missing data: {context.get("missing_data", [])}
Financial verdict: {financial_analysis.get("affordability_verdict")}, EMI/income: {computed_numbers["emi_to_income_ratio"]:.1%}, Runway: {computed_numbers["emergency_runway_months"]:.1f}mo
Stress tests passed: {survived}/4, Critical vulnerability: {risk_analysis.get("critical_vulnerability")}
Price verdict: {property_analysis.get("price_assessment", {}).get("verdict")}, Break-even: {computed_numbers["rent_vs_buy_break_even_years"]:.1f}yrs
Find everything the buyer and previous agents are NOT seeing."""
    raw = await llm.run_agent(SYSTEM_PROMPT, msg, max_tokens=3500)
    result = llm.parse_json(raw)
    logger.info("Assumption challenger complete — %d challenges", len(result.get("challenges", [])))
    return result
