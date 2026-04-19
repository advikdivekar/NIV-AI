/* ─── Niv AI — Frontend Logic ──────────────────────────────────────────────── */

const API_BASE = window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "";  // same origin in production

let currentStep = 1;
let lastReport = null;
let lastInput = null;

/* ─── View Management ─────────────────────────────────────────────────────── */

function showView(viewId) {
    document.querySelectorAll(".view").forEach(v => v.style.display = "none");
    const target = document.getElementById(viewId);
    if (target) target.style.display = "block";
    window.scrollTo(0, 0);
}

function resetToForm() {
    currentStep = 1;
    updateStepUI();
    showView("form-view");
    showStep(1);
}

function showAbout() {
    showView("about-view");
}

/* ─── Step Navigation ─────────────────────────────────────────────────────── */

function showStep(n) {
    document.querySelectorAll(".form-step").forEach(s => s.style.display = "none");
    const step = document.getElementById(`step-${n}`);
    if (step) step.style.display = "block";
}

function updateStepUI() {
    const fill = document.getElementById("step-fill");
    fill.style.width = `${(currentStep / 3) * 100}%`;

    for (let i = 1; i <= 3; i++) {
        const label = document.getElementById(`step-label-${i}`);
        label.className = "step-label";
        if (i < currentStep) label.classList.add("done");
        if (i === currentStep) label.classList.add("active");
    }
}

function nextStep(n) {
    if (!validateCurrentStep()) return;

    if (n === 3) buildReviewSummary();

    currentStep = n;
    showStep(n);
    updateStepUI();
    window.scrollTo(0, 0);
}

function prevStep(n) {
    currentStep = n;
    showStep(n);
    updateStepUI();
}

/* ─── Validation ──────────────────────────────────────────────────────────── */

function validateCurrentStep() {
    if (currentStep === 1) {
        const income = getNum("monthly_income");
        const savings = getNum("liquid_savings");
        if (!income || income <= 0) return showFieldError("monthly_income", "Enter your monthly income");
        if (savings < 0) return showFieldError("liquid_savings", "Savings cannot be negative");
        return true;
    }
    if (currentStep === 2) {
        const price = getNum("property_price");
        const area = getVal("location_area");
        const carpet = getNum("carpet_area_sqft");
        const dp = getNum("down_payment_available");

        if (!price || price < 100000) return showFieldError("property_price", "Enter a valid property price");
        if (!area || area.length < 2) return showFieldError("location_area", "Enter the area / location");
        if (!carpet || carpet < 50) return showFieldError("carpet_area_sqft", "Enter carpet area");
        if (dp < 0) return showFieldError("down_payment_available", "Down payment cannot be negative");
        if (dp >= price) return showFieldError("down_payment_available", "Down payment cannot exceed property price");
        return true;
    }
    return true;
}

function showFieldError(fieldId, msg) {
    const field = document.getElementById(fieldId);
    field.setAttribute("aria-invalid", "true");
    field.focus();

    // Remove error state after user starts typing
    field.addEventListener("input", function handler() {
        field.removeAttribute("aria-invalid");
        field.removeEventListener("input", handler);
    });

    alert(msg);
    return false;
}

/* ─── Form Data Collection ────────────────────────────────────────────────── */

function getVal(id) { return (document.getElementById(id)?.value || "").trim(); }
function getNum(id) { return parseFloat(document.getElementById(id)?.value) || 0; }

