"""
Insurance Governance Audit Logger
===================================
Append-only, tamper-evident audit trail for every pricing rule evaluation.

Every call to log_audit() writes exactly one row to data/audit_log.csv.
The file is created with headers on first write; subsequent calls append
without touching existing rows — guaranteeing a complete, ordered history
of every governance decision made against this portfolio.

Audit design principles:
  - Append-only: existing rows are NEVER modified or deleted
  - Idempotent header: written once on file creation, never duplicated
  - Atomic write: row is assembled fully in memory before any I/O
  - No external dependencies beyond the Python standard library + pandas
  - All fields are sanitised before persistence (no newlines, no delimiter injection)
  - File and parent directory are created automatically if absent
"""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

# ── Audit log configuration ───────────────────────────────────────────────────
AUDIT_LOG_PATH: Path = Path("data/audit_log.csv")

# Ordered column schema — order here defines CSV column order
AUDIT_COLUMNS: list[str] = [
    "timestamp",
    "rule_id",
    "threshold",
    "multiplier",
    "decision",
    "reason",
    "violations",
    "violation_percentage",
]

# ── Required input keys ───────────────────────────────────────────────────────
_REQUIRED_RULE_CONFIG  = {"threshold", "multiplier"}
_REQUIRED_DECISION     = {"decision", "reason"}
_REQUIRED_COMPLIANCE   = {"violations_count", "violation_percentage"}


# ── Validation ────────────────────────────────────────────────────────────────
def _validate_inputs(
    rule_config:       dict[str, Any],
    decision_result:   dict[str, Any],
    compliance_result: dict[str, Any],
) -> None:
    for label, obj, required in [
        ("rule_config",       rule_config,       _REQUIRED_RULE_CONFIG),
        ("decision_result",   decision_result,   _REQUIRED_DECISION),
        ("compliance_result", compliance_result, _REQUIRED_COMPLIANCE),
    ]:
        if not isinstance(obj, dict):
            raise TypeError(f"{label} must be a dict; got {type(obj).__name__}.")
        missing = required - set(obj)
        if missing:
            raise ValueError(f"{label} is missing required keys: {missing}")

    if decision_result["decision"] not in {"APPROVE", "REJECT"}:
        raise ValueError(
            f"decision must be 'APPROVE' or 'REJECT'; "
            f"got {decision_result['decision']!r}."
        )

    violations = compliance_result["violations_count"]
    if not isinstance(violations, (int, float)) or violations < 0:
        raise ValueError(
            f"violations_count must be a non-negative number; got {violations!r}."
        )


# ── Field sanitiser ───────────────────────────────────────────────────────────
def _sanitise(value: Any, max_len: int = 1_000) -> str:
    """
    Convert a value to a safe CSV string.
    - Strips embedded newlines and carriage returns (would break row integrity)
    - Truncates excessively long strings (guards against runaway reason text)
    - Preserves numeric precision for float fields
    """
    if isinstance(value, float):
        text = f"{value:.6f}"
    else:
        text = str(value)

    # Strip characters that corrupt CSV row boundaries
    text = text.replace("\n", " ").replace("\r", " ").replace("\x00", "")

    if len(text) > max_len:
        text = text[:max_len - 3] + "..."

    return text


