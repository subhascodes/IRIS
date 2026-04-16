"""
Explains agent decisions using Qwen 7B.
Provides context about why decision was made (APPROVE/REJECT).
"""

from ollama_client import query_qwen
from typing import Dict, Any


def build_decision_context(
    decision_data: Dict[str, Any]
) -> str:
    """
    Build system context for explaining a decision.
    
    Args:
        decision_data: Result from agent.py with keys:
            - decision: "APPROVE" or "REJECT"
            - reason: Explanation
            - analysis: Portfolio metrics
            - compliance: Compliance data
            - rule: {"threshold": 30, "multiplier": 1.5}
    
    Returns:
        System context string for Qwen
    """
    
    decision = decision_data.get("decision", "UNKNOWN")
    reason = decision_data.get("reason", "")
    analysis = decision_data.get("analysis", {})
    compliance = decision_data.get("compliance", {})
    
    context = f"""You are an insurance governance expert. You are explaining 
why an automated pricing rule was {decision}.

AGENT'S DECISION: {decision}
REASON: {reason}

PORTFOLIO IMPACT:
- Affected Policies: {analysis.get('affected_policies', 0)}
- Average Premium Change: ${analysis.get('avg_change', 0):.2f}
- Total Portfolio Impact: ${analysis.get('total_portfolio_delta', 0):,.2f}
- Percentage of Portfolio Affected: {analysis.get('pct_affected', 0):.2f}%

COMPLIANCE STATUS:
- Violations Found: {compliance.get('violations_count', 0)}
- Violation Rate: {compliance.get('violation_percentage', 0):.2f}%
- Deployable: {compliance.get('is_deployable', False)}

Your role: Help stakeholders understand the decision. Be concise (2-3 sentences).
Explain in simple business terms, not technical jargon. Focus on the business impact."""
    
    return context


def explain_decision(decision_data: Dict[str, Any]) -> str:
    """
    Generate plain-English explanation of why agent made a decision.
    
    Args:
        decision_data: Agent result dict
    
    Returns:
        Explanation string
    """
    
    context = build_decision_context(decision_data)
    prompt = (
        f"Explain why the rule was {decision_data.get('decision', 'UNKNOWN')} "
        f"in 2-3 sentences for business stakeholders. Focus on impact and constraints."
    )
    
    return query_qwen(
        prompt=prompt,
        system_context=context,
        temperature=0.3
    )


def answer_decision_query(
    query: str,
    decision_data: Dict[str, Any]
) -> str:
    """
    Answer user questions about the decision.
    
    Args:
        query: User question (e.g., "Why were 803 policies affected?")
        decision_data: Agent result dict
    
    Returns:
        Answer string
    """
    
    context = build_decision_context(decision_data)
    
    return query_qwen(
        prompt=query,
        system_context=context,
        temperature=0.5
    )
