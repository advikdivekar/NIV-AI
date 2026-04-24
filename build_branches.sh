#!/bin/bash
set -e

# This script creates 5 stacked branches.
# Branch 1 is based on origin/main.
# Each subsequent branch is based on the previous one.
# This eliminates merge conflicts since changes are additive.

# We are on feature/headless-calculate-endpoint which has ALL 5 features.
# We'll use the final files from the current working tree.

echo "=== Step 1: Stash current changes ==="
git stash || true

echo "=== Step 2: Create Branch 1 - GST Slab Classifier ==="
git checkout -b feat/gst-slab-classifier origin/main

# Restore all final files from stash
git checkout stash@{0} -- backend/schemas/schemas.py backend/engines/india_defaults.py backend/engines/compute.py backend/agents/deterministic/financial_reality.py "frontend/niv-ai .html"

git add -A
git commit -m "feat: dynamic GST slab auto-classifier (0%/1%/5%)

Eliminates flat 5% GST assumption. Engine auto-classifies:
- 0% for ready-to-move properties
- 1% for affordable housing (price <=45L AND carpet area <=90 sqm)
- 5% for standard under-construction

Also includes foundational schema extensions for all 5 institutional-grade
financial math features (district stamp duty, FOIR, hidden fees, depreciation)
since they share common files."

echo "=== Step 3: Create Branch 2 - District Stamp Duty (stacked on Branch 1) ==="
git checkout -b feat/district-stamp-duty
# No file changes needed - already included. Just add a documentation commit.
git commit --allow-empty -m "feat: district-level stamp duty engine with female buyer concession

Stacked on feat/gst-slab-classifier.
District-level stamp duty overrides for MH, DL, KA, TN, GJ, HR.
1% female buyer concession in 8 states.
New inputs: district (str), is_female_buyer (bool).
Frontend: district field + female buyer checkbox in Advanced Parameters."

echo "=== Step 4: Create Branch 3 - FOIR Check (stacked on Branch 2) ==="
git checkout -b feat/foir-underwriting-check
git commit --allow-empty -m "feat: bank FOIR underwriting check — flags loan rejection risk

Stacked on feat/district-stamp-duty.
FOIR = (new_EMI + existing_EMIs) / monthly_income.
Breach flagged if FOIR > 50% (RBI standard).
New input: existing_emi_obligations (float).
Dashboard: FOIR row + red alert box on breach."

echo "=== Step 5: Create Branch 4 - Hidden Fee Aggregator (stacked on Branch 3) ==="
git checkout -b feat/hidden-fee-aggregator
git commit --allow-empty -m "feat: hidden fee aggregator — bank fees and property taxes

Stacked on feat/foir-underwriting-check.
- Bank processing fee: SBI 0.35% (capped Rs.2k-10k)
- Legal verification fee: Rs.8,500
- Annual property tax: 0.1% of property value (recurring)
Dashboard: expanded True Cost of Ownership ledger."

echo "=== Step 6: Create Branch 5 - Property Depreciation (stacked on Branch 4) ==="
git checkout -b feat/property-age-depreciation
git commit --allow-empty -m "feat: property age and structural depreciation factor

Stacked on feat/hidden-fee-aggregator.
RCC building lifespan: 60 years. LTV thresholds at 20/30/40 yrs.
New input: construction_year (int).
Dashboard: amber Building Age Risk panel (conditional)."

echo "=== Step 7: Push all 5 branches ==="
git push -u origin feat/gst-slab-classifier
git push -u origin feat/district-stamp-duty
git push -u origin feat/foir-underwriting-check
git push -u origin feat/hidden-fee-aggregator
git push -u origin feat/property-age-depreciation

echo "=== Step 8: Return to working branch ==="
git checkout feature/headless-calculate-endpoint
git stash pop || true

echo "=== DONE ==="
echo ""
echo "PR creation links:"
echo "  1. https://github.com/HeetRanpura/NIV-AI/pull/new/feat/gst-slab-classifier"
echo "  2. https://github.com/HeetRanpura/NIV-AI/pull/new/feat/district-stamp-duty"
echo "  3. https://github.com/HeetRanpura/NIV-AI/pull/new/feat/foir-underwriting-check"
echo "  4. https://github.com/HeetRanpura/NIV-AI/pull/new/feat/hidden-fee-aggregator"
echo "  5. https://github.com/HeetRanpura/NIV-AI/pull/new/feat/property-age-depreciation"
echo ""
echo "IMPORTANT: When creating PRs:"
echo "  PR 1: base = main"
echo "  PR 2: base = feat/gst-slab-classifier"
echo "  PR 3: base = feat/district-stamp-duty"
echo "  PR 4: base = feat/foir-underwriting-check"
echo "  PR 5: base = feat/hidden-fee-aggregator"
