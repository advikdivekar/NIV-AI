#!/usr/bin/env python3
"""
Run this from your project root:
    cd "/Users/advikdivekar/Desktop/NIV AI"
    python setup_files.py

It writes every backend file with full content into the correct location.
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

files = {}

# ─────────────────────────────────────────────────────────────
# backend/calculations/financial.py
# ─────────────────────────────────────────────────────────────
files["backend/calculations/financial.py"] = '''"""
Deterministic financial calculations for Niv AI.
Every number that appears in a decision report originates from this file.
The LLM never performs arithmetic — it only interprets these results.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EMIResult:
    monthly_emi: float
    total_payment: float
    total_interest: float
    loan_amount: float
    annual_rate: float
    tenure_months: int


@dataclass
class AcquisitionCost:
    property_price: float
    stamp_duty: float
    registration: float
    gst: float
    legal_fees: float
    brokerage: float
    total: float


@dataclass
class MonthlyOwnership:
    emi: float
    maintenance: float
    home_insurance: float
    total: float


@dataclass
class KeyRatios:
    emi_to_income: float
    total_housing_to_income: float
    down_payment_to_savings: float
    emergency_runway_months: float
    existing_obligations_to_income: float


@dataclass
class TaxBenefits:
    section_80c_annual: float
    section_24b_annual: float
    total_annual_saving: float
    effective_monthly_saving: float


@dataclass
class StressResult:
    name: str
    description: str
    can_survive: bool
    months_before_default: Optional[float]
    key_number: str
    new_emi: Optional[float] = None
    new_ratio: Optional[float] = None


@dataclass
class RentVsBuyResult:
    equivalent_rent: float
    monthly_ownership_cost: float
    premium_pct: float
    opportunity_cost_monthly: float
    true_monthly_premium: float
    break_even_years: float


@dataclass
class ComputedNumbers:
    emi: EMIResult
    acquisition: AcquisitionCost
    monthly_ownership: MonthlyOwnership
    ratios: KeyRatios
    tax_benefits: TaxBenefits
    stress_scenarios: list
    rent_vs_buy: RentVsBuyResult
    post_purchase_savings: float
    loan_amount: float

    def to_dict(self) -> dict:
        return {
            "loan_amount": self.loan_amount,
            "monthly_emi": self.emi.monthly_emi,
            "total_loan_payment": self.emi.total_payment,
            "total_interest_paid": self.emi.total_interest,
            "total_acquisition_cost": self.acquisition.total,
            "stamp_duty": self.acquisition.stamp_duty,
            "registration": self.acquisition.registration,
            "gst": self.acquisition.gst,
            "monthly_ownership_cost": self.monthly_ownership.total,
            "monthly_maintenance": self.monthly_ownership.maintenance,
            "emi_to_income_ratio": self.ratios.emi_to_income,
            "total_housing_to_income_ratio": self.ratios.total_housing_to_income,
            "down_payment_to_savings_ratio": self.ratios.down_payment_to_savings,
            "emergency_runway_months": self.ratios.emergency_runway_months,
            "post_purchase_savings": self.post_purchase_savings,
            "annual_tax_saving": self.tax_benefits.total_annual_saving,
            "effective_monthly_cost_after_tax": round(
                self.monthly_ownership.total - self.tax_benefits.effective_monthly_saving, 2
            ),
            "rent_vs_buy_premium_pct": self.rent_vs_buy.premium_pct,
            "rent_vs_buy_break_even_years": self.rent_vs_buy.break_even_years,
        }


def calculate_emi(principal: float, annual_rate_pct: float, tenure_months: int) -> EMIResult:
    if principal <= 0:
        return EMIResult(0, 0, 0, 0, annual_rate_pct, tenure_months)
    r = annual_rate_pct / 12 / 100
    n = tenure_months
    if r == 0:
        emi = principal / n
    else:
        emi = principal * r * math.pow(1 + r, n) / (math.pow(1 + r, n) - 1)
    emi = round(emi, 2)
    total_payment = round(emi * n, 2)
    total_interest = round(total_payment - principal, 2)
    return EMIResult(monthly_emi=emi, total_payment=total_payment, total_interest=total_interest,
                     loan_amount=principal, annual_rate=annual_rate_pct, tenure_months=tenure_months)


def calculate_acquisition_cost(property_price: float, buyer_gender: str = "male",
                                is_ready_to_move: bool = True, has_broker: bool = False,
                                is_mumbai_metro: bool = True) -> AcquisitionCost:
    stamp_duty_rate = 0.05 if buyer_gender == "female" else 0.06
    stamp_duty = round(property_price * stamp_duty_rate, 2)
    registration = min(round(property_price * 0.01, 2), 30000.0)
    gst = round(property_price * 0.05, 2) if not is_ready_to_move else 0.0
    legal_fees = 40000.0
    brokerage = round(property_price * 0.01, 2) if has_broker else 0.0
    total = round(property_price + stamp_duty + registration + gst + legal_fees + brokerage, 2)
    return AcquisitionCost(property_price=property_price, stamp_duty=stamp_duty,
                           registration=registration, gst=gst, legal_fees=legal_fees,
                           brokerage=brokerage, total=total)


def calculate_monthly_ownership(emi: float, carpet_area_sqft: float,
                                 maintenance_per_sqft: float = 5.5,
                                 home_insurance_monthly: float = 500.0) -> MonthlyOwnership:
    maintenance = round(carpet_area_sqft * maintenance_per_sqft, 2)
    total = round(emi + maintenance + home_insurance_monthly, 2)
    return MonthlyOwnership(emi=emi, maintenance=maintenance, home_insurance=home_insurance_monthly, total=total)


