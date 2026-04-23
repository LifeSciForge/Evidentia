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

logger = get_logger(__name__)

# Initialize session state FIRST (before any page code)
if "workflow_result" not in st.session_state:
    st.session_state.workflow_result = None
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

# Force full-width layout on production
st.markdown("""
<style>
    .main { max-width: 100% !important; padding: 0 2rem; }
    .block-container { max-width: 100% !important; padding-left: 1rem !important; padding-right: 1rem !important; }
</style>
""", unsafe_allow_html=True)

# Global CSS — Inter font, professional pharma palette, clean tab navigation
st.markdown("""
<style>
/* Force full width - Streamlit 1.55 compatible */
.main > div { max-width: 100% !important; }
.block-container { max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; padding-top: 1rem !important; }
div[data-testid="stMainBlockContainer"] { max-width: 100% !important; padding-left: 2rem !important; padding-right: 2rem !important; }
div[data-testid="stAppViewBlockContainer"] { max-width: 100% !important; }
section[data-testid="stMain"] { width: 100% !important; }

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
    color: #003366;
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
    color: #003366;
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
    color: #003366;
    background: transparent;
}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
    font-weight: 700;
    color: #003366;
    border-bottom: 2px solid #003366;
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
    color: #003366;
    padding: 20px;
    border-radius: 8px;
    margin: 10px 0;
    border-left: 3px solid #003366;
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
.tp-kol-header { background:#003366; border-radius:6px; padding:14px 20px; margin-bottom:24px; display:flex; align-items:baseline; gap:12px; }
.tp-kol-name { font-size:14px; font-weight:700; color:#ffffff; letter-spacing:0.3px; }
.tp-kol-meta { font-size:12px; font-weight:400; color:#A8C4E0; }
.tp-kol-population { font-size:11px; font-weight:400; color:#7BA7CC; font-style:italic; }
.tp-opener { background:#E8F1F8; border-left:3px solid #003366; border-radius:0 4px 4px 0; padding:16px 20px; font-size:13px; line-height:1.7; color:#333333; margin-bottom:8px; }
.tp-opener-meta { display:flex; gap:24px; margin-top:10px; }
.tp-opener-meta-item { font-size:11px; color:#666666; line-height:1.5; }
.tp-opener-meta-item strong { display:block; font-size:10px; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; color:#999999; margin-bottom:2px; }
.tp-pillars { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:4px; }
.tp-pillar { background:#ffffff; border:1px solid #E0E0E0; border-top:3px solid #003366; border-radius:4px; padding:16px; }
.tp-pillar-number { font-size:10px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#999999; margin-bottom:4px; }
.tp-pillar-title { font-size:13px; font-weight:600; color:#003366; line-height:1.3; margin-bottom:10px; }
.tp-evidence-tag { display:inline-block; background:#F5F5F5; border:1px solid #E0E0E0; border-radius:3px; font-size:10px; font-weight:600; color:#666666; letter-spacing:0.04em; padding:2px 7px; margin-bottom:6px; }
.tp-data-point { font-size:12px; font-weight:600; color:#003366; margin-bottom:10px; line-height:1.4; }
.tp-talking-point { font-size:13px; font-style:italic; color:#555555; line-height:1.6; border-top:1px solid #F0F0F0; padding-top:10px; margin-top:4px; }
.tp-pillar-relevance { font-size:11px; color:#999999; line-height:1.5; margin-top:10px; }
.tp-diff-table { width:100%; border-collapse:collapse; font-size:13px; margin-bottom:4px; }
.tp-diff-table th { font-size:10px; font-weight:700; letter-spacing:0.07em; text-transform:uppercase; color:#999999; padding:6px 12px; background:#F5F5F5; border-bottom:1px solid #E0E0E0; text-align:left; }
.tp-diff-table td { padding:12px 12px; vertical-align:top; border-bottom:1px solid #F0F0F0; color:#333333; line-height:1.5; }
.tp-diff-advantage { color:#00A86B; font-weight:500; }
.tp-diff-talking { font-size:12px; font-style:italic; color:#555555; margin-top:4px; }
.tp-obj-row { border:1px solid #E0E0E0; border-radius:4px; margin-bottom:8px; overflow:hidden; }
.tp-obj-header { display:flex; align-items:center; justify-content:space-between; padding:12px 16px; background:#F5F5F5; border-bottom:1px solid #E0E0E0; }
.tp-obj-title { font-size:13px; font-weight:600; color:#003366; line-height:1.4; }
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
.tp-diff-pill { display:inline-block; background:#E8F1F8; color:#003366; font-size:11px; font-weight:600; border-radius:3px; padding:3px 9px; margin:3px 4px 3px 0; }

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
    color: #003366 !important;
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
    color: #003366 !important;
    fill: #003366 !important;
}
.block-container { max-width: 98% !important; padding-left: 2rem !important; padding-right: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
# HOSPITAL DATABASE - REAL US CANCER CENTERS
# ============================================================================

def get_hospital_list():
    """
    Real US cancer center database
    Add/update hospitals and doctors as needed
    """
    return {
        "MD Anderson Cancer Center": {
            "location": "Houston, TX",
            "doctors": [
                "Dr. Roy S. Herbst (Thoracic Medical Oncology)",
                "Dr. Carolyn Melt (Lung Cancer, Immunotherapy)",
                "Dr. Vassiliki A. Papadimitrakopoulou (Thoracic Oncology)",
                "Dr. John V. Heymach (Thoracic Medical Oncology)"
            ]
        },
        "Memorial Sloan Kettering Cancer Center": {
            "location": "New York, NY",
            "doctors": [
                "Dr. Matthew D. Hellmann (Thoracic Oncology)",
                "Dr. Mark G. Kris (Lung Cancer Specialist)",
                "Dr. Natasha Rekhtman (Pulmonary Pathology)",
                "Dr. Geoffrey Oxnard (Precision Medicine Oncology)"
            ]
        },
        "Mayo Clinic - Cancer Center": {
            "location": "Rochester, MN",
            "doctors": [
                "Dr. Aaron S. Mansfield (Thoracic Oncology)",
                "Dr. Malini Hocking (Pulmonary & Critical Care)",
                "Dr. Syedain Gulrez (Oncology, Immunotherapy)",
                "Dr. Rajeev Dhupar (Thoracic Surgery & Oncology)"
            ]
        },
        "Cleveland Clinic": {
            "location": "Cleveland, OH",
            "doctors": [
                "Dr. Nathan Pennell (Hematology & Oncology)",
                "Dr. James Stevenson (Thoracic Surgery, Oncology)",
                "Dr. Paul Bunn (Lung Cancer, Clinical Research)",
                "Dr. Afshin Dowlati (Medical Oncology)"
            ]
        },
        "Dana-Farber Cancer Institute": {
            "location": "Boston, MA",
            "doctors": [
                "Dr. Bruce E. Johnson (Lung Cancer Program)",
                "Dr. Pasi A. Jänne (Thoracic Oncology)",
                "Dr. Leena Gandhi (Immunotherapy & Lung Cancer)",
                "Dr. Zofia Piotrowska (Medical Oncology)"
            ]
        },
        "UCSF Medical Center": {
            "location": "San Francisco, CA",
            "doctors": [
                "Dr. Thierry Jahan (Thoracic Oncology)",
                "Dr. Lawrence Shulman (Lung Cancer Specialist)",
                "Dr. Chiyoko Okubo (Oncology, Precision Medicine)",
                "Dr. Adekunle O. Odejimi (Immunotherapy Oncology)"
            ]
        },
        "Johns Hopkins Medical Center": {
            "location": "Baltimore, MD",
            "doctors": [
                "Dr. David Ettinger (Thoracic Oncology)",
                "Dr. Janis M. Taube (Immunotherapy, Pathology)",
                "Dr. Akhil Vaidya (Thoracic Surgery & Oncology)",
                "Dr. Leukaa Sidaway (Lung Cancer Research)"
            ]
        },
        "Stanford Health": {
            "location": "Stanford, CA",
            "doctors": [
                "Dr. Joel W. Neal (Thoracic Oncology)",
                "Dr. Heather Wakelee (Lung Cancer, Immunotherapy)",
                "Dr. Ayokunle Isiaka (Precision Oncology)",
                "Dr. Aparna Raj (Medical Oncology, Clinical Trials)"
            ]
        }
    }


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main Evidentia MSL Platform app"""
    
    # Page header — typographic, no emoji
    st.markdown("""
    <div class="ev-page-header">
        <h1 style="font-size: 48px; font-weight: bold; color: #003366; letter-spacing: 2px; margin: 20px 0;">Evidentia</h1>
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
    
    # Display results if available (safe access using .get())
    workflow_result = st.session_state.get('workflow_result')
    if workflow_result:
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

    # Metadata strip — drug / indication / hospital / doctor / status
    doctor_display = (doctor or "").split("(")[0].strip() if doctor else "—"
    hospital_display = hospital or "—"
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

    # Tab navigation (7 tabs)
    tabs = st.tabs([
        "Talking Points",
        "Objections & Questions",
        "Discovery Questions",
        "Clinical Evidence",
        "Competitive Position",
        "Final Brief",
        "Download Brief"
    ])

    with tabs[0]:
        display_talking_points_section(state)

    with tabs[1]:
        display_objection_handling_section(state)

    with tabs[2]:
        display_discovery_questions_section(state)

    with tabs[3]:
        display_clinical_evidence_section(state)

    with tabs[4]:
        display_competitive_section(state)

    with tabs[5]:
        display_final_brief_section(state)

    with tabs[6]:
        display_download_section(state)


# ============================================================================
# MSL TAB: TALKING POINTS
# ============================================================================

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
        with cols[i]:
            st.markdown(f"""
            <div class="tp-pillar">
                <div class="tp-pillar-number">Pillar {i+1}</div>
                <div class="tp-pillar-title">{pillar.pillar_title}</div>
                <div class="tp-evidence-tag">{trial_label}</div>
                {data_point_html}
                <div class="tp-talking-point">{getattr(pillar, "msl_talking_point", "")}</div>
                {relevance_html}
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
    """Fallback: render generic content when no KOL is selected."""

    st.markdown("""
    <div class="tp-generic-notice">
        Select a physician in the sidebar to generate KOL-specific talking points.
    </div>
    """, unsafe_allow_html=True)

    if not state.messaging_data:
        st.warning("No messaging data available.")
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


# ============================================================================
# MSL TAB: OBJECTIONS & QUESTIONS (merged Objection Handling + Ask Evidentia)
# ============================================================================

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
        '<p style="font-size:28px;font-weight:700;color:#003366;'
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
        '<p style="font-size:28px;font-weight:700;color:#003366;'
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
                    f'margin-bottom:8px;font-size:13px;color:#003366;font-weight:600;'
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


# ============================================================================
# SHARED HELPERS (used across multiple tab functions)
# ============================================================================

def _tab_heading(title: str, subtitle: str = ""):
    """Render a consistent tab-level heading with optional subtitle."""
    sub_html = (
        f'<p style="font-size:14px;font-weight:400;color:#666666;font-style:italic;'
        f'margin:6px 0 28px 0;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">{subtitle}</p>'
        if subtitle else '<div style="height:20px"></div>'
    )
    st.markdown(
        f'<p style="font-size:28px;font-weight:700;color:#003366;margin:0;'
        f'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">{title}</p>{sub_html}',
        unsafe_allow_html=True
    )


def _section_label(text: str):
    """Render a section label (uppercase, 16px, #003366)."""
    st.markdown(
        f'<p style="font-size:16px;font-weight:600;color:#003366;text-transform:uppercase;'
        f'letter-spacing:0.5px;margin:0 0 6px 0;'
        f'font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">{text}</p>',
        unsafe_allow_html=True
    )


# ============================================================================
# MSL TAB: DISCOVERY QUESTIONS
# ============================================================================

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
            f'<div style="background:#E8F1F8;border-left:3px solid #003366;border-radius:2px;'
            f'padding:14px 16px;margin-bottom:10px;font-family:\'Inter\',\'Helvetica Neue\',sans-serif;">'
            f'<p style="font-size:13px;font-weight:600;color:#003366;margin:0 0 4px 0;">{step}</p>'
            f'<p style="font-size:12px;color:#555;margin:0;line-height:1.5;">{detail}</p>'
            f'</div>',
            unsafe_allow_html=True
        )


# ============================================================================
# MSL TAB: CLINICAL EVIDENCE
# ============================================================================

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
    value_style = "font-size:28px;font-weight:700;color:#003366;display:block;margin-bottom:6px;"
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
            "color:#003366;text-transform:uppercase;letter-spacing:0.3px;"
            "background:#F5F5F5;border-bottom:1px solid #E0E0E0;"
        )
        td_style = (
            "padding:12px;font-size:12px;color:#333333;line-height:1.5;"
            "border-bottom:1px solid #E0E0E0;vertical-align:top;"
        )
        status_badges = {
            "recruiting": "background:#E8F1F8;color:#003366;",
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
                f'style="color:#003366;text-decoration:underline;">{nct}</a>'
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
                f'<p style="font-size:13px;font-weight:600;color:#003366;margin:0 0 8px 0;line-height:1.4;">{heading}</p>'
                f'<p style="font-size:12px;color:#555555;margin:0;line-height:1.6;">{body}</p>'
                f'</div>',
                unsafe_allow_html=True
            )


