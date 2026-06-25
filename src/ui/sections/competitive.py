"""
MSL Tab: Competitive Position section.

Moved from src/ui/app.py as part of Stage 5 — Architecture Refactor (Part 2).
Interactive 2-drug comparison table added in Stage 6.
"""

import re
import streamlit as st
from src.ui.helpers import _tab_heading, _section_label
from src.ui.components import source_chip_html


_COMPARISON_ROWS = [
    ("mechanism",        "Mechanism"),
    ("efficacy",         "Efficacy"),
    ("key_safety",       "Key Safety"),
    ("primary_endpoint", "Primary Endpoint"),
    ("dosing",           "Dosing"),
    ("approval_status",  "Trial status"),
]

# Session state key for the competitor text input
_COMP_INPUT_KEY = "_comp_text_input"


def _short_endpoint(text: str) -> str:
    """Trim verbose registry tail from a primary endpoint string.

    Strips at common verbose suffixes: " as Assessed", " as assessed", " per "
    and any trailing parenthetical method clause.  If trimming would produce an
    empty string the original text is returned unchanged.
    """
    if not text:
        return text
    # Cut at known verbose suffixes (case-insensitive)
    pattern = re.compile(
        r"\s*(as assessed\b| as Assessed\b| per )",
        re.IGNORECASE,
    )
    trimmed = pattern.split(text)[0].strip()
    # Also strip a trailing bare parenthetical if it's now the last thing
    trimmed = re.sub(r"\s*\([^)]+\)\s*$", "", trimmed).strip()
    return trimmed if trimmed else text


