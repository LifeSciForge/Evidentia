# SKILL_03: KOL Engagement Tracker
## Interaction Quality Scoring + Coverage Gap Detection + Network Analysis

---

## Problem Statement

The current system has no concept of KOL relationship management. It generates a brief and stops. But MSLs are measured on metrics that don't capture the value they create:

- **Only 3% of organizations** say their MSL measurement systems are "very effective" (Global Survey, 1,023 MA professionals, 2024)
- **67% say measurement is "difficult" or "very difficult"**
- **30% of global KOLs have zero recorded MSL interactions** (Veeva Pulse) — coverage gaps nobody notices
- The most-used metric (raw call count) is considered only "moderately valuable" by the MSLs themselves
- KOLs who receive MSL engagement are **2–4x more likely to change treatment patterns** — but this only holds for quality interactions, not box-ticking

The result: MSL teams are growing (300% over a decade) but can't demonstrate ROI because they're measuring activity, not impact.

---

## Objective

Track KOL relationships with quality scoring, coverage gap visibility, and network analysis so that:

1. MSLs and their managers know **which KOLs are active, at-risk, or being missed**
2. Every interaction gets a **quality score (0–10)** based on scientific depth, not duration
3. **Coverage gaps** are surfaced proactively — "You haven't engaged Dr. X (Tier 1) in 67 days"
4. **KOL network maps** show who influences whom, enabling strategic prioritization

---

## Core Data Models (add to `src/schema/gtm_state.py`)

```python
@dataclass
class KOLInteraction:
    interaction_id: str                # uuid4()
    kol_id: str                        # kol_name_institution hash
    msl_id: str                        # from auth session
    drug_name: str
    indication: str
    interaction_date: str              # ISO format
    interaction_type: str              # "face_to_face" / "virtual" / "conference" / "phone"
    duration_minutes: int
    topics_discussed: List[str]        # scientific topics covered
    materials_shared: List[str]        # content IDs or titles used in meeting
    quality_score: float               # 0–10, computed by engagement_scoring_agent
    quality_rationale: str             # brief explanation of score
    dimension_scores: Dict[str, float] # {"scientific_depth": 2.5, "engagement": ...}
    follow_up_required: bool
    follow_up_actions: List[str]       # specific next steps
    insights_captured: int             # count of FieldInsights from SKILL_02 for this call

@dataclass
class KOLEngagementSummary:
    kol_id: str
    kol_name: str
    institution: str
    territory_id: str
    total_interactions: int
    interactions_last_90_days: int
    avg_quality_score: float
    quality_trend: str                 # "improving" / "stable" / "declining"
    last_interaction_date: Optional[str]
    days_since_last_contact: int
    coverage_status: str               # "Active" / "At-risk" / "Lapsed" / "Never-engaged"
    influence_tier: str                # "Tier 1" / "Tier 2" / "Tier 3"
    network_connections: List[str]     # other KOL IDs this KOL influences
    top_topics: List[str]              # most discussed topics across interactions
    action_items_pending: int          # open follow-up actions

# Add to GTMState:
# current_interaction: Optional[KOLInteraction] = None
# msl_id: Optional[str] = None
```

---

## KOL Tier Assignment Logic

Applied in `kol_profiling_agent.py` (SKILL_01) when building `KOLProfile`:

```python
def assign_kol_tier(profile: KOLProfile) -> str:
    """
    Tier 1: Top national/international KOL — drives clinical practice and guidelines.
    Tier 2: Regional KOL — influential in their institution/region.
    Tier 3: Local HCP — important volume prescriber but limited broader influence.
    """
    tier1_signals = [
        profile.publication_count > 50,
        len(profile.clinical_trial_pi) > 3,
        any(inst in profile.institution for inst in TOP_20_INSTITUTIONS),
        len(profile.conference_presentations) > 5
    ]
    tier2_signals = [
        profile.publication_count >= 20,
        len(profile.clinical_trial_pi) >= 1,
        len(profile.conference_presentations) >= 2
    ]

    if sum(tier1_signals) >= 2:
        return "Tier 1"
    elif sum(tier2_signals) >= 2:
        return "Tier 2"
    else:
        return "Tier 3"

TOP_20_INSTITUTIONS = [
    "MD Anderson", "Memorial Sloan Kettering", "Mayo Clinic", "Johns Hopkins",
    "Massachusetts General", "Dana-Farber", "Stanford", "UCSF", "Cleveland Clinic",
    "UCLA", "Columbia", "Duke", "Penn", "Yale", "Vanderbilt", "Michigan",
    "Washington University", "Northwestern", "Mount Sinai", "NYU"
]
```

