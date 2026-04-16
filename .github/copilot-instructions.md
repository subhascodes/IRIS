# IRIS: Insurance Rule Impact Simulation System

## Overview
This workspace contains **IRIS** (**Insurance Rule Impact Simulation** System) - a platform that autonomously simulates pricing rule impact on entire insurance portfolios, validates compliance, and makes deterministic deployment decisions.

## Agent Behavior & Principles

### Core Responsibilities
The IRIS Agent:
1. **Loads** policy dataset from `data/dataset.csv`
2. **Simulates** pricing rule impact using configurable threshold & multiplier
3. **Analyzes** financial and portfolio-wide effects
4. **Validates** regulatory compliance constraints
5. **Decides** whether to approve/reject the pricing rule
6. **Logs** outcome to append-only audit trail

### Safety & Compliance
- **Credential Protection**: Never reads or logs sensitive data from `data/credentials.json`
- **Deterministic Decisions**: All decisions derive from named constants; fully auditable
- **Append-Only Audit**: No mutations to historical audit records
- **Immutable Inputs**: All functions treat input DataFrames as read-only

### Default Execution Mode
```bash
# Full pipeline with defaults
python agent.py --task full_pipeline

# Or with custom rule parameters
python agent.py --task full_pipeline --threshold 30 --multiplier 1.5
```

## Available Skills

The agent dispatches work to five domain skills:

| Skill | Purpose | Inputs | Outputs |
|-------|---------|--------|---------|
| `data_ingest` | Load & validate policy dataset | `dataset_path` | `{'status': 'ok', 'rows': N, 'columns': [...]}` |
| `simulation` | Apply pricing multiplier rule | `threshold, multiplier` | Simulated DataFrame with deltas |
| `analysis` | Compute portfolio impact metrics | Simulated DataFrame | Impact report (segment breakdowns, avg change, %) |
| `compliance_decision` | Validate compliance & approve/reject | Impact + compliance analysis | Decision: APPROVE/REJECT + reason |
| `audit` | Log outcome to append-only trail | Rule config + decision | Write to `data/audit_log.csv` |

## Tool Restrictions

The agent is **restricted** from:
- Modifying source code files
- Deleting or overwriting audit logs
- Reading credential files
- Executing arbitrary shell commands
- Accessing external APIs without explicit approval

The agent **may**:
- Read policy dataset (`data/dataset.csv`)
- Write to audit log (append-only)
- Call Python functions via skills
- Emit structured logs to stdout/stderr

## Observability Hooks

Every agent execution logs:
- Timestamp (ISO 8601)
- Rule parameters (threshold, multiplier)
- Decision outcome (APPROVE/REJECT)
- Audit trail reference for traceability

View audit history:
```bash
# Last 10 decisions
tail -11 data/audit_log.csv

# Full audit trail
cat data/audit_log.csv
```

## Integration Points

### Streamlit UI (existing)
Continue using `app.py` as normal; the agent runs independently via CLI or API.

### CI/CD Pipeline
Integrate agent decision into approval workflow:
```bash
# In CI/CD
python agent.py --task full_pipeline --fail-on-reject
# Exit code 1 if rule rejected; 0 if approved
```

### Scheduled Tasks (Cron)
```bash
# Nightly rule evaluation (e.g., daily baseline multiplier check)
0 2 * * * cd /path/to/iris && python agent.py --task full_pipeline
```

## Error Handling & Recovery

- **Dataset missing**: Agent prints clear error, exits with code 1
- **Compliance violation**: Agent logs reason, outputs REJECT decision
- **Audit write failure**: Agent retries 3 times before failing
- **Invalid parameters**: Agent validates on entry; rejects non-sensical thresholds

## Extensions & Customization

To add a new skill or agent step:
1. Create `.github/skills/<name>/SKILL.md`
2. Implement Python wrapper in `agent.py`
3. Register skill in agent's `_SKILLS` registry
4. Add tests in `test_agent.py`
5. Update this document

## Key Files

- `agent.py` — Agent orchestrator & skill registry
- `.github/agents/iris.agent.md` — Agent metadata & tool whitelist
- `.github/skills/*/SKILL.md` — Domain skill definitions
- `.github/hooks/pretool.json` — Pre-execution security checks
- `test_agent.py` — Agent behavior tests
- `data/audit_log.csv` — Append-only decision history