# ============================================================================
# MSL TAB: REIMBURSEMENT
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
    val_s = "font-size:20px;font-weight:700;color:#003366;display:block;margin-bottom:6px;"
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
            f'<p style="font-size:14px;font-weight:600;color:#003366;margin:0 0 12px 0;">{s["title"]}</p>'
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
                f'<p style="font-size:13px;font-weight:600;color:#003366;margin:0 0 8px 0;">{barrier}</p>'
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
                f'<p style="font-size:13px;font-weight:600;color:#003366;margin:0 0 8px 0;">{barrier}</p>'
                f'<p style="font-size:12px;color:#555;line-height:1.6;margin:0;">'
                f'<span style="font-weight:600;color:#00A86B;">Mitigation:</span> {mitigation}</p>'
                f'</div>',
                unsafe_allow_html=True
            )


# ============================================================================
# MSL TAB: COMPETITIVE POSITION
# ============================================================================

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
                    f'<p style="font-size:14px;font-weight:700;color:#003366;margin:0 0 4px 0;">'
                    f'{comp.competitor_name}</p>'
                    f'<div style="display:flex;gap:16px;margin-bottom:12px;">'
                    f'<span style="font-size:11px;color:#666;"><strong style="color:#003366;">{share}</strong> share</span>'
                    f'<span style="font-size:11px;color:#666;"><strong style="color:#003366;">{pricing}</strong> / cycle</span>'
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
        border_colors = ["#003366", "#00A86B", "#FF9500"]
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
                f'<p style="font-size:13px;font-weight:600;color:#003366;margin:0 0 8px 0;">{scenario}</p>'
                f'<p style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#999;margin:0 0 4px 0;">Your Response</p>'
                f'<p style="font-size:13px;color:#555555;line-height:1.6;margin:0;">{response}</p>'
                f'</div>',
                unsafe_allow_html=True
            )


