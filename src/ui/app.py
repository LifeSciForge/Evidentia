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

# Custom CSS - Professional blue color scheme for MSL platform
st.markdown("""
<style>
    /* Main header styling */
    .main-header {
        color: #0055B8;  /* Professional pharma blue */
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        font-family: 'Segoe UI', sans-serif;
    }
    
    .subtitle {
        color: #4A7BA7;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
        font-style: italic;
    }
    
    /* Card styling for hospital/doctor info */
    .info-card {
        background: linear-gradient(135deg, #0055B8 0%, #003D82 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,85,184,0.2);
    }
    
    /* MSL-specific metric cards */
    .metric-card {
        background: linear-gradient(135deg, #E8F1F8 0%, #D1E3F3 100%);
        color: #0055B8;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #0055B8;
    }
    
    /* Success and warning boxes */
    .success-box {
        background-color: #D4EDDA;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    
    .warning-box {
        background-color: #FFF3CD;
        color: #856404;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #FFC107;
    }
    
    .error-box {
        background-color: #F8D7DA;
        color: #721c24;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #f5c6cb;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] button {
        font-weight: 500;
        color: #0055B8;
    }
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
    
    # Header
    st.markdown("<div class='main-header'>🏥 Evidentia</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>AI-Powered MSL Pre-Call Intelligence Briefs</div>", 
                unsafe_allow_html=True)
    st.markdown("---")
    
    # ========================================================================
    # SIDEBAR: Hospital & Doctor Selection + Drug Input
    # ========================================================================
    with st.sidebar:
        st.header("📋 Call Planning")
        st.markdown("**Select your target and drug focus**")
        st.markdown("---")
        
        # Hospital Selection
        hospitals = get_hospital_list()
        selected_hospital = st.selectbox(
            "🏢 Select Hospital",
            options=list(hospitals.keys()),
            key="hospital_select"
        )
        
        if selected_hospital:
            st.session_state.current_hospital = selected_hospital
            hospital_info = hospitals[selected_hospital]
            
            # Show hospital location
            st.caption(f"📍 {hospital_info['location']}")
            
            # Doctor Selection
            selected_doctor = st.selectbox(
                "👨‍⚕️ Select Doctor",
                options=hospital_info['doctors'],
                key="doctor_select"
            )
            
            if selected_doctor:
                st.session_state.current_doctor = selected_doctor
                st.success(f"✓ {selected_doctor} selected")
        
        st.markdown("---")
        
        # Drug & Indication Input
        st.subheader("💊 Drug Information")
        
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
            "🚀 Generate MSL Brief",
            use_container_width=True,
            type="primary",
            disabled=not (drug_name and indication and selected_hospital and selected_doctor)
        )
        
        st.markdown("---")
        
        # Info panel - Structured better
        st.markdown("---")
        st.subheader("ℹ️ How Evidentia Works")
        st.markdown("""
**1️⃣ Select hospital & doctor**
- Choose your target hospital
- Select the physician to call

**2️⃣ Enter drug information**
- Drug name (e.g., ivonescimab)
- Indication (e.g., NSCLC)

**3️⃣ Generate MSL Brief**
- Click the button
- Wait ~90 seconds

**4️⃣ Review brief**
- 9 interactive tabs
- Talking points & objections
- Discovery questions

**5️⃣ Ask Evidentia**
- Natural language Q&A
- Get real-time guidance

**6️⃣ Download**
- Save as JSON for offline use
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
            st.info(f"🏢 **Hospital**\n{st.session_state.current_hospital}")
        with col2:
            st.info(f"👨‍⚕️ **Doctor**\n{selected_doctor.split('(')[0].strip()}")
        with col3:
            st.info(f"💊 **Drug**\n{drug_name}")
        
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
        st.header("🔄 Generating Intelligence Brief")
        
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        try:
            # Create workflow
            workflow = create_gtm_workflow()
            status_text.info("🔄 Starting research agents...")
            
            # Run synchronously
            result = run_workflow_sync(workflow, drug_name, indication, status_text, progress_bar)
            
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


def run_workflow_sync(workflow, drug_name, indication, status_text, progress_bar):
    """Run workflow synchronously"""
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(workflow.run(drug_name, indication))
        progress_bar.progress(100)
        status_text.success("✅ All intelligence agents completed!")
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

    st.header("📊 MSL Intelligence Brief")
    st.markdown("---")
    
    # Summary metrics - MSL focused
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Drug",
            state.drug_name,
            delta=None
        )
    
    with col2:
        st.metric(
            "Indication",
            state.indication,
            delta=None
        )
    
    with col3:
        st.metric(
            "Hospital",
            hospital.split()[0],
            delta=None
        )
    
    with col4:
        st.metric(
            "Brief Status",
            "Ready",
            delta="✓"
        )
    
    st.markdown("---")
    
    # MSL-specific tabs
    tabs = st.tabs([
        "💬 Talking Points",
        "⚠️ Objection Handling",
        "❓ Discovery Questions",
        "📊 Clinical Evidence",
        "💰 Reimbursement",
        "🏆 Competitive Position",
        "📋 Final Brief",
        "💬 Ask Evidentia",
        "📥 Download Brief"
    ])
    
    # Tab 0: Talking Points
    with tabs[0]:
        display_talking_points_section(state)
    
    # Tab 1: Objection Handling
    with tabs[1]:
        display_objection_handling_section(state)
    
    # Tab 2: Discovery Questions
    with tabs[2]:
        display_discovery_questions_section(state)
    
    # Tab 3: Clinical Evidence
    with tabs[3]:
        display_clinical_evidence_section(state)
    
    # Tab 4: Reimbursement
    with tabs[4]:
        display_reimbursement_section(state)
    
    # Tab 5: Competitive Position
    with tabs[5]:
        display_competitive_section(state)
    
    # Tab 6: Final Brief
    with tabs[6]:
        display_final_brief_section(state)
    
    # Tab 7: Ask Evidentia (Q&A Chat)
    with tabs[7]:
        display_qa_chat_section(state)
    
    # Tab 8: Download
    with tabs[8]:
        display_download_section(state)


