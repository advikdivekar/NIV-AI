"""
Path to Safe Reverse Calculator — Deterministic binary search.

Given a user's financial situation that produces a "stretched" or "overextended"
verdict, this module calculates the exact rupee amounts needed to reach "safe"
status across three dimensions:

    1. Additional down payment needed (reduces loan → reduces EMI)
    2. Maximum safe property price at current down payment
    3. Minimum monthly income needed at current property price

"Safe" is defined as:
    - EMI-to-income ratio ≤ 0.35 (comfortable zone)
    - All 5 stress scenarios survivable

Pure math. Zero AI. Deterministic. Sub-5ms execution.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from schemas.schemas import UserInput, PathToSafeOutput
from agents.deterministic.financial_reality import calculate_affordability
from agents.deterministic.scenario_simulation import run_all_scenarios


def _is_safe(user_input: UserInput) -> bool:
    """
    Check if a given UserInput configuration is 'safe':
    EMI ≤ 35% of income AND all 5 stress scenarios survivable.
    """
    financial = calculate_affordability(user_input)
    if financial.emi_to_income_ratio > 0.35:
        return False
    scenarios = run_all_scenarios(user_input, financial)
    return scenarios.scenarios_survived == 5


def _make_modified_input(user_input: UserInput, **overrides) -> UserInput:
    """Create a copy of UserInput with specific field overrides."""
    data = user_input.model_dump()
    data.update(overrides)
    return UserInput(**data)


def _binary_search_down_payment(user_input: UserInput) -> float:
    """
    Binary search for the minimum down payment that makes the purchase safe.
    Returns the total down payment amount (not the additional amount).

    Search space: current down payment → property price (100% cash purchase).
    Precision: ₹1,000.
    """
    lo = user_input.down_payment
    hi = user_input.property_price
    precision = 1000.0

    # If even paying full cash isn't safe (income too low for expenses),
    # return property_price as the down payment (indicating impossible)
    full_cash = _make_modified_input(user_input, down_payment=hi)
    if not _is_safe(full_cash):
        return hi

    while hi - lo > precision:
        mid = (lo + hi) / 2.0
        candidate = _make_modified_input(user_input, down_payment=mid)
        if _is_safe(candidate):
            hi = mid
        else:
            lo = mid

    return round(hi, 2)


def _binary_search_property_price(user_input: UserInput) -> float:
    """
    Binary search for the maximum property price that is safe
    at the current down payment.

    Search space: down_payment (zero loan) → current property_price.
    Precision: ₹10,000.
    """
    lo = user_input.down_payment  # No loan at all
    hi = user_input.property_price
    precision = 10000.0

    # If even the cheapest property isn't safe, return the minimum
    cheapest = _make_modified_input(user_input, property_price=lo)
    if not _is_safe(cheapest):
        return lo

    while hi - lo > precision:
        mid = (lo + hi) / 2.0
        candidate = _make_modified_input(user_input, property_price=mid)
        if _is_safe(candidate):
            lo = mid
        else:
            hi = mid

    return round(lo, 2)


def _binary_search_monthly_income(user_input: UserInput) -> float:
    """
    Binary search for the minimum monthly income needed to make
    the current property price safe at the current down payment.

    Search space: current income → 10x current income.
    Precision: ₹1,000.
    """
    lo = user_input.monthly_income
    hi = user_input.monthly_income * 10.0
    precision = 1000.0

    # If even 10x income isn't safe, return that ceiling
    max_income = _make_modified_input(user_input, monthly_income=hi)
    if not _is_safe(max_income):
        return hi

    while hi - lo > precision:
        mid = (lo + hi) / 2.0
        candidate = _make_modified_input(user_input, monthly_income=mid)
        if _is_safe(candidate):
            hi = mid
        else:
            lo = mid

    return round(hi, 2)


def calculate_path_to_safe(user_input: UserInput) -> PathToSafeOutput:
    """
    Calculate the exact rupee amounts needed to fix a 'reconsider' verdict.

    Returns a PathToSafeOutput with:
    - How much more down payment is needed
    - What property price is safe at current down payment
    - What income is needed at current property price

    Runs three independent binary searches. Each converges in ~20 iterations
    (pure arithmetic), so total execution is well under 5ms.
    """
    financial = calculate_affordability(user_input)
    current_status = financial.affordability_status
    scenarios = run_all_scenarios(user_input, financial)
    already_safe = (
        financial.emi_to_income_ratio <= 0.35
        and scenarios.scenarios_survived == 5
    )

    if already_safe:
        return PathToSafeOutput(
            current_status=current_status,
            is_already_safe=True,
            additional_down_payment_needed=0.0,
            target_down_payment=user_input.down_payment,
            target_property_price=user_input.property_price,
            target_monthly_income=user_input.monthly_income,
            explanation=(
                f"Your current situation is already safe. "
                f"EMI is {financial.emi_to_income_ratio * 100:.1f}% of income "
                f"and you survive all 5 stress scenarios."
            ),
        )

    target_dp = _binary_search_down_payment(user_input)
    additional_dp = max(0.0, target_dp - user_input.down_payment)
    target_price = _binary_search_property_price(user_input)
    target_income = _binary_search_monthly_income(user_input)

    parts = []
    if additional_dp > 0 and target_dp < user_input.property_price:
        parts.append(
            f"Increase your down payment by \u20b9{additional_dp:,.0f} "
            f"(to \u20b9{target_dp:,.0f} total)"
        )
    if target_price < user_input.property_price:
        price_reduction = user_input.property_price - target_price
        parts.append(
            f"Or look at properties under \u20b9{target_price:,.0f} "
            f"(\u20b9{price_reduction:,.0f} less than current)"
        )
    if target_income > user_input.monthly_income:
        income_gap = target_income - user_input.monthly_income
        parts.append(
            f"Or increase monthly income by \u20b9{income_gap:,.0f} "
            f"(to \u20b9{target_income:,.0f})"
        )

    explanation = (
        f"Your current EMI is {financial.emi_to_income_ratio * 100:.1f}% of income "
        f"({current_status.value}). "
        f"You survive {scenarios.scenarios_survived}/5 stress scenarios. "
        f"To reach safe status: {'; '.join(parts)}."
        if parts
        else (
            f"Your situation is {current_status.value} with limited options "
            f"to reach safe status at this property price."
        )
    )

    return PathToSafeOutput(
        current_status=current_status,
        is_already_safe=False,
        additional_down_payment_needed=round(additional_dp, 2),
        target_down_payment=round(target_dp, 2),
        target_property_price=round(target_price, 2),
        target_monthly_income=round(target_income, 2),
        explanation=explanation,
    )
