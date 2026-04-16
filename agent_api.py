"""
Agent API wrapper for Streamlit UI integration.
Provides synchronous interface to agent orchestrator for UI calls.
"""

import subprocess
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

# Suppress verbose logging
logging.getLogger().setLevel(logging.ERROR)


def call_agent(
    task: str,
    threshold: Optional[int] = None,
    multiplier: Optional[float] = None,
    dataset_path: str = "data/dataset.csv"
) -> Dict[str, Any]:
    """
    Call agent.py via subprocess and return structured result.
    
    Args:
        task: Agent task name (e.g., 'full_pipeline', 'data_ingest', 'simulation')
        threshold: Age threshold for pricing rule (optional)
        multiplier: Premium multiplier (optional)
        dataset_path: Path to policy dataset
    
    Returns:
        Dict with keys: status, decision, reason, metrics, timestamp, audit_reference
    """
    cmd = [sys.executable, "agent.py", "--task", task, "--dataset", dataset_path]
    
    if threshold is not None:
        cmd.extend(["--threshold", str(threshold)])
    if multiplier is not None:
        cmd.extend(["--multiplier", str(multiplier)])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5min timeout
            cwd=Path(__file__).parent
        )
        
        # Combine stdout and stderr for parsing (try stdout first)
        output_text = (result.stdout or "").strip()
        if not output_text and result.stderr:
            output_text = result.stderr.strip()
        
        if not output_text:
            return {
                "status": "error",
                "error": "Agent produced no output"
            }
        
        # Parse JSON output (agent outputs single-line JSON)
        try:
            output = json.loads(output_text)
            if isinstance(output, dict) and "status" in output:
                return output
        except json.JSONDecodeError:
            pass
        
        # If single-line parsing failed, try line-by-line
        for line in output_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                output = json.loads(line)
                if isinstance(output, dict) and "status" in output:
                    return output
            except json.JSONDecodeError:
                continue
        
        # If we got here, couldn't parse as JSON
        if result.returncode != 0:
            return {
                "status": "error",
                "error": "Agent exited with error",
                "details": output_text[:300]
            }
        
        return {
            "status": "error",
            "error": "Agent did not return valid JSON output",
            "details": output_text[:300]
        }
    
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": "Agent execution timed out (5min)"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def get_audit_history(limit: int = 20) -> pd.DataFrame:
    """
    Load audit log and return last N entries.
    
    Args:
        limit: Number of recent entries to return
    
    Returns:
        DataFrame with audit log entries
    """
    audit_path = Path(__file__).parent / "data" / "audit_log.csv"
    
    if not audit_path.exists():
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(audit_path)
        return df.tail(limit)
    except Exception as e:
        print(f"Error reading audit log: {e}")
        return pd.DataFrame()
