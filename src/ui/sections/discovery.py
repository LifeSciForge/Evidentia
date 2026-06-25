"""
MSL Tab: Discovery Questions section.

Moved from src/ui/app.py as part of Stage 5 — Architecture Refactor (Part 2).
"""

import streamlit as st
from src.ui.helpers import _tab_heading, _section_label


def display_discovery_questions_section(state):
    """Tiered discovery questions with follow-up guidance."""

    drug = getattr(state, "drug_name", "this drug") or "this drug"
    doctor_name = (st.session_state.get("current_doctor") or "").split("(")[0].strip()

    _tab_heading("Discovery Questions",
                 f"Prioritized questions to understand{' ' + doctor_name + chr(39) + 's' if doctor_name else ' the doctor'}"
                 f"s practice and fit for {drug}")

    # ── Tier 1 ────────────────────────────────────────────────────────────────
    _section_label("Tier 1 — Must Ask  (every call)")
    st.markdown(
        '<p style="font-size:12px;color:#666;font-style:italic;margin:0 0 16px 0;">These establish fit and unmet need. Ask early.</p>',
        unsafe_allow_html=True
    )

    tier1 = [
        {
            "q": f'How many of your {state.indication if getattr(state, "indication", None) else "target"} patients'
                 ' have PD-L1 negative tumors or have developed resistance to standard IO?',
            "why": "Determines addressable patient population",
            "listen": "If >20% of caseload, they have unmet need",
            "followups": [
                '"Most are PD-L1 positive" → Pivot to resistance cases',
                '"We don\'t test PD-L1" → Highlight biomarker-independent activity',
                '"IO resistance is common" → This is your opening',
            ],
        },
        {
            "q": "What is your current treatment approach for patients who have failed checkpoint inhibitors?",
            "why": "Understand current standard of care for resistant disease",
            "listen": "Chemotherapy? Combination approaches? Clinical trials?",
            "followups": [
                '"Back to chemotherapy" → Emphasise avoiding chemo toxicity',
                '"We try combinations" → Highlight single-agent simplicity',
                '"We refer to trials" → Position as alternative option',
            ],
        },
        {
            "q": "What clinical outcomes matter most to your decisions — response rate, PFS, or overall survival?",
            "why": "Understand which data points resonate with them",
            "listen": "Which metrics drive prescribing decisions",
            "followups": [
                '"Response rate" → Lead with ORR data',
                '"PFS" → Highlight duration of response in Phase 2',
                '"OS" → Acknowledge Phase 3 ongoing, interim expected Q3 2026',
            ],
        },
    ]
    for item in tier1:
        with st.expander(item["q"], expanded=False):
            li = "".join(f'<li style="margin-bottom:4px;font-size:12px;color:#555;">{f}</li>' for f in item["followups"])
            st.markdown(f"""
            <div style="font-family:'Inter','Helvetica Neue',sans-serif;">
              <p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#999;margin:0 0 4px 0;">Why Ask</p>
              <p style="font-size:13px;color:#333;line-height:1.6;margin:0 0 14px 0;">{item['why']}</p>
              <hr style="border:none;border-top:1px solid #F0F0F0;margin:0 0 14px 0;">
              <p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#999;margin:0 0 4px 0;">Listen For</p>
              <p style="font-size:13px;color:#333;line-height:1.6;margin:0 0 14px 0;">{item['listen']}</p>
              <hr style="border:none;border-top:1px solid #F0F0F0;margin:0 0 14px 0;">
              <p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#999;margin:0 0 8px 0;">Follow-up If They Say...</p>
              <ul style="margin:0;padding-left:20px;">{li}</ul>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Tier 2 ────────────────────────────────────────────────────────────────
    _section_label("Tier 2 — Context-Dependent  (ask if relevant)")
    st.markdown(
        '<p style="font-size:12px;color:#666;font-style:italic;margin:0 0 16px 0;">Ask only if the conversation naturally leads there.</p>',
        unsafe_allow_html=True
    )

    tier2 = [
        {
            "q": "How does your P&T committee typically evaluate new oncology therapies? What's the review timeline?",
            "when": "When they mention formulary decisions or payer gatekeeping",
            "followup": "Happy to work with your P&T — we have health economic data and outcomes-based pricing models available.",
        },
        {
            "q": f"Are there specific data or evidence you would want to see before considering {drug} for your patients?",
            "when": "Near end of call, if they seem interested but hesitant",
            "followup": "Phase 3 interim data coming Q3 2026. I will send you the latest publications.",
        },
    ]
    for item in tier2:
        with st.expander(item["q"], expanded=False):
            st.markdown(f"""
            <div style="font-family:'Inter','Helvetica Neue',sans-serif;">
              <p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#999;margin:0 0 4px 0;">When to Ask</p>
              <p style="font-size:13px;color:#333;line-height:1.6;margin:0 0 14px 0;">{item['when']}</p>
              <hr style="border:none;border-top:1px solid #F0F0F0;margin:0 0 14px 0;">
              <p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#999;margin:0 0 4px 0;">Suggested Follow-up</p>
              <p style="font-size:13px;font-style:italic;color:#555;line-height:1.6;background:#F5F5F5;border-radius:3px;padding:10px 14px;margin:0;">{item['followup']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Tier 3 ────────────────────────────────────────────────────────────────
    _section_label("Tier 3 — Nice to Have  (skip if time limited)")
    st.markdown(
        '<p style="font-size:12px;color:#666;font-style:italic;margin:0 0 16px 0;">Ask only if you have extra time and conversation is flowing well.</p>',
        unsafe_allow_html=True
    )

    tier3 = [
        ("Are there clinical champions or opinion leaders at your hospital who drive treatment decisions?",
         "Identify other stakeholders to engage"),
        ("What conferences or educational events would be valuable for your team?",
         "Useful for future engagement planning; low priority on first call"),
    ]
    for q, note in tier3:
        with st.expander(q, expanded=False):
            st.markdown(
                f'<p style="font-size:13px;color:#666;line-height:1.6;font-style:italic;">{note}</p>',
                unsafe_allow_html=True
            )

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Conversation flow ─────────────────────────────────────────────────────
    _section_label("Recommended Conversation Flow")
    flow = [
        ("Opening  ·  2 min", "Relationship building. Learn about practice size, focus area, recent work."),
        ("Tier 1 Q1  ·  2 min", "How many patients have PD-L1 negative tumors or IO resistance?"),
        ("Tier 1 Q2  ·  2 min", "What is the current approach for patients who failed checkpoint inhibitors?"),
        ("Pivot to Talking Points  ·  2 min", f"Share {drug} positioning based on their unmet need answers."),
        ("Tier 1 Q3  ·  1 min", "What clinical outcomes matter most to their decisions?"),
        ("Close  ·  1 min", "Offer next steps: share publications, data, schedule follow-up."),
    ]
    for step, detail in flow:
        st.markdown(
            f'<div style="background:#E8F1F8;border-left:3px solid #5b5bd6;border-radius:2px;'
            f'padding:14px 16px;margin-bottom:10px;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
            f'<p style="font-size:13px;font-weight:600;color:#5b5bd6;margin:0 0 4px 0;">{step}</p>'
            f'<p style="font-size:12px;color:#555;margin:0;line-height:1.5;">{detail}</p>'
            f'</div>',
            unsafe_allow_html=True
        )