---

## Coverage Status Rules

```python
def compute_coverage_status(days_since_last_contact: int, tier: str) -> str:
    """
    Coverage status varies by tier — Tier 1 KOLs need more frequent contact.
    """
    thresholds = {
        "Tier 1": {"active": 45, "at_risk": 90},
        "Tier 2": {"active": 60, "at_risk": 120},
        "Tier 3": {"active": 90, "at_risk": 180},
    }
    t = thresholds.get(tier, thresholds["Tier 3"])

    if days_since_last_contact is None:  # never contacted
        return "Never-engaged"
    elif days_since_last_contact <= t["active"]:
        return "Active"
    elif days_since_last_contact <= t["at_risk"]:
        return "At-risk"
    else:
        return "Lapsed"
```

---

## New Agent: `engagement_scoring_agent`

### File
`src/agents/gtm_agents/engagement_scoring_agent.py`

### Quality Score Formula (0–10)

| Dimension | Max Points | Criteria |
|-----------|-----------|---------|
| Scientific depth | 0–3 | Were clinical topics substantively discussed? Trial data, MOA, safety profiles = depth |
| KOL engagement | 0–3 | Did KOL ask questions, share opinions, challenge data? (vs passive listening) |
| Actionability | 0–2 | Did the meeting produce specific follow-up actions or commitments? |
| Relationship building | 0–2 | Did MSL advance the relationship? (first meeting vs. repeat = different baseline) |

```python
async def engagement_scoring_agent(state: GTMState) -> GTMState:
    """
    Scores the quality of a KOL interaction on a 0–10 scale.
    Runs AFTER insight_extraction_agent in the post-call pipeline.
    Input:  state.current_interaction (partially populated by UI)
            state.captured_insights (from insight_extraction_agent)
    Output: state.current_interaction.quality_score populated
    """
    from src.core.llm import get_claude

    if not state.current_interaction:
        return state

    interaction = state.current_interaction
    insights_count = len(state.captured_insights) if state.captured_insights else 0

    llm = get_claude(temperature=0.2)

    scoring_prompt = f"""
    Score this MSL-KOL interaction for scientific engagement quality.

    Meeting details:
    - Drug: {state.drug_name}
    - Indication: {state.indication}
    - KOL: {state.current_doctor}
    - Duration: {interaction.duration_minutes} minutes
    - Meeting type: {interaction.interaction_type}
    - Topics discussed: {interaction.topics_discussed}
    - Materials shared: {len(interaction.materials_shared)} items
    - Follow-up actions: {interaction.follow_up_actions}
    - Field insights captured: {insights_count} distinct insights

    Scoring dimensions (score each 0 to max):
    1. Scientific depth (0–3): Were clinical topics substantively discussed?
       - 0 = No scientific exchange (scheduling, logistics, relationship building only)
       - 1 = Surface-level discussion (general disease state, no specific data)
       - 2 = Moderate depth (specific clinical data discussed, some back-and-forth)
       - 3 = Deep scientific exchange (trial design, endpoints, mechanism, safety data in detail)

    2. KOL engagement (0–3): Did the KOL actively engage?
       - 0 = KOL was passive, minimal response
       - 1 = KOL acknowledged but didn't probe
       - 2 = KOL asked questions or shared observations
       - 3 = KOL challenged data, shared proprietary observations, or expressed strong opinions

    3. Actionability (0–2): Did the meeting produce next steps?
       - 0 = No follow-up planned
       - 1 = Informal follow-up (send paper, schedule next meeting)
       - 2 = Formal action (IIT discussion, advisory board invite, data request submitted)

    4. Relationship advancement (0–2): Did the relationship progress?
       - 0 = No change or regression
       - 1 = Maintained existing relationship
       - 2 = Clear relationship advancement (new trust, commitment, or advocacy signal)

    Return JSON:
    {{
      "scientific_depth": float,
      "kol_engagement": float,
      "actionability": float,
      "relationship_advancement": float,
      "total_score": float,
      "rationale": "2-3 sentence explanation of the score"
    }}
    """

    try:
        response = llm.invoke(scoring_prompt)
        import json, re
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            scores = json.loads(json_match.group())
            interaction.quality_score = min(10.0, float(scores.get("total_score", 5.0)))
            interaction.quality_rationale = scores.get("rationale", "")
            interaction.dimension_scores = {
                "scientific_depth": scores.get("scientific_depth", 0),
                "kol_engagement": scores.get("kol_engagement", 0),
                "actionability": scores.get("actionability", 0),
                "relationship_advancement": scores.get("relationship_advancement", 0)
            }
    except Exception as e:
        interaction.quality_score = 5.0
        interaction.quality_rationale = "Score unavailable due to processing error"

    state.current_interaction = interaction
    state.mark_agent_complete("Engagement Scoring Agent")
    return state
```

