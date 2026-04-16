"""
Insurance Regulatory Compliance Validator
==========================================
Pre-deployment pricing rule validation engine.
Detects absolute and percentage-based premium increase violations
before any pricing change reaches the policyholder.

check_compliance(df) → dict
  Accepts the enriched DataFrame from simulation.simulate()
  and returns a structured compliance report with violation flags,
  segment breakdowns, and auditable sample rows.

Regulatory basis:
  - Absolute cap ($500): mirrors state DOI prior-approval thresholds
    common in CA, NY, FL for personal auto lines
  - Percentage cap (30%): aligns with NAIC model rate-filing guidelines
    and adverse-action notice triggers under most state insurance codes
"""

import numpy as np
import pandas as pd

# ── Rule thresholds (tune per jurisdiction) ───────────────────────────────────
ABSOLUTE_THRESHOLD:    float = 500.00   # max permissible dollar increase
PCT_THRESHOLD:         float = 0.30     # max permissible % increase (30 %)
DELTA_ZERO_TOLERANCE:  float = 0.005   # float-safe zero for pct-change guard
PRECISION:             int   = 4        # decimal places for output rates
MAX_SAMPLE_ROWS:       int   = 5        # rows returned in sample_violations

REQUIRED_COLS = {
    "customer_age", "current_premium", "new_premium",
    "premium_delta", "age_group",
}

SAMPLE_COLS = [
    "policy_id", "customer_age", "age_group",
    "current_premium", "new_premium",
    "premium_delta", "pct_change",
    "violation_absolute", "violation_pct",
]

AGE_LABELS = ["<25", "25-40", ">40"]


