"""
Reusable Streamlit UI components
"""

import html as _html
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

_CHIP_TIERS = {"verified", "web", "filing", "modeled", "unavailable"}


def source_chip_html(tier: str, label: str, url: str | None = None, note: str | None = None) -> str:
    """Build a provenance chip as an HTML string.

    tier: one of verified | web | filing | modeled | unavailable (unknown -> unavailable).
    Renders an <a> when a url is given, otherwise a <span>. All text is HTML-escaped.
    """
    safe_tier = tier if tier in _CHIP_TIERS else "unavailable"
    cls = f"ev-chip ev-chip-{safe_tier}"
    safe_label = _html.escape(label or "")
    title = f' title="{_html.escape(note)}"' if note else ""
    if url:
        safe_url = _html.escape(url, quote=True)
        return (
            f'<a class="{cls}" href="{safe_url}" target="_blank" '
            f'rel="noopener noreferrer"{title}>{safe_label} ↗</a>'
        )
    return f'<span class="{cls}"{title}>{safe_label}</span>'


def source_chip(tier: str, label: str, url: str | None = None, note: str | None = None) -> None:
    """Render a provenance chip inline."""
    st.markdown(source_chip_html(tier, label, url=url, note=note), unsafe_allow_html=True)


def market_sizing_waterfall(tam, sam, som):
    """Create TAM/SAM/SOM waterfall chart"""

    fig = go.Figure(go.Waterfall(
        name="Market Sizing",
        orientation="v",
        x=["TAM", "SAM Loss", "SAM", "SOM Loss", "SOM"],
        textposition="outside",
        y=[tam, -sam, sam, -som, som],
        connector={"line": {"color": "rgba(63, 63, 63, 0.5)"}},
        increasing=dict(marker=dict(color="#1aa564")),
        decreasing=dict(marker=dict(color="#c2741b")),
        totals=dict(marker=dict(color="#5b5bd6")),
    ))

    fig.update_layout(
        title="Market Sizing Waterfall",
        yaxis_title="Market Size (USD Millions)",
        xaxis_title="Market Segments",
        height=400,
        showlegend=False,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Inter", color="#1a1d29"),
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
        labels={"Price": "Price Point ($)", "Market_Share": "Market Share (%)"},
        color_discrete_sequence=["#5b5bd6"],
    )

    fig.update_layout(
        height=400,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Inter", color="#1a1d29"),
    )

    return fig


def metric_card_html(title: str, value: str, subtitle: str = "", source_html: str = "") -> str:
    """Direction C metric card (no gradient). Optionally embeds a source chip."""
    safe_title = _html.escape(title or "")
    safe_value = _html.escape(str(value))
    safe_sub = _html.escape(subtitle or "")
    sub = f'<div class="ev-metric-sub">{safe_sub}</div>' if safe_sub else ""
    chip = f'<div class="ev-metric-chip">{source_html}</div>' if source_html else ""
    return (
        f'<div class="ev-metric-card">'
        f'<div class="ev-metric-label">{safe_title}</div>'
        f'<div class="ev-metric-value">{safe_value}</div>'
        f'{chip}{sub}</div>'
    )


def metric_card(title: str, value: str, subtitle: str = "", icon: str = "", source_html: str = "") -> None:
    """Render a metric card. `icon` kept for backward compatibility (prefixed to title)."""
    title_text = f"{icon} {title}".strip() if icon else title
    st.markdown(metric_card_html(title_text, value, subtitle=subtitle, source_html=source_html),
                unsafe_allow_html=True)
