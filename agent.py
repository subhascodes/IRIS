"""
Guidewire Agentic AI Orchestrator
==================================
Autonomous insurance governance system that orchestrates policy pricing rule
evaluation, compliance checking, and audit logging.

Entry point:
  python agent.py --task full_pipeline --threshold 30 --multiplier 1.5

Execution order (deterministic):
  [1] Load Dataset
  [2] Simulate Pricing Rule
  [3] Analyze Portfolio Impact
  [4] Validate Compliance & Decide
  [5] Log Outcome to Audit Trail

Design Principles:
  - Deterministic: all decisions derive from named constants
  - Observable: every step emits structured logs
  - Safe: restricts file access, cannot modify audit history
  - Composable: skills are independent, can mix/match
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

import pandas as pd

# ── Domain modules ────────────────────────────────────────────────────────────
from pipeline import get_cache_status, invalidate_cache, _get_dataset
from simulation import simulate
from analysis import analyze
from compliance import check_compliance
from decision import make_decision
from audit import log_audit

# ── Constants ────────────────────────────────────────────────────────────────
AGENT_VERSION = "1.0.0"
DATASET_PATH = os.getenv("GUIDEWIRE_DATASET_PATH", "data/dataset.csv")
AUDIT_PATH = os.getenv("GUIDEWIRE_AUDIT_PATH", "data/audit_log.csv")

# ── Skill registry ────────────────────────────────────────────────────────────
_SKILLS = {
    "data_ingest",
    "simulation",
    "analysis",
    "compliance_decision",
    "audit",
    "full_pipeline",
    "dry_run",
}

# ── Decision thresholds (single source of truth) ───────────────────────────────
THRESHOLD_MIN, THRESHOLD_MAX = 18, 65
MULTIPLIER_MIN, MULTIPLIER_MAX = 1.0, 5.0


# ── Validation ────────────────────────────────────────────────────────────────
def _validate_rule_params(threshold: float, multiplier: float) -> None:
    """Fail fast on invalid rule parameters."""
    if not isinstance(threshold, (int, float)) or not THRESHOLD_MIN <= threshold <= THRESHOLD_MAX:
        raise ValueError(f"threshold must be in [{THRESHOLD_MIN}, {THRESHOLD_MAX}]; got {threshold}")
    if not isinstance(multiplier, (int, float)) or not (MULTIPLIER_MIN <= multiplier <= MULTIPLIER_MAX):
        raise ValueError(f"multiplier must be in [{MULTIPLIER_MIN}, {MULTIPLIER_MAX}]; got {multiplier}")


def _validate_args(args: argparse.Namespace) -> None:
    """Validate CLI arguments."""
    if args.task not in _SKILLS:
        raise ValueError(f"task must be one of {_SKILLS}; got {args.task}")
    if args.task in ("full_pipeline", "dry_run", "simulation", "analysis", "compliance_decision", "audit"):
        _validate_rule_params(args.threshold, args.multiplier)


# ── Skill implementations ────────────────────────────────────────────────────
def _skill_data_ingest(dataset_path: str) -> tuple[pd.DataFrame, dict]:
    """Load and validate dataset. Returns (DataFrame, metadata)."""
    try:
        df = _get_dataset()
        metadata = {
            "status": "ok",
            "rows": len(df),
            "columns": list(df.columns),
            "timestamp_loaded": datetime.now(timezone.utc).isoformat(),
        }
        return df, metadata
    except Exception as e:
        raise RuntimeError(f"[data_ingest] Failed to load dataset: {e}")


def _skill_simulation(df: pd.DataFrame, threshold: float, multiplier: float) -> tuple[pd.DataFrame, dict]:
    """Simulate pricing rule. Returns (simulated DataFrame, metadata)."""
    try:
        df_sim = simulate(df, threshold, multiplier)
        metadata = {
            "status": "ok",
            "policies_affected": (df_sim["premium_delta"].abs() > 0.01).sum(),
            "portfolio_avg_delta": df_sim["premium_delta"].mean(),
            "processing_time_ms": 0,  # timing not instrumented in simulation
        }
        return df_sim, metadata
    except Exception as e:
        raise RuntimeError(f"[simulation] Simulation failed: {e}")


def _skill_analysis(df: pd.DataFrame) -> tuple[dict, dict]:
    """Analyze portfolio impact. Returns (analysis result, metadata)."""
    try:
        result = analyze(df)
        metadata = {
            "status": "ok",
            "processing_time_ms": 0,  # timing not instrumented in analysis
        }
        return result, metadata
    except Exception as e:
        raise RuntimeError(f"[analysis] Analysis failed: {e}")


def _skill_compliance_decision(
    df: pd.DataFrame, analysis_result: dict
) -> tuple[dict, dict, dict]:
    """Check compliance and make decision. Returns (compliance, decision, metadata)."""
    try:
        compliance_result = check_compliance(df)
        decision_result = make_decision(analysis_result, compliance_result)
        metadata = {
            "status": "ok",
            "processing_time_ms": 0,
        }
        return compliance_result, decision_result, metadata
    except Exception as e:
        raise RuntimeError(f"[compliance_decision] Validation failed: {e}")


def _skill_audit(
    rule_config: dict, decision_result: dict, compliance_result: dict
) -> tuple[str, dict]:
    """Log outcome to audit trail. Returns (audit_id, metadata)."""
    try:
        audit_id = f"audit-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{os.getpid()}"
        log_audit(rule_config, decision_result, compliance_result)
        metadata = {
            "status": "ok",
            "audit_id": audit_id,
            "log_path": AUDIT_PATH,
            "processing_time_ms": 0,
        }
        return audit_id, metadata
    except Exception as e:
        raise RuntimeError(f"[audit] Audit write failed: {e}")


# ── Orchestration ────────────────────────────────────────────────────────────
def run_full_pipeline(
    threshold: float, multiplier: float, dry_run: bool = False, verbose: bool = False
) -> dict:
    """
    Execute the full governance pipeline.

    Steps:
      1. Load dataset
      2. Simulate pricing rule
      3. Analyze portfolio impact
      4. Validate compliance & decide
      5. Log to audit trail (skip if dry_run=True)

    Returns structured decision output.
    """
    result = {
        "status": "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_version": AGENT_VERSION,
        "rule": {"threshold": threshold, "multiplier": multiplier},
        "execution_path": [],
    }

    try:
        # [1] Load dataset
        start = datetime.now(timezone.utc)
        df, meta = _skill_data_ingest(DATASET_PATH)
        result["execution_path"].append({"step": "data_ingest", "status": "ok", **meta})
        if verbose:
            print(f"[data_ingest] OK: {len(df)} rows loaded")

        # [2] Simulate pricing rule
        df_sim, meta = _skill_simulation(df, threshold, multiplier)
        result["execution_path"].append({"step": "simulation", "status": "ok", **meta})
        if verbose:
            print(f"[simulation] OK: {meta['policies_affected']} policies affected")

        # [3] Analyze portfolio impact
        analysis_result, meta = _skill_analysis(df_sim)
        result["execution_path"].append({"step": "analysis", "status": "ok", **meta})
        result["analysis"] = analysis_result
        if verbose:
            print(f"[analysis] OK: {analysis_result['pct_affected']:.1f}% affected")

        # [4] Validate compliance & decide
        compliance_result, decision_result, meta = _skill_compliance_decision(df_sim, analysis_result)
        result["execution_path"].append({"step": "compliance_decision", "status": "ok", **meta})
        result["compliance"] = compliance_result
        result["decision"] = decision_result["decision"]
        result["reason"] = decision_result["reason"]
        if verbose:
            print(f"[compliance_decision] {decision_result['decision']}: {decision_result['reason']}")

        # [5] Log to audit trail (skip if dry_run)
        if not dry_run:
            rule_config = {"threshold": threshold, "multiplier": multiplier}
            audit_id, meta = _skill_audit(rule_config, decision_result, compliance_result)
            result["execution_path"].append({"step": "audit", "status": "ok", **meta})
            result["audit_id"] = audit_id
            if verbose:
                print(f"[audit] OK: logged as {audit_id}")
        else:
            result["dry_run"] = True
            if verbose:
                print("[dry_run] Skipping audit step")

        result["execution_time_seconds"] = (datetime.now(timezone.utc) - start).total_seconds()
        return result

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        return result


# ── CLI Entry Point ────────────────────────────────────────────────────────
def main():
    """Parse CLI arguments and execute agent task."""
    parser = argparse.ArgumentParser(
        description="Guidewire Agentic AI — Insurance Governance System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with custom rule
  python agent.py --task full_pipeline --threshold 30 --multiplier 1.5

  # Dry run (no audit write)
  python agent.py --task dry_run --threshold 35 --multiplier 1.2 --verbose

  # Get cache status
  python agent.py --task cache_status
        """,
    )

    parser.add_argument(
        "--task",
        type=str,
        required=True,
        help=f"Task to execute: {', '.join(sorted(_SKILLS))}",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=30,
        help="Age threshold for pricing multiplier (18-65)",
    )
    parser.add_argument(
        "--multiplier",
        type=float,
        default=1.5,
        help="Pricing multiplier for young segment (1.0-5.0)",
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default=DATASET_PATH,
        help="Path to insurance dataset CSV",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip audit log write (validation only)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Emit detailed execution logs",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["json", "human"],
        default="json",
        help="Output format (json or human-readable)",
    )

    args = parser.parse_args()

    try:
        _validate_args(args)

        if args.task == "full_pipeline":
            result = run_full_pipeline(args.threshold, args.multiplier, dry_run=False, verbose=args.verbose)
        elif args.task == "dry_run":
            result = run_full_pipeline(args.threshold, args.multiplier, dry_run=True, verbose=args.verbose)
        elif args.task == "cache_status":
            result = get_cache_status()
        else:
            result = {"error": f"Task '{args.task}' not yet implemented"}

        # Convert numpy/pandas types to native Python types for JSON serialization
        def convert_to_native(obj):
            """Recursively convert numpy/pandas types to native Python types."""
            import numpy as np
            import pandas as pd
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict(orient='records')
            elif isinstance(obj, pd.Series):
                return obj.to_dict()
            elif isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_native(item) for item in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return obj.item()
            elif hasattr(obj, 'item'):  # numpy scalar or pandas scalar
                return obj.item()
            else:
                return obj
        
        # Output result
        if args.output_format == "json":
            result_serializable = convert_to_native(result)
            # Output as single-line JSON for API parsing (indent=None)
            print(json.dumps(result_serializable))
        else:
            # Human-readable output
            if result.get("status") == "success":
                print(f"\n✓ Decision: {result.get('decision', 'N/A')}")
                print(f"  Reason: {result.get('reason', 'N/A')}")
                print(f"  Execution time: {result.get('execution_time_seconds', 0):.2f}s")
                if result.get("audit_id"):
                    print(f"  Audit ID: {result['audit_id']}")
            else:
                print(f"\n✗ Error: {result.get('error', 'Unknown error')}")
            print()

        # Exit code: 0 if success, 1 if error
        sys.exit(0 if result.get("status") == "success" else 1)

    except ValueError as e:
        error_result = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if args.output_format == "json":
            print(json.dumps(error_result))
        else:
            print(f"\n✗ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        error_result = {
            "status": "error",
            "error": "User interrupted",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if args.output_format == "json":
            print(json.dumps(error_result), file=sys.stderr)
        else:
            print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        error_result = {
            "status": "error",
            "error": f"{type(e).__name__}: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if args.output_format == "json":
            print(json.dumps(error_result))
        else:
            print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
