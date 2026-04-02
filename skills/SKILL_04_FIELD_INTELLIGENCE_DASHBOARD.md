# SKILL_04: Field Intelligence Dashboard
## Territory-Wide Intelligence Synthesis + Content Performance Tracking

---

## Problem Statement

Individual MSL insights exist in silos and never reach medical strategy. Three compounding failures:

1. **Insight aggregation failure:** Even if MSLs capture insights post-call (SKILL_02), those insights sit in individual records with no system to aggregate them into strategic signals. A medical affairs team managing 150 MSLs has no view of "what are KOLs in our NSCLC territory saying about unmet needs this quarter?"

2. **Content waste at scale:** Veeva Pulse 2025 data shows **~80% of approved scientific content is rarely or never used** in field meetings. Content teams create slides, reprints, and infographics that MSLs don't use — either because they don't know the material exists, or because it doesn't address what KOLs are asking about. Content-driven engagement **doubles treatment adoption** but is used in <50% of meetings.

3. **No proactive medical strategy triggers:** Emerging signals (a new competitor getting frequent mentions, a safety concern pattern, a consistent data gap request) only reach medical strategy when an MSL happens to flag it. There is no systematic monitoring.

---

## Objective

Build a territory intelligence layer that:

1. **Aggregates** field insights from all MSLs across a territory on a 90-day rolling basis
2. **Synthesizes** emerging themes via LLM clustering into actionable medical strategy signals
3. **Tracks content performance** — which materials are being used and which are gathering dust
4. **Surfaces proactive alerts** — new competitive signals, safety patterns, content gaps

---

## Core Data Models (add to `src/schema/gtm_state.py`)

```python
@dataclass
class UnmetNeedSignal:
    theme: str                         # synthesized theme name
    frequency: int                     # number of insights supporting this
    representative_quotes: List[str]   # source verbatim from KOLs
    first_seen: str                    # ISO date of earliest insight
    trend: str                         # "emerging" / "stable" / "declining"

@dataclass
class CompetitiveSignal:
    competitor_name: str
    signal_type: str                   # "new_mention" / "prescribing_shift" / "trial_result"
    mention_count: int
    key_quote: str
    urgency: str                       # "high" / "medium" / "low"
    first_seen: str
    is_new: bool                       # True if not seen in prior 30-day period

@dataclass
class ContentGap:
    requested_content: str             # what KOLs are asking for
    request_count: int
    existing_content_available: bool   # does this content exist?
    action: str                        # "create_new" / "improve_existing" / "distribute_better"

@dataclass
class TerritoryIntelligence:
    territory_id: str
    drug_name: str
    indication: str
    analysis_period_days: int
    total_interactions_analyzed: int
    total_msls_contributing: int
    generated_at: str                  # ISO timestamp
    cache_expires_at: str              # ISO timestamp (24h TTL)

    # Core intelligence outputs
    unmet_needs: List[UnmetNeedSignal]
    data_gaps: List[Dict]              # [{gap, count, urgency, action}]
    competitive_signals: List[CompetitiveSignal]
    sentiment_summary: Dict            # {trend, score, key_drivers, trajectory}
    strategy_recommendations: List[Dict]  # [{action, rationale, priority, owner}]
    content_gaps: List[ContentGap]
    safety_signals: List[Dict]         # [{signal, kol_count, escalation_required}]

    # Content performance
    content_usage_rate: float          # % of approved content used in period
    unused_content: List[str]          # content IDs/titles never used

@dataclass
class ContentItem:
    content_id: str
    title: str
    content_type: str                  # "slide_deck" / "publication_reprint" / "infographic" / "video"
    approved_date: str
    topics: List[str]                  # scientific topics this content covers
    usage_count: int
    last_used_date: Optional[str]
    requesting_kol_count: int          # how many KOLs have asked for this content

# Add to GTMState:
# territory_intelligence: Optional[TerritoryIntelligence] = None
```

---

## New Agent: `field_synthesis_agent`

### File
`src/agents/gtm_agents/field_synthesis_agent.py`

### Key Design Decisions

- This agent does **NOT run per-call**. It runs on-demand from the dashboard (or on a scheduled basis)
- Input: all `FieldInsights` from the last 90 days for a drug+indication combination
- It needs SKILL_06 `InsightStore` to query historical insights; degrades gracefully if not available
- Results are cached in SQLite `territory_intel_cache` for 24 hours
- Temperature=0.5 — synthesis requires some creativity but must stay grounded in the actual insight data

