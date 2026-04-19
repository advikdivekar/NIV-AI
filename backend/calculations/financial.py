"""
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