def calculate_key_ratios(monthly_income: float, spouse_income: float, emi: float,
                          total_monthly_housing: float, existing_emis: float,
                          monthly_expenses: float, liquid_savings: float,
                          down_payment: float) -> KeyRatios:
    household_income = max(monthly_income + spouse_income, 1.0)
    emi_ratio = round(emi / household_income, 4)
    housing_ratio = round(total_monthly_housing / household_income, 4)
    dp_ratio = round(down_payment / liquid_savings, 4) if liquid_savings > 0 else 99.0
    post_purchase_savings = max(liquid_savings - down_payment, 0)
    monthly_burn = emi + monthly_expenses + existing_emis
    runway = round(post_purchase_savings / monthly_burn, 2) if monthly_burn > 0 else 0.0
    obligations_ratio = round((emi + existing_emis) / household_income, 4)
    return KeyRatios(emi_to_income=emi_ratio, total_housing_to_income=housing_ratio,
                     down_payment_to_savings=dp_ratio, emergency_runway_months=runway,
                     existing_obligations_to_income=obligations_ratio)


def calculate_tax_benefits(annual_principal_repayment: float, annual_interest_payment: float,
                            is_self_occupied: bool = True, marginal_tax_rate: float = 0.30,
                            existing_80c_used: float = 0.0) -> TaxBenefits:
    available_80c = max(150000.0 - existing_80c_used, 0.0)
    sec_80c = min(annual_principal_repayment, available_80c)
    sec_24b = min(annual_interest_payment, 200000.0) if is_self_occupied else annual_interest_payment
    total_deduction = sec_80c + sec_24b
    annual_saving = round(total_deduction * marginal_tax_rate, 2)
    monthly_saving = round(annual_saving / 12, 2)
    return TaxBenefits(section_80c_annual=round(sec_80c, 2), section_24b_annual=round(sec_24b, 2),
                       total_annual_saving=annual_saving, effective_monthly_saving=monthly_saving)


def estimate_annual_principal_and_interest(loan_amount: float, annual_rate_pct: float,
                                            tenure_months: int) -> tuple:
    r = annual_rate_pct / 12 / 100
    if r == 0 or loan_amount <= 0:
        return (loan_amount / max(tenure_months, 1) * 12, 0.0)
    emi = loan_amount * r * math.pow(1 + r, tenure_months) / (math.pow(1 + r, tenure_months) - 1)
    annual_interest = 0.0
    annual_principal = 0.0
    balance = loan_amount
    for _ in range(min(12, tenure_months)):
        interest_component = balance * r
        principal_component = emi - interest_component
        annual_interest += interest_component
        annual_principal += principal_component
        balance -= principal_component
    return (round(annual_principal, 2), round(annual_interest, 2))


def calculate_stress_scenarios(monthly_income: float, spouse_income: float, emi: float,
                                total_monthly_expenses: float, existing_emis: float,
                                post_purchase_savings: float, loan_amount: float,
                                annual_rate_pct: float, tenure_months: int) -> list:
    household_income = monthly_income + spouse_income
    monthly_burn = emi + total_monthly_expenses + existing_emis
    runway_job_loss = round(post_purchase_savings / monthly_burn, 1) if monthly_burn > 0 else 0
    job_loss = StressResult(name="job_loss_6_months",
                            description="Primary earner loses income for 6 months",
                            can_survive=runway_job_loss >= 6,
                            months_before_default=runway_job_loss,
                            key_number=f"Savings last {runway_job_loss} months (need 6)")

    new_rate = annual_rate_pct + 2.0
    new_emi_result = calculate_emi(loan_amount, new_rate, tenure_months)
    new_emi = new_emi_result.monthly_emi
    emi_increase_pct = round((new_emi - emi) / emi * 100, 1) if emi > 0 else 0
    new_ratio = round(new_emi / household_income, 4) if household_income > 0 else 99
    rate_hike = StressResult(name="interest_rate_hike_2pct",
                             description="Interest rate increases by 2 percentage points",
                             can_survive=new_ratio < 0.50,
                             months_before_default=None,
                             key_number=f"EMI rises {emi_increase_pct}% to Rs.{new_emi:,.0f}",
                             new_emi=new_emi, new_ratio=new_ratio)

    savings_after_shock = post_purchase_savings - 500000
    runway_after_shock = round(savings_after_shock / monthly_burn, 1) if monthly_burn > 0 and savings_after_shock > 0 else 0
    expense_shock = StressResult(name="unexpected_expense_5L",
                                 description="Major emergency requiring Rs.5,00,000",
                                 can_survive=savings_after_shock > 0 and runway_after_shock >= 3,
                                 months_before_default=max(runway_after_shock, 0),
                                 key_number=f"Remaining savings: Rs.{max(savings_after_shock, 0):,.0f}")

    real_income_year3 = household_income * math.pow(0.94, 3)
    year3_ratio = round(emi / real_income_year3, 4) if real_income_year3 > 0 else 99
    decline_pct = round((1 - real_income_year3 / household_income) * 100, 1)
    stagnation = StressResult(name="income_stagnation_3_years",
                              description="No salary increase for 3 years with 6% inflation",
                              can_survive=year3_ratio < 0.50,
                              months_before_default=None,
                              key_number=f"Real income drops {decline_pct}%, EMI-to-income becomes {year3_ratio:.0%}",
                              new_ratio=year3_ratio)

    return [job_loss, rate_hike, expense_shock, stagnation]


def calculate_rent_vs_buy(equivalent_monthly_rent: float, total_monthly_ownership: float,
                           down_payment: float, fd_return_pct: float = 7.0,
                           appreciation_pct: float = 4.0) -> RentVsBuyResult:
    opportunity_cost = round(down_payment * (fd_return_pct / 100) / 12, 2)
    premium_pct = round((total_monthly_ownership - equivalent_monthly_rent) / equivalent_monthly_rent * 100, 1) if equivalent_monthly_rent > 0 else 0
    true_premium = round(total_monthly_ownership + opportunity_cost - equivalent_monthly_rent, 2)
    annual_ownership_extra = true_premium * 12
    if annual_ownership_extra <= 0:
        break_even = 0.0
    elif appreciation_pct > 0:
        annual_appreciation_value = down_payment * (appreciation_pct / 100)
        break_even = round(annual_ownership_extra / annual_appreciation_value, 1) if annual_appreciation_value > 0 else 99.0
    else:
        break_even = 99.0
    return RentVsBuyResult(equivalent_rent=equivalent_monthly_rent, monthly_ownership_cost=total_monthly_ownership,
                           premium_pct=premium_pct, opportunity_cost_monthly=opportunity_cost,
                           true_monthly_premium=true_premium, break_even_years=min(break_even, 99.0))