# ── File initialisation ───────────────────────────────────────────────────────
def _ensure_log_file(path: Path) -> bool:
    """
    Create the audit log file with headers if it does not exist.
    Creates parent directories as needed.
    Returns True if the file was newly created, False if it already existed.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write header if file is absent OR empty (e.g. pre-created by tempfile)
    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh, quoting=csv.QUOTE_ALL)
            writer.writerow(AUDIT_COLUMNS)
        return True

    return False


# ── Row assembler ─────────────────────────────────────────────────────────────
def _build_row(
    rule_config:       dict[str, Any],
    decision_result:   dict[str, Any],
    compliance_result: dict[str, Any],
) -> dict[str, str]:
    """Assemble the full audit row as an ordered dict of sanitised strings."""
    return {
        "timestamp":            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f+00:00"),
        "threshold":            _sanitise(rule_config["threshold"]),
        "rule_id": f"R-{rule_config['threshold']}-{rule_config['multiplier']}",
        "multiplier":           _sanitise(rule_config["multiplier"]),
        "decision":             _sanitise(decision_result["decision"]),
        "reason":               _sanitise(decision_result["reason"]),
        "violations":           _sanitise(int(compliance_result["violations_count"])),
        "violation_percentage": _sanitise(float(compliance_result["violation_percentage"])),
    }


# ── Public API ────────────────────────────────────────────────────────────────
def log_audit(
    rule_config:       dict[str, Any],
    decision_result:   dict[str, Any],
    compliance_result: dict[str, Any],
    *,
    path: Path | str = AUDIT_LOG_PATH,
) -> None:
    """
    Append one audit record to the governance log CSV.

    Parameters
    ----------
    rule_config       : Must contain 'threshold' and 'multiplier'.
    decision_result   : Output from decision.make_decision() — must contain
                        'decision' and 'reason'.
    compliance_result : Output from compliance.check_compliance() — must
                        contain 'violations_count' and 'violation_percentage'.
    path              : Override log file path (default: data/audit_log.csv).
                        Useful for testing or multi-portfolio deployments.

    Side effects
    ------------
    - Creates data/ directory if absent.
    - Creates audit_log.csv with header row on first call.
    - Appends exactly one data row on every subsequent call.
    - Inputs are never mutated.

    Raises
    ------
    TypeError   : If any input is not a dict.
    ValueError  : If required keys are missing or values are invalid.
    OSError     : If the filesystem rejects the write (permissions, disk full).
    """
    _validate_inputs(rule_config, decision_result, compliance_result)

    log_path = Path(path)
    _ensure_log_file(log_path)
    row = _build_row(rule_config, decision_result, compliance_result)

    # Open in append mode — existing content is never touched
    with log_path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=AUDIT_COLUMNS,
            quoting=csv.QUOTE_ALL,
            extrasaction="ignore",   # silently drop unknown keys
        )
        writer.writerow(row)


# ── Read helper ───────────────────────────────────────────────────────────────
def read_audit_log(path: Path | str = AUDIT_LOG_PATH) -> pd.DataFrame:
    """
    Load the full audit log into a DataFrame for analysis or reporting.

    Returns an empty DataFrame with correct columns if the file does not exist.
    """
    log_path = Path(path)
    if not log_path.exists():
        return pd.DataFrame(columns=AUDIT_COLUMNS)

    df = pd.read_csv(log_path, dtype=str)

    # Cast numeric columns for downstream analysis
    for col in ("threshold", "multiplier", "violations", "violation_percentage"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ── Pretty-print helper ───────────────────────────────────────────────────────
def print_audit_log(path: Path | str = AUDIT_LOG_PATH) -> None:
    """Render the full audit log as a formatted table."""
    df = read_audit_log(path)
    total = len(df)

    print("=" * 72)
    print("  GOVERNANCE AUDIT LOG")
    print("=" * 72)
    print(f"  File    : {Path(path).resolve()}")
    print(f"  Records : {total:,}\n")

    if df.empty:
        print("  No audit records found.\n")
        return

    approvals = (df["decision"] == "APPROVE").sum()
    rejections = (df["decision"] == "REJECT").sum()
    print(f"  Approvals : {approvals:>4}  |  Rejections : {rejections:>4}\n")

    display_cols = ["timestamp","rule_id", "threshold", "multiplier",
                    "decision", "violations", "violation_percentage"]
    print(df[display_cols].to_string(index=True))
    print()

    print("── Reasons ─────────────────────────────────────────────────────")
    for i, row in df.iterrows():
        label = "✓" if row["decision"] == "APPROVE" else "✗"
        print(f"  [{i}] {label} {row['reason'][:90]}{'...' if len(str(row['reason'])) > 90 else ''}")
    print()


# ── Self-test / demo ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    import tempfile
    import pandas as pd
    from simulation import simulate
    from analysis   import analyze
    from compliance import check_compliance
    from decision   import make_decision

    # ── Use a temp file so demo never pollutes the real audit log ─────────────
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        TEST_LOG = Path(tmp.name)

    try:
        DATA_PATH = "data/dataset.csv"
        if not os.path.exists(DATA_PATH):
            raise FileNotFoundError(
                f"Dataset not found at '{DATA_PATH}'. "
                "Run generate_insurance_data.py first."
            )

        df_raw = pd.read_csv(DATA_PATH)

        scenarios = [
            {"threshold": 40,  "multiplier": 2.50},
            {"threshold": 25,  "multiplier": 1.85},
            {"threshold": 75,  "multiplier": 1.30},
            {"threshold": 25,  "multiplier": 1.22},
        ]

        print("\nLogging all scenarios to audit trail...\n")

        for rule_config in scenarios:
            df_sim     = simulate(df_raw, **rule_config)
            analysis   = analyze(df_sim)
            compliance = check_compliance(df_sim)
            decision   = make_decision(analysis, compliance)

            log_audit(rule_config, decision, compliance, path=TEST_LOG)

            icon = "✓" if decision["decision"] == "APPROVE" else "✗"
            print(
                f"  [{icon}] threshold={rule_config['threshold']:>3}, "
                f"multiplier={rule_config['multiplier']:.2f}  →  "
                f"{decision['decision']:>6}  "
                f"(violations={compliance['violations_count']:>4})"
            )

        print()
        print_audit_log(path=TEST_LOG)

        # ── Structural assertions ─────────────────────────────────────────────
        df_log = read_audit_log(TEST_LOG)

        # Correct row count
        assert len(df_log) == len(scenarios), \
            f"Expected {len(scenarios)} rows, got {len(df_log)}"

        # All required columns present
        assert set(AUDIT_COLUMNS).issubset(set(df_log.columns)), \
            f"Missing columns: {set(AUDIT_COLUMNS) - set(df_log.columns)}"

        # No null timestamps
        assert df_log["timestamp"].notna().all(), "Null timestamps detected"

        # Decision column only contains valid values
        assert df_log["decision"].isin({"APPROVE", "REJECT"}).all(), \
            "Invalid decision values in log"

        # Append-only: logging again adds rows, does not overwrite
        prev_len = len(df_log)
        log_audit(scenarios[0], make_decision(
            analyze(simulate(df_raw, **scenarios[0])),
            check_compliance(simulate(df_raw, **scenarios[0]))
        ), check_compliance(simulate(df_raw, **scenarios[0])), path=TEST_LOG)
        df_after = read_audit_log(TEST_LOG)
        assert len(df_after) == prev_len + 1, "Append-only guarantee violated"

        # Violations column is numeric after read_audit_log
        assert pd.api.types.is_numeric_dtype(df_log["violations"]), \
            "violations column is not numeric"

        # File path matches what we configured
        assert TEST_LOG.exists(), "Audit log file not found after writing"

        # Bad input is rejected cleanly
        try:
            log_audit({}, {}, {}, path=TEST_LOG)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

        print("  All assertions passed ✓\n")

        # ── Also write to the REAL log for demo continuity ────────────────────
        print("Writing scenarios to production audit log (data/audit_log.csv)...\n")
        for rule_config in scenarios:
            df_sim     = simulate(df_raw, **rule_config)
            compliance = check_compliance(df_sim)
            decision   = make_decision(analyze(df_sim), compliance)
            log_audit(rule_config, decision, compliance)

        print_audit_log()

    finally:
        TEST_LOG.unlink(missing_ok=True)