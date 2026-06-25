"""
MSL Tab: Talking Points section.

Moved from src/ui/app.py as part of Stage 5 — Architecture Refactor (Part 2).
"""

import re
import streamlit as st
from src.ui.helpers import _tab_heading, _section_label


def _resolve_source_url(evidence, state) -> tuple[str, str]:
    """
    Return (display_label, url) for a pillar's evidence ONLY when a real
    retrieved record confirms the id.

    Strategy (honest / safe):
    1. If evidence.trial_name looks like an NCT id (starts with NCT), check
       state.market_data.clinical_trials for a matching nct_id.  If found,
       build the canonical ClinicalTrials.gov URL from that confirmed id.
    2. Otherwise, check whether evidence.trial_name (case-insensitive) appears
       in any clinical trial's title — if yes, use that trial's nct_id to build
       the URL.
    3. If evidence.source contains a PMID (digits only, or "PMID NNNNN"), check
       state.market_data.key_publications for a matching pmid and use
       pubmed.ncbi.nlm.nih.gov URL built from the confirmed pmid.
    4. If nothing matches, return ("", "") — no chip is shown.

    We NEVER fabricate a URL.  Only ids confirmed present in the retrieved
    market_data records produce a link.
    """
    if not evidence:
        return ("", "")

    market_data = getattr(state, "market_data", None)
    trials = (market_data.clinical_trials or []) if market_data else []
    pubs = (market_data.key_publications or []) if market_data else []

    trial_name = (evidence.trial_name or "").strip()
    source_text = (evidence.source or "").strip()

    # ── 1. Match by NCT id ────────────────────────────────────────────────────
    nct_match = re.match(r"(?i)(NCT\d{8})", trial_name)
    if nct_match:
        nct_id = nct_match.group(1).upper()
        for t in trials:
            if (t.get("nct_id") or "").upper() == nct_id:
                return (nct_id, f"https://clinicaltrials.gov/study/{nct_id}")

    # ── 2. Match by trial name substring ─────────────────────────────────────
    if trial_name:
        name_lower = trial_name.lower()
        for t in trials:
            t_title = (t.get("title") or "").lower()
            t_nct = (t.get("nct_id") or "").upper()
            if name_lower in t_title or (t_nct and t_nct.lower() in name_lower):
                if t_nct:
                    return (t_nct, f"https://clinicaltrials.gov/study/{t_nct}")

    # ── 3. Match by PMID in source field ──────────────────────────────────────
    pmid_match = re.search(r"(?i)(?:PMID\s*:?\s*)?(\b\d{7,8}\b)", source_text)
    if pmid_match:
        pmid = pmid_match.group(1)
        for p in pubs:
            if str(p.get("pmid") or "").strip() == pmid:
                return (f"PMID {pmid}", f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")

    return ("", "")


def display_talking_points_section(state):
    """Display MSL talking points — KOL-specific if available, generic fallback if not."""

    tp = getattr(state, "msl_talking_points", None)

    if tp:
        _render_msl_talking_points(state, tp)
    else:
        _render_generic_talking_points(state)


def _tp_styles() -> str:  # stub — CSS now lives in global <style> block
    return ""


def _render_msl_talking_points(state, tp):
    """Render the professional MSL talking points UI for a specific KOL."""

    # ── KOL header ───────────────────────────────────────────────────────────
    population_html = (
        f'<span class="tp-kol-population">&nbsp;&nbsp;/&nbsp;&nbsp;{tp.patient_population}</span>'
        if tp.patient_population else ""
    )
    st.markdown(f"""
    <div class="tp-kol-header">
        <span class="tp-kol-name">{tp.kol_name}</span>
        <span class="tp-kol-meta">{tp.kol_institution}</span>
        {population_html}
    </div>
    """, unsafe_allow_html=True)

    # ── Section 1: Conversation Opener ───────────────────────────────────────
    st.markdown('<p class="tp-label">Conversation Opener</p>', unsafe_allow_html=True)

    why_html = (
        f'<div class="tp-opener-meta-item"><strong>Why it works</strong>{tp.opener_why_it_works}</div>'
        if tp.opener_why_it_works else ""
    )
    tips_html = (
        f'<div class="tp-opener-meta-item"><strong>Delivery</strong>{tp.opener_delivery_tips}</div>'
        if tp.opener_delivery_tips else ""
    )
    meta_html = (
        f'<div class="tp-opener-meta">{why_html}{tips_html}</div>'
        if (why_html or tips_html) else ""
    )

    st.markdown(f"""
    <div class="tp-opener">
        {tp.conversation_opener}
        {meta_html}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── Section 2: Three Clinical Pillars ────────────────────────────────────
    st.markdown('<p class="tp-label">Three Clinical Pillars</p>', unsafe_allow_html=True)

    pillars = tp.three_pillars or []
    cols = st.columns(3)
    for i, pillar in enumerate(pillars[:3]):
        ev = getattr(pillar, "evidence", None)
        trial_label = (ev.trial_name if ev and ev.trial_name else "Clinical observation")
        data_point_html = (
            f'<div class="tp-data-point">{ev.key_data_point}</div>'
            if ev and ev.key_data_point else ""
        )
        relevance_html = (
            f'<div class="tp-pillar-relevance">{pillar.why_relevant_to_kol}</div>'
            if getattr(pillar, "why_relevant_to_kol", "") else ""
        )
        # Source chip: only when we can confirm the id against retrieved data
        chip_label, chip_url = _resolve_source_url(ev, state)
        if chip_label and chip_url:
            source_chip_html = (
                f'<a class="tp-source-chip" href="{chip_url}" target="_blank" '
                f'rel="noopener noreferrer">{chip_label}</a>'
            )
        else:
            source_chip_html = ""

        with cols[i]:
            st.markdown(f"""
            <div class="tp-pillar">
                <div class="tp-pillar-number">Pillar {i+1}</div>
                <div class="tp-pillar-title">{pillar.pillar_title}</div>
                <div class="tp-evidence-tag">{trial_label}</div>
                {data_point_html}
                <div class="tp-talking-point">{getattr(pillar, "msl_talking_point", "")}</div>
                {relevance_html}
                {source_chip_html}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── Section 3: Key Differentiators ───────────────────────────────────────
    if tp.key_differentiators:
        st.markdown('<p class="tp-label">vs Current Standard of Care</p>',
                    unsafe_allow_html=True)

        rows_html = ""
        for diff in tp.key_differentiators:
            talking_html = (
                f'<div class="tp-diff-talking">{diff.msl_talking_point}</div>'
                if diff.msl_talking_point else ""
            )
            rows_html += f"""
            <tr>
                <td>{diff.vs_standard_of_care}</td>
                <td class="tp-diff-advantage">{diff.advantage}</td>
                <td>
                    <span style="font-size:12px;color:#666666;">{diff.evidence}</span>
                    {talking_html}
                </td>
            </tr>
            """

        st.markdown(f"""
        <table class="tp-diff-table">
            <thead>
                <tr>
                    <th>Current practice</th>
                    <th>What changes</th>
                    <th>Evidence &amp; how to say it</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── Section 4: Anticipated Objections ────────────────────────────────────
    if tp.anticipated_objections:
        st.markdown('<p class="tp-label">Anticipated Objections</p>',
                    unsafe_allow_html=True)

        for obj in tp.anticipated_objections:
            prob = getattr(obj, "probability", "")
            label = obj.objection or ""
            expander_label = f"{label}  ({prob})" if prob else label

            with st.expander(expander_label, expanded=False):
                if getattr(obj, "why_they_ask", ""):
                    st.markdown(
                        '<p style="font-size:10px;font-weight:700;letter-spacing:.07em;'
                        'text-transform:uppercase;color:#999;margin:0 0 3px 0;">Why they ask</p>',
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f'<p style="font-size:13px;color:#333;line-height:1.5;margin:0 0 12px 0;">'
                        f'{obj.why_they_ask}</p>',
                        unsafe_allow_html=True
                    )
                if getattr(obj, "evidence_response", ""):
                    st.markdown(
                        '<p style="font-size:10px;font-weight:700;letter-spacing:.07em;'
                        'text-transform:uppercase;color:#999;margin:0 0 3px 0;">Evidence</p>',
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f'<p style="font-size:13px;color:#333;line-height:1.5;margin:0 0 12px 0;">'
                        f'{obj.evidence_response}</p>',
                        unsafe_allow_html=True
                    )
                if getattr(obj, "msl_response", ""):
                    st.markdown(
                        '<p style="font-size:10px;font-weight:700;letter-spacing:.07em;'
                        'text-transform:uppercase;color:#999;margin:0 0 3px 0;">How to respond</p>',
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f'<div class="tp-obj-response">{obj.msl_response}</div>',
                        unsafe_allow_html=True
                    )

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # ── Section 5: Guardrails ─────────────────────────────────────────────────
    if tp.guardrails:
        st.markdown(
            '<p style="font-size:16px;font-weight:600;color:#FF9500;text-transform:uppercase;'
            'letter-spacing:0.5px;margin:0 0 16px 0;">Do Not Say</p>',
            unsafe_allow_html=True
        )

        for g in tp.guardrails:
            instead_html = (
                f'<div class="tp-guardrail-instead">Instead: {g.alternative}</div>'
                if g.alternative else ""
            )
            st.markdown(f"""
            <div class="tp-guardrail">
                <div class="tp-guardrail-avoid">Avoid: <span>"{g.avoid_claim}"</span></div>
                <div class="tp-guardrail-reason">{g.reason}</div>
                {instead_html}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)


def _render_generic_talking_points(state):
    """Fallback: render generic positioning content when no KOL is selected.

    Layout is intentionally labelled "General positioning" so users are not
    misled into thinking the content below is KOL-specific.  A single,
    contextual note at the bottom invites them to select a physician — it is
    never shown above the content as if the content were already KOL-tailored.
    """

    # ── Section header — unambiguously general ────────────────────────────────
    st.markdown("""
    <div class="tp-general-header">
        <span class="tp-general-title">General positioning</span>
    </div>
    """, unsafe_allow_html=True)

    if not state.messaging_data:
        st.warning("No messaging data available.")
        # Still show the physician-select prompt — single, bottom-aligned
        st.markdown("""
        <div class="tp-kol-prompt">
            Select a physician in the sidebar for KOL-tailored talking points.
        </div>
        """, unsafe_allow_html=True)
        return

    if state.messaging_data.positioning_statement:
        st.markdown('<p class="tp-label">Positioning Statement</p>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="tp-opener">
            {state.messaging_data.positioning_statement}
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    differentiators = state.messaging_data.key_differentiators[:3]
    if differentiators:
        st.markdown('<p class="tp-label">Key Differentiators</p>', unsafe_allow_html=True)
        pills = "".join(
            f'<span class="tp-diff-pill">{d}</span>' for d in differentiators
        )
        st.markdown(f"<div>{pills}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    pillars = state.messaging_data.messaging_pillars[:3]
    if pillars:
        st.markdown('<p class="tp-label">Three Messaging Pillars</p>', unsafe_allow_html=True)
        for i, pillar in enumerate(pillars, 1):
            st.markdown(f"""
            <div class="tp-generic-pillar">
                <div class="tp-generic-pillar-num">Pillar {i}</div>
                {pillar}
            </div>
            """, unsafe_allow_html=True)

    # ── Single, unambiguous KOL prompt at the bottom ──────────────────────────
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="tp-kol-prompt">
        Select a physician in the sidebar for KOL-tailored talking points.
    </div>
    """, unsafe_allow_html=True)