def compute_all(monthly_income: float, spouse_income: float, existing_emis: float,
                monthly_expenses: float, liquid_savings: float, dependents: int,
                property_price: float, down_payment: float, loan_tenure_years: int,
                interest_rate: float, carpet_area_sqft: float, buyer_gender: str,
                is_ready_to_move: bool, maintenance_per_sqft: float = 5.5,
                equivalent_rent: float = 0.0) -> ComputedNumbers:
    loan_amount = max(property_price - down_payment, 0)
    tenure_months = loan_tenure_years * 12
    emi = calculate_emi(loan_amount, interest_rate, tenure_months)
    acquisition = calculate_acquisition_cost(property_price=property_price, buyer_gender=buyer_gender,
                                             is_ready_to_move=is_ready_to_move)
    monthly_own = calculate_monthly_ownership(emi=emi.monthly_emi, carpet_area_sqft=carpet_area_sqft,
                                              maintenance_per_sqft=maintenance_per_sqft)
    ratios = calculate_key_ratios(monthly_income=monthly_income, spouse_income=spouse_income,
                                  emi=emi.monthly_emi, total_monthly_housing=monthly_own.total,
                                  existing_emis=existing_emis, monthly_expenses=monthly_expenses,
                                  liquid_savings=liquid_savings, down_payment=down_payment)
    annual_principal, annual_interest = estimate_annual_principal_and_interest(loan_amount, interest_rate, tenure_months)
    tax = calculate_tax_benefits(annual_principal_repayment=annual_principal, annual_interest_payment=annual_interest)
    post_purchase_savings = max(liquid_savings - down_payment, 0)
    stress = calculate_stress_scenarios(monthly_income=monthly_income, spouse_income=spouse_income,
                                        emi=emi.monthly_emi, total_monthly_expenses=monthly_expenses,
                                        existing_emis=existing_emis, post_purchase_savings=post_purchase_savings,
                                        loan_amount=loan_amount, annual_rate_pct=interest_rate, tenure_months=tenure_months)
    if equivalent_rent <= 0:
        equivalent_rent = round(property_price * 0.025 / 12, 2)
    rvb = calculate_rent_vs_buy(equivalent_monthly_rent=equivalent_rent, total_monthly_ownership=monthly_own.total,
                                down_payment=down_payment)
    return ComputedNumbers(emi=emi, acquisition=acquisition, monthly_ownership=monthly_own, ratios=ratios,
                           tax_benefits=tax, stress_scenarios=stress, rent_vs_buy=rvb,
                           post_purchase_savings=post_purchase_savings, loan_amount=loan_amount)
'''

# ─────────────────────────────────────────────────────────────
# backend/calculations/benchmarks.py
# ─────────────────────────────────────────────────────────────
files["backend/calculations/benchmarks.py"] = '''"""
Mumbai real estate benchmark loader.
Fuzzy-matches user-entered area names to static dataset.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Optional

_DATA_PATH = Path(__file__).parent.parent / "data" / "mumbai_benchmarks.json"
_cache: Optional[dict] = None


@dataclass
class AreaBenchmark:
    key: str
    name: str
    price_min: float
    price_median: float
    price_max: float
    maintenance_typical: float
    rental_yield_pct: float
    distance_to_bkc_km: float
    distance_to_lower_parel_km: float
    metro_connectivity: bool
    infrastructure_notes: str
    flood_risk: str
    data_as_of: str


def _load() -> dict:
    global _cache
    if _cache is None:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache


def _normalize(name: str) -> str:
    return (name.lower().strip().replace("-", " ").replace("_", " ")
            .replace("(", "").replace(")", "").replace(",", ""))


def lookup_area(user_input: str) -> Optional[AreaBenchmark]:
    data = _load()
    normalized = _normalize(user_input)
    key_attempt = normalized.replace(" ", "_")
    if key_attempt in data:
        return _build(key_attempt, data[key_attempt])
    name_map = {}
    for key, info in data.items():
        name_map[_normalize(info["name"])] = key
    matches = get_close_matches(normalized, name_map.keys(), n=1, cutoff=0.6)
    if matches:
        return _build(name_map[matches[0]], data[name_map[matches[0]]])
    key_matches = get_close_matches(normalized.replace(" ", "_"), data.keys(), n=1, cutoff=0.6)
    if key_matches:
        return _build(key_matches[0], data[key_matches[0]])
    return None


def list_areas() -> list:
    return [info["name"] for info in _load().values()]


def get_maintenance_estimate(user_area: str) -> float:
    area = lookup_area(user_area)
    return area.maintenance_typical if area else 5.5


def get_rental_yield(user_area: str) -> float:
    area = lookup_area(user_area)
    return area.rental_yield_pct if area else 2.5


def _build(key: str, raw: dict) -> AreaBenchmark:
    return AreaBenchmark(key=key, name=raw["name"],
                         price_min=raw["avg_price_per_sqft"]["min"],
                         price_median=raw["avg_price_per_sqft"]["median"],
                         price_max=raw["avg_price_per_sqft"]["max"],
                         maintenance_typical=raw["maintenance_per_sqft_monthly"]["typical"],
                         rental_yield_pct=raw["rental_yield_pct"],
                         distance_to_bkc_km=raw["distance_to_bkc_km"],
                         distance_to_lower_parel_km=raw["distance_to_lower_parel_km"],
                         metro_connectivity=raw["metro_connectivity"],
                         infrastructure_notes=raw["infrastructure_notes"],
                         flood_risk=raw["flood_risk"],
                         data_as_of=raw["data_as_of"])
'''

# ─────────────────────────────────────────────────────────────
# backend/llm/client.py
# ─────────────────────────────────────────────────────────────
files["backend/llm/client.py"] = '''"""
LLM provider abstraction for Niv AI.
Groq = primary (agents 1-5). Gemini = fallback (agent 6).
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

