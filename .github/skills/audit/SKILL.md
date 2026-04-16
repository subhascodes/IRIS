---
name: audit
description: "Use when: logging governance decision to append-only audit trail. Writes one immutable row per decision to audit_log.csv with timestamp, rule params, decision, reason, and compliance metrics."
---

# Audit Skill

## Purpose
Persist governance decision to tamper-evident append-only audit log. Guaranteed immutability: existing rows are never modified or deleted; new rows are appended only.

## Input Parameters
```json
{
  "rule_config": {"threshold": 30, "multiplier": 1.5},
  "decision_result": {"decision": "APPROVE", "reason": "..."},
  "compliance_result": {"violations_count": 127, "violation_percentage": 1.27}
}
```

## Process

1. **Validation**: Ensure all inputs are properly typed, non-null
2. **Sanitization**: Strip embedded newlines, limit text length (prevent injection)
3. **File Check**: Create audit log if missing (write header once)
4. **Atomic Append**: Assemble row in memory, write single line, fsync to disk
5. **Verification**: Read back row; confirm it matches what was written

## Schema (CSV)

| Column | Type | Example |
|--------|------|---------|
| `timestamp` | ISO 8601 | `2026-04-14T15:30:00Z` |
| `rule_id` | string | `rule-20260414-001` |
| `threshold` | float | `30` |
| `multiplier` | float | `1.5` |
| `decision` | string | `APPROVE` \| `REJECT` |
| `reason` | text | `"Portfolio impact within..."` |
| `violations` | int | `127` |
| `violation_percentage` | float | `1.27` |

## Output
```json
{
  "status": "ok",
  "audit_id": "audit-20260414-001",
  "log_path": "data/audit_log.csv",
  "row_number": 42,
  "timestamp_written": "2026-04-14T15:30:00.123456Z",
  "row_data": {
    "timestamp": "2026-04-14T15:30:00Z",
    "rule_id": "rule-20260414-001",
    "threshold": 30,
    "multiplier": 1.5,
    "decision": "REJECT",
    "reason": "Compliance violations detected...",
    "violations": 127,
    "violation_percentage": 1.27
  }
}
```

## Error Codes
- `validation_error`: Input validation failed (malformed inputs)
- `write_failure`: Could not write to audit log (permissions, disk full)
- `verification_failed`: Written row doesn't match input (corruption detected)
- `unknown_error`: Unexpected error during write

## Audit Log Example

```csv
timestamp,rule_id,threshold,multiplier,decision,reason,violations,violation_percentage
2026-04-14T15:00:00Z,rule-20260414-001,30,1.5,APPROVE,Rule impact within acceptable bounds.,0,0.0
2026-04-14T15:15:00Z,rule-20260414-002,25,1.8,REJECT,Compliance violations detected: 245 policies...,245,2.45
2026-04-14T15:30:00Z,rule-20260414-003,35,1.2,APPROVE,Portfolio impact within bounds; 0.05% violations.,5,0.05
```

## Immutability Guarantees

- ✓ Rows never deleted: full history preserved
- ✓ Rows never modified: updates append as new entry
- ✓ Row order preserved: timestamp + insertion order
- ✓ No duplicates: each decision gets unique audit_id
- ✓ Atomicity: either entire row written or none (no partial writes)

## Query Examples

```bash
# Approve rate over time
awk -F',' '$5 == "APPROVE" { count++ } END { print count "/" NR }' data/audit_log.csv

# Rejections with reason
awk -F',' '$5 == "REJECT" { print $3 "," $4 "," $6 }' data/audit_log.csv

# High violation decisions
awk -F',' '$8 > 5.0 { print $0 }' data/audit_log.csv
```

## Performance
- Typical processing: 10ms - 50ms (I/O bound)
- File size: ~500 bytes per row; 10k rows ≈ 5MB
- Disk: SSD recommended; requires fsync for durability
- Concurrency: Single-writer (agent is single-threaded per execution)
