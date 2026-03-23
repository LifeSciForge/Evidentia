"""
Reusable Streamlit UI components
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def market_sizing_waterfall(tam, sam, som):
    """Create TAM/SAM/SOM waterfall chart"""
    
    fig = go.Figure(go.Waterfall(
        name="Market Sizing",
        orientation="v",
        x=["TAM", "SAM Loss", "SAM", "SOM Loss", "SOM"],
        textposition="outside",
        y=[tam, -sam, sam, -som, som],
        connector={"line": {"color": "rgba(63, 63, 63, 0.5)"}},
        marker={"color": ["#1f77b4", "#ff7f0e", "#2ca02c", "#ff7f0e", "#d62728"]}
    ))
    
    fig.update_layout(
        title="Market Sizing Waterfall",
        yaxis_title="Market Size (USD Millions)",
        xaxis_title="Market Segments",
        height=400,
        showlegend=False
    )
    
    return fig


def competitor_positioning_scatter(competitors):
    """Create competitor positioning scatter plot"""
    
    data = []
    for comp in competitors:
        data.append({
            "Name": comp.competitor_name,
            "Price": comp.pricing or 0,
            "Market_Share": comp.market_share or 0,
            "Clinical_Score": len(comp.clinical_advantages)
        })
    
    df = pd.DataFrame(data)
    
    fig = px.scatter(
        df,
        x="Price",
        y="Market_Share",
        size="Clinical_Score",
        hover_name="Name",
        title="Competitive Positioning Map",
        labels={"Price": "Price Point ($)", "Market_Share": "Market Share (%)"}
    )
    
    fig.update_layout(height=400)
    
    return fig


def metric_card(title, value, subtitle="", icon=""):
    """Create a metric card"""
    
    html = f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 10px 0;">
        <div style="font-size: 14px; opacity: 0.9;">{icon} {title}</div>
        <div style="font-size: 32px; font-weight: bold; margin: 10px 0;">{value}</div>
        <div style="font-size: 12px; opacity: 0.7;">{subtitle}</div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)