function collectFormData() {
    const reraVal = getVal("is_rera_registered");
    let reraRegistered = null;
    if (reraVal === "true") reraRegistered = true;
    if (reraVal === "false") reraRegistered = false;

    return {
        financial: {
            monthly_income: getNum("monthly_income"),
            employment_type: getVal("employment_type"),
            years_in_current_job: getNum("years_in_current_job"),
            expected_annual_growth_pct: getNum("expected_annual_growth_pct"),
            existing_emis: getNum("existing_emis"),
            monthly_expenses: getNum("monthly_expenses"),
            current_rent: getNum("current_rent"),
            liquid_savings: getNum("liquid_savings"),
            other_investments: getNum("other_investments"),
            dependents: getNum("dependents"),
            spouse_income: getNum("spouse_income"),
            financial_notes: getVal("financial_notes"),
        },
        property: {
            property_price: getNum("property_price"),
            location_area: getVal("location_area"),
            location_city: "Mumbai",
            configuration: getVal("configuration"),
            carpet_area_sqft: getNum("carpet_area_sqft"),
            is_ready_to_move: getVal("is_ready_to_move") === "true",
            is_rera_registered: reraRegistered,
            builder_name: getVal("builder_name"),
            possession_date: getVal("possession_date"),
            down_payment_available: getNum("down_payment_available"),
            loan_tenure_years: parseInt(getVal("loan_tenure_years")) || 20,
            expected_interest_rate: getNum("expected_interest_rate"),
            buyer_gender: getVal("buyer_gender"),
            is_first_property: document.getElementById("is_first_property")?.checked ?? true,
            property_notes: getVal("property_notes"),
        },
    };
}

/* ─── Review Summary ──────────────────────────────────────────────────────── */

function buildReviewSummary() {
    const data = collectFormData();
    const f = data.financial;
    const p = data.property;

    const loanAmt = p.property_price - p.down_payment_available;

    const html = `
        <article>
            <h3>Your Finances</h3>
            ${reviewRow("Monthly Income", formatINR(f.monthly_income))}
            ${f.spouse_income > 0 ? reviewRow("Spouse Income", formatINR(f.spouse_income)) : ""}
            ${reviewRow("Employment", f.employment_type + " (" + f.years_in_current_job + " yrs)")}
            ${reviewRow("Existing EMIs", formatINR(f.existing_emis))}
            ${reviewRow("Monthly Expenses", f.monthly_expenses > 0 ? formatINR(f.monthly_expenses) : "Auto-estimate (40% of income)")}
            ${reviewRow("Liquid Savings", formatINR(f.liquid_savings))}
            ${reviewRow("Dependents", f.dependents)}
            ${f.financial_notes ? reviewRow("Notes", f.financial_notes) : ""}
        </article>
        <article>
            <h3>The Property</h3>
            ${reviewRow("Price", formatINR(p.property_price))}
            ${reviewRow("Location", p.location_area + ", " + p.location_city)}
            ${reviewRow("Configuration", p.configuration + " — " + p.carpet_area_sqft + " sq ft")}
            ${reviewRow("Down Payment", formatINR(p.down_payment_available))}
            ${reviewRow("Loan Amount", formatINR(loanAmt))}
            ${reviewRow("Tenure / Rate", p.loan_tenure_years + " yrs @ " + p.expected_interest_rate + "%")}
            ${reviewRow("Status", p.is_ready_to_move ? "Ready to Move" : "Under Construction")}
            ${p.builder_name ? reviewRow("Builder", p.builder_name) : ""}
            ${p.property_notes ? reviewRow("Notes", p.property_notes) : ""}
        </article>
    `;

    document.getElementById("review-summary").innerHTML = html;
}

function reviewRow(label, value) {
    return `<div class="review-row"><span class="review-label">${label}</span><span class="review-value">${value}</span></div>`;
}

/* ─── API Call ─────────────────────────────────────────────────────────────── */

async function submitAnalysis() {
    const data = collectFormData();
    lastInput = data;

    showView("loading-view");
    startLoadingAnimation();

    try {
        const response = await fetch(`${API_BASE}/api/v1/analyze`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: "Server error" }));
            throw new Error(err.detail || `Server returned ${response.status}`);
        }

        const report = await response.json();
        lastReport = report;
        renderReport(report);
        showView("report-view");

    } catch (error) {
        console.error("Analysis failed:", error);
        document.getElementById("error-message").textContent = error.message;
        showView("error-view");
    }
}

/* ─── Loading Animation ───────────────────────────────────────────────────── */

