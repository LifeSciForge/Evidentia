"""
Characterization smoke tests for UI section render functions.

These tests are the REFACTOR SAFETY NET for Stage 5. They call every public
results-section function with:
  (a) a fully-populated GTMState — exercises the "happy path" branches
  (b) an empty GTMState          — exercises the "no data" / fallback branches

Streamlit runs in bare mode during tests, so all st.* calls emit
"missing ScriptRunContext" warnings but DO NOT raise. The only assertion
is "no exception raised".

DO NOT add try/except blocks that mask real exceptions. If a section raises
on the current code, that is a real finding — do not hide it.
"""

import warnings
import pytest

from src.schema.gtm_state import (
    GTMState,
    MarketResearchData,
    PayerIntelligenceData,
    CompetitorData,
    CompetitorAnalysisData,
    ICPProfile,
    MessagingData,
    MSLTalkingPoints,
    GTMStrategy,
    ClinicalPillar,
    ClinicalEvidence,
    KeyDifferentiator,
    AnticipatedObjection,
    Guardrail,
    Source,
)
from src.ui.app import (
    display_msl_results,
    display_talking_points_section,
    display_objection_handling_section,
    display_discovery_questions_section,
    display_clinical_evidence_section,
    display_competitive_section,
    display_final_brief_section,
    display_qa_chat_section,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _suppress_streamlit_warnings():
    """Suppress the 'missing ScriptRunContext' bare-mode noise."""
    warnings.filterwarnings(
        "ignore",
        message=".*ScriptRunContext.*",
    )
    warnings.filterwarnings(
        "ignore",
        message=".*Session.*",
    )
    warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        module="streamlit",
    )


