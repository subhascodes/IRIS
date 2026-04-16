---
name: decision
description: "Use when: making final approval/rejection decision based on compliance metrics. Outputs APPROVE or REJECT verdict with reasoning derived from named safety constraints."
---

# Decision Skill

## Purpose

Makes deterministic, fully-auditable approval/rejection decisions based on compliance analysis.

## Input

Compliance metrics from `compliance_decision` skill:
- `violations_count`: Number of policies violating constraints
- `is_deployable`: Boolean indicating compliance pass/fail
- `violation_percentage`: % of portfolio with violations
- `violations_by_rule`: Breakdown of violation types

## Output

Structured decision:

```json
{
  "decision": "APPROVE|REJECT",
  "reason": "Human-readable explanation",
  "metrics": {
    "violations_count": 0,
    "violation_percentage": 0.0,
    "is_deployable": true
  }
}
```

## Decision Logic

**APPROVE** if:
- ✅ All policies within absolute premium cap ($500 max per policy)
- ✅ All policies within percentage cap (30% max per policy)
- ✅ Portfolio average change ≤ 15%
- ✅ Rule affects ≥ 10% of portfolio (breadth requirement)
- ✅ Violation rate ≤ 5%

**REJECT** if any constraint violated.

## Named Constants

All decision rules are derived from named constants in `compliance.py`:

```python
MAX_SINGLE_POLICY_CHANGE = 0.5        # 50% max single policy
MAX_PORTFOLIO_CHANGE = 0.15           # 15% max portfolio avg
MIN_PORTFOLIO_BREADTH = 0.1           # 10% min affected policies
MAX_VIOLATION_RATE = 0.05             # 5% max violations
```

## Audit Trail

Each decision is logged with all constraints for reproducibility:

```csv
timestamp,agent_version,rule_id,decision,reason,violation_count,is_deployable
2026-04-14T18:19:46.595663+00:00,1.0.0,R-25-1.5,REJECT,Violates absolute premium cap,613,false
```

## Implementation

Called after `compliance_decision` analysis. Used by `agent.py` in full pipeline.

## Related Skills

- `compliance_decision` — Validates constraints
- `audit` — Logs final decision
