"""
Presentational helper functions for the Evidentia MSL Intelligence Platform.

These are pure presentational utilities — they call st.markdown / return HTML strings
and have no side effects on GTMState. Extracted from src/ui/app.py.

Import cycle note: this module may import from src.ui.components and src.schema,
but must NEVER import from src.ui.app.
"""

import streamlit as st


def chip_for(state, key: str) -> str:
    """Return source-chip HTML for a sources-map key, or '' if absent."""
    src = getattr(state, "sources", {}).get(key)
    if not src:
        return ""
    from src.ui.components import source_chip_html
    return source_chip_html(src.tier, src.label, url=src.url, note=src.note)


def glance_lead_points(state) -> tuple:
    """Return (lead_point, likely_objection) as Optional[str] each.

    Reads real GTMState fields first; also tolerates duck-typed shapes.
    Never raises — missing or None data returns None for that part.
    """
    lead = None
    objection = None

    # ── Lead talking point ───────────────────────────────────────────────────
    tp = getattr(state, "msl_talking_points", None)
    if tp is not None:
        # Real MSLTalkingPoints path: prefer conversation_opener
        opener = getattr(tp, "conversation_opener", None)
        if opener and isinstance(opener, str) and opener.strip():
            lead = opener.strip()
        else:
            # Fallback: first msl_talking_point from three_pillars
            pillars = getattr(tp, "three_pillars", None) or []
            for pillar in pillars:
                pt = getattr(pillar, "msl_talking_point", None)
                if pt and isinstance(pt, str) and pt.strip():
                    lead = pt.strip()
                    break

        # Duck-typed fallback: talking_points list (not in real schema)
        if not lead:
            duck_list = getattr(tp, "talking_points", None)
            if duck_list and isinstance(duck_list, (list, tuple)) and duck_list:
                first = duck_list[0]
                if first and isinstance(first, str) and first.strip():
                    lead = first.strip()

    # Generic MessagingData fallback for lead
    if not lead:
        md = getattr(state, "messaging_data", None)
        if md is not None:
            pillars = getattr(md, "messaging_pillars", None) or []
            if pillars and isinstance(pillars[0], str) and pillars[0].strip():
                lead = pillars[0].strip()
            if not lead:
                pos = getattr(md, "positioning_statement", None)
                if pos and isinstance(pos, str) and pos.strip():
                    lead = pos.strip()

    # ── Likely objection ─────────────────────────────────────────────────────
    tp = getattr(state, "msl_talking_points", None)
    if tp is not None:
        ant_objs = getattr(tp, "anticipated_objections", None) or []
        for obj in ant_objs:
            text = getattr(obj, "objection", None)
            if text and isinstance(text, str) and text.strip():
                objection = text.strip()
                break

    # Duck-typed top-level objections list (SimpleNamespace test shape)
    if not objection:
        duck_objs = getattr(state, "objections", None)
        if duck_objs and isinstance(duck_objs, (list, tuple)) and duck_objs:
            first = duck_objs[0]
            if isinstance(first, dict):
                text = first.get("objection") or first.get("response")
            else:
                text = getattr(first, "objection", None)
            if text and isinstance(text, str) and text.strip():
                objection = text.strip()

    # Generic MessagingData fallback for objection
    if not objection:
        md = getattr(state, "messaging_data", None)
        if md is not None:
            common = getattr(md, "common_objections", None) or {}
            if common and isinstance(common, dict):
                first_key = next(iter(common), None)
                if first_key and isinstance(first_key, str) and first_key.strip():
                    objection = first_key.strip()

    return (lead, objection)


def _tab_heading(title: str, subtitle: str = ""):
    """Render a consistent tab-level heading with optional subtitle."""
    sub_html = (
        f'<p style="font-size:14px;font-weight:400;color:#666666;font-style:italic;'
        f'margin:6px 0 28px 0;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">{subtitle}</p>'
        if subtitle else '<div style="height:20px"></div>'
    )
    st.markdown(
        f'<p style="font-size:28px;font-weight:700;color:#5b5bd6;margin:0;'
        f'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">{title}</p>{sub_html}',
        unsafe_allow_html=True
    )


def _section_label(text: str):
    """Render a section label (uppercase, 16px, #5b5bd6)."""
    st.markdown(
        f'<p style="font-size:16px;font-weight:600;color:#5b5bd6;text-transform:uppercase;'
        f'letter-spacing:0.5px;margin:0 0 6px 0;'
        f'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">{text}</p>',
        unsafe_allow_html=True
    )