function startLoadingAnimation() {
    const agents = 6;
    const avgTime = 5000; // ~5s per agent simulated

    for (let i = 1; i <= agents; i++) {
        const row = document.getElementById(`agent-${i}-status`);
        const stateEl = row.querySelector(".agent-state");
        stateEl.className = "agent-state waiting";
        stateEl.textContent = "waiting";
    }

    let current = 1;
    const interval = setInterval(() => {
        if (current > agents) {
            clearInterval(interval);
            return;
        }

        // Mark previous as done
        if (current > 1) {
            const prev = document.getElementById(`agent-${current - 1}-status`);
            const prevState = prev.querySelector(".agent-state");
            prevState.className = "agent-state done";
            prevState.textContent = "✓ done";
        }

        // Mark current as running
        const curr = document.getElementById(`agent-${current}-status`);
        const currState = curr.querySelector(".agent-state");
        currState.className = "agent-state running";
        currState.textContent = "running...";

        current++;
    }, avgTime);
}

/* ─── Report Rendering ────────────────────────────────────────────────────── */

function renderReport(r) {
    const container = document.getElementById("report-content");
    const computed = r.computed_numbers || {};

    let html = "";

    // Verdict banner
    html += renderVerdictBanner(r);

    // Top reasons
    if (r.top_reasons?.length) {
        html += `<section class="report-section">
            <h2>Key Findings</h2>
            <ul class="recommendations-list">${r.top_reasons.map(reason => `<li>${esc(reason)}</li>`).join("")}</ul>
        </section>`;
    }

    // Financial summary
    html += renderFinancialSection(r, computed);

    // Stress tests
    html += renderStressTests(r);

    // Property assessment
    html += renderPropertySection(r);

    // Assumptions challenged
    html += renderAssumptions(r);

    // Recommendations
    if (r.recommended_actions?.length) {
        html += `<section class="report-section">
            <h2>How to Make This Safer</h2>
            <ul class="recommendations-list">${r.recommended_actions.map(a => `<li>${esc(a)}</li>`).join("")}</ul>
        </section>`;
    }

    // Conditions for safety
    if (r.conditions_for_safety?.length) {
        html += `<section class="report-section">
            <h2>What Would Change This Verdict</h2>
            <ul class="recommendations-list">${r.conditions_for_safety.map(c => `<li>${esc(c)}</li>`).join("")}</ul>
        </section>`;
    }

    // Full reasoning (expandable)
    if (r.full_reasoning) {
        html += `<section class="report-section">
            <h2 class="expandable" onclick="toggleExpand('full-reasoning')">Full Analysis Details ▸</h2>
            <div class="expandable-content" id="full-reasoning">${esc(r.full_reasoning)}</div>
        </section>`;
    }

    // Limitations & disclaimer
    html += `<section class="report-section">
        <h2 class="expandable" onclick="toggleExpand('limitations')">Limitations & Disclaimer ▸</h2>
        <div class="expandable-content" id="limitations">
            <p><strong>Data sources:</strong> ${(r.data_sources || []).join(", ")}</p>
            <p><strong>Limitations:</strong></p>
            <ul>${(r.limitations || []).map(l => `<li>${esc(l)}</li>`).join("")}</ul>
            <p><strong>Disclaimer:</strong> ${esc(r.disclaimer || "")}</p>
        </div>
    </section>`;

    // Pipeline time
    if (r._meta?.pipeline_time_seconds) {
        html += `<p style="text-align:center;color:var(--pico-muted-color);font-size:0.85rem;">Analysis completed in ${r._meta.pipeline_time_seconds}s</p>`;
    }

    container.innerHTML = html;
}

function renderVerdictBanner(r) {
    const v = (r.verdict || "risky").toLowerCase();
    const icon = v === "safe" ? "✅" : v === "risky" ? "⚠️" : "🚨";
    return `
        <div class="verdict-banner ${v}">
            <div class="verdict-word">${icon} ${v.toUpperCase()}</div>
            <p class="verdict-reason">${esc(r.verdict_reason || "")}</p>
            <span class="confidence-badge">Confidence: ${r.confidence_score || "?"}/10</span>
        </div>`;
}

