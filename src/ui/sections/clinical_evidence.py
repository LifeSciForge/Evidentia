"""
MSL Tab: Clinical Evidence section.

Moved from src/ui/app.py as part of Stage 5 — Architecture Refactor (Part 2).
"""

import streamlit as st
from src.ui.helpers import _tab_heading, _section_label


def display_clinical_evidence_section(state):
    """Professional clinical evidence tab."""

    drug = getattr(state, "drug_name", "this drug") or "this drug"
    indication = getattr(state, "indication", "") or ""

    _tab_heading("Clinical Evidence",
                 f"Key trials and market landscape for {drug}" + (f" in {indication}" if indication else ""))

    if not state.market_data:
        st.warning("No clinical data available.")
        return

    # ── Stat cards ────────────────────────────────────────────────────────────
    trial_count = len(state.market_data.clinical_trials) if state.market_data.clinical_trials else 0
    tam_val = f"${state.market_data.tam_estimate:,.0f}M" if state.market_data.tam_estimate else "N/A"
    pop_val = f"{state.market_data.patient_population:,}" if state.market_data.patient_population else "N/A"

    card_style = (
        "background:#F5F5F5;border:1px solid #E0E0E0;border-radius:4px;"
        "padding:20px;text-align:center;font-family:'Inter','Helvetica Neue',sans-serif;"
    )
    label_style = "font-size:12px;font-weight:600;color:#666666;text-transform:uppercase;letter-spacing:0.3px;display:block;margin-bottom:8px;"
    value_style = "font-size:28px;font-weight:700;color:#5b5bd6;display:block;margin-bottom:6px;"
    source_style = "font-size:10px;color:#999999;font-style:italic;display:block;"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div style="{card_style}"><span style="{label_style}">Active Trials</span>'
            f'<span style="{value_style}">{trial_count}</span>'
            f'<span style="{source_style}">Source: ClinicalTrials.gov</span></div>',
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f'<div style="{card_style}"><span style="{label_style}">Target Market (TAM)</span>'
            f'<span style="{value_style}">{tam_val}</span>'
            f'<span style="{source_style}">Source: Market research estimate</span></div>',
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f'<div style="{card_style}"><span style="{label_style}">Patient Population</span>'
            f'<span style="{value_style}">{pop_val}</span>'
            f'<span style="{source_style}">Source: Epidemiology data</span></div>',
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Clinical trials table ─────────────────────────────────────────────────
    _section_label("Key Clinical Trials")
    st.markdown(
        '<p style="font-size:12px;color:#666;font-style:italic;margin:0 0 16px 0;">'
        'Click a trial ID to view on ClinicalTrials.gov</p>',
        unsafe_allow_html=True
    )

    if state.market_data.clinical_trials:
        th_style = (
            "padding:10px 12px;text-align:left;font-size:11px;font-weight:600;"
            "color:#5b5bd6;text-transform:uppercase;letter-spacing:0.3px;"
            "background:#F5F5F5;border-bottom:1px solid #E0E0E0;"
        )
        td_style = (
            "padding:12px;font-size:12px;color:#333333;line-height:1.5;"
            "border-bottom:1px solid #E0E0E0;vertical-align:top;"
        )
        status_badges = {
            "recruiting": "background:#E8F1F8;color:#5b5bd6;",
            "active": "background:#E8F5E9;color:#00A86B;",
            "completed": "background:#F5F5F5;color:#666666;",
        }

        rows = ""
        for trial in state.market_data.clinical_trials[:8]:
            nct = trial.get("nct_id", "") or ""
            title = trial.get("title", "") or ""
            status = trial.get("status", "") or ""
            phase = trial.get("phase", "") or ""
            endpoint = trial.get("primary_endpoint", trial.get("primary_outcome", "")) or "—"
            key_insight = trial.get("key_insight", "") or "—"

            nct_html = (
                f'<a href="https://clinicaltrials.gov/ct2/show/{nct}" target="_blank" '
                f'style="color:#5b5bd6;text-decoration:underline;">{nct}</a>'
                if nct else "—"
            )
            status_lower = status.lower()
            badge_color = next(
                (v for k, v in status_badges.items() if k in status_lower),
                "background:#F5F5F5;color:#666666;"
            )
            status_html = (
                f'<span style="{badge_color}padding:3px 7px;border-radius:3px;'
                f'font-size:10px;font-weight:600;white-space:nowrap;">'
                f'{status.upper() if status else "—"}</span>'
            )
            rows += (
                f'<tr>'
                f'<td style="{td_style}">{nct_html}</td>'
                f'<td style="{td_style}">{title[:80]}{"..." if len(title) > 80 else ""}</td>'
                f'<td style="{td_style}">{status_html}</td>'
                f'<td style="{td_style}">{phase}</td>'
                f'<td style="{td_style}">{str(endpoint)[:60]}</td>'
                f'<td style="{td_style}">{str(key_insight)[:80]}</td>'
                f'</tr>'
            )

        st.markdown(
            f'<div style="overflow-x:auto;">'
            f'<table style="width:100%;border-collapse:collapse;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
            f'<thead><tr>'
            f'<th style="{th_style}">Trial ID</th>'
            f'<th style="{th_style}">Title</th>'
            f'<th style="{th_style}">Status</th>'
            f'<th style="{th_style}">Phase</th>'
            f'<th style="{th_style}">Primary Endpoint</th>'
            f'<th style="{th_style}">Key Insight</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<p style="font-size:13px;color:#999;font-style:italic;">No trial data available.</p>',
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Market drivers ────────────────────────────────────────────────────────
    # Pull from direct field first (populated by agent), fall back to epidemiology dict
    drivers = getattr(state.market_data, "market_drivers", []) or []
    if not drivers and state.market_data.epidemiology:
        drivers = state.market_data.epidemiology.get("market_drivers", [])

    if drivers:
        _section_label("Market Drivers")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        for d in drivers[:6]:
            st.markdown(
                f'<div style="font-size:13px;color:#333;line-height:1.6;'
                f'padding:8px 0 8px 14px;border-left:3px solid #E0E0E0;margin-bottom:8px;'
                f'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">{d}</div>',
                unsafe_allow_html=True
            )
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── How to use this data ──────────────────────────────────────────────────
    st.markdown(
        '<hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 24px 0;">',
        unsafe_allow_html=True
    )
    _section_label("How to Use This Data in Calls")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    guidance = [
        ("When they ask: \"What's the data?\"",
         f"\"We have {trial_count} active trials across multiple settings. Phase 3 data is ongoing. "
         f"Our Phase 2 data showed compelling response rates in the target population.\""),
        ("When they ask: \"How does it compare to competitors?\"",
         "Reference the Competitive Position tab for head-to-head differentiation. "
         "Focus on mechanism advantage in PD-L1 negative and TKI-resistant subgroups."),
        ("When they ask: \"Where can I read the data?\"",
         "\"You can visit ClinicalTrials.gov and search the NCT ID, or I can send you the "
         "latest publications. We are also presenting at upcoming conferences.\""),
    ]
    cols = st.columns(3)
    card_s = (
        "background:#F5F5F5;border:1px solid #E0E0E0;border-radius:4px;padding:16px;"
        "font-family:'Inter','Helvetica Neue',sans-serif;height:100%;"
    )
    for i, (heading, body) in enumerate(guidance):
        with cols[i]:
            st.markdown(
                f'<div style="{card_s}">'
                f'<p style="font-size:13px;font-weight:600;color:#5b5bd6;margin:0 0 8px 0;line-height:1.4;">{heading}</p>'
                f'<p style="font-size:12px;color:#555555;margin:0;line-height:1.6;">{body}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
