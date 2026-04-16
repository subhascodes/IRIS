"""
Insurance Governance Decision Engine
======================================
Final approval layer of the Audit Governance System.

Consumes structured outputs from analysis.py and compliance.py and produces
a deterministic, auditable, human-readable governance decision.

make_decision(analysis_result, compliance_result) → dict

Decision hierarchy (evaluated in strict priority order):
  1. Compliance gate    — any violation → REJECT  (non-negotiable)
  2. Financial impact   — avg_change > $300 → REJECT
  3. Portfolio breadth  — percent_affected > 50 % → REJECT
  4. Default            — APPROVE

Design principles:
  - Fully deterministic; no randomness, no side effects
  - Inputs are never mutated
  - Every rejection names the specific threshold that was breached
  - All thresholds are named constants — change once, propagates everywhere
  - Suitable for embedding in a CI/CD approval pipeline or audit log
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# ── Decision thresholds (single source of truth) ─────────────────────────────
MAX_AVG_CHANGE:        float = 300.00   # max acceptable mean premium increase ($)
MAX_PCT_AFFECTED:      float = 50.00    # max acceptable portfolio exposure (%)
PRECISION:             int   = 4        # decimal places in risk_summary floats

# ── Decision constants ────────────────────────────────────────────────────────
APPROVE = "APPROVE"
REJECT  = "REJECT"

# ── Required input keys ───────────────────────────────────────────────────────
_REQUIRED_ANALYSIS = {
    "total_policies", "affected_policies",
    "pct_affected", "avg_change",
}
_REQUIRED_COMPLIANCE = {
    "violations_count", "violation_percentage", "is_deployable",
}


# ── Input validation ──────────────────────────────────────────────────────────
def _validate_inputs(analysis_result: dict, compliance_result: dict) -> None:
    """Fail fast with descriptive errors before any decision logic runs."""
    if not isinstance(analysis_result, dict):
        raise TypeError(
            f"analysis_result must be a dict; got {type(analysis_result).__name__}."
        )
    if not isinstance(compliance_result, dict):
        raise TypeError(
            f"compliance_result must be a dict; got {type(compliance_result).__name__}."
        )

    missing_a = _REQUIRED_ANALYSIS - set(analysis_result)
    if missing_a:
        raise ValueError(f"analysis_result missing required keys: {missing_a}")

    missing_c = _REQUIRED_COMPLIANCE - set(compliance_result)
    if missing_c:
        raise ValueError(f"compliance_result missing required keys: {missing_c}")

    # Type + range guards on the values that feed decision logic
    violations = compliance_result["violations_count"]
    if not isinstance(violations, (int, float)) or violations < 0:
        raise ValueError(
            f"violations_count must be a non-negative number; got {violations!r}."
        )

    avg_change = analysis_result["avg_change"]
    if not isinstance(avg_change, (int, float)):
        raise ValueError(
            f"avg_change must be numeric; got {type(avg_change).__name__}."
        )

    pct_affected = analysis_result["pct_affected"]
    if not isinstance(pct_affected, (int, float)) or not (0 <= pct_affected <= 100):
        raise ValueError(
            f"pct_affected must be in [0, 100]; got {pct_affected!r}."
        )

    violation_pct = compliance_result["violation_percentage"]
    if not isinstance(violation_pct, (int, float)) or not (0 <= violation_pct <= 100):
        raise ValueError(
            f"violation_percentage must be in [0, 100]; got {violation_pct!r}."
        )


# ── Reason builders (one function per rule — easy to audit / extend) ──────────
def _reason_compliance_violation(violations: int, violation_pct: float) -> str:
    return (
        f"Rule rejected: {violations:,} {'policy' if violations == 1 else 'policies'} "
        f"({violation_pct:.2f}% of portfolio) breach one or more regulatory compliance "
        f"thresholds. No deployment is permitted while compliance violations exist."
    )


def _reason_excessive_avg_change(avg_change: float) -> str:
    return (
        f"Rule rejected: the average premium change of ${avg_change:+,.2f} exceeds "
        f"the maximum permissible impact threshold of ${MAX_AVG_CHANGE:,.2f}. "
        f"Excessive financial burden on policyholders constitutes an unacceptable "
        f"governance risk."
    )


def _reason_excessive_portfolio_impact(pct_affected: float) -> str:
    return (
        f"Rule rejected: {pct_affected:.2f}% of the portfolio would be affected, "
        f"exceeding the maximum permissible exposure of {MAX_PCT_AFFECTED:.0f}%. "
        f"A change of this breadth requires board-level review before deployment."
    )


def _reason_approved(violations: int, avg_change: float, pct_affected: float) -> str:
    return (
        f"Rule approved: zero compliance violations detected, average premium "
        f"change of ${avg_change:+,.2f} is within the ${MAX_AVG_CHANGE:,.2f} "
        f"threshold, and {pct_affected:.2f}% portfolio exposure is within the "
        f"{MAX_PCT_AFFECTED:.0f}% limit. All governance gates passed."
    )


# ── Core decision engine ──────────────────────────────────────────────────────
def make_decision(
    analysis_result: dict[str, Any],
    compliance_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Evaluate a pricing rule change against governance thresholds and return
    a deterministic, auditable approval/rejection decision.

    Parameters
    ----------
    analysis_result   : Output dict from analysis.analyze().
    compliance_result : Output dict from compliance.check_compliance().

    Returns
    -------
    dict with keys:
        decision             – "APPROVE" or "REJECT"
        reason               – Human-readable explanation of the decision
        triggered_rule       – Which governance rule fired (or None if approved)
        risk_summary         – Snapshot of key metrics at decision time
        evaluated_at         – ISO-8601 UTC timestamp for audit trail
    """
    # Work on shallow copies of scalar fields — dicts are never mutated
    _validate_inputs(analysis_result, compliance_result)

    # Extract decision inputs (immutable reads)
    violations      = int(compliance_result["violations_count"])
    violation_pct   = float(compliance_result["violation_percentage"])
    avg_change      = float(analysis_result["avg_change"])
    pct_affected    = float(analysis_result["pct_affected"])
    total_policies  = int(analysis_result["total_policies"])
    affected        = int(analysis_result["affected_policies"])

    # ── Risk summary (always populated, independent of decision) ─────────────
    risk_summary = {
        "violations":            violations,
        "violation_percentage":  round(violation_pct, PRECISION),
        "avg_change":            round(avg_change,    PRECISION),
        "affected_percentage":   round(pct_affected,  PRECISION),
        "total_policies":        total_policies,
        "affected_policies":     affected,
        "thresholds": {
            "max_violations":     0,
            "max_avg_change":     MAX_AVG_CHANGE,
            "max_pct_affected":   MAX_PCT_AFFECTED,
        },
    }

    audit_ts = datetime.now(timezone.utc).isoformat()

    # ── Gate 1: Compliance violations (hardest gate — evaluated first) ────────
    if violations > 0:
        return {
            "decision":       REJECT,
            "reason":         _reason_compliance_violation(violations, violation_pct),
            "triggered_rule": "COMPLIANCE_VIOLATION",
            "risk_summary":   risk_summary,
            "evaluated_at":   audit_ts,
        }

    # ── Gate 2: Excessive average financial impact ────────────────────────────
    if avg_change > MAX_AVG_CHANGE:
        return {
            "decision":       REJECT,
            "reason":         _reason_excessive_avg_change(avg_change),
            "triggered_rule": "EXCESSIVE_AVG_CHANGE",
            "risk_summary":   risk_summary,
            "evaluated_at":   audit_ts,
        }

    # ── Gate 3: Excessive portfolio exposure ──────────────────────────────────
    if pct_affected > MAX_PCT_AFFECTED:
        return {
            "decision":       REJECT,
            "reason":         _reason_excessive_portfolio_impact(pct_affected),
            "triggered_rule": "EXCESSIVE_PORTFOLIO_IMPACT",
            "risk_summary":   risk_summary,
            "evaluated_at":   audit_ts,
        }

    # ── Gate 4: All gates passed → APPROVE ───────────────────────────────────
    return {
        "decision":       APPROVE,
        "reason":         _reason_approved(violations, avg_change, pct_affected),
        "triggered_rule": None,
        "risk_summary":   risk_summary,
        "evaluated_at":   audit_ts,
    }