```python
async def field_synthesis_agent(state: GTMState) -> GTMState:
    """
    Synthesizes territory-wide field intelligence from aggregated MSL insights.
    Triggered on-demand from the Field Intelligence Dashboard, not per-call.

    Input:  state.drug_name, state.indication, state.territory_id (new field)
    Output: state.territory_intelligence (TerritoryIntelligence)
    """
    from src.core.llm import get_claude
    from src.core.logger import get_logger
    from datetime import datetime, timedelta
    import json, re

    logger = get_logger(__name__)

    # Load insights from persistence layer (SKILL_06)
    # Graceful fallback if persistence not active
    insights_raw = []
    try:
        from src.service.persistence.insight_store import InsightStore
        store = InsightStore()
        insights_raw = store.get_insights(
            drug_name=state.drug_name,
            indication=state.indication,
            days_back=90
        )
        logger.info(f"Loaded {len(insights_raw)} insights for synthesis")
    except ImportError:
        logger.warning("InsightStore not available — using session insights as fallback")
        if hasattr(state, "captured_insights") and state.captured_insights:
            insights_raw = state.captured_insights

    if not insights_raw:
        logger.warning("No insights available for territory synthesis")
        state.territory_intelligence = TerritoryIntelligence(
            territory_id=getattr(state, "territory_id", "default"),
            drug_name=state.drug_name,
            indication=state.indication,
            analysis_period_days=90,
            total_interactions_analyzed=0,
            total_msls_contributing=0,
            generated_at=datetime.now().isoformat(),
            cache_expires_at=(datetime.now() + timedelta(hours=24)).isoformat(),
            unmet_needs=[], data_gaps=[], competitive_signals=[],
            sentiment_summary={"trend": "Unknown", "score": 0, "key_drivers": []},
            strategy_recommendations=[], content_gaps=[], safety_signals=[],
            content_usage_rate=0.0, unused_content=[]
        )
        return state

    # Format insights for synthesis
    def format_insights_for_llm(insights):
        by_category = {}
        for insight in insights:
            cat = insight.insight_category if hasattr(insight, "insight_category") else insight.get("insight_category", "other")
            if cat not in by_category:
                by_category[cat] = []
            text = insight.insight_text if hasattr(insight, "insight_text") else insight.get("insight_text", "")
            verbatim = insight.source_verbatim if hasattr(insight, "source_verbatim") else insight.get("source_verbatim", "")
            by_category[cat].append({"text": text, "verbatim": verbatim})
        return by_category

    categorized = format_insights_for_llm(insights_raw)
    unique_msls = len(set(
        (i.msl_id if hasattr(i, "msl_id") else i.get("msl_id", "")) for i in insights_raw
    ))

    llm = get_claude(temperature=0.5)

    synthesis_prompt = f"""
    You are a medical affairs strategist synthesizing field intelligence from MSL-KOL interactions.

    Drug: {state.drug_name}
    Indication: {state.indication}
    Analysis period: Last 90 days
    Total insights: {len(insights_raw)}
    Contributing MSLs: {unique_msls}

    Categorized insights:
    {json.dumps(categorized, indent=2)[:6000]}

    Synthesize this into a strategic intelligence report. Return JSON with EXACTLY these keys:

    {{
      "unmet_needs": [
        {{
          "theme": "Clear theme name",
          "frequency": integer,
          "representative_quotes": ["quote1", "quote2"],
          "trend": "emerging|stable|declining"
        }}
      ],
      "data_gaps": [
        {{
          "gap": "What data KOLs are asking for",
          "count": integer,
          "urgency": "high|medium|low",
          "action": "Specific action for medical affairs"
        }}
      ],
      "competitive_signals": [
        {{
          "competitor_name": "Drug or company name",
          "signal_type": "new_mention|prescribing_shift|trial_result",
          "mention_count": integer,
          "key_quote": "Most telling quote",
          "urgency": "high|medium|low"
        }}
      ],
      "sentiment_summary": {{
        "trend": "improving|stable|declining",
        "score": 0.0-10.0,
        "key_drivers": ["driver1", "driver2"],
        "trajectory": "Brief explanation"
      }},
      "strategy_recommendations": [
        {{
          "action": "Specific recommendation",
          "rationale": "Why this matters",
          "priority": "high|medium|low",
          "owner": "Medical Affairs|MSL Team|Market Access|Regulatory"
        }}
      ],
      "content_gaps": [
        {{
          "requested_content": "What KOLs are asking for",
          "request_count": integer,
          "action": "create_new|improve_existing|distribute_better"
        }}
      ],
      "safety_signals": [
        {{
          "signal": "Description of potential safety observation",
          "kol_count": integer,
          "escalation_required": true|false
        }}
      ]
    }}

    IMPORTANT:
    - Only report what is ACTUALLY present in the insight data
    - Do not invent themes or signals
    - Safety signals that require escalation MUST have escalation_required=true
    - Return JSON only. No prose.
    """

    try:
        response = llm.invoke(synthesis_prompt)
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON in response")
        parsed = json.loads(json_match.group())

        state.territory_intelligence = TerritoryIntelligence(
            territory_id=getattr(state, "territory_id", "default"),
            drug_name=state.drug_name,
            indication=state.indication,
            analysis_period_days=90,
            total_interactions_analyzed=len(insights_raw),
            total_msls_contributing=unique_msls,
            generated_at=datetime.now().isoformat(),
            cache_expires_at=(datetime.now() + timedelta(hours=24)).isoformat(),
            unmet_needs=[UnmetNeedSignal(**n) for n in parsed.get("unmet_needs", [])],
            data_gaps=parsed.get("data_gaps", []),
            competitive_signals=[CompetitiveSignal(**c) for c in parsed.get("competitive_signals", [])],
            sentiment_summary=parsed.get("sentiment_summary", {}),
            strategy_recommendations=parsed.get("strategy_recommendations", []),
            content_gaps=[ContentGap(**c) for c in parsed.get("content_gaps", [])],
            safety_signals=parsed.get("safety_signals", []),
            content_usage_rate=0.0,
            unused_content=[]
        )

    except Exception as e:
        logger.error(f"Field synthesis failed: {e}")

    state.mark_agent_complete("Field Synthesis Agent")
    return state
```