function renderFinancialSection(r, computed) {
    const fs = r.financial_summary || {};
    const kr = fs.key_ratios || {};

    return `<section class="report-section">
        <h2>💰 Financial Reality</h2>

        ${ratioBar("EMI to Income", kr.emi_to_income, 0.30, 0.45)}
        ${ratioBar("Total Housing to Income", kr.total_housing_to_income, 0.35, 0.50)}
        ${ratioBar("Down Payment to Savings", kr.down_payment_to_savings, 0.50, 0.80)}

        <article>
            <div class="review-row"><span class="review-label">Monthly EMI</span><span class="review-value">${formatINR(computed.monthly_emi)}</span></div>
            <div class="review-row"><span class="review-label">Total Monthly Housing Cost</span><span class="review-value">${formatINR(computed.monthly_ownership_cost)}</span></div>
            <div class="review-row"><span class="review-label">After-Tax Monthly Cost</span><span class="review-value">${formatINR(computed.effective_monthly_cost_after_tax)}</span></div>
            <div class="review-row"><span class="review-label">Total Acquisition Cost</span><span class="review-value">${formatINR(computed.total_acquisition_cost)}</span></div>
            <div class="review-row"><span class="review-label">Total Interest Over Loan Life</span><span class="review-value">${formatINR(computed.total_interest_paid)}</span></div>
            <div class="review-row"><span class="review-label">Post-Purchase Savings</span><span class="review-value">${formatINR(computed.post_purchase_savings)}</span></div>
            <div class="review-row"><span class="review-label">Emergency Runway</span><span class="review-value">${computed.emergency_runway_months?.toFixed(1) || "?"} months</span></div>
            <div class="review-row"><span class="review-label">Annual Tax Saving</span><span class="review-value">${formatINR(computed.annual_tax_saving)}</span></div>
        </article>

        ${(fs.red_flags?.length) ? `<article><strong>Red Flags:</strong><ul>${fs.red_flags.map(f => `<li>${esc(f)}</li>`).join("")}</ul></article>` : ""}
    </section>`;
}

function renderStressTests(r) {
    const scenarios = r.stress_scenarios || [];
    if (!scenarios.length) return "";

    const cards = scenarios.map(s => {
        const cls = s.can_survive ? "survive" : "fail";
        const badge = s.severity ? `<span class="badge ${s.severity}">${s.severity}</span>` : "";
        return `
            <div class="scenario-card ${cls}">
                <h4>${esc(s.name?.replace(/_/g, " "))} ${badge}</h4>
                <p>${esc(s.description || "")}</p>
                <p class="key-number">${s.can_survive ? "✅" : "❌"} ${esc(s.key_number || "")}</p>
                ${s.mitigation ? `<p class="mitigation"><strong>Mitigation:</strong> ${esc(s.mitigation)}</p>` : ""}
            </div>`;
    }).join("");

    return `<section class="report-section">
        <h2>⚠️ Stress Tests</h2>
        <p>${scenarios.filter(s => s.can_survive).length}/${scenarios.length} scenarios survived</p>
        <div class="scenario-grid">${cards}</div>
    </section>`;
}