def populated_state() -> GTMState:
    """
    Return a GTMState with all agent-output sub-objects populated using the
    real field names verified against src/schema/gtm_state.py.

    Values are realistic but synthetic — no live data, no API calls.
    """
    market = MarketResearchData(
        drug_name="sotorasib",
        indication="KRAS G12C NSCLC",
        tam_estimate=2_500.0,        # $2.5B
        sam_estimate=800.0,
        som_estimate=120.0,
        patient_population=35_000,
        clinical_trials=[
            {
                "nct_id": "NCT04665128",
                "title": "CodeBreaK 100 — sotorasib Phase 2",
                "status": "Completed",
                "phase": "Phase 2",
                "primary_endpoint": "Objective Response Rate",
                "key_insight": "37.1% ORR in KRAS G12C NSCLC patients",
            }
        ],
        key_publications=[
            {
                "title": "Sotorasib for Lung Cancers with KRAS p.G12C Mutation",
                "journal": "NEJM",
                "pmid": "34096690",
            }
        ],
        epidemiology={"incidence_us": 25000, "market_drivers": ["Unmet need in KRAS-mutant NSCLC"]},
        market_drivers=["Rising prevalence of KRAS G12C mutations", "Unmet need after IO failure"],
        research_notes="Data sourced from ClinicalTrials.gov and PubMed",
    )

    payer = PayerIntelligenceData(
        hta_status="FDA approved; NICE review pending",
        reimbursement_criteria=["KRAS G12C mutation confirmed", "Prior platinum-based chemotherapy"],
        qaly_threshold=50_000.0,
        pricing_ceiling=17_900.0,
        access_restrictions=["Biomarker testing required"],
        comparator_drugs=["docetaxel", "pembrolizumab"],
        payer_feedback={"US": "Positive coverage signal", "UK": "Under NICE review"},
        pricing_signals={"US_list_price": 17900},
        payer_notes="Based on Amgen pricing at launch",
    )

    comp1 = CompetitorData(
        competitor_name="adagrasib",
        competitor_indication="KRAS G12C NSCLC",
        market_share=28.5,
        pricing=17_900.0,
        positioning="Second-to-market KRAS G12C inhibitor with CNS penetration",
        key_differentiators=["CNS activity", "Combination data"],
        clinical_advantages=["CNS penetration", "MARIPOSA-2 combination data"],
        clinical_disadvantages=["More drug-drug interactions", "GI toxicity profile"],
        launch_date="2022-12-22",
        sales_data=300.0,
    )

    competitor_analysis = CompetitorAnalysisData(
        competitors=[comp1],
        competitive_gaps={"CNS": "adagrasib has more CNS data"},
        market_positioning_strategy="Lead with PFS and OS data in PD-L1 negative patients",
        competitive_threats=["adagrasib combination approvals"],
        competitive_opportunities=["First-mover advantage in KRAS G12C inhibition"],
        competitive_notes="Market data sourced from public filings",
    )

    icp = ICPProfile(
        primary_icp="KRAS G12C NSCLC patients post-platinum",
        secondary_icp="Treatment-naive KRAS G12C NSCLC",
        company_size_range="N/A",
        therapeutic_areas_focus=["Thoracic Oncology", "Lung Cancer"],
        key_personas=["Thoracic Oncologist", "Pulmonologist"],
        buying_committee={"Oncologist": "Primary prescriber", "Payer": "Formulary gatekeeper"},
        urgency_triggers=["IO failure", "KRAS G12C test positive"],
        geography_priority=["US", "EU"],
        estimated_tam_by_segment={"NSCLC": 2500.0},
        icp_notes="Profile based on CodeBreaK 100 trial eligibility",
    )

    messaging = MessagingData(
        category_definition="KRAS G12C inhibitor",
        positioning_statement=(
            "Sotorasib is the first KRAS G12C inhibitor to demonstrate durable responses "
            "in previously treated KRAS G12C NSCLC patients."
        ),
        key_differentiators=[
            "First-in-class KRAS G12C inhibitor",
            "37.1% ORR in Phase 2",
            "Once-daily oral dosing",
        ],
        competitive_vs_statements=["vs docetaxel: superior ORR and tolerability"],
        messaging_pillars=[
            "Clinical efficacy: 37.1% ORR in CodeBreaK 100",
            "Tolerability: lower grade 3/4 AE rate than chemotherapy",
            "Convenience: once-daily oral monotherapy",
        ],
        common_objections={
            "Limited OS data": "CodeBreaK 200 Phase 3 trial addresses OS; interim data compelling.",
            "Head-to-head vs adagrasib?": "No direct head-to-head; both target KRAS G12C with distinct profiles.",
        },
        messaging_notes="Positioning finalized pre-launch",
    )

    pillar1 = ClinicalPillar(
        pillar_title="First-in-class KRAS G12C inhibitor",
        evidence=ClinicalEvidence(
            trial_name="CodeBreaK 100",
            key_data_point="37.1% confirmed ORR (n=124)",
            source="NEJM 2021",
        ),
        msl_talking_point=(
            "In CodeBreaK 100, sotorasib achieved a 37.1% confirmed ORR — "
            "a landmark result in a previously 'undruggable' target."
        ),
        why_relevant_to_kol="KOL focuses on KRAS-mutant NSCLC; first approved option in this setting",
    )

    diff1 = KeyDifferentiator(
        vs_standard_of_care="Docetaxel chemotherapy",
        advantage="Oral, once-daily vs IV infusion; superior ORR",
        evidence="CodeBreaK 200: ORR 28.1% vs 13.2% docetaxel",
        msl_talking_point="For KRAS G12C patients, sotorasib offers better response with less toxicity.",
    )

    obj1 = AnticipatedObjection(
        objection="OS data is immature",
        why_they_ask="Overall survival is the gold standard for prescribing decisions",
        probability="High",
        evidence_response="CodeBreaK 200 OS data expected; interim PFS HR 0.66 favours sotorasib.",
        msl_response=(
            "You're right that OS is the gold standard. The Phase 3 CodeBreaK 200 trial "
            "showed PFS benefit. Full OS data is maturing — I can share the latest cut when available."
        ),
    )

    guard1 = Guardrail(
        avoid_claim="Sotorasib cures KRAS G12C lung cancer",
        reason="No cure claim is approved; this is a treatment option, not a cure",
        alternative="Sotorasib has demonstrated durable disease control in previously treated patients",
    )

    msl_tp = MSLTalkingPoints(
        kol_name="Dr. Pasi A. Jänne",
        kol_institution="Dana-Farber Cancer Institute",
        patient_population="Advanced NSCLC, KRAS G12C-mutant, 2L+",
        clinical_philosophy="Evidence-first; interested in biomarker-driven therapies",
        conversation_opener=(
            "Dr. Jänne, given your work in KRAS-mutant NSCLC, I'd love to discuss "
            "the CodeBreaK 100 data and how you're thinking about the KRAS G12C space."
        ),
        opener_why_it_works="Acknowledges KOL expertise; leads with specific trial data",
        opener_delivery_tips="Maintain peer-to-peer tone; avoid promotional language",
        three_pillars=[pillar1],
        key_differentiators=[diff1],
        anticipated_objections=[obj1],
        guardrails=[guard1],
        tone="Peer-to-peer clinical discussion, not pitch",
        pace="Deliverable in 2-3 minutes naturally",
        key_to_success="Lead with OS gap; offer to share latest data",
    )

    strategy = GTMStrategy(
        executive_summary=(
            "Sotorasib is the first approved KRAS G12C inhibitor. "
            "Prioritise thoracic oncologists treating 2L+ NSCLC patients with KRAS G12C mutation."
        ),
        market_overview="KRAS G12C NSCLC represents ~13% of all NSCLC cases (~25,000 US patients/yr).",
        market_sizing={"TAM": 2500.0, "SAM": 800.0, "SOM": 120.0},
        target_segment="2L+ NSCLC with KRAS G12C mutation",
        positioning_framework="First-in-class, oral, targeted therapy for KRAS G12C NSCLC",
        key_messages=[
            "First approved KRAS G12C inhibitor",
            "37.1% ORR in Phase 2",
        ],
        channel_strategy={"KOL engagement": "MSL-led scientific exchange"},
        pricing_strategy="Premium, outcomes-aligned pricing at $17,900/cycle",
        reimbursement_strategy="NICE submission in progress; US payer coverage established",
        success_metrics=["Market share in KRAS G12C NSCLC", "KOL advocacy"],
        key_risks=["adagrasib competition", "Combination therapy competition"],
        competitive_moat="First-mover advantage and robust Phase 3 data",
        synthesis_notes="Based on CodeBreaK program data",
    )

    # Sources provenance map (a couple of representative entries)
    sources = {
        "market.patient_population": Source(
            tier="verified",
            label="ClinicalTrials.gov",
            url="https://clinicaltrials.gov/ct2/show/NCT04665128",
            note="CodeBreaK 100 enrollment",
        ),
        "market.tam": Source(
            tier="modeled",
            label="Modeled from sourced inputs",
            url=None,
            note="Derived from epidemiology + pricing",
        ),
    }

    return GTMState(
        drug_name="sotorasib",
        indication="KRAS G12C NSCLC",
        current_doctor="Dr. Pasi A. Jänne (Thoracic Oncology)",
        current_hospital="Dana-Farber Cancer Institute",
        market_data=market,
        payer_data=payer,
        competitor_data=competitor_analysis,
        icp_profile=icp,
        messaging_data=messaging,
        msl_talking_points=msl_tp,
        final_gtm_strategy=strategy,
        sources=sources,
        agents_completed=[
            "Market Research", "Payer Intelligence", "Competitor Analysis",
            "ICP Definition", "Messaging", "Synthesis",
        ],
        agent_status="completed",
        progress_percentage=100,
    )