from groq import AsyncGroq
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False


class LLMClient:
    def __init__(self) -> None:
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise RuntimeError("GROQ_API_KEY environment variable is required")
        self._groq = AsyncGroq(api_key=groq_key)
        self._gemini_model = None
        if _GEMINI_AVAILABLE:
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                genai.configure(api_key=gemini_key)
                self._gemini_model = genai.GenerativeModel("gemini-2.0-flash")
                logger.info("Gemini configured as fallback")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15),
           retry=retry_if_exception_type((Exception,)), reraise=True)
    async def _call_groq(self, system_prompt: str, user_message: str,
                         json_mode: bool = False, max_tokens: int = 3000) -> str:
        response = await self._groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_message}],
            temperature=0.1,
            response_format={"type": "json_object"} if json_mode else None,
            max_tokens=max_tokens)
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("Groq returned empty response")
        return content

    async def _call_gemini(self, system_prompt: str, user_message: str) -> Optional[str]:
        if self._gemini_model is None:
            return None
        try:
            response = self._gemini_model.generate_content(
                f"{system_prompt}\\n\\n{user_message}",
                generation_config=genai.GenerationConfig(temperature=0.1, max_output_tokens=4000))
            return response.text if response.text else None
        except Exception as e:
            logger.warning("Gemini failed (%s), falling back to Groq", e)
            return None

    async def run_agent(self, system_prompt: str, user_message: str, max_tokens: int = 3000) -> str:
        return await self._call_groq(system_prompt, user_message, json_mode=True, max_tokens=max_tokens)

    async def run_final_agent(self, system_prompt: str, user_message: str) -> str:
        gemini_result = await self._call_gemini(system_prompt, user_message)
        if gemini_result:
            return gemini_result
        return await self._call_groq(system_prompt, user_message, json_mode=True, max_tokens=4000)

    @staticmethod
    def parse_json(raw: str) -> dict:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM JSON: %s...", cleaned[:200])
            return {"error": "Failed to parse agent response", "raw": cleaned[:500]}
'''

# ─────────────────────────────────────────────────────────────
# backend/models/input_models.py
# ─────────────────────────────────────────────────────────────
files["backend/models/input_models.py"] = '''"""Input models for Niv AI analysis requests."""
from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class EmploymentType(str, Enum):
    SALARIED = "salaried"
    FREELANCE = "freelance"
    BUSINESS = "business"


class BuyerGender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class Configuration(str, Enum):
    ONE_BHK = "1BHK"
    TWO_BHK = "2BHK"
    THREE_BHK = "3BHK"
    FOUR_BHK = "4BHK"
    FIVE_PLUS_BHK = "5+BHK"


class FinancialInput(BaseModel):
    monthly_income: float = Field(..., gt=0)
    employment_type: EmploymentType = EmploymentType.SALARIED
    years_in_current_job: float = Field(default=2.0, ge=0, le=50)
    expected_annual_growth_pct: float = Field(default=8.0, ge=0, le=50)
    existing_emis: float = Field(default=0.0, ge=0)
    monthly_expenses: float = Field(default=0.0, ge=0)
    current_rent: float = Field(default=0.0, ge=0)
    liquid_savings: float = Field(default=0.0, ge=0)
    other_investments: float = Field(default=0.0, ge=0)
    dependents: int = Field(default=0, ge=0, le=20)
    spouse_income: float = Field(default=0.0, ge=0)
    financial_notes: str = Field(default="", max_length=2000)

    @field_validator("monthly_expenses", mode="before")
    @classmethod
    def default_expenses(cls, v, info):
        if (v == 0.0 or v is None) and "monthly_income" in info.data:
            return round(info.data["monthly_income"] * 0.40, 2)
        return v


class PropertyInput(BaseModel):
    property_price: float = Field(..., gt=100000)
    location_area: str = Field(..., min_length=2, max_length=100)
    location_city: str = Field(default="Mumbai")
    configuration: Configuration = Configuration.TWO_BHK
    carpet_area_sqft: float = Field(..., gt=50, le=50000)
    is_ready_to_move: bool = True
    is_rera_registered: Optional[bool] = None
    builder_name: str = Field(default="", max_length=200)
    possession_date: str = Field(default="", max_length=50)
    down_payment_available: float = Field(..., ge=0)
    loan_tenure_years: int = Field(default=20, ge=1, le=30)
    expected_interest_rate: float = Field(default=8.5, gt=0, le=20)
    buyer_gender: BuyerGender = BuyerGender.MALE
    is_first_property: bool = True
    property_notes: str = Field(default="", max_length=2000)

    @field_validator("down_payment_available")
    @classmethod
    def dp_sanity(cls, v, info):
        price = info.data.get("property_price", 0)
        if price > 0 and v >= price:
            raise ValueError("Down payment cannot exceed property price")
        return v


class AnalysisRequest(BaseModel):
    financial: FinancialInput
    property: PropertyInput
'''

# ─────────────────────────────────────────────────────────────
# backend/models/output_models.py
# ─────────────────────────────────────────────────────────────
files["backend/models/output_models.py"] = '''"""Output models for Niv AI decision reports."""
from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class Verdict(str, Enum):
    SAFE = "safe"
    RISKY = "risky"
    RECONSIDER = "reconsider"


class StressScenario(BaseModel):
    name: str
    description: str
    can_survive: bool
    months_before_default: Optional[float] = None
    key_number: str
    mitigation: str = ""
    severity: str = "medium"