---

## Coverage Analytics Service

### File: `src/service/coverage_analytics.py`

```python
class CoverageAnalytics:
    """
    Territory-level KOL coverage analysis.
    Requires SKILL_06 InsightStore + KOLStore for persistence.
    Falls back to session data if persistence not yet active.
    """

    def get_coverage_gaps(
        self,
        territory_id: str,
        tier_filter: Optional[str] = "Tier 1"
    ) -> List[Dict]:
        """
        Returns KOLs with coverage_status in ["Never-engaged", "Lapsed", "At-risk"]
        sorted by influence tier (Tier 1 first) and days since last contact.
        """
        # Query kol_engagement_summaries from SQLite (SKILL_06)
        # Fall back to session state if SKILL_06 not active
        ...

    def get_territory_coverage_rate(self, territory_id: str) -> Dict:
        """
        Returns:
        {
          "total_kols": int,
          "active": int,
          "at_risk": int,
          "lapsed": int,
          "never_engaged": int,
          "coverage_rate": float,       # active / total
          "tier_breakdown": {
            "Tier 1": {"total": int, "active": int, "coverage_rate": float},
            "Tier 2": {...},
            "Tier 3": {...}
          }
        }
        """
        ...

    def get_quality_trend(
        self,
        msl_id: str,
        days_back: int = 90
    ) -> List[Dict]:
        """
        Returns weekly average quality scores for an MSL.
        [{week: "2026-W10", avg_score: 7.2, interaction_count: 8}]
        Used for MSL coaching and performance reviews.
        """
        ...

    def get_network_influence_map(self, kol_id: str) -> Dict:
        """
        Returns the collaboration network for a KOL:
        - Direct co-authors (from PubMed publication data)
        - Co-PIs on trials (from ClinicalTrials.gov)
        - Institutional colleagues (same institution in KOL database)

        This identifies who else to engage if you want to move this KOL's network.
        """
        from src.service.tools.pubmed_tools import PubMedClient
        from src.service.tools.clinical_trials_tools import ClinicalTrialsClient
        ...

    def get_at_risk_alerts(self, territory_id: str) -> List[Dict]:
        """
        Returns Tier 1 + Tier 2 KOLs approaching At-risk status within 14 days.
        Proactive alert: "Dr. X will become At-risk in 8 days if not contacted."
        """
        ...
```

---

## UI: Engagement Tracker Page

### File: `pages/engagement_tracker.py`

