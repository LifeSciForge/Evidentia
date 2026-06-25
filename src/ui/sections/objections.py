"""
MSL Tab: Objection Handling section (includes inline Ask Evidentia Q&A chat).

Moved from src/ui/app.py as part of Stage 5 — Architecture Refactor (Part 2).
"""

import streamlit as st
from src.service.qa_service import generate_qa_answer


# Reusable helper: build HTML block for a single objection's expanded content
def _obj_content_html(why="", evidence="", response="",
                      followup_lines=None):
    """Return a single HTML string for the full body of one objection."""
    parts = []

    field_label_style = (
        "font-size:11px;font-weight:700;letter-spacing:.07em;"
        "text-transform:uppercase;color:#999999;margin:0 0 6px 0;"
        "font-family:'Inter','Helvetica Neue',sans-serif;"
    )
    field_value_style = (
        "font-size:13px;color:#333333;line-height:1.7;margin:0 0 20px 0;"
        "font-family:'Inter','Helvetica Neue',sans-serif;"
    )
    divider_style = "border:none;border-top:1px solid #F0F0F0;margin:0 0 20px 0;"
    response_style = (
        "font-size:13px;font-style:italic;color:#555555;line-height:1.7;"
        "background:#F5F5F5;border-radius:3px;padding:12px 16px;margin:0 0 20px 0;"
        "font-family:'Inter','Helvetica Neue',sans-serif;"
    )

    if why:
        parts.append(
            f'<p style="{field_label_style}">Why they ask</p>'
            f'<p style="{field_value_style}">{why}</p>'
            f'<hr style="{divider_style}">'
        )
    if evidence:
        parts.append(
            f'<p style="{field_label_style}">Evidence to use</p>'
            f'<p style="{field_value_style}">{evidence}</p>'
            f'<hr style="{divider_style}">'
        )
    if response:
        parts.append(
            f'<p style="{field_label_style}">How to respond</p>'
            f'<div style="{response_style}">{response}</div>'
            f'<hr style="{divider_style}">'
        )

    lines = followup_lines or [
        "Have supporting trial data ready",
        "Link the evidence to their patient population",
        "Offer to schedule a deeper scientific exchange",
    ]
    li_style = "font-size:13px;color:#555555;line-height:1.7;margin-bottom:6px;"
    li_items = "".join(f'<li style="{li_style}">{ln}</li>' for ln in lines)
    parts.append(
        f'<p style="{field_label_style}">Follow-up points</p>'
        f'<ul style="margin:0;padding-left:20px;">{li_items}</ul>'
    )

    return "".join(parts)


def display_objection_handling_section(state):
    """Professional objection handling + inline Ask Evidentia Q&A."""

    # ── Section A: Anticipated Objections ────────────────────────────────────
    doctor_name = (st.session_state.get("current_doctor") or "").split("(")[0].strip()
    subtitle = (
        f"Based on {doctor_name}'s practice pattern, expect these questions"
        if doctor_name else
        "Anticipated questions based on this drug-indication profile"
    )

    st.markdown(
        '<p style="font-size:28px;font-weight:700;color:#5b5bd6;'
        'letter-spacing:0px;margin:0 0 8px 0;'
        'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
        'Objection Handling Guide</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<p style="font-size:14px;font-weight:400;color:#666666;font-style:italic;'
        f'margin:0 0 32px 0;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
        f'{subtitle}</p>',
        unsafe_allow_html=True
    )

    # Prefer KOL-specific objections from MSL talking points
    tp = getattr(state, "msl_talking_points", None)
    if tp and getattr(tp, "anticipated_objections", None):
        for obj in tp.anticipated_objections:
            prob = getattr(obj, "probability", "")
            label = (obj.objection or "").strip()
            expander_label = f"{label}  ·  {prob}" if prob else label

            with st.expander(expander_label, expanded=False):
                st.markdown(
                    _obj_content_html(
                        why=getattr(obj, "why_they_ask", ""),
                        evidence=getattr(obj, "evidence_response", ""),
                        response=getattr(obj, "msl_response", ""),
                    ),
                    unsafe_allow_html=True
                )

    elif state.messaging_data and state.messaging_data.common_objections:
        for objection, response in list(state.messaging_data.common_objections.items())[:5]:
            with st.expander(objection, expanded=False):
                st.markdown(
                    _obj_content_html(response=response),
                    unsafe_allow_html=True
                )
    else:
        st.markdown(
            '<p style="font-size:13px;color:#999999;font-style:italic;'
            'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
            'No objection data available. Generate a brief with a physician selected '
            'to see KOL-specific objections.</p>',
            unsafe_allow_html=True
        )

    # ── Section B: Ask Evidentia ──────────────────────────────────────────────
    st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
    st.markdown(
        '<hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 32px 0;">',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="font-size:28px;font-weight:700;color:#5b5bd6;'
        'letter-spacing:0px;margin:0 0 8px 0;'
        'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
        'Ask Evidentia</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p style="font-size:14px;font-weight:400;color:#666666;font-style:italic;'
        'margin:0 0 24px 0;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
        'Real-time Q&A for clinical questions not covered above</p>',
        unsafe_allow_html=True
    )

    # Chat history
    chat_history = st.session_state.get("chat_history", [])
    if chat_history:
        for message in chat_history:
            if message["role"] == "user":
                st.markdown(
                    f'<div style="background:#F5F5F5;border-radius:4px;padding:12px 16px;'
                    f'margin-bottom:8px;font-size:13px;color:#5b5bd6;font-weight:600;'
                    f'line-height:1.5;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
                    f'You: {message["content"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div style="background:#E8F1F8;border:1px solid #B3D9E8;border-radius:4px;'
                    f'padding:16px;margin-bottom:20px;font-size:13px;color:#333333;line-height:1.7;'
                    f'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
                    f'{message["content"]}</div>',
                    unsafe_allow_html=True
                )

    with st.form(key="qa_form_merged", clear_on_submit=True):
        drug_label = getattr(state, "drug_name", "this drug") or "this drug"
        user_question = st.text_area(
            "Your question",
            placeholder=f"Ask a clinical question about {drug_label}...",
            height=100,
            label_visibility="collapsed"
        )
        col_btn, col_hint = st.columns([2, 8])
        with col_btn:
            submit = st.form_submit_button("Get Response", type="primary",
                                           use_container_width=True)
        with col_hint:
            st.markdown(
                '<p style="font-size:11px;color:#999999;font-style:italic;padding-top:10px;">'
                'Powered by Evidentia AI</p>',
                unsafe_allow_html=True
            )

    if submit and user_question:
        chat_history = st.session_state.get("chat_history", [])
        chat_history.append({"role": "user", "content": user_question})
        answer = generate_qa_answer(user_question, state)
        chat_history.append({"role": "assistant", "content": answer})
        st.session_state.chat_history = chat_history
        st.rerun()

    if st.session_state.get("chat_history"):
        if st.button("Clear conversation", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()
