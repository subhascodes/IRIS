"""
Risk Visualization & Heatmap Engine
====================================
Interactive charts for portfolio risk analysis.

Functions:
- plot_premium_change_heatmap: Age vs premium change distribution
- plot_segment_impact: Revenue impact by age segment
- plot_compliance_timeline: Violations by rule type
- plot_scenario_comparison: Side-by-side scenario metrics
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


def plot_premium_change_heatmap(df: pd.DataFrame, title: str = "Premium Change Heatmap") -> go.Figure:
    """
    Interactive heatmap: Customer age (rows) vs premium change distribution (columns).
    Shows density of policies at each premium change level.
    
    Parameters
    ----------
    df : DataFrame with columns: customer_age, premium_delta
    
    Returns
    -------
    plotly.graph_objects.Figure
    """
    # Bin age and premium change
    age_bins = pd.cut(df["customer_age"], bins=[0, 25, 35, 45, 55, 65, 120], 
                       labels=["<25", "25-35", "35-45", "45-55", "55-65", ">65"])
    premium_bins = pd.cut(df["premium_delta"], 
                          bins=[-1000, -100, 0, 100, 300, 500, 1000],
                          labels=["<-$100", "-$100-0", "$0-100", "$100-300", "$300-500", ">$500"])
    
    heatmap_data = pd.crosstab(age_bins, premium_bins)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale="Viridis",
        hovertemplate="<b>Age Group:</b> %{y}<br><b>Premium Change:</b> %{x}<br><b>Count:</b> %{z}<extra></extra>",
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Premium Change Range",
        yaxis_title="Customer Age Group",
        height=500,
        template="plotly_dark",
        margin=dict(l=100, r=50, t=80, b=80),
    )
    
    return fig


def plot_segment_impact(analysis: dict, title: str = "Revenue Impact by Age Segment") -> go.Figure:
    """
    Bar chart: Revenue impact (portfolio delta) by age segment.
    Green bars = revenue increase, Red bars = revenue decrease.
    
    Parameters
    ----------
    analysis : dict with segment_analysis data
    
    Returns
    -------
    plotly.graph_objects.Figure
    """
    seg_data = analysis.get("segment_analysis", {})
    
    segments = []
    revenue_impacts = []
    colors = []
    
    for label in ["<25", "25-40", ">40"]:
        s = seg_data.get(label, {})
        total_delta = s.get("total_delta", 0)
        segments.append(label)
        revenue_impacts.append(total_delta)
        colors.append("#22c55e" if total_delta > 0 else "#ef4444")
    
    fig = go.Figure(data=[
        go.Bar(
            x=segments,
            y=revenue_impacts,
            marker_color=colors,
            text=[f"${v:,.0f}" for v in revenue_impacts],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Revenue Impact: $%{y:,.0f}<extra></extra>",
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="Age Segment",
        yaxis_title="Total Revenue Impact ($)",
        height=400,
        template="plotly_dark",
        showlegend=False,
        margin=dict(l=80, r=50, t=80, b=50),
    )
    
    return fig


def plot_compliance_violations(compliance: dict, title: str = "Compliance Violations by Rule") -> go.Figure:
    """
    Pie or donut chart showing violation breakdown by rule type.
    
    Parameters
    ----------
    compliance : dict with violations_by_rule data
    
    Returns
    -------
    plotly.graph_objects.Figure
    """
    v_by_rule = compliance.get("violations_by_rule", {})
    
    labels = ["Absolute Only", "Percentage Only", "Both Rules"]
    values = [
        v_by_rule.get("absolute_only", 0),
        v_by_rule.get("percentage_only", 0),
        v_by_rule.get("both_rules", 0),
    ]
    colors = ["#fbbf24", "#f97316", "#ef4444"]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    )])
    
    fig.update_layout(
        title=title,
        height=400,
        template="plotly_dark",
        margin=dict(l=50, r=50, t=80, b=50),
    )
    
    return fig


def plot_scenario_comparison_chart(results: list[dict], metric: str = "total_revenue_impact") -> go.Figure:
    """
    Compare multiple scenarios across a specified metric.
    
    Metrics: total_revenue_impact, violations, avg_premium_change, affected_pct
    
    Parameters
    ----------
    results : list of scenario results from compare_scenarios()
    metric : metric key to compare
    
    Returns
    -------
    plotly.graph_objects.Figure
    """
    successful = [r for r in results if r["status"] == "success"]
    
    names = [r["name"] for r in successful]
    values = [r["key_metrics"].get(metric, 0) for r in successful]
    deployable = [r["key_metrics"]["is_deployable"] for r in successful]
    
    # Color by deployability
    colors = ["#22c55e" if d else "#ef4444" for d in deployable]
    
    metric_labels = {
        "total_revenue_impact": "Total Revenue Impact ($)",
        "violations": "Violations (Count)",
        "avg_premium_change": "Avg Premium Change ($)",
        "affected_pct": "% of Portfolio Affected",
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=names,
            y=values,
            marker_color=colors,
            text=[f"{v:,.0f}" for v in values],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Value: %{y:,.0f}<extra></extra>",
        )
    ])
    
    fig.update_layout(
        title=f"Scenario Comparison: {metric_labels.get(metric, metric)}",
        xaxis_title="Scenario",
        yaxis_title=metric_labels.get(metric, metric),
        height=450,
        template="plotly_dark",
        showlegend=False,
        margin=dict(l=80, r=50, t=80, b=100),
        xaxis_tickangle=-45,
    )
    
    return fig


def plot_sensitivity_curve(df_sensitivity: pd.DataFrame, title: str = "Sensitivity Analysis") -> go.Figure:
    """
    Line chart showing how metrics vary with multiplier changes.
    
    Parameters
    ----------
    df_sensitivity : DataFrame with columns: multiplier, violations, revenue_impact, deployable
    
    Returns
    -------
    plotly.graph_objects.Figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_sensitivity["multiplier"],
        y=df_sensitivity["violations"],
        name="Violations",
        yaxis="y",
        line=dict(color="#ef4444"),
        hovertemplate="<b>Multiplier:</b> %{x:.2f}x<br><b>Violations:</b> %{y:,}<extra></extra>",
    ))
    
    fig.add_trace(go.Scatter(
        x=df_sensitivity["multiplier"],
        y=df_sensitivity["revenue_impact"] / 1_000_000,  # Convert to millions
        name="Revenue Impact ($M)",
        yaxis="y2",
        line=dict(color="#22c55e"),
        hovertemplate="<b>Multiplier:</b> %{x:.2f}x<br><b>Revenue:</b> $%{y:.2f}M<extra></extra>",
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Premium Multiplier",
        yaxis=dict(title="Violations", titlefont=dict(color="#ef4444"), tickfont=dict(color="#ef4444")),
        yaxis2=dict(title="Revenue Impact ($M)", titlefont=dict(color="#22c55e"), tickfont=dict(color="#22c55e"), overlaying="y", side="right"),
        height=450,
        template="plotly_dark",
        hovermode="x unified",
        margin=dict(l=80, r=80, t=80, b=50),
    )
    
    return fig


def plot_age_distribution_violin(df: pd.DataFrame, title: str = "Premium Change Distribution by Age") -> go.Figure:
    """
    Violin plot showing distribution of premium changes across age spectrum.
    
    Parameters
    ----------
    df : DataFrame with columns: customer_age, premium_delta
    
    Returns
    -------
    plotly.graph_objects.Figure
    """
    # Create age groups for cleaner visualization
    df_plot = df.copy()
    df_plot["age_group"] = pd.cut(df_plot["customer_age"], 
                                   bins=[0, 25, 35, 45, 55, 65, 120],
                                   labels=["<25", "25-35", "35-45", "45-55", "55-65", ">65"])
    
    fig = go.Figure()
    
    for age_group in ["<25", "25-35", "35-45", "45-55", "55-65", ">65"]:
        fig.add_trace(go.Violin(
            y=df_plot[df_plot["age_group"] == age_group]["premium_delta"],
            name=age_group,
            box_visible=True,
            meanline_visible=True,
            hovertemplate="<b>Age:</b> " + age_group + "<br><b>Premium Change:</b> $%{y:.2f}<extra></extra>",
        ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Age Group",
        yaxis_title="Premium Change ($)",
        height=500,
        template="plotly_dark",
        showlegend=False,
        margin=dict(l=80, r=50, t=80, b=50),
    )
    
    return fig