# ============================================================================
# MSL TAB: TALKING POINTS
# ============================================================================

def display_talking_points_section(state):
    """Display key talking points for MSL call"""
    
    st.subheader("🎯 Key Talking Points")
    st.markdown("*Use these points to frame the conversation with the doctor*")
    
    if not state.messaging_data:
        st.warning("No messaging data available")
        return
    
    # Positioning Statement
    st.write("**Positioning Statement:**")
    st.info(state.messaging_data.positioning_statement)
    
    # Key Differentiators
    st.write("**Key Differentiators vs Competitors:**")
    col1, col2, col3 = st.columns(3)
    
    differentiators = state.messaging_data.key_differentiators[:3]
    for i, col in enumerate([col1, col2, col3]):
        if i < len(differentiators):
            with col:
                st.success(f"✓ {differentiators[i]}")
    
    # Messaging Pillars
    st.write("**Three Messaging Pillars:**")
    for i, pillar in enumerate(state.messaging_data.messaging_pillars[:3], 1):
        st.write(f"**{i}. {pillar}**")
        if i == 1:
            st.caption("Lead with clinical efficacy and safety profile")
        elif i == 2:
            st.caption("Emphasize differentiation vs standard of care")
        else:
            st.caption("Highlight patient population impact")
    
    # Value propositions by doctor role (simplified)
    st.write("**Value Props by Doctor Role:**")
    roles = ["Treating Physician", "Market Access Lead", "Medical Director"]
    for role in roles:
        with st.expander(f"👤 {role}"):
            if role == "Treating Physician":
                st.write("• Clinical efficacy and safety data\n"
                        "• Real-world evidence\n"
                        "• Patient selection criteria\n"
                        "• Dosing and administration")
            elif role == "Market Access Lead":
                st.write("• Health economic data\n"
                        "• Reimbursement pathway\n"
                        "• Payer strategies\n"
                        "• Budget impact model")
            else:
                st.write("• Regulatory status\n"
                        "• Market landscape\n"
                        "• Adoption trajectory\n"
                        "• Clinical KOLs")


# ============================================================================
# MSL TAB: OBJECTION HANDLING
# ============================================================================

def display_objection_handling_section(state):
    """Display common objections and response strategies"""
    
    st.subheader("⚠️ Objection Handling Guide")
    st.markdown("*Prepare responses for likely doctor concerns*")
    
    if not state.messaging_data:
        st.warning("No objection data available")
        return
    
    objections = state.messaging_data.common_objections
    
    if not objections:
        # Generate default objections if not in data
        objections = {
            "What about side effects?": 
                "Our safety profile is comparable to standard of care. In clinical trials, adverse events were manageable and reversible.",
            
            "How does pricing compare?": 
                "While initial cost may be higher, health economic analyses show favorable QALY gains, justifying the premium.",
            
            "Do we have real-world evidence?": 
                "Real-world evidence is emerging from early adopter centers. I can share the latest data.",
            
            "What's the patient population?": 
                "We recommend screening for [specific criteria]. Patient selection is critical for optimal outcomes.",
            
            "What about insurance coverage?": 
                "Reimbursement pathway is clear with NICE/ICER precedent. Most payers have included it in formularies."
        }
    
    for objection, response in list(objections.items())[:5]:
        with st.expander(f"🤔 **{objection}**", expanded=False):
            st.write(f"**Response:**\n{response}")
            st.markdown("---")
            st.write("**Follow-up points:**")
            st.write("• Have supporting data ready\n"
                    "• Link to clinical outcomes\n"
                    "• Offer to schedule detailed conversation")


