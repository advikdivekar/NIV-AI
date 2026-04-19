"""Agent 4: Property & Market Analyst — evaluates property vs Mumbai benchmarks."""
from __future__ import annotations
import logging
from typing import Optional
from backend.calculations.benchmarks import lookup_area, AreaBenchmark
from backend.llm.client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Property & Market Analyst agent for Indian / Mumbai home purchases.
Evaluate price fairness, flag property risks, analyze location, interpret rent-vs-buy.

price verdict: "good_value" (<median), "fair" (within 10%), "slightly_overpriced" (10-25% above), "overpriced" (>25% above), "no_benchmark"
flag severity: "low", "medium", "high"

Respond ONLY with JSON:
{
  "price_assessment": {"price_per_sqft": <n>, "area_median_per_sqft": <n>, "premium_over_market_pct": <n>, "verdict": "<v>"},
  "property_flags": [{"flag": "<name>", "severity": "<level>", "detail": "<explanation>"}],
  "location_analysis": "<paragraph>",
  "rent_vs_buy": {"equivalent_monthly_rent": <n>, "buying_monthly_cost": <n>, "premium_for_ownership_pct": <n>, "break_even_years": <n>},
  "reasoning": "<2-3 paragraphs>"
}"""


async def run(llm: LLMClient, context: dict, computed_numbers: dict, raw_input: dict) -> dict:
    prop = raw_input["property"]
    benchmark = lookup_area(prop["location_area"])
    price_per_sqft = round(prop["property_price"] / prop["carpet_area_sqft"], 0) if prop["carpet_area_sqft"] > 0 else 0
    rera = {True: "Yes", False: "No"}.get(prop.get("is_rera_registered"), "Unknown")

    if benchmark:
        premium = round((price_per_sqft - benchmark.price_median) / benchmark.price_median * 100, 1)
        bench_text = f"Area: {benchmark.name}, Range: Rs.{benchmark.price_min:,.0f}-{benchmark.price_median:,.0f}(median)-{benchmark.price_max:,.0f}/sqft, This property: Rs.{price_per_sqft:,.0f}/sqft ({'+' if premium>0 else ''}{premium}% vs median), Rental yield: {benchmark.rental_yield_pct}%, BKC: {benchmark.distance_to_bkc_km}km, Metro: {benchmark.metro_connectivity}, Flood risk: {benchmark.flood_risk}, Notes: {benchmark.infrastructure_notes}"
    else:
        bench_text = "No benchmark data available for this area."

    msg = f"""Evaluate this property:
Price: Rs.{prop["property_price"]:,.0f}, Location: {prop["location_area"]}, Config: {prop["configuration"]}, Area: {prop["carpet_area_sqft"]}sqft, Price/sqft: Rs.{price_per_sqft:,.0f}
Ready: {prop["is_ready_to_move"]}, RERA: {rera}, Builder: {prop["builder_name"] or "Not specified"}, Possession: {prop["possession_date"] or "N/A"}, Notes: {prop["property_notes"] or "None"}
Monthly ownership cost: Rs.{computed_numbers["monthly_ownership_cost"]:,.0f}, Rent-vs-buy premium: {computed_numbers["rent_vs_buy_premium_pct"]:.0f}%, Break-even: {computed_numbers["rent_vs_buy_break_even_years"]:.1f}yrs
BENCHMARK: {bench_text}"""
    raw = await llm.run_agent(SYSTEM_PROMPT, msg)
    result = llm.parse_json(raw)
    logger.info("Property analyst complete")
    return result
