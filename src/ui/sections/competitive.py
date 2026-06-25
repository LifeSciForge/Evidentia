"""
MSL Tab: Competitive Position section.

Moved from src/ui/app.py as part of Stage 5 — Architecture Refactor (Part 2).
"""

import streamlit as st
from src.ui.helpers import _tab_heading, _section_label


_COMPARISON_ROWS = [
    ("mechanism",        "Mechanism"),
    ("efficacy",         "Efficacy"),
    ("key_safety",       "Key Safety"),
    ("primary_endpoint", "Primary Endpoint"),
    ("dosing",           "Dosing"),
    ("approval_status",  "Approval Status"),
]


def _render_comparison_table(drug: str, competitor_data) -> None:
    """Render a side-by-side HTML comparison table.

    Columns: dimension label | subject drug | up to 3 competitors.
    Empty / missing values show "—".
    Renders gracefully with zero competitors (subject column only).
    """
    subject = getattr(competitor_data, "subject_comparison", {}) or {}
    competitors = list(getattr(competitor_data, "competitors", []) or [])[:3]

    # --- build header row ---
    header_cells = (
        '<th style="background:#5b5bd6;color:#fff;font-size:11px;font-weight:700;'
        'text-transform:uppercase;letter-spacing:.07em;padding:8px 12px;text-align:left;'
        'min-width:110px;">Dimension</th>'
        f'<th style="background:#5b5bd6;color:#fff;font-size:11px;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:.07em;padding:8px 12px;text-align:left;'
        f'min-width:130px;">{drug}</th>'
    )
    for comp in competitors:
        name = getattr(comp, "competitor_name", "") or "Competitor"
        header_cells += (
            f'<th style="background:#3d3d7a;color:#fff;font-size:11px;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:.07em;padding:8px 12px;text-align:left;'
            f'min-width:130px;">{name}</th>'
        )

    # --- build data rows ---
    data_rows = ""
    for i, (field_key, label) in enumerate(_COMPARISON_ROWS):
        bg = "#ffffff" if i % 2 == 0 else "#f7f7fb"
        label_cell = (
            f'<td style="background:{bg};font-size:11px;font-weight:700;color:#666;'
            f'text-transform:uppercase;letter-spacing:.06em;padding:8px 12px;'
            f'border-bottom:1px solid #e8e8f0;white-space:nowrap;">{label}</td>'
        )
        subject_val = subject.get(field_key, "") or ""
        subject_display = subject_val if subject_val.strip() else "—"
        subject_cell = (
            f'<td style="background:{bg};font-size:12px;color:#333;padding:8px 12px;'
            f'border-bottom:1px solid #e8e8f0;line-height:1.4;">{subject_display}</td>'
        )
        comp_cells = ""
        for comp in competitors:
            raw = getattr(comp, field_key, "") or ""
            display = raw if (isinstance(raw, str) and raw.strip()) else "—"
            comp_cells += (
                f'<td style="background:{bg};font-size:12px;color:#555;padding:8px 12px;'
                f'border-bottom:1px solid #e8e8f0;line-height:1.4;">{display}</td>'
            )
        data_rows += f"<tr>{label_cell}{subject_cell}{comp_cells}</tr>"

    html = (
        '<div style="overflow-x:auto;margin-bottom:24px;">'
        '<table style="border-collapse:collapse;width:100%;font-family:\'Inter\','
        '\'Helvetica Neue\',sans-serif;border:1px solid #e0e0e0;border-radius:4px;">'
        f"<thead><tr>{header_cells}</tr></thead>"
        f"<tbody>{data_rows}</tbody>"
        "</table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def display_competitive_section(state):
    """Professional competitive landscape tab."""

    drug = getattr(state, "drug_name", "this drug") or "this drug"
    indication = getattr(state, "indication", "") or ""

    _tab_heading("Competitive Landscape",
                 f"Competitor comparison and {drug} differentiation" + (f" in {indication}" if indication else ""))

    if not state.competitor_data:
        st.warning("No competitor data available.")
        return

    competitors = state.competitor_data.competitors[:3]

    # ── Side-by-side comparison table ─────────────────────────────────────────
    _section_label("Head-to-Head Comparison")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    _render_comparison_table(drug, state.competitor_data)

    # ── Competitor cards (side-by-side) ───────────────────────────────────────
    _section_label("How We Compare")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    if competitors:
        cols = st.columns(len(competitors))
        for i, comp in enumerate(competitors):
            share = f"{comp.market_share:.1f}%" if comp.market_share else "N/A"
            pricing = f"${comp.pricing:,.0f}" if comp.pricing else "N/A"
            positioning = comp.positioning or "Standard of care"
            advantages = comp.clinical_advantages[:3] if comp.clinical_advantages else []
            vulnerabilities = comp.clinical_disadvantages[:3] if comp.clinical_disadvantages else []

            adv_li = "".join(
                f'<li style="font-size:12px;color:#00A86B;line-height:1.5;margin-bottom:3px;">{a}</li>'
                for a in advantages
            ) or '<li style="font-size:12px;color:#999;line-height:1.5;">N/A</li>'
            vuln_li = "".join(
                f'<li style="font-size:12px;color:#555555;line-height:1.5;margin-bottom:3px;">{v}</li>'
                for v in vulnerabilities
            ) or '<li style="font-size:12px;color:#999;line-height:1.5;">N/A</li>'

            with cols[i]:
                st.markdown(
                    f'<div style="border:1px solid #E0E0E0;border-radius:4px;padding:16px;'
                    f'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
                    f'<p style="font-size:14px;font-weight:700;color:#5b5bd6;margin:0 0 4px 0;">'
                    f'{comp.competitor_name}</p>'
                    f'<div style="display:flex;gap:16px;margin-bottom:12px;">'
                    f'<span style="font-size:11px;color:#666;"><strong style="color:#5b5bd6;">{share}</strong> share</span>'
                    f'<span style="font-size:11px;color:#666;"><strong style="color:#5b5bd6;">{pricing}</strong> / cycle</span>'
                    f'</div>'
                    f'<p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#999;margin:0 0 4px 0;">Positioning</p>'
                    f'<p style="font-size:12px;color:#555;line-height:1.5;margin:0 0 12px 0;">{positioning[:120]}</p>'
                    f'<p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#00A86B;margin:0 0 4px 0;">Strengths</p>'
                    f'<ul style="margin:0 0 12px 0;padding-left:16px;">{adv_li}</ul>'
                    f'<p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#999;margin:0 0 4px 0;">Vulnerabilities</p>'
                    f'<ul style="margin:0;padding-left:16px;">{vuln_li}</ul>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Our advantages ────────────────────────────────────────────────────────
    if state.messaging_data and state.messaging_data.key_differentiators:
        st.markdown(
            '<hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 24px 0;">',
            unsafe_allow_html=True
        )
        _section_label(f"Why {drug} Matters")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        diffs = state.messaging_data.key_differentiators[:3]
        border_colors = ["#5b5bd6", "#00A86B", "#FF9500"]
        adv_labels = ["Clinical Edge", "Commercial Advantage", "Strategic Differentiation"]
        cols = st.columns(len(diffs))
        for i, diff in enumerate(diffs):
            with cols[i]:
                bc = border_colors[i % len(border_colors)]
                lbl = adv_labels[i % len(adv_labels)]
                st.markdown(
                    f'<div style="border-left:3px solid {bc};background:#F5F5F5;border-radius:2px;'
                    f'padding:16px;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
                    f'<p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:{bc};margin:0 0 8px 0;">{lbl}</p>'
                    f'<p style="font-size:13px;color:#333333;line-height:1.6;margin:0;">{diff}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Tactical responses ────────────────────────────────────────────────────
    if competitors:
        st.markdown(
            '<hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 24px 0;">',
            unsafe_allow_html=True
        )
        _section_label("What to Say When...")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        for comp in competitors:
            comp_name = comp.competitor_name
            comp_advantages = comp.clinical_advantages[:1]
            adv_text = comp_advantages[0] if comp_advantages else "established market presence"
            vuln_text = (comp.clinical_disadvantages[0] if comp.clinical_disadvantages
                        else "limited in specific patient subgroups")

            scenario = f'"But {comp_name} is proven and well-established"'
            response = (
                f"True — {comp_name} has strong market presence. However, their advantage is primarily "
                f"in {adv_text.lower()[:80]}. The clinical gap is in patients where {drug} addresses "
                f"unmet need: {vuln_text.lower()[:100]}."
            )
            st.markdown(
                f'<div style="background:#F5F5F5;border:1px solid #E0E0E0;border-radius:4px;'
                f'padding:16px;margin-bottom:12px;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
                f'<p style="font-size:13px;font-weight:600;color:#5b5bd6;margin:0 0 8px 0;">{scenario}</p>'
                f'<p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#999;margin:0 0 4px 0;">Your Response</p>'
                f'<p style="font-size:13px;color:#555555;line-height:1.6;margin:0;">{response}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