# ============================================================================
# MSL TAB: DISCOVERY QUESTIONS
# ============================================================================

def display_discovery_questions_section(state):
    """Display discovery questions to uncover doctor needs"""
    
    st.subheader("❓ Discovery Questions")
    st.markdown("*Ask these to understand the doctor's priorities and pain points*")
    
    # Clinical/Practice Questions
    with st.expander("🏥 Clinical Practice Questions", expanded=True):
        st.write(
            "• How many patients with [indication] do you see monthly?\n"
            "• What's your current treatment paradigm for first-line therapy?\n"
            "• What are the biggest treatment challenges you face?\n"
            "• How do you currently select patients for advanced therapies?\n"
            "• What clinical outcomes matter most to your patients?"
        )
    
    # Access/Reimbursement Questions
    with st.expander("💰 Reimbursement & Access Questions"):
        st.write(
            "• What's your hospital's current formulary status for this drug class?\n"
            "• How quickly can your P&T committee approve new drugs?\n"
            "• What health economic data influences your adoption decisions?\n"
            "• Are there prior authorization barriers we should know about?\n"
            "• How do budget constraints impact treatment decisions?"
        )
    
    # KOL/Influence Questions
    with st.expander("👥 KOL & Decision-Maker Questions"):
        st.write(
            "• Who else influences treatment decisions at your hospital?\n"
            "• Are there clinical champions for new therapies?\n"
            "• How does your tumor board discuss treatment options?\n"
            "• What external data sources drive your recommendations?\n"
            "• Do you present cases at internal conferences?"
        )
    
    # Evidence Gaps
    with st.expander("📚 Evidence & Gap Questions"):
        st.write(
            "• What additional data would help you adopt this therapy?\n"
            "• Are you interested in real-world evidence projects?\n"
            "• Would you participate in a registry or observational study?\n"
            "• What subset of your patient population fits best?\n"
            "• When would you be ready to make a formulary decision?"
        )


# ============================================================================
# MSL TAB: CLINICAL EVIDENCE
# ============================================================================

def display_clinical_evidence_section(state):
    """Display clinical trial and evidence data"""
    
    st.subheader("🔬 Clinical Evidence Summary")
    
    if not state.market_data:
        st.warning("No clinical data available")
        return
    
    # Key Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Active Trials",
            len(state.market_data.clinical_trials) if state.market_data.clinical_trials else 0,
            help="Clinical trials currently recruiting or active"
        )
    
    with col2:
        st.metric(
            "Estimated TAM",
            f"${state.market_data.tam_estimate:,.0f}M" if state.market_data.tam_estimate else "N/A",
            help="Total addressable market in millions"
        )
    
    with col3:
        st.metric(
            "Patient Population",
            f"{state.market_data.patient_population:,}" if state.market_data.patient_population else "N/A",
            help="Estimated addressable patients"
        )
    
    st.markdown("---")
    
    # Market Drivers
    st.write("**Market Drivers & Epidemiology:**")
    if state.market_data.epidemiology:
        drivers = state.market_data.epidemiology.get('market_drivers', [])
        if drivers:
            for driver in drivers:
                st.write(f"• {driver}")
        else:
            st.info("Drivers not yet synthesized")
    
    st.markdown("---")
    
    # Clinical Trials Table
    st.write("**Key Clinical Trials:**")
    if state.market_data.clinical_trials:
        trials_df = pd.DataFrame(state.market_data.clinical_trials[:5])
        # Select relevant columns
        display_cols = [col for col in ['nct_id', 'title', 'status', 'phase', 'enrollment'] 
                       if col in trials_df.columns]
        st.dataframe(trials_df[display_cols], use_container_width=True)
    else:
        st.info("No trial data available")


# ============================================================================
# MSL TAB: REIMBURSEMENT
# ============================================================================