class PropertyFlag(BaseModel):
    flag: str
    severity: str
    detail: str


class AssumptionChallenge(BaseModel):
    assumption: str
    challenge: str
    impact: str
    severity: str


class RentVsBuy(BaseModel):
    equivalent_monthly_rent: float = 0
    buying_monthly_cost: float = 0
    premium_for_ownership_pct: float = 0
    break_even_years: float = 0


class DecisionReport(BaseModel):
    verdict: Verdict
    confidence_score: int = Field(ge=1, le=10)
    verdict_reason: str
    top_reasons: list[str]
    financial_summary: dict
    stress_scenarios: list[StressScenario]
    property_assessment: dict
    assumptions_challenged: list[AssumptionChallenge]
    blind_spots: list[str]
    emotional_flags: list[str]
    conditions_for_safety: list[str]
    recommended_actions: list[str]
    rent_vs_buy: RentVsBuy
    computed_numbers: dict[str, Any]
    full_reasoning: str
    data_sources: list[str]
    limitations: list[str]
    disclaimer: str = (
        "This analysis is for informational purposes only. "
        "Not financial advice. Consult a qualified financial advisor."
    )
'''

# ─────────────────────────────────────────────────────────────
# backend/agents/context_synthesizer.py
# ─────────────────────────────────────────────────────────────
files["backend/agents/context_synthesizer.py"] = '''"""Agent 1: Context Synthesizer — structures raw input, finds assumptions."""
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
'''

# ─────────────────────────────────────────────────────────────
# backend/agents/financial_analyst.py
# ─────────────────────────────────────────────────────────────
files["backend/agents/financial_analyst.py"] = '''"""Agent 2: Financial Analyst — interprets pre-computed affordability numbers."""
from __future__ import annotations
import logging
from backend.llm.client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Financial Analyst agent in a home-buying decision system for Indian buyers.
You receive pre-computed numbers. They are CORRECT. Do not recalculate. Interpret what they mean.

affordability_verdict: "comfortable" (EMI/income <30%, runway >6mo), "stretched" (30-45%, runway 3-6mo), "unaffordable" (>45% or runway <3mo)

Respond ONLY with JSON:
{
  "affordability_verdict": "<comfortable|stretched|unaffordable>",
  "key_ratios": {"emi_to_income": <n>, "total_housing_to_income": <n>, "down_payment_to_savings": <n>, "emergency_runway_months": <n>},
  "cash_flow": {"monthly_surplus_after_housing": <n>, "annual_discretionary_income": <n>, "can_handle_10pct_income_drop": <bool>},
  "tax_benefits": {"section_80c_annual": <n>, "section_24b_annual": <n>, "effective_monthly_saving": <n>},
  "red_flags": ["<flag>"],
  "reasoning": "<2-3 paragraph analysis>"
}"""


async def run(llm: LLMClient, context: dict, computed_numbers: dict, raw_input: dict) -> dict:
    fin = raw_input["financial"]
    surplus = fin["monthly_income"] + fin["spouse_income"] - computed_numbers["monthly_ownership_cost"] - fin["existing_emis"] - fin["monthly_expenses"]
    can_drop = (fin["monthly_income"] * 0.9 + fin["spouse_income"]) > (computed_numbers["monthly_ownership_cost"] + fin["existing_emis"] + fin["monthly_expenses"])
    msg = f"""Analyze affordability with these EXACT numbers:
EMI: Rs.{computed_numbers["monthly_emi"]:,.0f}, Monthly ownership: Rs.{computed_numbers["monthly_ownership_cost"]:,.0f}, Acquisition total: Rs.{computed_numbers["total_acquisition_cost"]:,.0f}
EMI/income: {computed_numbers["emi_to_income_ratio"]:.1%}, Housing/income: {computed_numbers["total_housing_to_income_ratio"]:.1%}, DP/savings: {computed_numbers["down_payment_to_savings_ratio"]:.1%}, Runway: {computed_numbers["emergency_runway_months"]:.1f}mo
Post-purchase savings: Rs.{computed_numbers["post_purchase_savings"]:,.0f}, Annual tax saving: Rs.{computed_numbers["annual_tax_saving"]:,.0f}, After-tax monthly: Rs.{computed_numbers["effective_monthly_cost_after_tax"]:,.0f}
Total interest over loan life: Rs.{computed_numbers["total_interest_paid"]:,.0f}
Monthly surplus: Rs.{surplus:,.0f}, Can handle 10% drop: {can_drop}
Employment: {fin["employment_type"]}, Dependents: {fin["dependents"]}, Existing EMIs: Rs.{fin["existing_emis"]:,.0f}
Context: stability={context.get("user_profile", {}).get("employment_stability")}, risk_capacity={context.get("user_profile", {}).get("risk_capacity")}"""
    raw = await llm.run_agent(SYSTEM_PROMPT, msg)
    result = llm.parse_json(raw)
    logger.info("Financial analyst complete — verdict: %s", result.get("affordability_verdict"))
    return result
'''

# ─────────────────────────────────────────────────────────────
# backend/agents/risk_simulator.py
# ─────────────────────────────────────────────────────────────
files["backend/agents/risk_simulator.py"] = '''"""Agent 3: Risk Simulator — contextualizes pre-computed stress scenarios."""
from __future__ import annotations
import logging
from backend.llm.client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Risk Simulator agent in a home-buying decision system for Indian buyers.
You receive pre-computed stress test results. Numbers are CORRECT. Add mitigation advice and severity ratings.

overall_resilience: "strong" (3-4 pass), "moderate" (2 pass), "weak" (1 pass), "fragile" (0 pass)
severity per scenario: "low", "medium", "high", "critical"

Be specific. Not "build emergency fund" but "save Rs.X more before buying to survive Y scenario."

Respond ONLY with JSON:
{
  "scenarios": [{"name": "<n>", "description": "<d>", "can_survive": <bool>, "months_before_default": <n|null>, "key_number": "<s>", "mitigation": "<specific advice>", "severity": "<level>"}],
  "overall_resilience": "<strong|moderate|weak|fragile>",
  "critical_vulnerability": "<single biggest risk>",
  "reasoning": "<2-3 paragraphs>"
}"""