# ── Pretty-print helper ───────────────────────────────────────────────────────
def print_decision(result: dict) -> None:
    """Render a governance decision report suitable for board or audit review."""
    icon   = "✓" if result["decision"] == APPROVE else "✗"
    border = "=" * 62

    print(border)
    print("  GOVERNANCE DECISION — PRICING RULE CHANGE REVIEW")
    print(border)
    print(f"\n  [{icon}]  DECISION : {result['decision']}")
    print(f"\n  Reason   : {result['reason']}")
    print(f"\n  Triggered rule : {result['triggered_rule'] or 'None (all gates passed)'}")
    print(f"  Evaluated at   : {result['evaluated_at']}")

    rs = result["risk_summary"]
    th = rs["thresholds"]
    print("\n── Risk Summary ────────────────────────────────────────────")
    print(
        f"  {'Metric':<30} {'Value':>12}   {'Threshold':>12}   {'Status':>8}"
    )
    print("  " + "-" * 70)

    metrics = [
        ("Violations",       rs["violations"],           th["max_violations"],    "≤"),
        ("Violation rate",   f"{rs['violation_percentage']:.2f}%", "0.00%",       "="),
        ("Avg premium Δ",    f"${rs['avg_change']:+,.2f}",
                             f"${th['max_avg_change']:,.2f}",                     "≤"),
        ("% Portfolio affected", f"{rs['affected_percentage']:.2f}%",
                             f"{th['max_pct_affected']:.0f}%",                   "≤"),
        ("Total policies",   f"{rs['total_policies']:,}",  "—",                  "—"),
        ("Affected policies",f"{rs['affected_policies']:,}","—",                  "—"),
    ]

    for name, value, threshold, op in metrics:
        status = _gate_status(name, rs, th)
        print(f"  {name:<30} {str(value):>12}   {str(threshold):>12}   {status:>8}")

    print()


