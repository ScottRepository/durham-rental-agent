"""
AI Tenant Screening, Credit Report Analyzer, Showing Scheduler & Gmail (315kentstreet@gmail.com) CRM Module
Evaluates applicant income, credit score, credit utilization, payment history, and house rules for 315 Kent Street, Whitby.
"""

from typing import Dict, Any, List
from urllib.parse import quote

LANDLORD_EMAIL = "315kentstreet@gmail.com"
INTAKE_FORM_URL = "https://forms.gle/UZSrP8PUSh9GsdLX8"


def analyze_tenant_application(applicant: Dict[str, Any], unit: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes an applicant's credit report metrics, income, employment, and house rules compliance
    against the target unit at 315 Kent Street, Whitby.
    Returns a 0-100 score, verdict (APPROVE / CONDITIONAL / DECLINE), rent-to-income ratio,
    strengths, risk flags, and recommended reference check questions.
    """
    target_rent = float(unit.get("financials", {}).get("target_rent", 2075))
    estimated_hydro = 65.0  # Heat & water included at 315 Kent St; tenant pays personal hydro
    total_housing_cost = target_rent + estimated_hydro

    credit_score = int(applicant.get("credit_score") or 0)
    monthly_income = float(applicant.get("monthly_income") or 0)
    credit_utilization = float(applicant.get("credit_utilization") or 25)
    late_payments = int(applicant.get("late_payments") or 0)
    collections_or_insolvency = bool(applicant.get("collections_or_insolvency", False))
    employment_status = str(applicant.get("employment_status") or "Full-Time Permanent")
    employment_months = int(applicant.get("employment_months") or 12)
    has_pets = bool(applicant.get("has_pets", False))
    smokes = bool(applicant.get("smokes", False))
    landlord_ref_verified = bool(applicant.get("landlord_ref_verified", False))
    occupants = int(applicant.get("occupants") or 1)

    # Calculate Rent-to-Income Ratio (RTI)
    if monthly_income > 0:
        rent_to_income_pct = round((target_rent / monthly_income) * 100, 1)
        total_housing_pct = round((total_housing_cost / monthly_income) * 100, 1)
        income_multiplier = round(monthly_income / target_rent, 2)
    else:
        rent_to_income_pct = 100.0
        total_housing_pct = 100.0
        income_multiplier = 0.0

    score = 0
    strengths: List[str] = []
    risks: List[str] = []
    questions: List[str] = []

    # 1. Credit Score Evaluation (Max 40 pts)
    if credit_score >= 740:
        score += 40
        strengths.append(f"Excellent Credit Score ({credit_score} — Tier A+ borrower)")
    elif credit_score >= 680:
        score += 33
        strengths.append(f"Good Credit Score ({credit_score} — Meets standard 680+ benchmark)")
    elif credit_score >= 640:
        score += 22
        risks.append(f"Fair Credit Score ({credit_score}) — slightly below 680 benchmark")
        questions.append("Ask applicant what caused the dip in credit score and verify last 6 months of on-time rent receipts.")
    elif credit_score > 0:
        score += 8
        risks.append(f"Low Credit Score ({credit_score}) — High default risk without a strong Canadian guarantor")
        questions.append("Require a qualified homeowner guarantor/co-signer with 720+ credit score.")
    else:
        risks.append("Credit Score not yet verified — request full Equifax or TransUnion PDF report")
        questions.append("Request full Equifax/TransUnion credit report (with trade lines, not just a screenshot of the number).")

    # 2. Income & Affordability Evaluation (Max 35 pts)
    if rent_to_income_pct <= 30:
        score += 35
        strengths.append(f"Strong Affordability: Rent is {rent_to_income_pct}% of gross income ({income_multiplier}x rent coverage)")
    elif rent_to_income_pct <= 36:
        score += 27
        strengths.append(f"Healthy Affordability: Rent is {rent_to_income_pct}% of gross income (Heat & Water included saves ~$180/mo)")
    elif rent_to_income_pct <= 42:
        score += 16
        risks.append(f"Tight Rent-to-Income Ratio ({rent_to_income_pct}% of gross income; {total_housing_pct}% with hydro)")
        questions.append("Verify net take-home pay on recent paystubs and check if there is secondary household income or savings buffer.")
    else:
        score += 5
        risks.append(f"High Rent Burden: Rent consumes {rent_to_income_pct}% of gross income (target is <35%)")
        questions.append("Income is insufficient on its own; require a co-applicant or guarantor.")

    # 3. Debt Utilization & Derogatory Marks (Max 15 pts)
    if not collections_or_insolvency and late_payments == 0 and credit_utilization <= 35:
        score += 15
        strengths.append(f"Clean Credit History: 0 late payments, 0 collections, low utilization ({int(credit_utilization)}%)")
    else:
        if credit_utilization <= 50:
            score += 8
        if credit_utilization > 50:
            risks.append(f"High Revolving Credit Utilization ({int(credit_utilization)}% of credit limits used)")
            questions.append("Check total monthly minimum debt payments on credit report to ensure cash flow isn't stretched.")
        if late_payments > 0:
            score = max(0, score - (late_payments * 5))
            risks.append(f"{late_payments} late payment(s) reported on credit file")
        if collections_or_insolvency:
            score = max(0, score - 25)
            risks.append("Active collections, consumer proposal, or bankruptcy flagged on credit report")
            questions.append("Verify nature and status of collections/insolvency before proceeding.")

    # 4. Employment & Stability + House Rules (Max 10 pts)
    if employment_status in ("Full-Time Permanent", "Retired / Pension") and employment_months >= 6:
        score += 10
        strengths.append(f"Stable Income Source: {employment_status} ({employment_months} mos tenure)")
    else:
        score += 5
        questions.append(f"Confirm employment continuity ({employment_status}, {employment_months} months) directly with HR/supervisor.")

    if smokes:
        score = max(0, score - 30)
        risks.append("Applicant indicated smoking/vaping — conflicts with 315 Kent St strict non-smoking building policy")

    if has_pets:
        risks.append("Applicant noted pet(s) in household — review against building pet note")

    if occupants > 3:
        risks.append(f"Household size ({occupants} occupants) is high for an 820–850 sqft 2-bedroom suite")

    if landlord_ref_verified:
        strengths.append("Previous landlord reference verified (on-time rent & clean unit)")
    else:
        questions.append("Call current & previous landlord (verify property ownership via tax roll/registry to rule out fake friend references).")

    score = max(0, min(100, round(score)))

    # Determine Verdict
    if score >= 78 and not collections_or_insolvency and not smokes and rent_to_income_pct <= 37:
        verdict = "STRONG APPROVE"
        verdict_color = "emerald"
        summary = (
            f"Highly qualified candidate for {unit.get('name', '315 Kent St')}. "
            f"Credit score ({credit_score}) and rent-to-income ratio ({rent_to_income_pct}%) meet all landlord benchmarks."
        )
    elif score >= 58 and not collections_or_insolvency and not smokes:
        verdict = "CONDITIONAL APPROVE (VERIFY REFS / GUARANTOR)"
        verdict_color = "amber"
        summary = (
            f"Borderline/Moderate candidate (Score: {score}/100). "
            f"Proceed only after verifying last 6 months of rent e-transfers, employer reference, or adding a co-signer."
        )
    else:
        verdict = "DECLINE — HIGH RISK"
        verdict_color = "red"
        summary = (
            f"Does not meet screening criteria for {unit.get('name', '315 Kent St')} (Score: {score}/100). "
            f"Key risk factors identified in credit, affordability ({rent_to_income_pct}% RTI), or building policies."
        )

    return {
        "score": score,
        "verdict": verdict,
        "verdict_color": verdict_color,
        "summary": summary,
        "metrics": {
            "target_rent": target_rent,
            "estimated_hydro": estimated_hydro,
            "total_housing_cost": total_housing_cost,
            "monthly_income": monthly_income,
            "rent_to_income_pct": rent_to_income_pct,
            "total_housing_pct": total_housing_pct,
            "income_multiplier": income_multiplier,
            "credit_score": credit_score,
            "credit_utilization": credit_utilization
        },
        "strengths": strengths,
        "risks": risks,
        "recommended_questions": questions
    }


def generate_gmail_compose_url(to_email: str, subject: str, body: str) -> str:
    """
    Generates a direct Gmail web compose URL authenticated as 315kentstreet@gmail.com.
    """
    return (
        f"https://mail.google.com/mail/?view=cm&fs=1&tf=1"
        f"&authuser={quote(LANDLORD_EMAIL)}"
        f"&to={quote(to_email)}"
        f"&su={quote(subject)}"
        f"&body={quote(body)}"
    )