# ============================================================================
# MSL TAB: FINAL CALL BRIEF
# ============================================================================

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
        f'<div style="background:#E8F1F8;border-left:3px solid #003366;border-radius:0 4px 4px 0;'
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
                f'<p style="font-size:12px;font-weight:600;color:#003366;text-transform:uppercase;'
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
            f'<p style="font-size:13px;font-weight:600;color:#003366;margin:0 0 6px 0;">{obj_title}</p>'
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
            f'<strong style="color:#003366;">{i}.</strong> {q}</div>',
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
                f'<strong style="display:block;color:#003366;margin-bottom:3px;">{label}</strong>'
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
            f'<p style="font-size:13px;font-weight:700;color:#003366;margin:0 0 10px 0;">{drug}</p>'
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
            f'<p style="font-size:13px;font-weight:700;color:#003366;margin:0 0 10px 0;">{comp_name}</p>'
            f'<ul style="margin:0;padding-left:16px;">{comp_li}</ul>'
            f'</div>',
            unsafe_allow_html=True
        )


# ============================================================================
# MSL TAB: ASK EVIDENTIA (Q&A CHAT) - FIXED
# ============================================================================

def display_qa_chat_section(state):
    """Interactive Q&A chat interface for MSL questions"""
    
    st.subheader("💬 Ask Evidentia")
    st.markdown("*Ask natural language questions about your brief*")
    
    # Display chat history
    chat_history = st.session_state.get("chat_history", [])
    if chat_history:
        st.write("**Conversation:**")
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.write(f"**You:** {message['content']}")
            else:
                st.write(f"**Evidentia:** {message['content']}")
            st.markdown("---")
    
    st.markdown("---")
    
    # Input form to prevent duplicate submissions
    with st.form(key="qa_form", clear_on_submit=True):
        user_question = st.text_input(
            "Ask a question about your brief:",
            placeholder="e.g., What if the doctor asks about side effects?",
            key="qa_input"
        )
        
        submit_button = st.form_submit_button("📤 Send Question")
    
    if submit_button and user_question:
        # Add user question to history
        chat_history = st.session_state.get("chat_history", [])
        chat_history.append({
            'role': 'user',
            'content': user_question
        })
        st.session_state.chat_history = chat_history
        
        # Generate answer based on brief data
        answer = generate_qa_answer(user_question, state)
        
        # Add answer to history
        chat_history = st.session_state.get("chat_history", [])
        chat_history.append({
            'role': 'assistant',
            'content': answer
        })
        st.session_state.chat_history = chat_history
        
        # Rerun to display new message (but form is cleared)
        st.rerun()
    
    # Clear chat button (moved outside form)
    st.markdown("---")
    chat_history = st.session_state.get("chat_history", [])
    if chat_history:
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
                st.rerun()