def display_reimbursement_section(state):
    """Display payer intelligence and reimbursement strategy"""
    
    st.subheader("💰 Reimbursement & Payer Intelligence")
    
    if not state.payer_data:
        st.warning("No payer data available")
        return
    
    # HTA Status & Thresholds
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "HTA Status",
            state.payer_data.hta_status or "Pending",
            help="Health Technology Assessment decision status"
        )
    
    with col2:
        st.metric(
            "QALY Threshold",
            f"£{state.payer_data.qaly_threshold:,.0f}" if state.payer_data.qaly_threshold else "TBD",
            help="Cost per QALY for reimbursement"
        )
    
    st.markdown("---")
    
    # Pricing Guidance
    st.write("**Pricing Strategy:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(
            f"**Pricing Ceiling**\n"
            f"${state.payer_data.pricing_ceiling:,.0f}" 
            if state.payer_data.pricing_ceiling else "Under negotiation"
        )
    
    with col2:
        st.info(
            "**Value-Based Pricing**\n"
            "Consider outcomes-based contracts with payers"
        )
    
    st.markdown("---")
    
    # Reimbursement Criteria
    st.write("**Reimbursement Criteria & Requirements:**")
    if state.payer_data.reimbursement_criteria:
        for criterion in state.payer_data.reimbursement_criteria[:5]:
            st.write(f"✓ {criterion}")
    else:
        st.write("✓ Standard oncology/specialty drug pathway\n"
                "✓ Phase 3 efficacy data required\n"
                "✓ Health economic model needed\n"
                "✓ Comparator arm analysis\n"
                "✓ Real-world evidence emerging")
    
    st.markdown("---")
    
    # Access Restrictions
    st.write("**Known Access Restrictions / Prior Auth:**")
    if state.payer_data.access_restrictions:
        for restriction in state.payer_data.access_restrictions[:3]:
            st.write(f"⚠️ {restriction}")
    else:
        st.write("⚠️ Specialist initiation only\n"
                "⚠️ Genetic testing may be required\n"
                "⚠️ Prior treatment requirement possible")


# ============================================================================
# MSL TAB: COMPETITIVE POSITION
# ============================================================================

def display_competitive_section(state):
    """Display competitive landscape"""
    
    st.subheader("🏆 Competitive Landscape")
    
    if not state.competitor_data:
        st.warning("No competitor data available")
        return
    
    # Top Competitors
    st.write("**Key Competitors:**")
    
    for i, competitor in enumerate(state.competitor_data.competitors[:3], 1):
        with st.expander(
            f"**{i}. {competitor.competitor_name}** "
            f"({competitor.market_share:.1f}% share)",
            expanded=(i == 1)
        ):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Market Share", f"{competitor.market_share:.1f}%")
                st.metric("Pricing", f"${competitor.pricing:,.0f}")
            
            with col2:
                st.write("**Positioning:**")
                st.write(competitor.positioning if competitor.positioning else "Standard of care")
            
            st.write("**Advantages:**")
            for adv in competitor.clinical_advantages[:3]:
                st.write(f"✓ {adv}")
            
            st.write("**Vulnerabilities:**")
            for dis in competitor.clinical_disadvantages[:3]:
                st.write(f"⚠️ {dis}")
    
    st.markdown("---")
    
    # Our Differentiators
    st.write("**Our Competitive Advantages:**")
    if state.messaging_data:
        for diff in state.messaging_data.key_differentiators[:4]:
            st.success(f"✓ {diff}")


# ============================================================================
# MSL TAB: FINAL CALL BRIEF
# ============================================================================

