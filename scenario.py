"""
Scenario Comparison Engine
===========================
Multi-rule simulation and comparison framework for governance decision-making.

Compare multiple pricing rule variations to identify optimal outcomes.

compare_scenarios(df, scenarios) → list[dict]
  - Execute pipeline with different threshold/multiplier combinations
  - Return comparable results with metrics for each scenario
  - Enable A/B decision-making and trade-off analysis
"""

import pandas as pd
from pipeline import run_pipeline


def compare_scenarios(scenarios: list[dict]) -> list[dict]:
    """
    Execute multiple rule variations and return comparable results.
    
    Parameters
    ----------
    scenarios : list[dict]
        List of scenario definitions:
        [
            {
                "name": "Aggressive Growth",
                "threshold": 25,
                "multiplier": 1.35,
                "description": "Target high-value segments"
            },
            ...
        ]
    
    Returns
    -------
    list[dict]
        Comparable results with metrics for each scenario:
        [
            {
                "name": "Aggressive Growth",
                "threshold": 25,
                "multiplier": 1.35,
                "description": "...",
                "pipeline_result": {...},
                "analysis": {...},
                "compliance": {...},
                "decision": {...},
                "key_metrics": {
                    "total_revenue_impact": float,
                    "violations": int,
                    "is_deployable": bool,
                    "avg_premium_change": float,
                    "affected_pct": float,
                }
            },
            ...
        ]
    """
    results = []
    
    for scenario in scenarios:
        name = scenario.get("name", "Untitled")
        threshold = scenario.get("threshold", 25)
        multiplier = scenario.get("multiplier", 1.20)
        description = scenario.get("description", "")
        
        try:
            # Run full pipeline for this scenario
            pipeline_result = run_pipeline(threshold, multiplier)
            
            analysis = pipeline_result.get("analysis", {})
            compliance = pipeline_result.get("compliance", {})
            decision = pipeline_result.get("decision", {})
            
            # Extract key metrics for comparison
            key_metrics = {
                "total_revenue_impact": analysis.get("total_portfolio_delta", 0),
                "violations": compliance.get("violations_count", 0),
                "is_deployable": compliance.get("is_deployable", False),
                "avg_premium_change": analysis.get("avg_change", 0),
                "affected_pct": analysis.get("pct_affected", 0),
                "compliant_count": compliance.get("compliant_count", 0),
                "decision": decision.get("decision", "UNKNOWN"),
            }
            
            results.append({
                "name": name,
                "threshold": threshold,
                "multiplier": multiplier,
                "description": description,
                "pipeline_result": pipeline_result,
                "analysis": analysis,
                "compliance": compliance,
                "decision": decision,
                "key_metrics": key_metrics,
                "status": "success",
            })
            
        except Exception as e:
            # Gracefully handle failed scenarios
            results.append({
                "name": name,
                "threshold": threshold,
                "multiplier": multiplier,
                "description": description,
                "status": "error",
                "error": str(e),
            })
    
    return results


def build_comparison_table(results: list[dict]) -> pd.DataFrame:
    """
    Build a pandas DataFrame for side-by-side scenario comparison.
    Includes metrics, decision status, and key flags.
    """
    rows = []
    
    for r in results:
        if r["status"] == "success":
            metrics = r["key_metrics"]
            rows.append({
                "Scenario": r["name"],
                "Threshold": r["threshold"],
                "Multiplier": f"{r['multiplier']:.2f}x",
                "Avg Premium Δ": f"${metrics['avg_premium_change']:,.2f}",
                "Portfolio Impact": f"${metrics['total_revenue_impact']:,.0f}",
                "% Affected": f"{metrics['affected_pct']:.1f}%",
                "Violations": metrics["violations"],
                "Deployable": "✓ Yes" if metrics["is_deployable"] else "✗ No",
                "Decision": metrics["decision"],
            })
        else:
            rows.append({
                "Scenario": r["name"],
                "Threshold": r["threshold"],
                "Multiplier": f"{r['multiplier']:.2f}x",
                "Error": r.get("error", "Unknown error"),
            })
    
    return pd.DataFrame(rows)


def get_best_scenario(results: list[dict], criterion: str = "balanced") -> dict | None:
    """
    Recommend the best scenario based on criterion.
    
    Criteria:
    - "deployable": First deployable scenario (compliance-first)
    - "revenue": Highest portfolio revenue impact
    - "least_violations": Lowest violation count
    - "least_affected": Affects fewest customers
    - "balanced": Best compromise (deployable + high revenue + low violations)
    """
    successful = [r for r in results if r["status"] == "success"]
    
    if not successful:
        return None
    
    if criterion == "deployable":
        for r in successful:
            if r["key_metrics"]["is_deployable"]:
                return r
        return None
    
    elif criterion == "revenue":
        return max(successful, key=lambda r: r["key_metrics"]["total_revenue_impact"])
    
    elif criterion == "least_violations":
        return min(successful, key=lambda r: r["key_metrics"]["violations"])
    
    elif criterion == "least_affected":
        return min(successful, key=lambda r: r["key_metrics"]["affected_pct"])
    
    elif criterion == "balanced":
        # Score: deployable is essential, then maximize revenue while minimizing violations
        def score(r):
            metrics = r["key_metrics"]
            if not metrics["is_deployable"]:
                return -float('inf')
            # Weighted score: revenue + penalty for violations
            return (
                metrics["total_revenue_impact"] * 0.5
                - metrics["violations"] * 1000  # Heavy penalty per violation
                - metrics["affected_pct"] * 100  # Penalty for affecting many customers
            )
        
        return max(successful, key=score)
    
    return None