def empty_state() -> GTMState:
    """Minimal GTMState with no agent outputs — tests the fallback/empty paths."""
    return GTMState(drug_name="x", indication="y")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

HOSPITAL = "Dana-Farber Cancer Institute"
DOCTOR = "Dr. Pasi A. Jänne (Thoracic Oncology)"


@pytest.fixture(autouse=True)
def silence_streamlit_warnings():
    """Silence Streamlit bare-mode ScriptRunContext warnings for the whole module."""
    _suppress_streamlit_warnings()


# ---------------------------------------------------------------------------
# Populated state: section smoke tests
# ---------------------------------------------------------------------------

class TestPopulatedState:
    """Each section renders without exception given a fully-populated GTMState."""

    def test_display_msl_results(self):
        state = populated_state()
        display_msl_results(state, HOSPITAL, DOCTOR)

    def test_display_talking_points_section(self):
        state = populated_state()
        display_talking_points_section(state)

    def test_display_objection_handling_section(self):
        state = populated_state()
        display_objection_handling_section(state)

    def test_display_discovery_questions_section(self):
        state = populated_state()
        display_discovery_questions_section(state)

    def test_display_clinical_evidence_section(self):
        state = populated_state()
        display_clinical_evidence_section(state)

    def test_display_competitive_section(self):
        state = populated_state()
        display_competitive_section(state)

    def test_display_final_brief_section(self):
        state = populated_state()
        display_final_brief_section(state)

    def test_display_qa_chat_section(self):
        state = populated_state()
        display_qa_chat_section(state)


