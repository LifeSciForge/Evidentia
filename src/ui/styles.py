"""
Global stylesheets for the Evidentia MSL Intelligence Platform.

Two constants are provided:
- EV_STYLES_FULLWIDTH: the small force-full-width override injected first.
- EV_STYLES: the main global stylesheet (Inter font, pharma palette, tab nav, etc.)

Use inject_styles() to inject both at module level in app.py.
"""

import streamlit as st

EV_STYLES_FULLWIDTH = """
<style>
    .main { max-width: 100% !important; padding: 0 2rem; }
    .block-container { max-width: 100% !important; padding-left: 1rem !important; padding-right: 1rem !important; }
</style>
"""

EV_STYLES = """
<style>
/* ── Direction C Design Tokens ───────────────────────────────────────────── */
:root{
  --ev-bg:#f7f8fb; --ev-surface:#ffffff; --ev-border:#ececf3;
  --ev-text:#1a1d29; --ev-muted:#6b7280; --ev-accent:#5b5bd6;
  --ev-verified:#1aa564; --ev-web:#4b4bc7; --ev-filing:#c2741b; --ev-unavailable:#9aa0ad;
}
.ev-chip{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:600;
  padding:4px 9px;border-radius:999px;text-decoration:none;border:1px solid transparent;}
.ev-chip-verified{background:#e9f7f0;color:var(--ev-verified);}
.ev-chip-web{background:#eef0fe;color:var(--ev-web);}
.ev-chip-filing{background:#fff3e9;color:var(--ev-filing);}
.ev-chip-modeled{background:#fff3e9;color:var(--ev-filing);}
.ev-chip-unavailable{background:#f1f2f5;color:var(--ev-unavailable);}
.ev-metric-card{background:var(--ev-surface);border:1px solid var(--ev-border);border-radius:14px;
  padding:16px;box-shadow:0 1px 3px rgba(20,20,50,.05);}
.ev-metric-label{font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--ev-muted);}
.ev-metric-value{font-size:24px;font-weight:700;color:var(--ev-text);margin:4px 0 8px;}
.ev-metric-chip{margin-bottom:6px;} .ev-metric-sub{font-size:12px;color:var(--ev-muted);}
.ev-glance{margin:8px 0 4px;} .ev-glance-row{display:flex;gap:14px;flex-wrap:wrap;}
.ev-glance-row > div{flex:1;min-width:180px;}
.ev-glance-box{background:var(--ev-surface);border:1px solid var(--ev-border);border-radius:12px;padding:13px;}
.ev-glance-h{font-size:11px;font-weight:700;color:var(--ev-accent);text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px;}
.ev-glance-box p{font-size:13px;color:#3f4654;margin:0;line-height:1.5;}

/* Force full width - Streamlit 1.55 compatible */
.main > div { max-width: 100% !important; }
.block-container { max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; padding-top: 1rem !important; }
div[data-testid="stMainBlockContainer"] { max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; }
div[data-testid="stAppViewBlockContainer"] { max-width: 100% !important; }
section[data-testid="stMain"] { width: 100% !important; background:var(--ev-bg); }

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Base ───────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
}

/* ── Page header ─────────────────────────────────────────────────────────── */
.ev-page-header {
    padding: 28px 0 4px 0;
    margin-bottom: 0;
}
.ev-brand-title {
    font-family: 'Inter', sans-serif;
    font-size: 32px;
    font-weight: 700;
    color: var(--ev-accent);
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin: 0;
    line-height: 1.2;
}
.ev-brand-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    font-weight: 400;
    color: #999999;
    margin: 4px 0 0 0;
    letter-spacing: 0.01em;
}
.ev-divider {
    border: none;
    border-top: 1px solid #E8E8E8;
    margin: 16px 0 0 0;
}

/* ── Metadata strip ─────────────────────────────────────────────────────── */
.ev-meta-strip {
    display: flex;
    align-items: center;
    gap: 32px;
    padding: 14px 0 14px 0;
    border-bottom: 1px solid #E8E8E8;
    flex-wrap: wrap;
}
.ev-meta-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
}
.ev-meta-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #999999;
    line-height: 1.2;
}
.ev-meta-value {
    font-size: 14px;
    font-weight: 600;
    color: var(--ev-text);
    line-height: 1.3;
}
.ev-meta-value-sm {
    font-size: 12px;
    font-weight: 400;
    color: #666666;
    line-height: 1.3;
}
.ev-status-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    font-weight: 500;
    color: #1A7F4B;
    background: #E6F4EE;
    border: 1px solid #A8D5BE;
    border-radius: 20px;
    padding: 3px 10px;
    line-height: 1.4;
}
.ev-status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #1A7F4B;
    display: inline-block;
}

/* ── Tab navigation ─────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 2px solid #E8E8E8;
    background: transparent;
}
.stTabs [data-baseweb="tab-list"] button {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 400;
    color: #666666;
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
    padding: 10px 18px;
    border-radius: 0;
    transition: color 0.15s ease, border-color 0.15s ease;
}
.stTabs [data-baseweb="tab-list"] button:hover {
    color: var(--ev-accent);
    background: transparent;
}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    font-weight: 700;
    color: var(--ev-accent);
    border-bottom: 2px solid var(--ev-accent);
    background: transparent;
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}

/* ── Utility ─────────────────────────────────────────────────────────────── */
.info-card {
    background: linear-gradient(135deg, #0055B8 0%, #003D82 100%);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
    box-shadow: 0 2px 8px rgba(0,85,184,0.2);
}
.metric-card {
    background: #F4F7FB;
    color: var(--ev-text);
    padding: 20px;
    border-radius: 8px;
    margin: 10px 0;
    border-left: 3px solid var(--ev-accent);
}
.success-box {
    background-color: #E6F4EE;
    color: #1A7F4B;
    padding: 15px;
    border-radius: 5px;
    border-left: 4px solid #1A7F4B;
}
.warning-box {
    background-color: #FFF8E6;
    color: #856404;
    padding: 15px;
    border-radius: 5px;
    border-left: 4px solid #FFC107;
}
.error-box {
    background-color: #FDF0F0;
    color: #B91C1C;
    padding: 15px;
    border-radius: 5px;
    border-left: 4px solid #B91C1C;
}

/* ── Talking Points tab classes ─────────────────────────────────────────── */
.tp-root { font-family: 'Inter','Helvetica Neue','Open Sans',sans-serif; color: #333333; }
.tp-label { font-size:11px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#999999; margin:0 0 8px 0; line-height:1.2; }
.tp-kol-header { background:var(--ev-accent); border-radius:6px; padding:14px 20px; margin-bottom:24px; display:flex; align-items:baseline; gap:12px; }
.tp-kol-name { font-size:14px; font-weight:700; color:#ffffff; letter-spacing:0.3px; }
.tp-kol-meta { font-size:12px; font-weight:400; color:#A8C4E0; }
.tp-kol-population { font-size:11px; font-weight:400; color:#7BA7CC; font-style:italic; }
.tp-opener { background:#E8F1F8; border-left:3px solid var(--ev-accent); border-radius:0 4px 4px 0; padding:16px 20px; font-size:13px; line-height:1.7; color:#333333; margin-bottom:8px; }
.tp-opener-meta { display:flex; gap:24px; margin-top:10px; }
.tp-opener-meta-item { font-size:11px; color:#666666; line-height:1.5; }
.tp-opener-meta-item strong { display:block; font-size:10px; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; color:#999999; margin-bottom:2px; }
.tp-pillars { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:4px; }
.tp-pillar { background:#ffffff; border:1px solid #E0E0E0; border-top:3px solid var(--ev-accent); border-radius:4px; padding:16px; }
.tp-pillar-number { font-size:10px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#999999; margin-bottom:4px; }
.tp-pillar-title { font-size:13px; font-weight:600; color:var(--ev-accent); line-height:1.3; margin-bottom:10px; }
.tp-evidence-tag { display:inline-block; background:#F5F5F5; border:1px solid #E0E0E0; border-radius:3px; font-size:10px; font-weight:600; color:#666666; letter-spacing:0.04em; padding:2px 7px; margin-bottom:6px; }
.tp-data-point { font-size:12px; font-weight:600; color:var(--ev-accent); margin-bottom:10px; line-height:1.4; }
.tp-talking-point { font-size:13px; font-style:italic; color:#555555; line-height:1.6; border-top:1px solid #F0F0F0; padding-top:10px; margin-top:4px; }
.tp-pillar-relevance { font-size:11px; color:#999999; line-height:1.5; margin-top:10px; }
.tp-diff-table { width:100%; border-collapse:collapse; font-size:13px; margin-bottom:4px; }
.tp-diff-table th { font-size:10px; font-weight:700; letter-spacing:0.07em; text-transform:uppercase; color:#999999; padding:6px 12px; background:#F5F5F5; border-bottom:1px solid #E0E0E0; text-align:left; }
.tp-diff-table td { padding:12px 12px; vertical-align:top; border-bottom:1px solid #F0F0F0; color:#333333; line-height:1.5; }
.tp-diff-advantage { color:#00A86B; font-weight:500; }
.tp-diff-talking { font-size:12px; font-style:italic; color:#555555; margin-top:4px; }
.tp-obj-row { border:1px solid #E0E0E0; border-radius:4px; margin-bottom:8px; overflow:hidden; }
.tp-obj-header { display:flex; align-items:center; justify-content:space-between; padding:12px 16px; background:#F5F5F5; border-bottom:1px solid #E0E0E0; }
.tp-obj-title { font-size:13px; font-weight:600; color:var(--ev-accent); line-height:1.4; }
.tp-obj-prob { font-size:11px; font-weight:600; color:#FF9500; background:#FFF3E0; border-radius:3px; padding:2px 8px; white-space:nowrap; margin-left:12px; }
.tp-obj-body { padding:12px 16px; background:#ffffff; }
.tp-obj-field-label { font-size:10px; font-weight:700; letter-spacing:0.07em; text-transform:uppercase; color:#999999; margin-bottom:3px; }
.tp-obj-field-value { font-size:13px; color:#333333; line-height:1.5; margin-bottom:12px; }
.tp-obj-response { font-size:13px; font-style:italic; color:#555555; line-height:1.6; background:#F5F5F5; border-radius:3px; padding:10px 14px; }
.tp-guardrail { border-left:3px solid #FF9500; background:#FFFBF5; border-radius:0 4px 4px 0; padding:12px 16px; margin-bottom:8px; }
.tp-guardrail-avoid { font-size:13px; font-weight:600; color:#333333; margin-bottom:4px; }
.tp-guardrail-avoid span { font-weight:400; font-style:italic; color:#666666; }
.tp-guardrail-reason { font-size:12px; color:#666666; margin-bottom:6px; line-height:1.5; }
.tp-guardrail-instead { font-size:12px; color:#00A86B; font-weight:500; }
.tp-generic-notice { font-size:12px; color:#999999; margin-bottom:20px; padding:10px 14px; background:#F5F5F5; border-radius:4px; border-left:3px solid #E0E0E0; }
.tp-generic-pillar { padding:10px 0; border-bottom:1px solid #F0F0F0; font-size:13px; color:#333333; line-height:1.5; }
.tp-generic-pillar-num { font-size:10px; font-weight:700; color:#999999; letter-spacing:0.07em; text-transform:uppercase; margin-bottom:2px; }
.tp-diff-pill { display:inline-block; background:#eef0fe; color:var(--ev-accent); font-size:11px; font-weight:600; border-radius:3px; padding:3px 9px; margin:3px 4px 3px 0; }

/* ── Spacing / whitespace reduction ─────────────────────────────────────── */
.block-container {
    padding-top: 1rem !important;
}
section.main > div.block-container {
    padding-top: 1rem !important;
}
[data-testid="stVerticalBlock"] {
    gap: 0.5rem !important;
}
[data-testid="stVerticalBlockWithBorder"] {
    gap: 0.5rem !important;
}
div[data-testid="stMarkdown"] p {
    margin-top: 0.25rem !important;
    margin-bottom: 0.25rem !important;
}
.ev-page-header {
    padding-top: 12px !important;
    padding-bottom: 2px !important;
}
.ev-meta-strip {
    padding-top: 8px !important;
    padding-bottom: 8px !important;
}

/* ── Expander overrides (Objections tab) ────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #E0E0E0 !important;
    border-radius: 4px !important;
    margin-bottom: 16px !important;
    overflow: hidden !important;
    box-shadow: none !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] .streamlit-expanderHeader {
    background: #F5F5F5 !important;
    padding: 16px 20px !important;
    font-family: 'Inter','Helvetica Neue',sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    color: var(--ev-accent) !important;
    line-height: 1.5 !important;
    border-bottom: none !important;
    min-height: unset !important;
}
[data-testid="stExpander"] summary:hover,
[data-testid="stExpander"] .streamlit-expanderHeader:hover {
    background: #E8E8E8 !important;
}
[data-testid="stExpander"][open] summary,
[data-testid="stExpander"][open] .streamlit-expanderHeader {
    background: #E8F1F8 !important;
    border-bottom: 1px solid #E0E0E0 !important;
}
[data-testid="stExpander"] .streamlit-expanderContent,
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    padding: 24px 20px !important;
    background: #FFFFFF !important;
}
[data-testid="stExpander"] .streamlit-expanderContent p,
[data-testid="stExpander"] [data-testid="stExpanderDetails"] p {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}
[data-testid="stExpander"] summary svg,
[data-testid="stExpander"] .streamlit-expanderHeader svg {
    color: var(--ev-accent) !important;
    fill: var(--ev-accent) !important;
}
.block-container { max-width: 98% !important; padding-left: 2rem !important; padding-right: 2rem !important; }
</style>
"""


def inject_styles() -> None:
    """Inject the global Evidentia stylesheets into the Streamlit page."""
    st.markdown(EV_STYLES_FULLWIDTH, unsafe_allow_html=True)
    st.markdown(EV_STYLES, unsafe_allow_html=True)