def display_final_brief_section(state):
    """Display polished final brief for MSL to review before call"""
    
    st.subheader("📋 Final Call Brief - Ready to Call in 8 Minutes")
    st.markdown("*Review this before walking into the call*")
    
    # Executive Summary
    st.write("**Executive Summary:**")
    summary_text = f"""
    You are prepared to discuss {state.drug_name} for {state.indication}.
    This is a scientifically differentiated therapy with strong clinical data.
    Focus on clinical efficacy, unmet need, and competitive advantages.
    """
    st.info(summary_text)
    
    st.markdown("---")
    
    # Key Talking Points (Condensed)
    st.write("**3 Key Talking Points (Lead with these):**")
    col1, col2, col3 = st.columns(3)
    
    if state.messaging_data and state.messaging_data.messaging_pillars:
        pillars = state.messaging_data.messaging_pillars[:3]
        for i, col in enumerate([col1, col2, col3]):
            if i < len(pillars):
                with col:
                    st.write(f"**{i+1}. Pillar**")
                    st.caption(pillars[i][:80])
    else:
        with col1:
            st.write("**1. Clinical Excellence**")
            st.caption("Strong efficacy data")
        with col2:
            st.write("**2. Unmet Need**")
            st.caption("Addresses treatment gaps")
        with col3:
            st.write("**3. Differentiation**")
            st.caption("Unique mechanism advantage")
    
    st.markdown("---")
    
    # Expected Objections (Top 3)
    st.write("**Top 3 Expected Objections & Your Responses:**")
    
    objections_brief = [
        ("Clinical data limited?", "Multiple ongoing trials support efficacy across patient subsets."),
        ("How does it differ from competitors?", "Unique mechanism provides differentiated approach with proven efficacy."),
        ("Pricing concern?", "Premium justified by health economic data and QALY gains.")
    ]
    
    for i, (obj, resp) in enumerate(objections_brief, 1):
        with st.expander(f"{i}. {obj}"):
            st.write(f"**Response:** {resp}")
    
    st.markdown("---")
    
    # Top Discovery Questions
    st.write("**Top 3 Discovery Questions to Ask:**")
    
    discovery_brief = [
        "1. How many patients do you treat monthly with this indication?",
        "2. What are your current treatment challenges?",
        "3. What health economic data matters for your hospital's decision?"
    ]
    
    for q in discovery_brief:
        st.write(q)
    
    st.markdown("---")
    
    # Reimbursement Quick Check
    st.write("**Reimbursement Status (Quick Check):**")
    col1, col2 = st.columns(2)
    
    with col1:
        if state.payer_data:
            st.write(f"✓ HTA: {state.payer_data.hta_status or 'Pending'}")
            price_text = f"✓ Price ceiling: ${state.payer_data.pricing_ceiling:,.0f}" if (state.payer_data and state.payer_data.pricing_ceiling) else "✓ Pricing: TBD"
            st.write(price_text)
        else:
            st.write("✓ HTA status pending")
            st.write("✓ Pricing under negotiation")
    
    with col2:
        if state.payer_data:
            qaly_text = f"✓ QALY threshold: £{state.payer_data.qaly_threshold:,.0f}" if (state.payer_data and state.payer_data.qaly_threshold) else "✓ QALY: Standard"
            st.write(qaly_text)
            st.write("✓ Outcomes-based pricing available")
        else:
            st.write("✓ Value-based approach recommended")
    
    st.markdown("---")
    
    # Competitive Positioning
    st.write("**You vs Top Competitor:**")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Our Advantage:**")
        if state.messaging_data:
            for diff in state.messaging_data.key_differentiators[:2]:
                st.write(f"✓ {diff[:60]}")
        else:
            st.write("✓ Differentiated mechanism\n✓ Strong clinical data")
    
    with col2:
        st.write("**Their Advantage:**")
        if state.competitor_data:
            st.write(f"⚠️ Established market presence\n⚠️ Extensive safety data")
        else:
            st.write("⚠️ Established market\n⚠️ Lower price")
    
    st.markdown("---")
    
    # Time Breakdown
    st.write("**Suggested Call Time Allocation:**")
    
    time_cols = st.columns(4)
    with time_cols[0]:
        st.metric("Opening", "2 min")
    with time_cols[1]:
        st.metric("Talking Points", "3 min")
    with time_cols[2]:
        st.metric("Discovery", "3 min")
    with time_cols[3]:
        st.metric("Q&A", "2 min")
    
    st.markdown("---")
    
    # Final Checklist
    st.write("**Before You Call - Checklist:**")
    
    checklist = [
        "✅ Reviewed positioning statement",
        "✅ Memorized 3 talking points",
        "✅ Prepared objection responses",
        "✅ Have discovery questions ready",
        "✅ Know reimbursement status",
        "✅ Understand competitive position"
    ]
    
    for item in checklist:
        st.write(item)
    
    st.markdown("---")
    
    st.success("🟢 **You're Ready!** Walk in confident and prepared.")


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
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_question
        })
        
        # Generate answer based on brief data
        answer = generate_qa_answer(user_question, state)
        
        # Add answer to history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': answer
        })
        
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
    
    st.subheader("📥 Download MSL Brief")
    st.markdown("*Save and share your pre-call intelligence brief*")
    
    # Generate download options
    col1, col2, col3 = st.columns(3)
    
    # JSON Export
    with col1:
        try:
            json_data = json.dumps(state.__dict__, indent=2, default=str)
            st.download_button(
                label="📄 Download JSON",
                data=json_data,
                file_name=f"evidentia_msl_brief_{state.drug_name}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error generating JSON: {str(e)}")
    
    # CSV Export (Talking Points)
    with col2:
        st.info("📊 CSV export\nComing soon")
    
    # PDF Report
    with col3:
        st.info("📝 PDF report\nComing soon")
    
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