```python
import streamlit as st
from src.service.coverage_analytics import CoverageAnalytics

st.set_page_config(page_title="KOL Engagement Tracker", layout="wide")
st.title("KOL Engagement Tracker")

analytics = CoverageAnalytics()
territory_id = st.session_state.get("territory_id", "default")

# --- Coverage Overview ---
col1, col2, col3, col4 = st.columns(4)
coverage = analytics.get_territory_coverage_rate(territory_id)

col1.metric("Total KOLs", coverage.get("total_kols", 0))
col2.metric(
    "Coverage Rate",
    f"{coverage.get('coverage_rate', 0):.0%}",
    delta="+2% vs last quarter"
)
col3.metric("At-Risk KOLs", coverage.get("at_risk", 0), delta_color="inverse")
col4.metric("Never Engaged", coverage.get("never_engaged", 0), delta_color="inverse")

# --- Tier Breakdown ---
st.subheader("Coverage by Tier")
tier_data = coverage.get("tier_breakdown", {})
for tier, data in tier_data.items():
    rate = data.get("coverage_rate", 0)
    color = "green" if rate > 0.8 else "orange" if rate > 0.5 else "red"
    st.write(f"**{tier}**: {data.get('active', 0)}/{data.get('total', 0)} active "
             f"(:{color}[{rate:.0%}])")

# --- Coverage Gap List ---
st.subheader("Coverage Gaps — Priority KOLs to Engage")
gaps = analytics.get_coverage_gaps(territory_id, tier_filter=None)

if not gaps:
    st.success("No critical coverage gaps detected.")
else:
    for gap in gaps[:20]:
        status_color = {
            "Never-engaged": "red",
            "Lapsed": "red",
            "At-risk": "orange"
        }.get(gap.get("coverage_status"), "gray")

        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            col1.write(f"**{gap.get('kol_name')}** — {gap.get('institution')}")
            col2.write(gap.get("influence_tier"))
            col3.write(f":{status_color}[{gap.get('coverage_status')}]")
            col4.write(
                f"{gap.get('days_since_last_contact', 'Never')} days"
                if gap.get("days_since_last_contact") else "Never contacted"
            )

# --- Quality Score Trend ---
st.subheader("Interaction Quality Trend")
msl_id = st.session_state.get("msl_id", "unknown")
quality_trend = analytics.get_quality_trend(msl_id, days_back=90)

if quality_trend:
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[d["week"] for d in quality_trend],
        y=[d["avg_score"] for d in quality_trend],
        mode="lines+markers",
        name="Avg Quality Score",
        line=dict(color="#0055B8", width=2)
    ))
    fig.update_layout(
        yaxis=dict(range=[0, 10], title="Quality Score"),
        xaxis_title="Week",
        title="Weekly Average Interaction Quality Score"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Quality trend data will appear after logging interactions.")

# --- At-Risk Alerts ---
alerts = analytics.get_at_risk_alerts(territory_id)
if alerts:
    st.warning(f"⚠️ {len(alerts)} KOL(s) approaching At-risk status in the next 14 days")
    for alert in alerts:
        st.write(f"• **{alert.get('kol_name')}** ({alert.get('influence_tier')}) — "
                 f"{alert.get('days_until_at_risk')} days until At-risk")
```

---

## Files Modified

| File | Change |
|------|--------|
| `src/schema/gtm_state.py` | Add `KOLInteraction`, `KOLEngagementSummary`; add `current_interaction`, `msl_id` to `GTMState` |
| `src/agents/gtm_agents/kol_profiling_agent.py` (SKILL_01) | Add `assign_kol_tier()` call; populate `influence_tier` on `KOLProfile` |

## Files Created

| File | Purpose |
|------|---------|
| `src/agents/gtm_agents/engagement_scoring_agent.py` | LLM-based interaction quality scoring (0–10) |
| `src/service/coverage_analytics.py` | Coverage gaps, territory coverage rate, quality trends, network maps |
| `pages/engagement_tracker.py` | Streamlit engagement tracking dashboard |