---

## Content Analytics Service

### File: `src/service/content_analytics.py`

Tracks which approved materials are used across MSL interactions. Addresses the 80% unused content finding from Veeva Pulse.

```python
class ContentAnalytics:
    """
    Tracks content usage across MSL-KOL interactions.
    Requires SKILL_06 for persistence; degrades gracefully without it.
    """

    def record_content_use(
        self,
        content_id: str,
        interaction_id: str,
        kol_id: str
    ):
        """
        Called from Post-Call Capture UI when MSL selects materials used.
        Increments usage_count + updates last_used_date.
        """
        ...

    def get_unused_content(
        self,
        drug_name: str,
        days_threshold: int = 90
    ) -> List[ContentItem]:
        """
        Returns approved content items with usage_count == 0 in last N days.
        The 80% unused content problem — surface it so it can be fixed.
        """
        ...

    def get_content_performance_report(
        self,
        territory_id: str
    ) -> Dict:
        """
        Returns:
        {
          "total_content_items": int,
          "used_in_90_days": int,
          "never_used": int,
          "usage_rate": float,
          "top_5_used": [{content_id, title, usage_count}],
          "bottom_5_used": [{content_id, title, usage_count}]
        }
        """
        ...

    def get_content_gap_analysis(
        self,
        territory_intelligence: TerritoryIntelligence
    ) -> List[Dict]:
        """
        Cross-references content_gaps from field_synthesis_agent
        with existing content library.
        Returns gaps with action recommendations:
        - Gap with no existing content → create_new
        - Gap where content exists but unused → distribute_better
        """
        ...
```

---

## UI: Field Intelligence Dashboard

### File: `pages/field_intelligence.py`