# ── Validation ────────────────────────────────────────────────────────────────
def _validate(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")
    if df.empty:
        raise ValueError("DataFrame must not be empty.")
    for col in ("current_premium", "new_premium", "premium_delta"):
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise TypeError(f"Column '{col}' must be numeric; got {df[col].dtype}.")
    if (df["current_premium"] <= DELTA_ZERO_TOLERANCE).any():
        raise ValueError(
            "current_premium contains zero/negative values — "
            "percentage-change calculation would be undefined."
        )


# ── Core compliance engine ────────────────────────────────────────────────────
def check_compliance(df: pd.DataFrame) -> dict:
    """
    Evaluate every policy in the simulated portfolio against regulatory
    pricing rules and return a structured compliance report.

    Parameters
    ----------
    df : Enriched DataFrame from simulation.simulate().
         Must contain: customer_age, age_group, current_premium,
                       new_premium, premium_delta.

    Returns
    -------
    dict
        violations_count       – int: total policies breaching any rule
        violation_percentage   – float: share of portfolio in violation (%)
        violations_by_rule     – dict: breakdown by rule type
        violations_by_segment  – dict: violation counts by age_group
        sample_violations      – pd.DataFrame: up to 5 worst violating rows
        compliant_count        – int: policies fully within thresholds
        is_deployable          – bool: True only if violations_count == 0
    """
    _validate(df)

    # ── Immutable working slice — original df never mutated ──────────────────
    work = df.assign(
        # Percentage change: signed, float64, zero-safe
        pct_change=(
            df["premium_delta"].astype(np.float64)
            / df["current_premium"].astype(np.float64)
        ),

        # Rule 1: absolute dollar increase exceeds threshold
        violation_absolute=(df["premium_delta"] > ABSOLUTE_THRESHOLD),

        # Rule 2: percentage increase exceeds threshold
        # Guard: only flag increases — decreases are never a regulatory concern
        violation_pct=(
            (df["premium_delta"] > DELTA_ZERO_TOLERANCE) &
            (df["premium_delta"] / df["current_premium"] > PCT_THRESHOLD)
        ),
    )

    # Combined violation flag: breach of EITHER rule = violation
    work = work.assign(
        any_violation=(work["violation_absolute"] | work["violation_pct"])
    )

    # ── Portfolio-level metrics ──────────────────────────────────────────────
    total_policies    = len(work)
    violations_mask   = work["any_violation"]
    violations_count  = int(violations_mask.sum())
    compliant_count   = total_policies - violations_count
    violation_pct_out = round(violations_count / total_policies * 100, PRECISION)

    # ── Rule-level breakdown ─────────────────────────────────────────────────
    abs_only   = work["violation_absolute"] & ~work["violation_pct"]
    pct_only   = work["violation_pct"]      & ~work["violation_absolute"]
    both_rules = work["violation_absolute"] & work["violation_pct"]

    violations_by_rule = {
        "absolute_only":       int(abs_only.sum()),
        "percentage_only":     int(pct_only.sum()),
        "both_rules":          int(both_rules.sum()),
        "absolute_threshold":  f"${ABSOLUTE_THRESHOLD:,.2f}",
        "percentage_threshold": f"{PCT_THRESHOLD*100:.0f}%",
    }

    # ── Segment-level violation counts (groupby, no loops) ───────────────────
    # Ensure all three labels are present even with zero counts
    seg_counts_raw = (
        work[violations_mask]
        .groupby("age_group", observed=True)["any_violation"]
        .sum()
        .reindex(AGE_LABELS, fill_value=0)
        .astype(int)
    )

    # Segment violation rates
    seg_totals = (
        work.groupby("age_group", observed=True)["any_violation"]
        .count()
        .reindex(AGE_LABELS, fill_value=0)
    )

    violations_by_segment = {
        label: {
            "violation_count":    int(seg_counts_raw.get(label, 0)),
            "segment_total":      int(seg_totals.get(label, 0)),
            "violation_rate_pct": round(
                (int(seg_counts_raw.get(label, 0)) /
                 max(int(seg_totals.get(label, 0)), 1)) * 100,
                PRECISION
            ),
        }
        for label in AGE_LABELS
    }

    # ── Sample violations: worst offenders by premium_delta ──────────────────
    available_sample_cols = [c for c in SAMPLE_COLS if c in work.columns]
    sample_violations = (
        work.loc[violations_mask, available_sample_cols]
        .sort_values("premium_delta", ascending=False)
        .head(MAX_SAMPLE_ROWS)
        .reset_index(drop=True)
    )
    sample_violations["pct_change"] = (
        sample_violations["pct_change"] * 100
    ).round(2).astype(str) + "%"

    return {
        "violations_count":       violations_count,
        "violation_percentage":   violation_pct_out,
        "compliant_count":        compliant_count,
        "is_deployable":          violations_count == 0,
        "violations_by_rule":     violations_by_rule,
        "violations_by_segment":  violations_by_segment,
        "sample_violations":      sample_violations,
    }


# ── Pretty-print helper ───────────────────────────────────────────────────────
def print_compliance_report(report: dict) -> None:
    """Regulatory-grade terminal report for actuarial/compliance review."""
    status = "✓  APPROVED FOR DEPLOYMENT" if report["is_deployable"] \
             else "✗  DEPLOYMENT BLOCKED — VIOLATIONS DETECTED"

    print("=" * 62)
    print("  REGULATORY COMPLIANCE VALIDATION REPORT")
    print("=" * 62)
    print(f"\n  Deployment Status : {status}\n")

    print("── Portfolio Overview ──────────────────────────────────────")
    print(f"  Total policies     : {report['violations_count'] + report['compliant_count']:>8,}")
    print(f"  Compliant          : {report['compliant_count']:>8,}")
    print(f"  Violations         : {report['violations_count']:>8,}")
    print(f"  Violation rate     : {report['violation_percentage']:>8.2f}%")

    br = report["violations_by_rule"]
    print("\n── Violations by Rule ──────────────────────────────────────")
    print(f"  Absolute cap only  ({br['absolute_threshold']}+)  : {br['absolute_only']:>6,}")
    print(f"  Percentage cap only ({br['percentage_threshold']}+) : {br['percentage_only']:>6,}")
    print(f"  Both rules breached              : {br['both_rules']:>6,}")

    print("\n── Violations by Age Segment ───────────────────────────────")
    print(f"  {'Segment':<10} {'Violations':>12} {'Segment Total':>15} {'Rate':>10}")
    print("  " + "-" * 52)
    for label in AGE_LABELS:
        s = report["violations_by_segment"][label]
        print(
            f"  {label:<10} {s['violation_count']:>12,}"
            f" {s['segment_total']:>15,}"
            f" {s['violation_rate_pct']:>9.2f}%"
        )

    print("\n── Sample Violations (Top 5 by Δ Premium) ─────────────────")
    sv = report["sample_violations"]
    if sv.empty:
        print("  No violations detected.\n")
    else:
        print(sv.to_string(index=False))
        print()


# ── Self-test / demo ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    from simulation import simulate

    DATA_PATH = "data/dataset.csv"
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Dataset not found at '{DATA_PATH}'. "
            "Run generate_insurance_data.py first."
        )

    df_raw = pd.read_csv(DATA_PATH)

    print("\n━━━  Scenario A: Aggressive multiplier (expect violations)  ━━━")
    df_sim_a = simulate(df_raw, threshold=40, multiplier=2.50)
    report_a  = check_compliance(df_sim_a)
    print_compliance_report(report_a)

    print("\n━━━  Scenario B: Conservative multiplier (expect clean)  ━━━━━")
    df_sim_b = simulate(df_raw, threshold=25, multiplier=1.20)
    report_b  = check_compliance(df_sim_b)
    print_compliance_report(report_b)

    # ── Structural assertions ────────────────────────────────────────────────
    for report, label in [(report_a, "A"), (report_b, "B")]:
        assert isinstance(report["violations_count"], int),   f"{label}: count type"
        assert isinstance(report["violation_percentage"], float), f"{label}: pct type"
        assert isinstance(report["is_deployable"], bool),     f"{label}: deployable type"
        assert set(report["violations_by_segment"]) == {"<25", "25-40", ">40"}, \
            f"{label}: segment keys"
        seg_sum = sum(
            s["violation_count"] for s in report["violations_by_segment"].values()
        )
        assert seg_sum == report["violations_count"], \
            f"{label}: segment counts {seg_sum} ≠ total {report['violations_count']}"
        assert len(report["sample_violations"]) <= 5, f"{label}: sample size"

    # Original df untouched
    assert "any_violation" not in df_raw.columns
    assert "pct_change"    not in df_raw.columns

    assert not report_a["is_deployable"], "Scenario A should be blocked"

    print("  All assertions passed ✓\n")