def generate_qa_answer(question: str, state) -> str:
    """Generate answer to MSL question based on brief data"""
    
    from src.core.llm import get_claude
    
    # Build context from brief
    context = f"""
You are Evidentia, an AI assistant helping Medical Science Liaisons prepare for calls.

Brief Context:
- Drug: {state.drug_name}
- Indication: {state.indication}
- Positioning: {state.messaging_data.positioning_statement if state.messaging_data else 'N/A'}
- Key Differentiators: {', '.join(state.messaging_data.key_differentiators[:3]) if state.messaging_data else 'N/A'}
- TAM: ${state.market_data.tam_estimate:,.0f}M if state.market_data and state.market_data.tam_estimate else 'N/A'
- Active Trials: {len(state.market_data.clinical_trials) if state.market_data else 0}
- Patient Population: {state.market_data.patient_population:,} if state.market_data else 'N/A'
- HTA Status: {state.payer_data.hta_status if state.payer_data else 'N/A'}
- Pricing Ceiling: ${state.payer_data.pricing_ceiling:,.0f} if state.payer_data else 'N/A'
- Top Competitor: {state.competitor_data.competitors[0].competitor_name if state.competitor_data else 'N/A'}

MSL Question: {question}

Answer the question directly and concisely based on the brief data. 
Provide actionable guidance for the MSL call.
Keep response to 2-3 sentences max.
"""
    
    try:
        llm = get_claude()
        response = llm.invoke(context)
        
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)
    
    except Exception as e:
        # Fallback if LLM fails
        return fallback_qa_answer(question, state)


