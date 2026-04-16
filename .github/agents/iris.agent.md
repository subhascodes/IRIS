---
name: iris
description: IRIS - Insurance Rule Impact Simulation System. Autonomously simulates portfolio-level pricing rule impact, evaluates compliance, makes deterministic decisions, and maintains audit logs. Use for portfolio impact analysis, compliance validation, rule evaluation, and audit trails. Fully deterministic, observable, safe.
---

# IRIS Agent

## Purpose
Autonomously simulate pricing rule impact on insurance portfolios: apply rules to 5,000+ policies, calculate financial impact, validate compliance constraints, make APPROVE/REJECT decisions, maintain immutable audit trail.

## Design Philosophy
- **Portfolio-Focused**: Full impact simulation across entire portfolio
- **Deterministic**: Same input → Always same decision (based on named constraints)
- **Observable**: Every decision fully auditable with immutable logs
- **Safe**: Protects credentials, never modifies audit history
- **Fast**: Full pipeline in ~65ms

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Orchestrator                         │
│                       (agent.py)                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Input: {threshold, multiplier, ...}                           │
│    ↓                                                            │
│  [1] Load Dataset (5,000 policies)                             │
│    ↓                                                            │
│  [2] Simulate Pricing Rule (apply to each policy)              │
│    ↓                                                            │
│  [3] Analyze Portfolio Impact (metrics, segments)              │
│    ↓                                                            │
│  [4] Validate Compliance + Decide (APPROVE/REJECT)             │
│    ↓                                                            │
│  [5] Log Decision (immutable audit trail)                      │
│    ↓                                                            │
│  Output: {decision, analysis, compliance, audit_id, ...}       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Skills

| Skill | Purpose | Function | Impact |
|-------|---------|----------|--------|
| data_ingest | Load 5,000 policies | pipeline._get_dataset() | Dataset in memory |
| simulation | Apply rule to portfolio | simulation.simulate() | Premium deltas |
| analysis | Calculate impact metrics | analysis.analyze() | Affected count, avg delta |
| compliance_decision | Check constraints & decide | compliance.check() + decision.make() | APPROVE/REJECT |
| audit | Log decision immutably | audit.log_audit() | Audit trail entry |

## Constraints (Source of Truth)

```python
MAX_SINGLE_POLICY_CHANGE = 0.50      # Max 50% per policy
MAX_PORTFOLIO_CHANGE = 0.15          # Max 15% avg change
MIN_PORTFOLIO_BREADTH = 0.10         # Min 10% affected
MAX_VIOLATION_RATE = 0.05            # Max 5% violations
```

## Output Format

```json
{
  "status": "success",
  "decision": "APPROVE" or "REJECT",
  "reason": "Human-readable explanation",
  "analysis": {
    "affected_policies": 450,
    "avg_change": 152.30,
    "total_portfolio_delta": 68535.00,
    "pct_affected": 9.0
  },
  "compliance": {
    "violations_count": 0,
    "is_deployable": true
  },
  "audit_id": "audit-20260416-xxxxx"
}
```

## Safety Features

✅ Credential Protection: Blocks access to data/credentials.json  
✅ Audit Integrity: Cannot delete/overwrite audit_log.csv  
✅ Code Protection: Cannot modify source files  
✅ Tool Restrictions: No arbitrary command execution  

## Integration Points

**CLI**: `python agent.py --task full_pipeline --threshold X --multiplier Y`  
**Python API**: `call_agent(task="full_pipeline", threshold=X, multiplier=Y)`  
**CI/CD**: Exit code 0 (APPROVE) or 1 (REJECT)  
