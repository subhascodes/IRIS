"""
Actuarial Portfolio Impact Analysis
=====================================
Evaluates the financial and distributional impact of a pricing simulation
across the full policy portfolio and by age segment.

analyze(df) → dict
  Accepts the enriched DataFrame produced by simulation.simulate()
  and returns a structured actuarial impact report.
"""

import numpy as np
import pandas as pd

# ── Constants ────────────────────────────────────────────────────────────────
DELTA_TOLERANCE: float = 0.005          # cents-level zero test (float safety)
PRECISION:       int   = 4              # decimal places for rate/percentage output
AGE_BINS:   list = [0,   25,  40,  120]
AGE_LABELS: list = ["<25", "25-40", ">40"]
REQUIRED_COLS = {"customer_age", "base_rate", "current_premium",
                 "new_premium", "premium_delta"}


# ── Validation ───────────────────────────────────────────────────────────────
def _validate(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame missing required columns: {missing}")
    if df.empty:
        raise ValueError("DataFrame must not be empty.")
    for col in REQUIRED_COLS:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise TypeError(f"Column '{col}' must be numeric; got {df[col].dtype}.")
    if df["premium_delta"].isnull().any():
        raise ValueError("premium_delta contains null values — run simulation first.")


# ── Segment labeller (vectorized, no loops) ──────────────────────────────────
def _assign_segments(age: pd.Series) -> pd.Series:
    """Bin customer_age into actuarial age bands using pd.cut (single C pass)."""
    return pd.cut(
        age,
        bins=AGE_BINS,
        labels=AGE_LABELS,
        right=False,          # intervals: [0,25), [25,40), [40,120)
    ).astype(str)


# ── Per-segment metric aggregation (pure groupby, no loops) ─────────────────
def _segment_metrics(df: pd.DataFrame) -> dict:
    """
    Group by age_segment and compute actuarial metrics in one aggregation pass.
    Returns a nested dict keyed by segment label.
    """
    grp = df.groupby("_segment", observed=True)

    agg = grp.agg(
        count          = ("premium_delta", "count"),
        avg_change     = ("premium_delta", "mean"),
        total_delta    = ("premium_delta", "sum"),
        affected_count = ("_affected",     "sum"),
        avg_new_prem   = ("new_premium",   "mean"),
        avg_cur_prem   = ("current_premium","mean"),
    )

    # Percentage affected per segment (vectorized over agg frame)
    agg["pct_affected"] = (agg["affected_count"] / agg["count"] * 100).round(PRECISION)
    agg["avg_change"]   = agg["avg_change"].round(PRECISION)
    agg["avg_new_prem"] = agg["avg_new_prem"].round(PRECISION)
    agg["avg_cur_prem"] = agg["avg_cur_prem"].round(PRECISION)
    agg["total_delta"]  = agg["total_delta"].round(PRECISION)

    # Build output dict — iterate over agg rows (3 rows max, not N rows)
    result = {}
    for segment, row in agg.iterrows():
        result[segment] = {
            "count":           int(row["count"]),
            "avg_premium_change": float(row["avg_change"]),
            "pct_affected":    float(row["pct_affected"]),
            "total_delta":     float(row["total_delta"]),
            "avg_new_premium": float(row["avg_new_prem"]),
            "avg_current_premium": float(row["avg_cur_prem"]),
        }

    # Guarantee all three labels present even if a segment has zero policies
    for label in AGE_LABELS:
        if label not in result:
            result[label] = {
                "count": 0, "avg_premium_change": 0.0,
                "pct_affected": 0.0, "total_delta": 0.0,
                "avg_new_premium": 0.0, "avg_current_premium": 0.0,
            }

    return result


# ── Main entry point ─────────────────────────────────────────────────────────
def analyze(df: pd.DataFrame) -> dict:
    """
    Compute portfolio-level and segment-level actuarial impact metrics.

    Parameters
    ----------
    df : Enriched DataFrame returned by simulation.simulate().
         Must contain: customer_age, base_rate, current_premium,
                       new_premium, premium_delta.

    Returns
    -------
    dict with keys:
        total_policies    – int
        affected_policies – int   (|premium_delta| > DELTA_TOLERANCE)
        pct_affected      – float (%)
        avg_change        – float ($)
        total_portfolio_delta – float ($)
        avg_new_premium   – float ($)
        avg_current_premium – float ($)
        segment_analysis  – dict keyed by "<25", "25-40", ">40"
    """
    _validate(df)

    # ── Work on a lightweight projection — no full copy needed ───────────────
    work = df[list(REQUIRED_COLS)].copy()

    # ── Derived boolean mask: policy is "affected" if delta is non-trivial ───
    work["_affected"] = (work["premium_delta"].abs() > DELTA_TOLERANCE).astype(np.int8)

    # ── Age segmentation (single vectorized pd.cut call) ────────────────────
    work["_segment"] = _assign_segments(work["customer_age"])

    # ── Portfolio-level metrics ──────────────────────────────────────────────
    total_policies    = len(work)
    affected_policies = int(work["_affected"].sum())
    pct_affected      = round(affected_policies / total_policies * 100, PRECISION)
    avg_change        = round(work["premium_delta"].mean(), PRECISION)
    total_delta       = round(work["premium_delta"].sum(), PRECISION)
    avg_new_premium   = round(work["new_premium"].mean(), PRECISION)
    avg_cur_premium   = round(work["current_premium"].mean(), PRECISION)

    # ── Segment-level metrics ────────────────────────────────────────────────
    segment_analysis = _segment_metrics(work)

    return {
        "total_policies":         total_policies,
        "affected_policies":      affected_policies,
        "pct_affected":           pct_affected,
        "avg_change":             avg_change,
        "total_portfolio_delta":  total_delta,
        "avg_new_premium":        avg_new_premium,
        "avg_current_premium":    avg_cur_premium,
        "segment_analysis":       segment_analysis,
    }


# ── Pretty-print helper ──────────────────────────────────────────────────────
def print_report(report: dict) -> None:
    """Human-readable actuarial impact report for terminal review."""
    seg = report["segment_analysis"]

    print("=" * 62)
    print("  ACTUARIAL PORTFOLIO IMPACT REPORT")
    print("=" * 62)

    print("\n── Portfolio Summary ───────────────────────────────────────")
    print(f"  Total policies          : {report['total_policies']:>8,}")
    print(f"  Affected policies       : {report['affected_policies']:>8,}")
    print(f"  % Affected              : {report['pct_affected']:>8.2f}%")
    print(f"  Avg current premium     : ${report['avg_current_premium']:>10,.2f}")
    print(f"  Avg new premium         : ${report['avg_new_premium']:>10,.2f}")
    print(f"  Avg premium change      : ${report['avg_change']:>+10,.2f}")
    print(f"  Total portfolio delta   : ${report['total_portfolio_delta']:>+12,.2f}")

    print("\n── Segment Analysis ────────────────────────────────────────")
    header = f"  {'Segment':<10} {'Policies':>10} {'% Affected':>12} "
    header += f"{'Avg Cur $':>12} {'Avg New $':>12} {'Avg Δ':>12} {'Total Δ':>14}"
    print(header)
    print("  " + "-" * 84)

    for label in AGE_LABELS:
        s = seg[label]
        row = (
            f"  {label:<10}"
            f"  {s['count']:>8,}"
            f"  {s['pct_affected']:>10.1f}%"
            f"  ${s['avg_current_premium']:>10,.2f}"
            f"  ${s['avg_new_premium']:>10,.2f}"
            f"  ${s['avg_premium_change']:>+10,.2f}"
            f"  ${s['total_delta']:>+12,.2f}"
        )
        print(row)

    print()


# ── Self-test / demo ─────────────────────────────────────────────────────────
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
    df_sim = simulate(df_raw, threshold=25, multiplier=1.85)

    report = analyze(df_sim)
    print_report(report)

    # ── Structural assertions ────────────────────────────────────────────────
    assert set(report.keys()) == {
        "total_policies", "affected_policies", "pct_affected",
        "avg_change", "total_portfolio_delta", "avg_new_premium",
        "avg_current_premium", "segment_analysis",
    }
    assert set(report["segment_analysis"].keys()) == {"<25", "25-40", ">40"}
    assert report["total_policies"] == len(df_sim)
    assert 0.0 <= report["pct_affected"] <= 100.0
    assert report["affected_policies"] <= report["total_policies"]

    # ── Segment count integrity ──────────────────────────────────────────────
    seg_total = sum(s["count"] for s in report["segment_analysis"].values())
    assert seg_total == report["total_policies"], \
        f"Segment counts {seg_total} ≠ total policies {report['total_policies']}"

    # ── Total delta consistency ──────────────────────────────────────────────
    seg_delta = sum(s["total_delta"] for s in report["segment_analysis"].values())
    assert abs(seg_delta - report["total_portfolio_delta"]) < 0.10, \
        f"Segment delta sum {seg_delta} ≠ portfolio delta {report['total_portfolio_delta']}"

    print("  All assertions passed ✓\n")