def _render_interactive_comparison_table(
    drug: str,
    subject_row: dict,
    comp_row: dict,
    chosen_competitor: str,
) -> None:
    """Render an interactive 2-drug side-by-side HTML comparison table.

    Columns: dimension label | subject drug | chosen competitor.
    Each drug column header shows: drug name, trial phase, NCT chip (when
    available) AND a PMID publication chip (when available).
    Empty / missing values show "—".
    """

    def _header_cell(drug_label: str, row: dict, bg: str) -> str:
        phase = row.get("phase", "") or ""
        nct_id = row.get("nct_id", "") or ""
        nct_url = row.get("nct_url", "") or ""
        pmid = row.get("pmid", "") or ""
        pmid_url = row.get("pmid_url", "") or ""

        phase_html = (
            f'<span style="font-size:10px;font-weight:500;color:rgba(255,255,255,0.75);'
            f'margin-left:6px;">({phase})</span>'
            if phase else ""
        )

        chips_parts = []
        if nct_id:
            chip = source_chip_html("verified", nct_id, url=nct_url or None,
                                    note="ClinicalTrials.gov — highest-phase trial")
            chips_parts.append(chip)
        if pmid:
            pub_chip = source_chip_html("verified", f"PMID {pmid}", url=pmid_url or None,
                                        note="PubMed publication")
            chips_parts.append(pub_chip)

        if chips_parts:
            chip_html = (
                f'<div style="margin-top:6px;font-size:10px;display:flex;gap:6px;'
                f'flex-wrap:wrap;">'
                + "".join(chips_parts)
                + "</div>"
            )
        else:
            chip_html = (
                '<div style="margin-top:6px;font-size:10px;color:rgba(255,255,255,0.55);">'
                'No source found</div>'
            )

        return (
            f'<th style="background:{bg};color:#fff;font-size:11px;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:.07em;padding:10px 12px;text-align:left;'
            f'min-width:180px;vertical-align:top;">'
            f'{drug_label}{phase_html}'
            f'{chip_html}'
            f'</th>'
        )

    dim_header = (
        '<th style="background:#5b5bd6;color:#fff;font-size:11px;font-weight:700;'
        'text-transform:uppercase;letter-spacing:.07em;padding:10px 12px;text-align:left;'
        'min-width:120px;">Dimension</th>'
    )
    subject_header = _header_cell(drug, subject_row, "#5b5bd6")
    comp_header = _header_cell(chosen_competitor, comp_row, "#3d3d7a")

    # --- data rows ---
    data_rows = ""
    subj_dims = subject_row.get("dimensions", {}) or {}
    comp_dims = comp_row.get("dimensions", {}) or {}

    for i, (field_key, label) in enumerate(_COMPARISON_ROWS):
        bg = "#ffffff" if i % 2 == 0 else "#f7f7fb"

        label_cell = (
            f'<td style="background:{bg};font-size:11px;font-weight:700;color:#666;'
            f'text-transform:uppercase;letter-spacing:.06em;padding:8px 12px;'
            f'border-bottom:1px solid #e8e8f0;white-space:nowrap;">{label}</td>'
        )

        subj_val = subj_dims.get(field_key, "") or ""
        if field_key == "primary_endpoint":
            subj_val = _short_endpoint(subj_val)
        subj_display = subj_val.strip() if subj_val.strip() else "—"
        subject_cell = (
            f'<td style="background:{bg};font-size:12px;color:#333;padding:8px 12px;'
            f'border-bottom:1px solid #e8e8f0;line-height:1.4;">{subj_display}</td>'
        )

        comp_val = comp_dims.get(field_key, "") or ""
        if field_key == "primary_endpoint":
            comp_val = _short_endpoint(comp_val)
        comp_display = comp_val.strip() if comp_val.strip() else "—"
        comp_cell = (
            f'<td style="background:{bg};font-size:12px;color:#555;padding:8px 12px;'
            f'border-bottom:1px solid #e8e8f0;line-height:1.4;">{comp_display}</td>'
        )

        data_rows += f"<tr>{label_cell}{subject_cell}{comp_cell}</tr>"

    html = (
        '<div style="overflow-x:auto;margin-bottom:24px;">'
        '<table style="border-collapse:collapse;width:100%;font-family:\'Inter\','
        '\'Helvetica Neue\',sans-serif;border:1px solid #e0e0e0;border-radius:4px;">'
        f'<thead><tr>{dim_header}{subject_header}{comp_header}</tr></thead>'
        f'<tbody>{data_rows}</tbody>'
        '</table></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def display_competitive_section(state):
    """Professional competitive landscape tab with interactive 2-drug CI comparison."""

    drug = getattr(state, "drug_name", "this drug") or "this drug"
    indication = getattr(state, "indication", "") or ""

    _tab_heading("Competitive Landscape",
                 f"Competitor comparison and {drug} differentiation"
                 + (f" in {indication}" if indication else ""))

    if not state.competitor_data:
        st.warning("No competitor data available.")
        return

    competitors = list(getattr(state.competitor_data, "competitors", []) or [])

    # ── Interactive 2-drug comparison ─────────────────────────────────────────
    _section_label("Head-to-Head Comparison")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Single text input (sole source of truth for chosen competitor)
    typed = st.text_input(
        "Compare against",
        placeholder="e.g. adagrasib",
        key=_COMP_INPUT_KEY,
    ).strip()

    # Suggestion chips — quick-pick buttons for each named competitor in the brief
    comp_names = [
        c.competitor_name
        for c in competitors
        if getattr(c, "competitor_name", None)
    ]
    if comp_names:
        chip_cols = st.columns(len(comp_names))
        for idx, name in enumerate(comp_names):
            with chip_cols[idx]:
                if st.button(name, key=f"_chip_{name}"):
                    st.session_state[_COMP_INPUT_KEY] = name
                    st.rerun()

    # Resolve chosen competitor — text input value (typed or chip-set), stripped
    chosen_competitor = typed if typed else None

    if chosen_competitor is None:
        # No selection — show prompt, skip any fetch
        st.info(
            f"Select or type a competitor above to compare against **{drug}**."
        )
    else:
        # Lazy import to keep module-level imports minimal
        from src.service.comparison import build_comparison_row
        from src.service.cache.cache_manager import CacheManager

        # Reuse or create a session-scoped cache
        if "_cmp_cache" not in st.session_state:
            st.session_state["_cmp_cache"] = CacheManager()
        cache = st.session_state["_cmp_cache"]

        subject_row: dict | None = None
        comp_row: dict | None = None
        fetch_error: str | None = None

        with st.spinner("Fetching highest-phase trial data…"):
            try:
                subject_row = build_comparison_row(
                    drug,
                    retrieved_trials=(
                        getattr(state.market_data, "clinical_trials", None) or []
                    ),
                    cache=cache,
                )
            except Exception as exc:
                fetch_error = f"Could not load subject drug data: {exc}"

            try:
                comp_row = build_comparison_row(
                    chosen_competitor,
                    retrieved_trials=None,  # live fetch for competitor
                    cache=cache,
                )
            except Exception as exc:
                if fetch_error:
                    fetch_error += f" | {exc}"
                else:
                    fetch_error = f"Could not load competitor data: {exc}"

        if fetch_error:
            st.warning(
                f"Some trial data could not be retrieved ({fetch_error}). "
                "Partial results are shown below."
            )

        # Always render the table (with whatever rows we have — use empty dicts on failure)
        _render_interactive_comparison_table(
            drug=drug,
            subject_row=subject_row or {},
            comp_row=comp_row or {},
            chosen_competitor=chosen_competitor,
        )

    # ── Competitor cards (side-by-side) ───────────────────────────────────────
    # Only render "HOW WE COMPARE" header when there are actual competitors to show
    top_competitors = competitors[:3]
    if top_competitors:
        _section_label("How We Compare")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        cols = st.columns(len(top_competitors))
        for i, comp in enumerate(top_competitors):
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
    if top_competitors:
        st.markdown(
            '<hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 24px 0;">',
            unsafe_allow_html=True
        )
        _section_label("What to Say When...")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        for comp in top_competitors:
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
