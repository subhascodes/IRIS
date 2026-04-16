"""
Insurance Pricing Simulation Engine
=====================================
Portfolio-wide premium re-pricing simulation using vectorized operations.

simulate(df, threshold, multiplier)
  - Applies age-conditional risk multiplier across the full portfolio
  - Returns an enriched copy; original dataframe is never mutated
  - All arithmetic is float64 for numerical stability
"""

import numpy as np
import pandas as pd

# ── Constants ────────────────────────────────────────────────────────────────
DEFAULT_MULTIPLIER: float = 1.20          # standard book multiplier (non-triggered)
PREMIUM_PRECISION: int    = 2             # cents-level rounding (carrier standard)
MIN_PREMIUM:       float  = 1.0           # floor: premium must be positive
MAX_MULTIPLIER:    float  = 10.0          # guard rail: implausible if exceeded


# ── Validation helpers ───────────────────────────────────────────────────────
def _validate_inputs(df: pd.DataFrame, threshold: float, multiplier: float) -> None:
    """Fail fast on bad inputs before touching any data."""
    required_cols = {"customer_age", "base_rate", "current_premium"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame is missing required columns: {missing}")

    if df.empty:
        raise ValueError("DataFrame must not be empty.")

    if not np.isfinite(threshold):
        raise ValueError(f"threshold must be a finite number; got {threshold!r}.")

    if not np.isfinite(multiplier) or multiplier <= 0:
        raise ValueError(
            f"multiplier must be a finite positive number; got {multiplier!r}."
        )

    if multiplier > MAX_MULTIPLIER:
        raise ValueError(
            f"multiplier {multiplier} exceeds guard-rail ceiling {MAX_MULTIPLIER}. "
            "Pass override_guard=True to bypass."
        )

    for col in ("customer_age", "base_rate", "current_premium"):
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise TypeError(f"Column '{col}' must be numeric; got {df[col].dtype}.")

    if (df["base_rate"] <= 0).any():
        raise ValueError("base_rate contains non-positive values — check your data.")


# ── Core simulation ──────────────────────────────────────────────────────────
def simulate(
    df: pd.DataFrame,
    threshold: float,
    multiplier: float,
    override_guard: bool = False,
) -> pd.DataFrame:
    """
    Apply age-conditional risk multiplier to every policy in the portfolio.

    Parameters
    ----------
    df          : Source insurance DataFrame (never mutated).
    threshold   : Age threshold. Policies with customer_age < threshold
                  receive `multiplier`; all others receive DEFAULT_MULTIPLIER (1.20).
    multiplier  : Risk multiplier applied to high-risk (young) segment.
    override_guard : Set True to bypass the MAX_MULTIPLIER guard rail.

    Returns
    -------
    pd.DataFrame
        Copy of df with three new columns appended:
          risk_multiplier  – float64, per-policy multiplier applied
          new_premium      – float64, re-priced premium (rounded to cents)
          premium_delta    – float64, new_premium − current_premium
    """
    # ── Relax guard if caller explicitly opts out ────────────────────────────
    _max = float("inf") if override_guard else MAX_MULTIPLIER
    if not override_guard and multiplier > MAX_MULTIPLIER:
        raise ValueError(
            f"multiplier {multiplier} exceeds guard-rail ceiling {MAX_MULTIPLIER}. "
            "Pass override_guard=True to bypass."
        )

    _validate_inputs(df, threshold, multiplier)

    # ── Immutable copy — original df is NEVER modified ───────────────────────
    out = df.copy()

    # ── Cast critical columns to float64 for numerical stability ─────────────
    age       = out["customer_age"].astype(np.float64)
    base_rate = out["base_rate"].astype(np.float64)
    current_p = out["current_premium"].astype(np.float64)

    # ── Vectorized conditional multiplier (no Python loops) ──────────────────
    #    np.where broadcasts across the full Series in a single C-level pass
    risk_multiplier: pd.Series = np.where(
        age < float(threshold),
        float(multiplier),          # triggered: young / high-risk segment
        float(DEFAULT_MULTIPLIER),  # default:   mature / standard segment
    )
    risk_multiplier = pd.Series(risk_multiplier, index=out.index, dtype=np.float64)

    # ── Premium calculations ─────────────────────────────────────────────────
    new_premium_raw: pd.Series = current_p * (risk_multiplier / 1.2)

    # Enforce minimum premium floor and round to carrier precision
    new_premium: pd.Series = (
        new_premium_raw
        .clip(lower=MIN_PREMIUM)
        .round(PREMIUM_PRECISION)
    )

    premium_delta: pd.Series = (new_premium - current_p).round(PREMIUM_PRECISION)

    # ── Attach new columns ───────────────────────────────────────────────────
    out["risk_multiplier"] = risk_multiplier
    out["new_premium"]     = new_premium
    out["premium_delta"]   = premium_delta

    return out


# ── Quick self-test / demo ───────────────────────────────────────────────────
if __name__ == "__main__":
    import os

    DATA_PATH = "data/dataset.csv"
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Dataset not found at '{DATA_PATH}'. "
            "Run generate_insurance_data.py first."
        )

    df_raw = pd.read_csv(DATA_PATH)

    THRESHOLD  = 25     # age threshold (years)
    MULTIPLIER = 1.85   # young-driver surcharge multiplier

    print("=" * 62)
    print("  INSURANCE PRICING SIMULATION ENGINE")
    print("=" * 62)
    print(f"\n  Threshold  : customer_age < {THRESHOLD}")
    print(f"  Multiplier : {MULTIPLIER}  (triggered segment)")
    print(f"  Default    : {DEFAULT_MULTIPLIER}  (standard segment)\n")

    df_sim = simulate(df_raw, threshold=THRESHOLD, multiplier=MULTIPLIER)

    # ── Confirm original is untouched ────────────────────────────────────────
    assert "risk_multiplier" not in df_raw.columns, "MUTATION DETECTED on original df!"
    assert list(df_sim.columns[:len(df_raw.columns)]) == list(df_raw.columns), \
        "Original columns were reordered or dropped!"

    triggered = df_sim["risk_multiplier"] == MULTIPLIER
    standard  = ~triggered

    print("── Segment Breakdown ───────────────────────────────────────")
    print(f"  Triggered  (age < {THRESHOLD}) : {triggered.sum():>5,} policies")
    print(f"  Standard   (age ≥ {THRESHOLD}) : {standard.sum():>5,} policies")

    print("\n── Premium Delta Summary ───────────────────────────────────")
    d = df_sim["premium_delta"]
    print(f"  Total portfolio delta  : ${d.sum():>12,.2f}")
    print(f"  Mean delta per policy  : ${d.mean():>12,.2f}")
    print(f"  Triggered seg mean Δ   : ${d[triggered].mean():>12,.2f}")
    print(f"  Standard  seg mean Δ   : ${d[standard].mean():>12,.2f}")
    print(f"  Max single-policy Δ    : ${d.max():>12,.2f}")
    print(f"  Min single-policy Δ    : ${d.min():>12,.2f}")

    print("\n── New Premium Distribution ────────────────────────────────")
    np_ = df_sim["new_premium"]
    print(f"  Min    : ${np_.min():>10,.2f}")
    print(f"  Mean   : ${np_.mean():>10,.2f}")
    print(f"  Median : ${np_.median():>10,.2f}")
    print(f"  Max    : ${np_.max():>10,.2f}")

    print("\n── Sample Rows (5 triggered, 3 standard) ───────────────────")
    cols = ["policy_id", "customer_age", "base_rate",
            "current_premium", "risk_multiplier", "new_premium", "premium_delta"]
    sample = pd.concat([
        df_sim[triggered][cols].head(5),
        df_sim[standard][cols].head(3),
    ])
    print(sample.to_string(index=False))

    print("\n── All Assertions Passed ✓ ─────────────────────────────────\n")