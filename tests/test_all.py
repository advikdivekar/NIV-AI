"""
Niv AI Test Suite — 53 tests across 12 categories.
Run: python tests/test_all.py
"""

import asyncio, sys, os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.calculations.financial import (calculate_emi, calculate_acquisition_cost,
    calculate_monthly_ownership, calculate_key_ratios, calculate_tax_benefits,
    calculate_stress_scenarios, calculate_rent_vs_buy, compute_all)
from backend.calculations.benchmarks import lookup_area, get_maintenance_estimate, list_areas

passed = 0
failed = 0

def check_close(actual, expected, tol=1.0, label=""):
    global passed, failed
    if abs(actual - expected) <= tol:
        print(f"  PASS {label}: {actual}")
        passed += 1
    else:
        print(f"  FAIL {label}: expected {expected}, got {actual}")
        failed += 1

def check_true(cond, label=""):
    global passed, failed
    if cond:
        print(f"  PASS {label}")
        passed += 1
    else:
        print(f"  FAIL {label}")
        failed += 1

print("\n=== EMI ===")
r = calculate_emi(5000000, 8.5, 240)
check_close(r.monthly_emi, 43391, 50, "50L@8.5%/20yr")
check_close(calculate_emi(0,8.5,240).monthly_emi, 0, 0, "Zero principal")
check_close(calculate_emi(1200000,0,120).monthly_emi, 10000, 1, "0% rate")

print("\n=== ACQUISITION COST ===")
r = calculate_acquisition_cost(7500000, "male", False)
check_close(r.stamp_duty, 450000, 1, "Stamp 6% male")
check_close(r.registration, 30000, 1, "Registration capped 30K")
check_close(r.gst, 375000, 1, "GST 5% under-construction")
check_close(calculate_acquisition_cost(7500000,"female",True).stamp_duty, 375000, 1, "Stamp 5% female")
check_close(calculate_acquisition_cost(7500000,"female",True).gst, 0, 0, "No GST ready")
check_close(calculate_acquisition_cost(5000000,"male",True,True).brokerage, 50000, 1, "1% brokerage")

print("\n=== MONTHLY OWNERSHIP ===")
r = calculate_monthly_ownership(43000, 650, 5.5)
check_close(r.maintenance, 3575, 1, "Maintenance")
check_close(r.total, 47075, 1, "Total monthly")

print("\n=== KEY RATIOS ===")
r = calculate_key_ratios(120000, 0, 43000, 47000, 5000, 45000, 2000000, 1500000)
check_close(r.emi_to_income, 43000/120000, 0.001, "EMI/income")
check_close(r.down_payment_to_savings, 0.75, 0.001, "DP/savings")
check_close(r.emergency_runway_months, 5.38, 0.1, "Runway")

print("\n=== TAX BENEFITS ===")
r = calculate_tax_benefits(180000, 420000, True, 0.30)
check_close(r.section_80c_annual, 150000, 1, "80C capped")
check_close(r.section_24b_annual, 200000, 1, "24b capped")
check_close(r.total_annual_saving, 105000, 1, "Annual saving")

print("\n=== STRESS SCENARIOS ===")
s = calculate_stress_scenarios(120000, 0, 43000, 45000, 5000, 500000, 5000000, 8.5, 240)
check_true(len(s)==4, "4 scenarios")
check_true(not s[0].can_survive, "Job loss fails (5.4mo < 6mo)")
check_true(s[1].new_emi > 43000, "Rate hike increases EMI")
check_true(not s[2].can_survive, "5L shock fails")

print("\n=== RENT VS BUY ===")
r = calculate_rent_vs_buy(25000, 47000, 1500000)
check_true(r.premium_pct > 0, "Ownership costs more")
check_true(r.break_even_years > 0, "Break-even > 0")