function renderPropertySection(r) {
    const pa = r.property_assessment || {};
    const price = pa.price_assessment || {};
    const flags = pa.property_flags || [];
    const rvb = r.rent_vs_buy || {};

    let html = `<section class="report-section"><h2>🏠 Property Assessment</h2>`;

    // Price comparison
    html += `<article>
        <div class="review-row"><span class="review-label">Price per sq ft</span><span class="review-value">${formatINR(price.price_per_sqft)}</span></div>
        <div class="review-row"><span class="review-label">Area Median</span><span class="review-value">${formatINR(price.area_median_per_sqft)}</span></div>
        <div class="review-row"><span class="review-label">Market Premium</span><span class="review-value">${price.premium_over_market_pct > 0 ? "+" : ""}${price.premium_over_market_pct?.toFixed(1) || "?"}%</span></div>
        <div class="review-row"><span class="review-label">Price Verdict</span><span class="review-value">${esc((price.verdict || "").replace(/_/g, " "))}</span></div>
    </article>`;

    // Rent vs Buy
    html += `<article>
        <h3>Rent vs Buy</h3>
        <div class="review-row"><span class="review-label">Equivalent Rent</span><span class="review-value">${formatINR(rvb.equivalent_monthly_rent)}/month</span></div>
        <div class="review-row"><span class="review-label">Buying Cost</span><span class="review-value">${formatINR(rvb.buying_monthly_cost)}/month</span></div>
        <div class="review-row"><span class="review-label">Ownership Premium</span><span class="review-value">${rvb.premium_for_ownership_pct?.toFixed(0) || "?"}%</span></div>
        <div class="review-row"><span class="review-label">Break-Even</span><span class="review-value">${rvb.break_even_years?.toFixed(1) || "?"} years</span></div>
    </article>`;

    // Flags
    if (flags.length) {
        html += `<article><h3>Property Flags</h3>`;
        flags.forEach(f => {
            html += `<div style="margin-bottom:0.75rem;">
                <span class="badge ${f.severity}">${f.severity}</span>
                <strong> ${esc(f.flag)}</strong>
                <p style="margin:0.25rem 0 0;font-size:0.9rem;">${esc(f.detail)}</p>
            </div>`;
        });
        html += `</article>`;
    }

    // Location analysis
    if (pa.location_analysis) {
        html += `<article><h3>Location Analysis</h3><p>${esc(pa.location_analysis)}</p></article>`;
    }

    html += `</section>`;
    return html;
}

function renderAssumptions(r) {
    const challenges = r.assumptions_challenged || [];
    const blindSpots = r.blind_spots || [];
    const emotional = r.emotional_flags || [];

    if (!challenges.length && !blindSpots.length) return "";

    let html = `<section class="report-section"><h2>🔍 Assumptions Challenged</h2>`;

    challenges.forEach(c => {
        html += `<div class="challenge-card">
            <span class="badge ${c.severity}">${c.severity}</span>
            <p class="assumption"><strong>Assumption:</strong> ${esc(c.assumption)}</p>
            <p class="challenge-text"><strong>Challenge:</strong> ${esc(c.challenge)}</p>
            <p class="impact"><strong>Impact:</strong> ${esc(c.impact)}</p>
        </div>`;
    });

    if (blindSpots.length) {
        html += `<article><h3>Blind Spots</h3><ul>${blindSpots.map(b => `<li>${esc(b)}</li>`).join("")}</ul></article>`;
    }

    if (emotional.length) {
        html += `<article><h3>Emotional Flags</h3><ul>${emotional.map(e => `<li>${esc(e)}</li>`).join("")}</ul></article>`;
    }

    html += `</section>`;
    return html;
}

/* ─── Helper Functions ────────────────────────────────────────────────────── */

function formatINR(n) {
    if (n === undefined || n === null || isNaN(n)) return "—";
    return "₹" + Math.round(n).toLocaleString("en-IN");
}

function esc(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = String(str);
    return div.innerHTML;
}

function ratioBar(label, value, warnThreshold, dangerThreshold) {
    if (value === undefined || value === null) return "";
    const pct = Math.min(value * 100, 100);
    let cls = "good";
    if (value >= dangerThreshold) cls = "danger";
    else if (value >= warnThreshold) cls = "warn";

    return `<div class="ratio-bar-container">
        <div class="ratio-bar-label"><span>${label}</span><span>${(value * 100).toFixed(1)}%</span></div>
        <div class="ratio-bar"><div class="ratio-bar-fill ${cls}" style="width:${pct}%"></div></div>
    </div>`;
}

function toggleExpand(id) {
    const el = document.getElementById(id);
    if (el) el.classList.toggle("open");
}