```python
import streamlit as st
from src.agents.gtm_agents.field_synthesis_agent import field_synthesis_agent
from src.service.content_analytics import ContentAnalytics
from src.schema.gtm_state import GTMState
import asyncio

st.set_page_config(page_title="Field Intelligence Dashboard", layout="wide")
st.title("Field Intelligence Dashboard")
st.write("Territory-wide synthesis of MSL field insights — last 90 days")

# --- Controls ---
col1, col2, col3 = st.columns(3)
with col1:
    drug_name = st.text_input("Drug", value=st.session_state.get("drug_name", ""))
with col2:
    indication = st.text_input("Indication", value=st.session_state.get("indication", ""))
with col3:
    st.write("")  # spacing
    run_synthesis = st.button("Run Territory Analysis", type="primary")

if run_synthesis and drug_name and indication:
    state = GTMState(drug_name=drug_name, indication=indication)
    state.territory_id = st.session_state.get("territory_id", "default")

    with st.spinner("Synthesizing field intelligence across territory..."):
        loop = asyncio.new_event_loop()
        state = loop.run_until_complete(field_synthesis_agent(state))
        loop.close()

    if state.territory_intelligence:
        st.session_state["territory_intel"] = state.territory_intelligence
        st.success(f"Analysis complete — {state.territory_intelligence.total_interactions_analyzed} interactions synthesized")

intel = st.session_state.get("territory_intel")

if not intel:
    st.info("Enter a drug and indication above and click 'Run Territory Analysis' to generate insights.")
    st.stop()

# --- Safety Signals (always first, always visible) ---
if intel.safety_signals:
    for sig in intel.safety_signals:
        if sig.get("escalation_required"):
            st.error(f"⚠️ SAFETY SIGNAL — {sig.get('signal')} (reported by {sig.get('kol_count')} KOL(s)). Escalation required.")

# --- Emerging Unmet Needs ---
st.subheader("Top Unmet Medical Needs")
if intel.unmet_needs:
    import plotly.graph_objects as go
    fig = go.Figure(go.Bar(
        y=[n.theme for n in intel.unmet_needs],
        x=[n.frequency for n in intel.unmet_needs],
        orientation="h",
        marker_color="#0055B8"
    ))
    fig.update_layout(xaxis_title="Insight Count", height=300, margin=dict(l=200))
    st.plotly_chart(fig, use_container_width=True)

    for need in intel.unmet_needs[:3]:
        trend_icon = {"emerging": "🔺", "stable": "➡️", "declining": "🔻"}.get(need.trend, "")
        with st.expander(f"{trend_icon} {need.theme} ({need.frequency} insights)"):
            for quote in need.representative_quotes[:3]:
                if quote:
                    st.write(f"> \"{quote}\"")
else:
    st.info("No unmet need patterns detected in current insight data.")

# --- Competitive Intelligence Alerts ---
st.subheader("Competitive Intelligence")
new_signals = [s for s in intel.competitive_signals if s.is_new]
if new_signals:
    st.warning(f"🟡 {len(new_signals)} new competitive signal(s) detected in the last 30 days")

for signal in intel.competitive_signals:
    urgency_color = {"high": "red", "medium": "orange", "low": "blue"}.get(signal.urgency, "gray")
    st.write(
        f"**{signal.competitor_name}** — {signal.signal_type.replace('_', ' ').title()} "
        f"(mentioned {signal.mention_count}x) :{urgency_color}[{signal.urgency.upper()}]"
    )
    if signal.key_quote:
        st.caption(f'"{signal.key_quote}"')

# --- Data Gaps ---
st.subheader("Data Gaps KOLs Are Asking For")
for gap in intel.data_gaps[:5]:
    urgency_color = {"high": "red", "medium": "orange", "low": "blue"}.get(gap.get("urgency"), "gray")
    st.write(f"• **{gap.get('gap')}** ({gap.get('count')} requests) :{urgency_color}[{gap.get('urgency', 'medium').upper()}]")
    if gap.get("action"):
        st.caption(f"Recommended action: {gap.get('action')}")

# --- Content Performance ---
st.subheader("Content Performance")
analytics = ContentAnalytics()
perf = analytics.get_content_performance_report(
    territory_id=st.session_state.get("territory_id", "default")
)

col1, col2, col3 = st.columns(3)
col1.metric("Content Usage Rate", f"{perf.get('usage_rate', 0):.0%}", help="% of approved content used in last 90 days")
col2.metric("Never Used", perf.get("never_used", 0), delta_color="inverse")
col3.metric("Total Items", perf.get("total_content_items", 0))

# Content gaps from synthesis
if intel.content_gaps:
    st.subheader("Content Gaps — KOLs Are Asking for Material That Doesn't Exist")
    for gap in intel.content_gaps:
        action_icons = {
            "create_new": "🆕 Create new content",
            "improve_existing": "✏️ Improve existing content",
            "distribute_better": "📤 Distribute existing content better"
        }
        st.write(f"• **{gap.requested_content}** ({gap.request_count} requests) — {action_icons.get(gap.action, gap.action)}")

# --- Medical Strategy Recommendations ---
st.subheader("Medical Strategy Recommendations")
for rec in intel.strategy_recommendations:
    priority_color = {"high": "red", "medium": "orange", "low": "blue"}.get(rec.get("priority"), "gray")
    with st.container():
        st.write(f"**[{rec.get('owner', 'Medical Affairs')}]** {rec.get('action')}")
        st.caption(f"Rationale: {rec.get('rationale')} | Priority: :{priority_color}[{rec.get('priority', 'medium').upper()}]")

# --- Footer ---
if intel.generated_at:
    st.caption(f"Analysis generated: {intel.generated_at[:10]} | Expires: {intel.cache_expires_at[:10]}")
    st.caption(f"Based on {intel.total_interactions_analyzed} interactions from {intel.total_msls_contributing} MSLs")
```

---

## Files Modified

| File | Change |
|------|--------|
| `src/schema/gtm_state.py` | Add `UnmetNeedSignal`, `CompetitiveSignal`, `ContentGap`, `TerritoryIntelligence`, `ContentItem`; add `territory_intelligence`, `territory_id` to `GTMState` |

## Files Created

| File | Purpose |
|------|---------|
| `src/agents/gtm_agents/field_synthesis_agent.py` | Territory-wide insight synthesis via LLM |
| `src/service/content_analytics.py` | Content usage tracking and gap analysis |
| `pages/field_intelligence.py` | Streamlit field intelligence dashboard |