# ---------------------------------------------------------------------------
# Empty state: section smoke tests (fallback / no-data paths)
# ---------------------------------------------------------------------------

class TestEmptyState:
    """Each section renders without exception given an empty GTMState."""

    def test_display_msl_results_empty(self):
        # display_msl_results returns early (no exception) when all three
        # agent outputs are None — that is the intended contract.
        state = empty_state()
        display_msl_results(state, "Some Hospital", "Some Doctor")

    def test_display_talking_points_section_empty(self):
        state = empty_state()
        display_talking_points_section(state)

    def test_display_objection_handling_section_empty(self):
        state = empty_state()
        display_objection_handling_section(state)

    def test_display_discovery_questions_section_empty(self):
        state = empty_state()
        display_discovery_questions_section(state)

    def test_display_clinical_evidence_section_empty(self):
        state = empty_state()
        display_clinical_evidence_section(state)

    def test_display_competitive_section_empty(self):
        state = empty_state()
        display_competitive_section(state)

    def test_display_final_brief_section_empty(self):
        state = empty_state()
        display_final_brief_section(state)

    def test_display_qa_chat_section_empty(self):
        state = empty_state()
        display_qa_chat_section(state)


# ---------------------------------------------------------------------------
# At-a-glance band: scientific metrics (patients / trials / pubs)
# ---------------------------------------------------------------------------

class TestAtAGlanceBand:
    """Focused tests for the three scientific metric cards in the at-a-glance band."""

    def test_band_with_counts(self):
        """Populated market_data with trials and publications renders without exception."""
        market = MarketResearchData(
            drug_name="sotorasib",
            indication="KRAS G12C NSCLC",
            patient_population=13_000,
            clinical_trials=[
                {"nct_id": "NCT04665128", "title": "CodeBreaK 100", "status": "Completed"},
                {"nct_id": "NCT04303780", "title": "CodeBreaK 200", "status": "Completed"},
            ],
            key_publications=[
                {"title": "Sotorasib for Lung Cancers", "journal": "NEJM", "pmid": "34096690"},
            ],
        )
        state = GTMState(
            drug_name="sotorasib",
            indication="KRAS G12C NSCLC",
            market_data=market,
            sources={
                "market.patient_population": Source(
                    tier="verified",
                    label="PubMed",
                    url="https://pubmed.ncbi.nlm.nih.gov/34096690",
                ),
            },
        )
        display_msl_results(state, "MD Anderson", "Dr. X")

    def test_band_market_data_none(self):
        """When market_data is None the at-a-glance band skips metrics without crashing."""
        state = GTMState(drug_name="x", indication="y", market_data=None)
        display_msl_results(state, "Some Hospital", "Some Doctor")

    def test_band_empty_lists(self):
        """Empty clinical_trials and key_publications lists render '—' gracefully."""
        market = MarketResearchData(
            drug_name="x",
            indication="y",
            patient_population=None,
            clinical_trials=[],
            key_publications=[],
        )
        state = GTMState(drug_name="x", indication="y", market_data=market)
        display_msl_results(state, "Hospital X", "Dr. Y")
