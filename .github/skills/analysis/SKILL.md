---
name: analysis
description: "Use when: computing portfolio-wide and segment-level actuarial impact metrics. Produces structured report of premium changes, affected policies, and exposure by age band."
---

# Analysis Skill

## Purpose
Compute portfolio-level and segment-level impact metrics from simulated datasets. Answers: How many customers are affected? What is the average change by age group? What is total portfolio exposure?

## Input Parameters
```json
{
  "simulated_dataframe": "df",
  "segment_by": "age_group",
  "precision": 4
}
```

**Parameters:**
- `simulated_dataframe`: DataFrame from simulation skill (with premium_delta column)
- `segment_by`: Column to group by (default: age_group)
- `precision`: Decimal places for rounding (default: 4)

## Process

1. **Validation**: Ensure required columns (premium_delta, age_group, etc.)
2. **Portfolio Aggregation**: Count affected, sum deltas, compute mean change
3. **Percentage Affected**: affected_count / total_count
4. **Segment Breakdown**: Group by age band; compute each segment's metrics
5. **Rounding**: Apply precision rounding for output consistency

## Output
```json
{
  "status": "ok",
  "total_policies": 10000,
  "affected_policies": 3200,
  "pct_affected": 32.0,
  "avg_premium_change": 45.67,
  "total_portfolio_delta": 456700.00,
  "min_change": -50.00,
  "max_change": 750.00,
  "segments": {
    "<25": {
      "count": 2100,
      "affected_count": 2100,
      "pct_affected": 100.0,
      "avg_premium_change": 67.89,
      "total_delta": 142597.00,
      "avg_new_premium": 567.89,
      "avg_current_premium": 499.99
    },
    "25-40": {
      "count": 6500,
      "affected_count": 1300,
      "pct_affected": 20.0,
      "avg_premium_change": 23.45,
      "total_delta": 30485.00,
      "avg_new_premium": 523.45,
      "avg_current_premium": 500.00
    },
    ">40": {
      "count": 1400,
      "affected_count": 70,
      "pct_affected": 5.0,
      "avg_premium_change": 5.00,
      "total_delta": 350.00,
      "avg_new_premium": 505.00,
      "avg_current_premium": 500.00
    }
  },
  "processing_time_ms": 87
}
```

## Key Metrics
| Metric | Definition |
|--------|-----------|
| `total_policies` | Total policies in portfolio |
| `affected_policies` | Count with premium_delta > $0.01 |
| `pct_affected` | (affected / total) × 100 |
| `avg_premium_change` | Mean of all premium_delta values |
| `segments` | Breakdown by age_group |

## Age Segments
- `<25`: Customer age in [0, 25)
- `25-40`: Customer age in [25, 40)
- `>40`: Customer age in [40, 120)

## Performance
- Typical processing: 100ms - 300ms (groupby aggregation)
- Memory: ~1x input DataFrame size
- Scales logarithmically with number of segments