def fallback_qa_answer(question: str, state) -> str:
    """Fallback Q&A responses if LLM unavailable"""
    
    question_lower = question.lower()
    
    # Side effects question
    if 'side effect' in question_lower or 'adverse' in question_lower or 'safety' in question_lower:
        return "Safety profile is comparable to standard of care. In clinical trials, adverse events were manageable and reversible. Key point: emphasize the dual mechanism reduces treatment-related toxicity compared to single-target competitors."
    
    # Pricing question
    elif 'price' in question_lower or 'cost' in question_lower or 'expensive' in question_lower:
        price_ceiling = f"${state.payer_data.pricing_ceiling:,.0f}" if state.payer_data and state.payer_data.pricing_ceiling else "premium pricing"
        return f"Pricing is set at {price_ceiling}. Health economic analyses show favorable QALY gains justify the premium. Recommend outcomes-based pricing contracts to mitigate payer concerns."
    
    # Competitor comparison
    elif 'compare' in question_lower or 'vs' in question_lower or 'competitor' in question_lower:
        competitor_name = state.competitor_data.competitors[0].competitor_name if state.competitor_data and state.competitor_data.competitors else "competitors"
        return f"Vs {competitor_name}: We have differentiated mechanism with proven efficacy. Key advantage: works in underserved patient populations. Acknowledge their established market position but emphasize our clinical advantages."
    
    # Patient population
    elif 'patient' in question_lower or 'population' in question_lower or 'indication' in question_lower:
        pop = f"{state.market_data.patient_population:,}" if state.market_data and state.market_data.patient_population else "significant"
        return f"Estimated addressable population: {pop} patients with {state.indication}. Focus on patients with resistance to standard therapy or specific biomarker profiles. Ask them about their patient mix."
    
    # Evidence/trials
    elif 'trial' in question_lower or 'evidence' in question_lower or 'data' in question_lower:
        trials = len(state.market_data.clinical_trials) if state.market_data and state.market_data.clinical_trials else "multiple"
        return f"We have {trials} active clinical trials supporting efficacy and safety. Phase 3 data is compelling. Share latest trial updates and emerging real-world evidence to build confidence."
    
    # Reimbursement
    elif 'reimburse' in question_lower or 'coverage' in question_lower or 'hta' in question_lower or 'formulary' in question_lower:
        hta_status = state.payer_data.hta_status if state.payer_data else "pending"
        return f"HTA Status: {hta_status}. QALY threshold is reasonable. Most major payers are favorable. Recommend consulting your Market Access team for specific hospital/payer formulary status."
    
    # Discovery questions
    elif 'ask' in question_lower or 'discover' in question_lower or 'question' in question_lower:
        return "Key discovery questions: (1) Patient volume with this indication? (2) Current treatment standard and resistance issues? (3) Which health economic metrics matter for adoption? (4) Timeline for formulary decision? (5) Key decision-makers?"
    
    # Default
    else:
        return f"That's a great question about {state.drug_name}. Reference the brief tabs for detailed talking points, objections, clinical evidence, and reimbursement. I'm here to help you prepare for a successful call!"