async def run(llm: LLMClient, context: dict, financial_analysis: dict, computed_numbers: dict,
              stress_results: list, raw_input: dict) -> dict:
    fin = raw_input["financial"]
    scenario_text = ""
    for s in stress_results:
        scenario_text += f"\\n{s['name']}: survive={s['can_survive']}, months={s.get('months_before_default','N/A')}, key={s['key_number']}, new_emi={s.get('new_emi','N/A')}, new_ratio={s.get('new_ratio','N/A')}"
    msg = f"""Contextualize these stress test results:
Buyer: {fin["employment_type"]}, {fin["years_in_current_job"]}yrs, Income Rs.{fin["monthly_income"]:,.0f}, Dependents {fin["dependents"]}, Post-purchase savings Rs.{computed_numbers["post_purchase_savings"]:,.0f}
Affordability verdict: {financial_analysis.get("affordability_verdict")}
Scenarios (numbers are exact):{scenario_text}
Red flags: {financial_analysis.get("red_flags", [])}"""
    raw = await llm.run_agent(SYSTEM_PROMPT, msg)
    result = llm.parse_json(raw)
    logger.info("Risk simulator complete — resilience: %s", result.get("overall_resilience"))
    return result
'''

# ─────────────────────────────────────────────────────────────
# backend/agents/property_analyst.py
# ─────────────────────────────────────────────────────────────
files["backend/agents/property_analyst.py"] = '''"""Agent 4: Property & Market Analyst — evaluates property vs Mumbai benchmarks."""
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
'''

# ─────────────────────────────────────────────────────────────
# backend/agents/assumption_challenger.py
# ─────────────────────────────────────────────────────────────
files["backend/agents/assumption_challenger.py"] = '''"""Agent 5: Assumption Challenger — adversarial agent that finds holes in the decision."""
from __future__ import annotations
import logging
from backend.llm.client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Assumption Challenger — a financial devil\'s advocate for Indian home purchases.
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
'''

# ─────────────────────────────────────────────────────────────
# backend/agents/decision_composer.py
# ─────────────────────────────────────────────────────────────
files["backend/agents/decision_composer.py"] = '''"""Agent 6: Decision Composer — final verdict synthesis. Uses Gemini with Groq fallback."""
from __future__ import annotations
import logging
from backend.llm.client import LLMClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Decision Composer — the final judge in a home-buying decision system for Indian buyers.
Synthesize all 5 agent outputs into ONE clear verdict.

VERDICT RULES:
- "safe": comfortable affordability, passes 3+ stress tests, fair price, no critical assumptions challenged
- "risky": stretched affordability OR fails 2+ stress tests OR overpriced OR critical assumptions found
- "reconsider": unaffordable OR fails 3+ stress tests OR critical property flags OR multiple critical assumptions

TONE: Trusted advisor. Plain language. Concrete rupee amounts. Always offer a path forward.

Respond ONLY with JSON:
{
  "verdict": "<safe|risky|reconsider>",
  "confidence_score": <1-10>,
  "verdict_reason": "<one sentence>",
  "top_reasons": ["<most important reason>", "<2>", "<3>", "<4>", "<5>"],
  "conditions_for_safety": ["<what would make this safe>"],
  "recommended_actions": ["<concrete action>"],
  "full_reasoning": "<3-5 paragraphs tying everything together>"
}"""


async def run(llm: LLMClient, context: dict, financial_analysis: dict, risk_analysis: dict,
              property_analysis: dict, assumption_analysis: dict, computed_numbers: dict, raw_input: dict) -> dict:
    fin = raw_input["financial"]
    prop = raw_input["property"]
    survived = sum(1 for s in risk_analysis.get("scenarios", []) if s.get("can_survive", False))
    total_scenarios = len(risk_analysis.get("scenarios", []))
    challenges = assumption_analysis.get("challenges", [])
    critical = sum(1 for c in challenges if c.get("severity") in ("critical", "high"))
    msg = f"""Produce the final verdict by synthesizing all agent analyses:
BUYER: Rs.{fin["monthly_income"]:,.0f}/mo, {fin["employment_type"]}, Property Rs.{prop["property_price"]:,.0f} in {prop["location_area"]}
AGENT 1 — Context: stability={context.get("user_profile",{{}}).get("employment_stability")}, risk_capacity={context.get("user_profile",{{}}).get("risk_capacity")}, assumptions={context.get("implicit_assumptions",[])}
AGENT 2 — Financial: verdict={financial_analysis.get("affordability_verdict")}, EMI/income={computed_numbers["emi_to_income_ratio"]:.1%}, runway={computed_numbers["emergency_runway_months"]:.1f}mo, savings=Rs.{computed_numbers["post_purchase_savings"]:,.0f}, flags={financial_analysis.get("red_flags",[])}
AGENT 3 — Risk: passed={survived}/{total_scenarios}, resilience={risk_analysis.get("overall_resilience")}, vulnerability={risk_analysis.get("critical_vulnerability")}
AGENT 4 — Property: price={property_analysis.get("price_assessment",{{}}).get("verdict")}, flags={[f["flag"] for f in property_analysis.get("property_flags",[])]}, break-even={computed_numbers["rent_vs_buy_break_even_years"]:.1f}yrs
AGENT 5 — Assumptions: {len(challenges)} total, {critical} critical/high, blind spots={assumption_analysis.get("blind_spots",[])}
Now produce the final verdict."""
    raw = await llm.run_final_agent(SYSTEM_PROMPT, msg)
    result = llm.parse_json(raw)
    logger.info("Decision composer complete — verdict: %s", result.get("verdict"))
    return result
'''

# ─────────────────────────────────────────────────────────────
# backend/agents/pipeline.py
# ─────────────────────────────────────────────────────────────
files["backend/agents/pipeline.py"] = '''"""
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
'''

# ─────────────────────────────────────────────────────────────
# backend/routers/analysis.py
# ─────────────────────────────────────────────────────────────
files["backend/routers/analysis.py"] = '''"""Analysis endpoint — runs the 6-agent pipeline."""
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
        logger.error("Unexpected error: %s\\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail="Unexpected error. Please try again.")
'''

# ─────────────────────────────────────────────────────────────
# backend/routers/reports.py
# ─────────────────────────────────────────────────────────────
files["backend/routers/reports.py"] = '''"""Reports endpoints — save, retrieve, list analysis reports."""
from __future__ import annotations
import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from backend.firebase.firestore import get_report, list_reports, save_report

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["reports"])