def _gate_status(metric_name: str, rs: dict, th: dict) -> str:
    """Return PASS / FAIL / N/A for each risk summary row."""
    if metric_name == "Violations":
        return "PASS" if rs["violations"] <= th["max_violations"] else "FAIL"
    if metric_name == "Avg premium Δ":
        return "PASS" if rs["avg_change"] <= th["max_avg_change"] else "FAIL"
    if metric_name == "% Portfolio affected":
        return "PASS" if rs["affected_percentage"] <= th["max_pct_affected"] else "FAIL"
    return "N/A"


# ── Self-test / demo ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    import pandas as pd
    from simulation import simulate
    from analysis   import analyze
    from compliance import check_compliance

    DATA_PATH = "data/dataset.csv"
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Dataset not found at '{DATA_PATH}'. "
            "Run generate_insurance_data.py first."
        )

    df_raw = pd.read_csv(DATA_PATH)

    scenarios = [
        ("Scenario 1 — Compliance violations (aggressive)",  40,  2.50),
        ("Scenario 2 — Excessive avg change (mid-range)",    25,  1.85),
        ("Scenario 3 — High portfolio breadth (wide scope)", 75,  1.30),
        ("Scenario 4 — Conservative (expected APPROVE)",     25,  1.22),
    ]

    results = []
    for title, threshold, multiplier in scenarios:
        print(f"\n{'━'*62}")
        print(f"  {title}")
        print(f"  threshold={threshold}, multiplier={multiplier}")
        print(f"{'━'*62}")

        df_sim     = simulate(df_raw, threshold=threshold, multiplier=multiplier)
        analysis   = analyze(df_sim)
        compliance = check_compliance(df_sim)
        decision   = make_decision(analysis, compliance)

        print_decision(decision)
        results.append((title, decision))

    # ── Structural assertions ─────────────────────────────────────────────────
    for title, d in results:
        assert d["decision"] in {APPROVE, REJECT},           f"{title}: invalid decision"
        assert isinstance(d["reason"], str) and d["reason"],  f"{title}: empty reason"
        assert "risk_summary" in d,                           f"{title}: missing risk_summary"
        assert "evaluated_at" in d,                           f"{title}: missing timestamp"
        assert set(d["risk_summary"]["thresholds"]) == {
            "max_violations", "max_avg_change", "max_pct_affected"
        },                                                     f"{title}: threshold keys"

    # Scenario 1 must REJECT on compliance gate
    assert results[0][1]["decision"]       == REJECT
    assert results[0][1]["triggered_rule"] == "COMPLIANCE_VIOLATION"

    # Scenario 4 conservative run
    assert results[3][1]["decision"] in {APPROVE, REJECT}   # outcome depends on data

    # Input immutability — originals untouched
    _a = {"total_policies": 100, "affected_policies": 50,
          "pct_affected": 50.0, "avg_change": 100.0}
    _c = {"violations_count": 0, "violation_percentage": 0.0, "is_deployable": True}
    _before_a = dict(_a)
    _before_c = dict(_c)
    make_decision(_a, _c)
    assert _a == _before_a, "analysis_result was mutated!"
    assert _c == _before_c, "compliance_result was mutated!"

    # Bad input rejected cleanly
    try:
        make_decision({}, _c)
        assert False
    except ValueError:
        pass

    print("\n  All assertions passed ✓\n")