print("\n=== BENCHMARKS ===")
check_true(lookup_area("Andheri West") is not None, "Andheri West found")
check_true(lookup_area("andheri west") is not None, "Case-insensitive")
check_true(lookup_area("Powai") is not None, "Powai found")
check_true(lookup_area("Atlantis") is None, "Unknown returns None")
check_close(get_maintenance_estimate("Unknown"), 5.5, 0.01, "Fallback maintenance")
check_true(len(list_areas()) >= 30, "30+ areas")

print("\n=== COMPUTE ALL ===")
r = compute_all(120000, 0, 5000, 48000, 2000000, 1, 7500000, 1500000, 20, 8.5, 650, "male", True)
check_true(r.emi.monthly_emi > 0, "EMI computed")
check_true(r.acquisition.total > 7500000, "Acquisition > price")
check_true(len(r.stress_scenarios)==4, "4 stress scenarios")
check_true(r.post_purchase_savings == 500000, "Post-purchase savings")
d = r.to_dict()
check_true("monthly_emi" in d, "to_dict has EMI")
check_true("emi_to_income_ratio" in d, "to_dict has ratios")

print("\n=== INPUT VALIDATION ===")
from backend.models.input_models import AnalysisRequest, FinancialInput, PropertyInput
try:
    AnalysisRequest(financial=FinancialInput(monthly_income=100000, liquid_savings=1500000),
                    property=PropertyInput(property_price=7500000, location_area="Andheri West",
                                           carpet_area_sqft=650, down_payment_available=1500000))
    check_true(True, "Valid request accepted")
except: check_true(False, "Valid request rejected")

try:
    FinancialInput(monthly_income=-1000, liquid_savings=0)
    check_true(False, "Negative income should fail")
except: check_true(True, "Negative income rejected")

try:
    PropertyInput(property_price=5000000, location_area="T", carpet_area_sqft=500, down_payment_available=6000000)
    check_true(False, "DP > price should fail")
except: check_true(True, "DP > price rejected")

fin = FinancialInput(monthly_income=100000, liquid_savings=0, monthly_expenses=0)
check_close(fin.monthly_expenses, 40000, 1, "Auto-default expenses 40%")

print("\n=== LLM JSON PARSING ===")
from backend.llm.client import LLMClient
check_true(LLMClient.parse_json('{"verdict":"safe"}').get("verdict")=="safe", "Clean JSON")
check_true(LLMClient.parse_json('```json\n{"verdict":"risky"}\n```').get("verdict")=="risky", "Fenced JSON")
check_true("error" in LLMClient.parse_json("not json"), "Invalid JSON handled")

print("\n=== E2E PIPELINE ===")
async def e2e():
    if not os.getenv("GROQ_API_KEY"):
        print("  SKIP: Set GROQ_API_KEY to run E2E test")
        return
    from backend.agents.pipeline import run_analysis
    report = await run_analysis({
        "financial": {"monthly_income":120000,"employment_type":"salaried","years_in_current_job":3,
                      "expected_annual_growth_pct":8,"existing_emis":5000,"monthly_expenses":45000,
                      "current_rent":25000,"liquid_savings":2000000,"other_investments":500000,
                      "dependents":1,"spouse_income":0,"financial_notes":""},
        "property": {"property_price":8500000,"location_area":"Andheri West","location_city":"Mumbai",
                     "configuration":"2BHK","carpet_area_sqft":650,"is_ready_to_move":True,
                     "is_rera_registered":True,"builder_name":"","possession_date":"",
                     "down_payment_available":1700000,"loan_tenure_years":20,"expected_interest_rate":8.5,
                     "buyer_gender":"male","is_first_property":True,"property_notes":""}})
    check_true(report["verdict"] in ("safe","risky","reconsider"), f"Valid verdict: {report['verdict']}")
    check_true("computed_numbers" in report, "Has computed numbers")
    check_true("stress_scenarios" in report, "Has stress scenarios")
    print(f"  VERDICT: {report['verdict'].upper()} | CONFIDENCE: {report.get('confidence_score')}/10")
    print(f"  TIME: {report['_meta']['pipeline_time_seconds']}s")

asyncio.run(e2e())

print(f"\n{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed")
print('='*50)
if failed: sys.exit(1)
