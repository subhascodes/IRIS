---
name: simulation
description: "Use when: applying a pricing rule (age threshold + multiplier) across the portfolio to simulate rule impact. Produces DataFrame with simulated premiums and deltas for downstream analysis."
---

# Simulation Skill

## Purpose
Apply age-conditional pricing multiplier to the full portfolio. Simulates what happens if a pricing rule is deployed.

## Input Parameters
```json
{
  "threshold": 30,
  "multiplier": 1.5,
  "override_guard": false
}
```

**Parameters:**
- `threshold` (float): Age below which policies receive elevated multiplier (18-65)
- `multiplier` (float): Applied to young segment; default 1.2 for others (1.0-5.0)
- `override_guard` (bool): Bypass multiplier guard rail if >5.0

## Process

1. **Validation**: Check threshold/multiplier are sensible
2. **Vectorized Calc**: Conditional multiplier applied to all policies in one pass
3. **Premium Update**: new_premium = current_premium × multiplier
4. **Delta Calc**: premium_delta = new_premium - current_premium
5. **Immutability**: Original DataFrame never modified (returns copy)

## Output Dataframe Columns (Appended)
```
risk_multiplier  (float64)  - multiplier applied to each policy
new_premium      (float64)  - re-priced premium (rounded to cents)
premium_delta    (float64)  - dollar change (new - current)
```

## Example
```
Input:
  customer_age=28, current_premium=500, threshold=30, multiplier=1.5
Output:
  risk_multiplier=1.5, new_premium=750.00, premium_delta=250.00

Input:
  customer_age=45, current_premium=500, threshold=30, multiplier=1.5
Output:
  risk_multiplier=1.2 (default), new_premium=600.00, premium_delta=100.00
```

## Guardrails
- Multiplier must be positive: 0 < m ≤ 5.0
- Threshold must be in [18, 65]
- Minimum premium floor: $1.00
- All premiums rounded to nearest cent

## Output
```json
{
  "status": "ok",
  "policies_affected": 3200,
  "policies_unchanged": 6800,
  "portfolio_avg_delta": 45.67,
  "min_delta": -50.00,
  "max_delta": 750.00,
  "dataframe_hash": "df-abc123...",
  "processing_time_ms": 145
}
```

## Performance
- Typical processing: 200ms - 1000ms (vectorized, no loops)
- Memory: ~2x input DataFrame size (copy + new columns)
- Scales linearly with portfolio size
