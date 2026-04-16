---
name: compliance_decision
description: "Use when: validating pricing rule against regulatory caps and making final approval decision. Checks absolute/percentage premium caps, portfolio breadth, financial impact; outputs APPROVE or REJECT with reason."
---

# Compliance & Decision Skill

## Purpose
Validate simulated pricing rule against regulatory constraints and make final governance decision. Combines two evaluations:

1. **Compliance**: Check for individual policy violations (absolute/% caps)
2. **Decision**: Apply portfolio-level gates and output APPROVE/REJECT

## Input Parameters
```json
{
  "simulated_dataframe": "df",
  "analysis_result": "{...}",
  "verbose": false
}
```

## Process

### Compliance Check
1. **Absolute Cap**: Flag policies with premium_delta > $500
2. **Percentage Cap**: Flag policies with %(delta / current_premium) > 30%
3. **Violation Count**: Aggregate violations by type
4. **Sample Rows**: Return 5 violating policies for human review

### Decision Gate (in order, first match wins)
1. **Compliance Gate**: Any violation → **REJECT** (non-negotiable)
2. **Financial Gate**: avg_change > $300 → **REJECT** (portfolio impact too high)
3. **Breadth Gate**: pct_affected > 50% → **REJECT** (too many customers affected)
4. **Default**: **APPROVE** (all gates passed)

## Output
```json
{
  "status": "ok",
  "compliance": {
    "violations_count": 127,
    "violation_percentage": 1.27,
    "absolute_cap_violations": 87,
    "percentage_cap_violations": 40,
    "is_deployable": false,
    "sample_violations": [
      {
        "policy_id": "POL-00001",
        "customer_age": 22,
        "age_group": "<25",
        "current_premium": 450.00,
        "new_premium": 967.50,
        "premium_delta": 517.50,
        "pct_change": 114.89,
        "violation_absolute": true,
        "violation_pct": true
      }
    ]
  },
  "decision": {
    "decision": "REJECT",
    "reason": "Compliance violations detected: 127 policies exceed absolute premium cap ($500). Suggest reducing multiplier or adjusting threshold.",
    "confidence": 1.0,
    "risk_summary": {
      "total_policies": 10000,
      "affected_policies": 3200,
      "pct_affected": 32.0,
      "avg_premium_change": 45.67
    }
  },
  "processing_time_ms": 156
}
```

## Decision Reasons (Examples)

| Decision | Reason |
|----------|--------|
| APPROVE | "Rule impact within acceptable bounds. 1.27% of policies have compliance violations (below 5% threshold)." |
| REJECT | "Compliance violations detected: 127 policies exceed absolute premium cap ($500)." |
| REJECT | "Portfolio impact too high: 67% of customers affected (threshold: 50%)." |
| REJECT | "Average premium increase of $450 exceeds financial impact gate ($300)." |

## Regulatory Caps (Tunable)

| Cap | Value | Rationale |
|-----|-------|-----------|
| Absolute | $500 | Mirrors state DOI prior-approval threshold (CA, NY, FL) |
| Percentage | 30% | NAIC model rate-filing guideline |
| Financial | $300 | Internal portfolio impact ceiling |
| Breadth | 50% | Max portfolio exposure per governance policy |

## Performance
- Typical processing: 150ms - 400ms (vectorized validation + decision tree)
- Memory: ~1x input DataFrame size
- Scales linearly with policy count
