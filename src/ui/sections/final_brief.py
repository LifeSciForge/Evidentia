"""
MSL Tab: Final Call Brief section.

Moved from src/ui/app.py as part of Stage 5 — Architecture Refactor (Part 2).
"""

import streamlit as st
from src.ui.helpers import _tab_heading, _section_label


def display_final_brief_section(state):
    """Professional final call brief — scannable in 5 minutes."""

    drug = getattr(state, "drug_name", "this drug") or "this drug"
    indication = getattr(state, "indication", "") or ""
    hospital = st.session_state.get("current_hospital") or ""
    doctor = (st.session_state.get("current_doctor") or "").split("(")[0].strip()

    _tab_heading("Final Call Brief",
                 "Comprehensive reference. Review before call. Reference during call.")

    # ── Executive summary ─────────────────────────────────────────────────────
    _section_label("Executive Summary — Read This First")
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    summary = (
        state.final_gtm_strategy.executive_summary
        if state.final_gtm_strategy and state.final_gtm_strategy.executive_summary
        else (
            f"You are prepared to discuss {drug}"
            + (f" for {indication}" if indication else "")
            + (f" at {hospital}" if hospital else "")
            + ". This is a scientifically differentiated therapy with strong clinical data in "
            "checkpoint inhibitor-resistant and PD-L1 negative patients. "
            "Focus the conversation on clinical efficacy, unmet need, and competitive differentiation."
        )
    )
    st.markdown(
        f'<div style="background:#E8F1F8;border-left:3px solid #5b5bd6;border-radius:0 4px 4px 0;'
        f'padding:16px 20px;font-size:13px;line-height:1.7;color:#333333;margin-bottom:8px;'
        f'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">{summary}</div>',
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── 3 key talking points ──────────────────────────────────────────────────
    st.markdown(
        '<hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 24px 0;">',
        unsafe_allow_html=True
    )
    _section_label("3 Key Talking Points — Lead with These")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    pillars_raw = []
    if state.messaging_data and state.messaging_data.messaging_pillars:
        pillars_raw = state.messaging_data.messaging_pillars[:3]

    default_pillars = [
        ("Engineered Innovation",
         "First-in-class design targets dual pathways in a single molecule. "
         "Blocks immune suppression and tumour microenvironment resistance simultaneously."),
        ("Resistance Breakthrough",
         "Proven efficacy in checkpoint inhibitor-resistant and PD-L1 negative patients. "
         "Addresses a subgroup where single-agent IO options have limited activity."),
        ("Simplified Excellence",
         "Single-agent approach eliminates combination complexity. "
         "IV q3w dosing. Manageable safety profile. Reduces hospitalisation and drug interaction burden."),
    ]

    cols = st.columns(3)
    for i, col in enumerate(cols):
        if i < len(pillars_raw):
            title = f"Pillar {i+1}"
            body = pillars_raw[i]
        else:
            title, body = default_pillars[i]

        with col:
            st.markdown(
                f'<div style="background:#F5F5F5;border:1px solid #E0E0E0;border-radius:4px;'
                f'padding:16px;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
                f'<p style="font-size:12px;font-weight:600;color:#5b5bd6;text-transform:uppercase;'
                f'letter-spacing:0.3px;margin:0 0 8px 0;">{title}</p>'
                f'<p style="font-size:13px;color:#555555;line-height:1.6;margin:0;">{body}</p>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Top 3 objections ──────────────────────────────────────────────────────
    st.markdown(
        '<hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 24px 0;">',
        unsafe_allow_html=True
    )
    _section_label("Top 3 Expected Objections")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Use KOL objections if available, else generic
    tp = getattr(state, "msl_talking_points", None)
    brief_objections = []
    if tp and getattr(tp, "anticipated_objections", None):
        for obj in tp.anticipated_objections[:3]:
            brief_objections.append((
                obj.objection or "",
                obj.msl_response or obj.evidence_response or ""
            ))
    if not brief_objections:
        brief_objections = [
            ("Limited clinical data compared to established competitors",
             "Phase 2 data in the target population is compelling. Phase 3 interim data expected Q3 2026. "
             "Our data specifically targets PD-L1 negative and TKI-resistant patients."),
            ("Safety concerns with dual targeting",
             "Single-molecule design reduces off-target effects vs combination therapy. "
             "Phase 2 safety profile is comparable to single-agent checkpoints."),
            ("Payer coverage uncertainty",
             "HTA submissions ongoing. Early payer signals are positive — dual mechanism plus unmet need "
             "is a compelling reimbursement case. Outcomes-based pricing models available."),
        ]

    for obj_title, obj_resp in brief_objections:
        st.markdown(
            f'<div style="background:#F5F5F5;border-left:2px solid #FF9500;border-radius:2px;'
            f'padding:14px 16px;margin-bottom:10px;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
            f'<p style="font-size:13px;font-weight:600;color:#5b5bd6;margin:0 0 6px 0;">{obj_title}</p>'
            f'<p style="font-size:12px;color:#555555;line-height:1.6;margin:0;">'
            f'<strong style="color:#333333;">Response: </strong>{obj_resp}</p>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Discovery questions ───────────────────────────────────────────────────
    st.markdown(
        '<hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 24px 0;">',
        unsafe_allow_html=True
    )
    _section_label("Discovery Questions to Ask  (pick 2-3)")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    indication_str = indication or "target indication"
    dqs = [
        f'How many of your {indication_str} patients have PD-L1 negative tumours or have developed IO resistance?',
        "What is your current treatment approach for patients who have failed checkpoint inhibitors?",
        "What health economic or outcomes data would be most useful for your formulary committee?",
    ]
    for i, q in enumerate(dqs, 1):
        st.markdown(
            f'<div style="padding:10px 14px;border-left:3px solid #E0E0E0;margin-bottom:8px;'
            f'font-size:13px;color:#333333;line-height:1.6;'
            f'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
            f'<strong style="color:#5b5bd6;">{i}.</strong> {q}</div>',
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Reimbursement quick check ─────────────────────────────────────────────
    st.markdown(
        '<hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 24px 0;">',
        unsafe_allow_html=True
    )
    _section_label("Reimbursement Quick Check")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    hta = (state.payer_data.hta_status or "Under review") if state.payer_data else "Under review"
    price_str = (f"${state.payer_data.pricing_ceiling:,.0f}" if (state.payer_data and state.payer_data.pricing_ceiling) else "TBD")
    qaly_str = (f"£{state.payer_data.qaly_threshold:,.0f}" if (state.payer_data and state.payer_data.qaly_threshold) else "£30,000 standard")

    check_items = [
        ("HTA Status", hta),
        ("Pricing", price_str + " — subject to payer negotiations"),
        ("QALY Threshold", qaly_str),
        ("Patient Access", "Copay assistance and outcomes-based pricing available"),
    ]
    c1, c2 = st.columns(2)
    for i, (label, value) in enumerate(check_items):
        col = c1 if i % 2 == 0 else c2
        with col:
            st.markdown(
                f'<div style="background:#F5F5F5;border:1px solid #E0E0E0;border-radius:4px;'
                f'padding:12px;margin-bottom:12px;font-size:13px;color:#555555;line-height:1.6;'
                f'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
                f'<strong style="display:block;color:#5b5bd6;margin-bottom:3px;">{label}</strong>'
                f'{value}</div>',
                unsafe_allow_html=True
            )

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Competitive quick reference ───────────────────────────────────────────
    st.markdown(
        '<hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 24px 0;">',
        unsafe_allow_html=True
    )
    _section_label("You vs Top Competitor  (Quick Reference)")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    our_diffs = (state.messaging_data.key_differentiators[:2] if state.messaging_data else [])
    top_comp = (state.competitor_data.competitors[0] if state.competitor_data and state.competitor_data.competitors else None)

    c1, c2 = st.columns(2)
    with c1:
        our_li = "".join(
            f'<li style="font-size:12px;color:#555;line-height:1.6;margin-bottom:4px;">{d}</li>'
            for d in our_diffs
        ) or f'<li style="font-size:12px;color:#555;">Differentiated dual mechanism</li>'
        st.markdown(
            f'<div style="background:#E8F5E9;border-left:3px solid #00A86B;border-radius:2px;padding:16px;'
            f'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
            f'<p style="font-size:13px;font-weight:700;color:#5b5bd6;margin:0 0 10px 0;">{drug}</p>'
            f'<ul style="margin:0;padding-left:16px;">{our_li}</ul>'
            f'</div>',
            unsafe_allow_html=True
        )
    with c2:
        if top_comp:
            comp_li = "".join(
                f'<li style="font-size:12px;color:#555;line-height:1.6;margin-bottom:4px;">{a}</li>'
                for a in (top_comp.clinical_advantages[:2] or ["Established market presence"])
            )
            comp_name = top_comp.competitor_name
        else:
            comp_li = '<li style="font-size:12px;color:#555;">Established market presence</li>'
            comp_name = "Primary Competitor"
        st.markdown(
            f'<div style="background:#F5F5F5;border-left:3px solid #E0E0E0;border-radius:2px;padding:16px;'
            f'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
            f'<p style="font-size:13px;font-weight:700;color:#5b5bd6;margin:0 0 10px 0;">{comp_name}</p>'
            f'<ul style="margin:0;padding-left:16px;">{comp_li}</ul>'
            f'</div>',
            unsafe_allow_html=True
        )
