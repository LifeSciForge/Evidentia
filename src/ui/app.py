"""
Evidentia - MSL Intelligence Platform
AI-powered pre-call intelligence briefs for Medical Science Liaisons
Refactored from Pharma GTM Simulator to MSL-focused workflow
"""

import streamlit as st
import pandas as pd
#import plotly.graph_objects as go
#import plotly.express as px
from datetime import datetime
import asyncio
import json
from src.agents.gtm_workflow import create_gtm_workflow
from src.core.logger import get_logger
from src.ui.components import metric_card
from src.service.validators.input_validator import InputValidator

logger = get_logger(__name__)

# Initialize session state FIRST (before any page code)
if "workflow_result" not in st.session_state:
    st.session_state.workflow_result = None
if "last_brief_key" not in st.session_state:
    st.session_state.last_brief_key = None
if "workflow_running" not in st.session_state:
    st.session_state.workflow_running = False
if "drug_name" not in st.session_state:
    st.session_state.drug_name = ""
if "indication" not in st.session_state:
    st.session_state.indication = ""
if "current_hospital" not in st.session_state:
    st.session_state.current_hospital = None
if "current_doctor" not in st.session_state:
    st.session_state.current_doctor = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# Page config - Evidentia branding
st.set_page_config(
    page_title="Evidentia - MSL Intelligence",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject global stylesheets (force-full-width + main CSS)
from src.ui.styles import inject_styles
inject_styles()

# Initialize session state
# HOSPITAL DATABASE - REAL US CANCER CENTERS
# ============================================================================

from src.ui.data.hospitals import HOSPITALS


def get_hospital_list():
    """
    Real US cancer center database.
    Data lives in src/ui/data/hospitals.py; in v2 this will query SQLite (SKILL_06).
    """
    return HOSPITALS


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main Evidentia MSL Platform app"""
    
    # Page header — typographic, no emoji
    st.markdown("""
    <div class="ev-page-header">
        <h1 style="font-size: 48px; font-weight: bold; color: #5b5bd6; letter-spacing: 2px; margin: 20px 0;">Evidentia</h1>
        <p class="ev-brand-subtitle">Clinical Pre-Call Intelligence for Medical Science Liaisons</p>
    </div>
    <hr class="ev-divider">
    """, unsafe_allow_html=True)
    
    # ========================================================================
    # SIDEBAR: Hospital & Doctor Selection + Drug Input
    # ========================================================================
    with st.sidebar:
        st.markdown("**MSL Call Planning**")
        st.caption("Evidence-based pre-call preparation for Medical Science Liaisons")
        st.markdown("---")
        st.warning(
            "⚠️ **For MSLs only.**\n\n"
            "This platform is designed for Medical Science Liaisons engaged in "
            "non-promotional scientific exchange.\n\n"
            "Field sales representatives should contact their sales operations team "
            "for rep-specific briefing tools."
        )
        st.markdown("---")
        
        # Hospital Selection
        hospitals = get_hospital_list()
        selected_hospital = st.selectbox(
            "Hospital",
            options=list(hospitals.keys()),
            key="hospital_select"
        )
        
        if selected_hospital:
            st.session_state.current_hospital = selected_hospital
            hospital_info = hospitals[selected_hospital]
            
            # Show hospital location
            st.caption(hospital_info['location'])

            # Doctor Selection
            selected_doctor = st.selectbox(
                "Physician",
                options=hospital_info['doctors'],
                key="doctor_select"
            )
            
            if selected_doctor:
                st.session_state.current_doctor = selected_doctor
                st.success(f"✓ {selected_doctor} selected")
        
        st.markdown("---")
        
        # Drug & Indication Input
        st.markdown("**Drug Information**")
        
        drug_name = st.text_input(
            "Drug Name",
            value="",
            placeholder="e.g., ivonescimab",
            help="Enter the pharmaceutical drug name"
        )
        
        indication = st.text_input(
            "Indication / Therapeutic Area",
            value="",
            placeholder="e.g., Non-Small Cell Lung Cancer",
            help="Medical indication or therapeutic area"
        )
        
        st.markdown("---")
        
        # Generate Intelligence Button
        generate_brief = st.button(
            "Generate MSL Brief",
            use_container_width=True,
            type="primary",
            disabled=not (drug_name and indication and selected_hospital and selected_doctor)
        )
        
        st.markdown("---")
        
        # Info panel — MSL Pre-Call Prep Workflow
        st.markdown("---")
        st.markdown("**MSL Pre-Call Prep Workflow**")
        st.markdown("""
**1️⃣ Physician research**
- Select hospital and KOL
- Review their publication and trial history

**2️⃣ Clinical evidence review**
- Active trials and PubMed literature
- Market landscape and patient population data

**3️⃣ Discovery planning**
- Tiered questions to understand unmet need
- Tailored to the KOL's likely patient population

**4️⃣ Objection preparation**
- Anticipated clinical questions from this KOL
- Evidence-backed, peer-to-peer response guidance

**5️⃣ Competitive context**
- Affirmative positioning vs established agents
- Focus on what the drug uniquely offers patients

**6️⃣ Download brief**
- PDF for offline reference before the call
        """)
    
    # ========================================================================
    # MAIN CONTENT AREA
    # ========================================================================
    
    if generate_brief:
        try:
            drug_name = InputValidator.validate_drug_name(drug_name)
            indication = InputValidator.validate_indication(indication)
        except ValueError as e:
            st.error(f"Please fix your input: {e}")
            st.stop()

        st.session_state.workflow_running = True
        st.session_state.drug_name = drug_name
        st.session_state.indication = indication
        
        # Show call context
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Hospital**\n{st.session_state.current_hospital}")
        with col2:
            st.info(f"**Physician**\n{selected_doctor.split('(')[0].strip()}")
        with col3:
            st.info(f"**Drug**\n{drug_name}")
        
        st.markdown("---")
        
        # Run workflow
        run_workflow(drug_name, indication, selected_hospital, selected_doctor)
    
    # Display results if available and inputs match the stored brief key.
    # This ensures: (a) a rerun/refresh with the same inputs restores the stored
    # brief without re-running agents; (b) changing inputs hides the stale result
    # until the user explicitly clicks Generate.
    workflow_result = st.session_state.get('workflow_result')
    stored_key = st.session_state.get('last_brief_key')
    current_key = (drug_name, indication, selected_hospital, selected_doctor)
    if workflow_result and stored_key == current_key:
        display_msl_results(
            workflow_result,
            st.session_state.get('current_hospital'),
            st.session_state.get('current_doctor')
        )


# ============================================================================
# WORKFLOW EXECUTION
# ============================================================================

def run_workflow(drug_name: str, indication: str, hospital: str, doctor: str):
    """Run the GTM workflow for MSL context"""
    
    progress_container = st.container()
    
    with progress_container:
        st.markdown("**Generating Intelligence Brief**")
        
        status_text = st.empty()
        progress_bar = st.progress(0.0)
        
        try:
            # Create workflow
            workflow = create_gtm_workflow()
            status_text.info("🔄 Starting research agents...")
            
            # Run synchronously
            result = run_workflow_sync(workflow, drug_name, indication, status_text, progress_bar,
                                       doctor=doctor, hospital=hospital)
            
            if result and result.agent_status == "completed":
                st.session_state.workflow_result = result
                st.session_state.last_brief_key = (drug_name, indication, hospital, doctor)
                st.success("✅ Intelligence Brief Ready!")
                st.balloons()
            else:
                st.error("❌ Brief generation failed")
                if result and result.errors:
                    st.error(f"Errors: {result.errors}")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            logger.error(f"Workflow error: {str(e)}")


def run_workflow_sync(workflow, drug_name, indication, status_text, progress_bar,
                      doctor=None, hospital=None):
    """Run workflow synchronously"""
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def make_callback(status_text, progress_bar):
        def callback(agent_name, agents_completed, pct):
            status_text.success(f"✅ {agent_name} complete ({pct}%)")
            progress_bar.progress(pct / 100)
        return callback

    try:
        result = loop.run_until_complete(
            workflow.run(
                drug_name, indication,
                current_doctor=doctor, current_hospital=hospital,
                progress_callback=make_callback(status_text, progress_bar)
            )
        )
        progress_bar.progress(1.0)
        status_text.success("All intelligence agents completed!")
        return result
    finally:
        loop.close()


# ============================================================================
# MSL RESULTS DISPLAY
# ============================================================================

from src.ui.helpers import chip_for, glance_lead_points, _tab_heading, _section_label

# Section modules (Stage 5 Part 2 refactor)
from src.ui.sections.talking_points import display_talking_points_section
from src.ui.sections.objections import display_objection_handling_section
from src.ui.sections.discovery import display_discovery_questions_section
from src.ui.sections.clinical_evidence import display_clinical_evidence_section
from src.ui.sections.competitive import display_competitive_section
from src.ui.sections.final_brief import display_final_brief_section
from src.ui.sections.qa import display_qa_chat_section

# Re-export QA service functions so existing imports from src.ui.app still resolve
from src.service.qa_service import generate_qa_answer, fallback_qa_answer


def display_msl_results(state, hospital, doctor):
    """Display MSL-focused intelligence brief"""

    # Check if we have any actual data
    if not state.market_data and not state.payer_data and not state.competitor_data:
        st.error("❌ No data found for this drug-indication combination")
        st.warning(
            "This could mean:\n"
            "• The drug may not exist in public clinical trial databases\n"
            "• It may be too early-stage (pre-clinical or Phase 1)\n"
            "• The indication may not match trial registrations\n"
            "• Try a different drug name or established competitor"
        )
        return

    # Metadata strip — drug / indication / hospital / doctor / status + Export button
    doctor_display = (doctor or "").split("(")[0].strip() if doctor else "—"
    hospital_display = hospital or "—"
    _meta_col, _export_col = st.columns([4, 1])
    with _meta_col:
        st.markdown(f"""
    <div class="ev-meta-strip">
        <div class="ev-meta-item">
            <span class="ev-meta-label">Drug</span>
            <span class="ev-meta-value">{state.drug_name}</span>
        </div>
        <div class="ev-meta-item">
            <span class="ev-meta-label">Indication</span>
            <span class="ev-meta-value">{state.indication}</span>
        </div>
        <div class="ev-meta-item">
            <span class="ev-meta-label">Hospital</span>
            <span class="ev-meta-value-sm">{hospital_display}</span>
        </div>
        <div class="ev-meta-item">
            <span class="ev-meta-label">Physician</span>
            <span class="ev-meta-value-sm">{doctor_display}</span>
        </div>
        <div class="ev-meta-item">
            <span class="ev-meta-label">Brief</span>
            <span class="ev-status-badge"><span class="ev-status-dot"></span>Ready</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    with _export_col:
        _render_export_buttons(state)

    # ── At a glance band ─────────────────────────────────────────────────────
    lead_point, likely_objection = glance_lead_points(state)
    market_data = getattr(state, "market_data", None)
    _has_glance = market_data is not None or lead_point or likely_objection

    if _has_glance:
        st.markdown(
            '<p style="font-size:11px;font-weight:700;letter-spacing:.08em;'
            'text-transform:uppercase;color:#999999;margin:28px 0 12px 0;'
            'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
            'At a glance</p>',
            unsafe_allow_html=True,
        )

        # Metric cards row — always 3 cards; honest "—" when value absent/zero
        if market_data is not None:
            _metric_cols = st.columns(3)

            _pop = getattr(market_data, "patient_population", None)
            _pop_value = f"{int(_pop):,}" if _pop else "—"
            with _metric_cols[0]:
                metric_card(
                    "Eligible patients",
                    _pop_value,
                    source_html=chip_for(state, "market.patient_population"),
                )

            _trials_count = len(getattr(market_data, "clinical_trials", None) or [])
            _trials_value = str(_trials_count) if _trials_count else "—"
            with _metric_cols[1]:
                metric_card(
                    "Pivotal trials",
                    _trials_value,
                    subtitle="Clinical trials (ClinicalTrials.gov)",
                )

            _pubs_count = len(getattr(market_data, "key_publications", None) or [])
            _pubs_value = str(_pubs_count) if _pubs_count else "—"
            with _metric_cols[2]:
                metric_card(
                    "Key publications",
                    _pubs_value,
                    subtitle="Key publications (PubMed)",
                )

        # Two-box row for lead point + likely objection
        if lead_point or likely_objection:
            _box_parts = []
            if lead_point:
                _box_parts.append(
                    f'<div class="ev-glance-box">'
                    f'<div class="ev-glance-h">Lead talking point</div>'
                    f'<div style="font-size:14px;color:#1a1d29;line-height:1.6;">{lead_point}</div>'
                    f'</div>'
                )
            if likely_objection:
                _box_parts.append(
                    f'<div class="ev-glance-box">'
                    f'<div class="ev-glance-h">Likely objection</div>'
                    f'<div style="font-size:14px;color:#1a1d29;line-height:1.6;">{likely_objection}</div>'
                    f'</div>'
                )
            if _box_parts:
                st.markdown(
                    f'<div style="display:flex;gap:16px;margin-top:16px;">'
                    + "".join(_box_parts)
                    + '</div>',
                    unsafe_allow_html=True,
                )

    # Tab navigation (6 tabs — call flow order)
    tabs = st.tabs([
        "Pre-Call Brief",
        "Talking Points",
        "Objections & Questions",
        "Discovery Questions",
        "Clinical Evidence",
        "Competitive Position",
    ])

    with tabs[0]:
        display_final_brief_section(state)

    with tabs[1]:
        display_talking_points_section(state)

    with tabs[2]:
        display_objection_handling_section(state)

    with tabs[3]:
        display_discovery_questions_section(state)

    with tabs[4]:
        display_clinical_evidence_section(state)

    with tabs[5]:
        display_competitive_section(state)


# ============================================================================
# MSL TAB: REIMBURSEMENT (orphaned — not wired into any tab; kept for reference)
# ============================================================================

def display_reimbursement_section(state):
    """Professional reimbursement and payer intelligence tab."""

    _tab_heading("Reimbursement & Payer Intelligence",
                 "Quick-reference guide for reimbursement conversations with doctors, pharmacies, and payers")

    if not state.payer_data:
        st.warning("No payer data available.")
        return

    # ── Status cards ──────────────────────────────────────────────────────────
    hta = state.payer_data.hta_status or "Under review"
    qaly = f"£{state.payer_data.qaly_threshold:,.0f}" if state.payer_data.qaly_threshold else "£30,000"
    price = f"${state.payer_data.pricing_ceiling:,.0f}" if state.payer_data.pricing_ceiling else "TBD"

    card_s = (
        "background:#F5F5F5;border:1px solid #E0E0E0;border-radius:4px;padding:20px;"
        "font-family:'Inter','Helvetica Neue',sans-serif;"
    )
    lbl_s = "font-size:12px;font-weight:600;color:#666666;text-transform:uppercase;letter-spacing:0.3px;display:block;margin-bottom:8px;"
    val_s = "font-size:20px;font-weight:700;color:#5b5bd6;display:block;margin-bottom:6px;"
    note_s = "font-size:11px;color:#999999;font-style:italic;display:block;line-height:1.4;"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div style="{card_s}"><span style="{lbl_s}">HTA Status</span>'
            f'<span style="{val_s}">{hta}</span>'
            f'<span style="{note_s}">NICE/ICER/EMA appraisal status</span></div>',
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f'<div style="{card_s}"><span style="{lbl_s}">QALY Threshold</span>'
            f'<span style="{val_s}">{qaly}</span>'
            f'<span style="{note_s}">Cost-effectiveness threshold (UK standard)</span></div>',
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f'<div style="{card_s}"><span style="{lbl_s}">Pricing Ceiling</span>'
            f'<span style="{val_s}">{price}</span>'
            f'<span style="{note_s}">Subject to payer negotiations</span></div>',
            unsafe_allow_html=True
        )

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

    # ── Payer conversation playbook ───────────────────────────────────────────
    _section_label("Payer Conversation Playbook")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    drug = getattr(state, "drug_name", "this drug") or "this drug"

    payer_scenarios = [
        {
            "title": 'Scenario 1: "Prove cost-effectiveness"',
            "response": (
                f"Our health economic model shows cost savings vs standard of care when you account for "
                f"reduced combination therapy costs, simplified administration, and improved outcomes in "
                f"PD-L1 negative patients. We are conducting outcomes-based pricing discussions to align payer risk."
            ),
            "evidence": [
                f"QALY threshold: {qaly} (aligns with UK standard)",
                "Efficacy in PD-L1 negative: demonstrated response advantage vs single-agent IO",
                "Single-agent simplicity reduces combination therapy costs",
            ],
        },
        {
            "title": 'Scenario 2: "Formulary placement?"',
            "response": (
                "We are in discussions with major payers for Tier 1/2 placement. Current strategy: "
                "outcomes-based contracts where payers only pay if patients achieve defined clinical milestones."
            ),
            "evidence": [
                "Risk-sharing agreement templates available for review",
                "Real-world data generation planned for 2026",
                "Companion diagnostic bundling options available",
            ],
        },
        {
            "title": 'Scenario 3: "Prior authorisation requirements?"',
            "response": (
                "We are working with payers to minimise PA burden. Current proposal: streamlined PA "
                "for patients with documented PD-L1 negative or IO-resistant disease."
            ),
            "evidence": [
                "Patient access schemes in development",
                "Copay assistance available for eligible patients",
                "Dedicated pharmacy team for pre-authorisation support",
            ],
        },
    ]

    scen_card = (
        "background:#F5F5F5;border:1px solid #E0E0E0;border-radius:4px;padding:20px;margin-bottom:16px;"
        "font-family:'Inter','Helvetica Neue',sans-serif;"
    )
    for s in payer_scenarios:
        li_items = "".join(
            f'<li style="font-size:13px;color:#555555;line-height:1.6;margin-bottom:4px;">{e}</li>'
            for e in s["evidence"]
        )
        st.markdown(
            f'<div style="{scen_card}">'
            f'<p style="font-size:14px;font-weight:600;color:#5b5bd6;margin:0 0 12px 0;">{s["title"]}</p>'
            f'<p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#999;margin:0 0 4px 0;">Your Response</p>'
            f'<p style="font-size:13px;font-style:italic;color:#555555;line-height:1.6;background:#FFFFFF;border-radius:3px;padding:10px 14px;margin:0 0 14px 0;">{s["response"]}</p>'
            f'<hr style="border:none;border-top:1px solid #E0E0E0;margin:0 0 14px 0;">'
            f'<p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#999;margin:0 0 8px 0;">Evidence to Reference</p>'
            f'<ul style="margin:0;padding-left:20px;">{li_items}</ul>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Access barriers ───────────────────────────────────────────────────────
    st.markdown(
        '<hr style="border:none;border-top:1px solid #E8E8E8;margin:0 0 24px 0;">',
        unsafe_allow_html=True
    )
    _section_label("Known Access Barriers & Mitigation")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    raw_restrictions = (state.payer_data.access_restrictions or [])[:5]
    solutions = (state.payer_data.reimbursement_solutions or []) if hasattr(state.payer_data, "reimbursement_solutions") else []

    if raw_restrictions:
        for i, barrier in enumerate(raw_restrictions):
            mitigation = solutions[i] if i < len(solutions) else "Mitigation strategy in development — check with market access team."
            st.markdown(
                f'<div style="background:#FFF8F0;border-left:3px solid #FF9500;border-radius:2px;'
                f'padding:16px;margin-bottom:12px;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
                f'<p style="font-size:13px;font-weight:600;color:#5b5bd6;margin:0 0 8px 0;">{barrier}</p>'
                f'<p style="font-size:12px;color:#555;line-height:1.6;margin:0 0 4px 0;">'
                f'<span style="font-weight:600;color:#FF9500;">Barrier:</span> May delay payer approval or limit patient access</p>'
                f'<p style="font-size:12px;color:#555;line-height:1.6;margin:0;">'
                f'<span style="font-weight:600;color:#00A86B;">Mitigation:</span> {mitigation}</p>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        default_barriers = [
            ("Limited HTA evidence outside primary markets",
             "NICE appraisal ongoing; interim Phase 3 data will strengthen the case."),
            ("No head-to-head comparative effectiveness data",
             "Health economic model based on trial data; outcomes-based pricing available to share payer risk."),
            ("Uncertain long-term survival benefit",
             "Long-term follow-up data being collected; real-world evidence generation ongoing."),
        ]
        for barrier, mitigation in default_barriers:
            st.markdown(
                f'<div style="background:#FFF8F0;border-left:3px solid #FF9500;border-radius:2px;'
                f'padding:16px;margin-bottom:12px;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
                f'<p style="font-size:13px;font-weight:600;color:#5b5bd6;margin:0 0 8px 0;">{barrier}</p>'
                f'<p style="font-size:12px;color:#555;line-height:1.6;margin:0;">'
                f'<span style="font-weight:600;color:#00A86B;">Mitigation:</span> {mitigation}</p>'
                f'</div>',
                unsafe_allow_html=True
            )


# ============================================================================
# EXPORT HELPERS
# ============================================================================

def _render_export_buttons(state):
    """Compact export controls for the results header area.

    Renders a JSON download button and a PDF download button without any
    surrounding prose or section headings, so they sit cleanly inside the
    narrow right-hand column next to the metadata strip.
    Reuses the same export logic as display_download_section.
    """
    from src.service.generators.pdf_generator import generate_brief_pdf

    drug_name = getattr(state, "drug_name", "drug") or "drug"
    doctor = st.session_state.get("current_doctor", "") or ""
    hospital = st.session_state.get("current_hospital", "") or ""
    date_str = datetime.now().strftime("%Y%m%d")

    try:
        json_data = json.dumps(state.__dict__, indent=2, default=str)
        st.download_button(
            label="Export JSON",
            data=json_data,
            file_name=f"evidentia_msl_brief_{drug_name}_{date_str}.json",
            mime="application/json",
            use_container_width=True,
        )
    except Exception:
        pass

    try:
        pdf_bytes = generate_brief_pdf(
            state=state,
            drug_name=drug_name,
            hospital=hospital,
            physician=doctor,
        )
        st.download_button(
            label="Export PDF",
            data=pdf_bytes,
            file_name=f"evidentia_msl_brief_{drug_name}_{date_str}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception:
        pass



# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()