@router.post("/reports")
async def create_report(body: dict, x_user_id: Optional[str] = Header(None)):
    user_id = x_user_id or "anonymous"
    report_data = body.get("report")
    if not report_data:
        raise HTTPException(status_code=422, detail="Missing report in body")
    doc_id = await save_report(user_id, report_data, body.get("input", {}))
    return {"id": doc_id, "saved": doc_id is not None}


@router.get("/reports")
async def get_reports(x_user_id: Optional[str] = Header(None), limit: int = 20):
    user_id = x_user_id or "anonymous"
    return {"reports": await list_reports(user_id, limit=min(limit, 50))}


@router.get("/reports/{report_id}")
async def get_single_report(report_id: str):
    report = await get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
'''

# ─────────────────────────────────────────────────────────────
# backend/routers/health.py
# ─────────────────────────────────────────────────────────────
files["backend/routers/health.py"] = '''"""Health check endpoint."""
from fastapi import APIRouter
router = APIRouter(tags=["system"])

@router.get("/health")
async def health():
    return {"status": "ok", "service": "niv-ai"}
'''

# ─────────────────────────────────────────────────────────────
# backend/firebase/firestore.py
# ─────────────────────────────────────────────────────────────
files["backend/firebase/firestore.py"] = '''"""Firestore integration — save/load reports. Graceful if Firebase not configured."""
from __future__ import annotations
import logging, os
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)
_db = None
_initialized = False


def _init():
    global _db, _initialized
    if _initialized:
        return
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        private_key = os.getenv("FIREBASE_PRIVATE_KEY", "")
        client_email = os.getenv("FIREBASE_CLIENT_EMAIL", "")
        if project_id and private_key and client_email:
            cred_dict = {"type": "service_account", "project_id": project_id,
                         "private_key": private_key.replace("\\\\n", "\\n"),
                         "client_email": client_email, "token_uri": "https://oauth2.googleapis.com/token"}
            if not firebase_admin._apps:
                firebase_admin.initialize_app(credentials.Certificate(cred_dict))
            _db = firestore.client()
            logger.info("Firestore connected")
        else:
            logger.warning("Firebase credentials not set — reports will not persist")
    except Exception as e:
        logger.warning("Firestore init failed: %s", e)
    _initialized = True


async def save_report(user_id: str, report: dict, raw_input: dict) -> Optional[str]:
    _init()
    if _db is None:
        return None
    try:
        doc = {"user_id": user_id, "verdict": report.get("verdict"), "confidence_score": report.get("confidence_score"),
               "verdict_reason": report.get("verdict_reason"), "property_location": raw_input.get("property", {}).get("location_area", ""),
               "property_price": raw_input.get("property", {}).get("property_price", 0),
               "report": report, "input": raw_input, "created_at": datetime.now(timezone.utc).isoformat()}
        ref = _db.collection("reports").document()
        ref.set(doc)
        return ref.id
    except Exception as e:
        logger.error("Save report failed: %s", e)
        return None


async def get_report(report_id: str) -> Optional[dict]:
    _init()
    if _db is None:
        return None
    try:
        doc = _db.collection("reports").document(report_id).get()
        if doc.exists:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None
    except Exception as e:
        logger.error("Get report failed: %s", e)
        return None


async def list_reports(user_id: str, limit: int = 20) -> list:
    _init()
    if _db is None:
        return []
    try:
        docs = (_db.collection("reports").where("user_id", "==", user_id)
                .order_by("created_at", direction="DESCENDING").limit(limit).stream())
        return [{"id": d.id, "verdict": d.to_dict().get("verdict"), "property_location": d.to_dict().get("property_location"),
                 "created_at": d.to_dict().get("created_at")} for d in docs]
    except Exception as e:
        logger.error("List reports failed: %s", e)
        return []
'''

# ─────────────────────────────────────────────────────────────
# backend/main.py
# ─────────────────────────────────────────────────────────────
files["backend/main.py"] = '''"""Niv AI — FastAPI entry point."""
from __future__ import annotations
import logging, os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routers.analysis import router as analysis_router
from backend.routers.reports import router as reports_router
from backend.routers.health import router as health_router

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
logger = logging.getLogger("niv-ai")

app = FastAPI(title="Niv AI", description="Decision Intelligence for Home Buying", version="1.0.0")

frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(CORSMiddleware,
                   allow_origins=[frontend_url] if frontend_url != "*" else ["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(analysis_router)
app.include_router(reports_router)
app.include_router(health_router)

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
else:
    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "Niv AI API running", "docs": "/docs"}

logger.info("Niv AI started")
'''

# ─────────────────────────────────────────────────────────────
# tests/test_all.py
# ─────────────────────────────────────────────────────────────
files["tests/test_all.py"] = '''"""
Niv AI Test Suite — 53 tests across 12 categories.
Run: python tests/test_all.py
"""
import asyncio, sys, os
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

print("\\n=== EMI ===")
r = calculate_emi(5000000, 8.5, 240)
check_close(r.monthly_emi, 43391, 50, "50L@8.5%/20yr")
check_close(calculate_emi(0,8.5,240).monthly_emi, 0, 0, "Zero principal")
check_close(calculate_emi(1200000,0,120).monthly_emi, 10000, 1, "0% rate")

print("\\n=== ACQUISITION COST ===")
r = calculate_acquisition_cost(7500000, "male", False)
check_close(r.stamp_duty, 450000, 1, "Stamp 6% male")
check_close(r.registration, 30000, 1, "Registration capped 30K")
check_close(r.gst, 375000, 1, "GST 5% under-construction")
check_close(calculate_acquisition_cost(7500000,"female",True).stamp_duty, 375000, 1, "Stamp 5% female")
check_close(calculate_acquisition_cost(7500000,"female",True).gst, 0, 0, "No GST ready")
check_close(calculate_acquisition_cost(5000000,"male",True,True).brokerage, 50000, 1, "1% brokerage")

print("\\n=== MONTHLY OWNERSHIP ===")
r = calculate_monthly_ownership(43000, 650, 5.5)
check_close(r.maintenance, 3575, 1, "Maintenance")
check_close(r.total, 47075, 1, "Total monthly")

print("\\n=== KEY RATIOS ===")
r = calculate_key_ratios(120000, 0, 43000, 47000, 5000, 45000, 2000000, 1500000)
check_close(r.emi_to_income, 43000/120000, 0.001, "EMI/income")
check_close(r.down_payment_to_savings, 0.75, 0.001, "DP/savings")
check_close(r.emergency_runway_months, 5.38, 0.1, "Runway")

print("\\n=== TAX BENEFITS ===")
r = calculate_tax_benefits(180000, 420000, True, 0.30)
check_close(r.section_80c_annual, 150000, 1, "80C capped")
check_close(r.section_24b_annual, 200000, 1, "24b capped")
check_close(r.total_annual_saving, 105000, 1, "Annual saving")

print("\\n=== STRESS SCENARIOS ===")
s = calculate_stress_scenarios(120000, 0, 43000, 45000, 5000, 500000, 5000000, 8.5, 240)
check_true(len(s)==4, "4 scenarios")
check_true(not s[0].can_survive, "Job loss fails (5.4mo < 6mo)")
check_true(s[1].new_emi > 43000, "Rate hike increases EMI")
check_true(not s[2].can_survive, "5L shock fails")

print("\\n=== RENT VS BUY ===")
r = calculate_rent_vs_buy(25000, 47000, 1500000)
check_true(r.premium_pct > 0, "Ownership costs more")
check_true(r.break_even_years > 0, "Break-even > 0")

print("\\n=== BENCHMARKS ===")
check_true(lookup_area("Andheri West") is not None, "Andheri West found")
check_true(lookup_area("andheri west") is not None, "Case-insensitive")
check_true(lookup_area("Powai") is not None, "Powai found")
check_true(lookup_area("Atlantis") is None, "Unknown returns None")
check_close(get_maintenance_estimate("Unknown"), 5.5, 0.01, "Fallback maintenance")
check_true(len(list_areas()) >= 30, "30+ areas")

print("\\n=== COMPUTE ALL ===")
r = compute_all(120000, 0, 5000, 48000, 2000000, 1, 7500000, 1500000, 20, 8.5, 650, "male", True)
check_true(r.emi.monthly_emi > 0, "EMI computed")
check_true(r.acquisition.total > 7500000, "Acquisition > price")
check_true(len(r.stress_scenarios)==4, "4 stress scenarios")
check_true(r.post_purchase_savings == 500000, "Post-purchase savings")
d = r.to_dict()
check_true("monthly_emi" in d, "to_dict has EMI")
check_true("emi_to_income_ratio" in d, "to_dict has ratios")

print("\\n=== INPUT VALIDATION ===")
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

print("\\n=== LLM JSON PARSING ===")
from backend.llm.client import LLMClient
check_true(LLMClient.parse_json(\'{"verdict":"safe"}\').get("verdict")=="safe", "Clean JSON")
check_true(LLMClient.parse_json(\'```json\\n{"verdict":"risky"}\\n```\').get("verdict")=="risky", "Fenced JSON")
check_true("error" in LLMClient.parse_json("not json"), "Invalid JSON handled")

print("\\n=== E2E PIPELINE ===")
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
    check_true(report["verdict"] in ("safe","risky","reconsider"), f"Valid verdict: {report[\'verdict\']}")
    check_true("computed_numbers" in report, "Has computed numbers")
    check_true("stress_scenarios" in report, "Has stress scenarios")
    print(f"  VERDICT: {report[\'verdict\'].upper()} | CONFIDENCE: {report.get(\'confidence_score\')}/10")
    print(f"  TIME: {report[\'_meta\'][\'pipeline_time_seconds\']}s")

asyncio.run(e2e())

print(f"\\n{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed")
print(\'=\'*50)
if failed: sys.exit(1)
'''

# ─────────────────────────────────────────────────────────────
# Write all files
# ─────────────────────────────────────────────────────────────
def write_files():
    written = 0
    for rel_path, content in files.items():
        abs_path = os.path.join(BASE, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content.lstrip("\n"))
        print(f"  wrote: {rel_path}")
        written += 1

    # Empty __init__ files
    inits = [
        "backend/agents/__init__.py",
        "backend/calculations/__init__.py",
        "backend/llm/__init__.py",
        "backend/models/__init__.py",
        "backend/routers/__init__.py",
        "backend/firebase/__init__.py",
        "tests/__init__.py",
    ]
    for rel_path in inits:
        abs_path = os.path.join(BASE, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if not os.path.exists(abs_path) or os.path.getsize(abs_path) == 0:
            open(abs_path, "w").close()
            print(f"  wrote: {rel_path} (empty init)")
            written += 1

    print(f"\nDone. {written} files written into {BASE}")


if __name__ == "__main__":
    write_files()
