"""Legal transparency & simplification: plain-language stages and delay risk."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

STAGE_STEPS = (
    "Scrutiny",
    "Pleadings",
    "Evidence",
    "Final Hearing",
)

# Indicative days a typical matter may remain in each pipeline step.
STAGE_BENCHMARK_DAYS = {
    "Scrutiny": 30,
    "Pleadings": 90,
    "Evidence": 180,
    "Final Hearing": 60,
}

_STAGE_ALIASES = {
    "scrutiny": "Scrutiny",
    "filing": "Scrutiny",
    "registration": "Scrutiny",
    "pending documents": "Scrutiny",
    "police report & verification": "Scrutiny",
    "police report and verification": "Scrutiny",
    "pleadings": "Pleadings",
    "notice": "Pleadings",
    "notice under order v cpc": "Pleadings",
    "summons": "Pleadings",
    "written statement": "Pleadings",
    "framing of issues": "Pleadings",
    "evidence": "Evidence",
    "evidence & arguments": "Evidence",
    "evidence and arguments": "Evidence",
    "arguments & evidence": "Evidence",
    "arguments and evidence": "Evidence",
    "arguments": "Evidence",
    "regular hearing": "Evidence",
    "final hearing": "Final Hearing",
    "final arguments": "Final Hearing",
    "judgment reserved": "Final Hearing",
    "judgment": "Final Hearing",
}

_EXPLANATIONS = {
    "Scrutiny": (
        "The court registry is checking whether the papers are complete and correctly "
        "filed. If something is missing (fees, vakalatnama, annexures), the office may "
        "ask you to fix it before the case is numbered and listed before a judge."
    ),
    "Pleadings": (
        "Both sides are exchanging their written case. Notices or summons (including "
        "notice under Order V of the Civil Procedure Code) tell the other party to appear "
        "and file a reply. The court may then 'frame issues' — a short list of questions "
        "it must decide."
    ),
    "Evidence": (
        "Witnesses and documents are being presented and tested. Lawyers may also make "
        "arguments on what the evidence proves. This is usually the longest stage; extra "
        "adjournments here often mean the next hearing is pushed out."
    ),
    "Final Hearing": (
        "The court has heard (or is hearing) concluding arguments and may reserve judgment. "
        "A decision, order, or further directions should follow after this stage."
    ),
}

_PHRASE_EXPLANATIONS = {
    "framing of issues": (
        "The judge is writing down the exact legal questions that must be answered "
        "(for example, whether a notice was valid). Evidence later will be limited to those questions."
    ),
    "notice under order v cpc": (
        "The court is sending an official summons so the other party is told about the case "
        "and given a date to appear. This is a standard first step in many civil matters."
    ),
    "arguments & evidence": (
        "The court is taking witness testimony, documents, and oral arguments from both sides. "
        "In plain terms: each party is trying to prove their version of events."
    ),
    "arguments and evidence": (
        "The court is taking witness testimony, documents, and oral arguments from both sides. "
        "In plain terms: each party is trying to prove their version of events."
    ),
}


def canonical_stage(stage_name: str | None) -> str:
    if not stage_name:
        return "Scrutiny"
    key = stage_name.strip().lower()
    if key in _STAGE_ALIASES:
        return _STAGE_ALIASES[key]
    for step in STAGE_STEPS:
        if step.lower() in key:
            return step
    return stage_name.strip()


def stage_step_from_name(stage_name: str | None) -> int:
    canonical = canonical_stage(stage_name)
    try:
        return STAGE_STEPS.index(canonical) + 1
    except ValueError:
        return 1


def parse_filing_date(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    for fmt in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def compute_delay_status(
    adjournments_count: int = 0,
    stage_name: str | None = None,
    filing_date: str | None = None,
) -> tuple[str, str]:
    """Return (delay_status, delay_reason)."""
    adjournments_count = int(adjournments_count or 0)
    if adjournments_count > 3:
        return (
            "High Delay Risk",
            f"This matter has been adjourned {adjournments_count} times (more than 3), "
            "which is a strong signal of delay.",
        )

    canonical = canonical_stage(stage_name)
    filed = parse_filing_date(filing_date)
    if filed:
        today = datetime.now(timezone.utc).replace(tzinfo=None)
        elapsed = max((today - filed).days, 0)
        benchmark = STAGE_BENCHMARK_DAYS.get(canonical, 90)
        if elapsed > benchmark * 1.5:
            return (
                "High Delay Risk",
                f"Time since filing ({elapsed} days) is well beyond the typical "
                f"{benchmark}-day benchmark for the {canonical} stage.",
            )
        if elapsed > benchmark or adjournments_count == 3:
            reason = []
            if elapsed > benchmark:
                reason.append(
                    f"this stage often completes around {benchmark} days; {elapsed} days have passed since filing"
                )
            if adjournments_count == 3:
                reason.append("three adjournments have already been recorded")
            return ("Watch — Moderate Delay", "; ".join(reason).capitalize() + ".")

    if adjournments_count == 3:
        return (
            "Watch — Moderate Delay",
            "Three adjournments have been recorded. Further postponements will flag high delay risk.",
        )

    return (
        "On Track",
        "Adjournments and time since filing are within typical court-process benchmarks.",
    )


def explain_stage(
    stage_name: str,
    adjournments_count: int = 0,
    filing_date: str | None = None,
) -> dict[str, Any]:
    """Map legal jargon to a citizen-friendly explanation and compute delay risk."""
    raw = (stage_name or "").strip()
    key = raw.lower()
    if key in _PHRASE_EXPLANATIONS:
        explanation = _PHRASE_EXPLANATIONS[key]
    else:
        canonical = canonical_stage(raw)
        explanation = _EXPLANATIONS.get(
            canonical,
            (
                f"The case is currently at “{raw or 'an unspecified stage'}”. "
                "Ask the court registry or your lawyer what papers or appearances are next."
            ),
        )

    delay_status, delay_reason = compute_delay_status(
        adjournments_count=adjournments_count,
        stage_name=raw,
        filing_date=filing_date,
    )
    return {
        "explanation": explanation,
        "delay_status": delay_status,
        "delay_reason": delay_reason,
        "canonical_stage": canonical_stage(raw),
        "stage_step": stage_step_from_name(raw),
    }