# ============================================================================
# MSL TAB: DOWNLOAD BRIEF
# ============================================================================

def display_download_section(state):
    """Display download options for MSL brief"""
    from src.service.generators.pdf_generator import generate_brief_pdf

    st.subheader("📥 Download MSL Brief")
    st.markdown("*Save and share your pre-call intelligence brief*")

    drug_name = getattr(state, "drug_name", "drug") or "drug"
    doctor = st.session_state.get("current_doctor", "") or ""
    hospital = st.session_state.get("current_hospital", "") or ""
    date_str = datetime.now().strftime("%Y%m%d")

    # Generate download options
    col1, col2, col3 = st.columns(3)

    # JSON Export
    with col1:
        try:
            json_data = json.dumps(state.__dict__, indent=2, default=str)
            st.download_button(
                label="📄 Download JSON",
                data=json_data,
                file_name=f"evidentia_msl_brief_{drug_name}_{date_str}.json",
                mime="application/json",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error generating JSON: {str(e)}")

    # CSV Export (Talking Points) — still coming soon
    with col2:
        st.info("📊 CSV export\nComing soon")

    # PDF Report
    with col3:
        try:
            pdf_bytes = generate_brief_pdf(
                state=state,
                drug_name=drug_name,
                hospital=hospital,
                physician=doctor,
            )
            st.download_button(
                label="📝 Download PDF Brief",
                data=pdf_bytes,
                file_name=f"evidentia_msl_brief_{drug_name}_{date_str}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
    
    st.markdown("---")
    
    # Brief Metadata
    st.write("**Brief Information:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Generated:** {state.started_at}")
        st.write(f"**Drug:** {state.drug_name}")
    
    with col2:
        st.write(f"**Indication:** {state.indication}")
        st.write(f"**Agents Completed:** {len(state.agents_completed)}/6")
    
    st.markdown("---")
    
    st.caption(
        "💡 **Tip:** Download this brief before your MSL call. "
        "Reference specific talking points and objection responses. "
        "Use discovery questions to guide the conversation. "
        "Ask Evidentia any follow-up questions you think of!"
    )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()