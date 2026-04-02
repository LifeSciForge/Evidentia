# SKILL_02: Insight Capture Engine
## Post-Call Structured Intelligence Extraction from MSL Field Notes

---

## Problem Statement

At the 9th Annual MSL Society Conference, attendees were asked: "Does your organization have a clear, documented process to analyze insights and capture outcomes from KOL interactions?"

**Only 4 of ~500 people answered yes.**

This is not a technology problem — it is a process failure baked into how MSLs work. After a KOL meeting:
- Most MSLs write freeform notes in personal documents or the CRM free-text field
- Notes are not categorized, not searchable, not analyzed
- Insights that could inform medical strategy — unmet needs, competitive intelligence, data gaps, safety signals — disappear into a black hole
- **95% of MSLs face increased pressure to gather actionable insights** but have no tool to do it consistently

The result: a $200K/year employee with unique access to scientific thought leaders produces intelligence that is never used.

---

## Objective

Build a post-call structured insight capture flow that:

1. Accepts freeform MSL field notes (typed or pasted — voice-to-text integration is optional)
2. Extracts 1–10 structured insights per call via LLM (temperature=0.2 for deterministic extraction)
3. Categorizes each insight into one of 10 clinically meaningful categories
4. Lets the MSL review, edit, and confirm before saving
5. Stores insights persistently for trend analysis (SKILL_06 provides the database layer)

**Success criteria:**
- MSL can capture a full post-call insight summary in <2 minutes
- Each insight has: category, urgency, action required, source verbatim (KOL quote if present)
- Insights are searchable by drug, indication, category, and date range
- Trend analytics: "What are the top 3 unmet needs surfaced in the last 90 days?"

---

## Core Data Models (add to `src/schema/gtm_state.py`)

```python
from enum import Enum

class InsightCategory(str, Enum):
    UNMET_MEDICAL_NEED    = "unmet_medical_need"
    COMPETITIVE_INTEL     = "competitive_intelligence"
    DATA_GAP              = "data_gap"
    SAFETY_SIGNAL         = "safety_signal"
    PRESCRIBING_BARRIER   = "prescribing_barrier"
    KOL_SENTIMENT         = "kol_sentiment"
    PAYER_BARRIER         = "payer_barrier"
    CLINICAL_QUESTION     = "clinical_question"
    PUBLICATION_REQUEST   = "publication_request"
    TRIAL_INTEREST        = "trial_interest"        # KOL interested in participating in a trial

@dataclass
class FieldInsight:
    insight_id: str                    # uuid4()
    kol_id: str                        # links to KOLProfile (kol_name + institution hash)
    msl_id: str                        # user_id from session (SKILL_06 auth)
    drug_name: str
    indication: str
    interaction_date: str              # ISO format: "2026-03-31"
    raw_notes: str                     # original freeform text (preserved, never modified)
    insight_category: str              # InsightCategory value
    insight_text: str                  # cleaned, actionable 1–2 sentence summary
    sentiment: str                     # "positive" / "neutral" / "negative"
    urgency: str                       # "high" / "medium" / "low"
    action_required: bool
    action_description: str            # what medical affairs should do next
    source_verbatim: str               # direct KOL quote if present, else ""
    confidence_score: float            # LLM extraction confidence 0.0–1.0
    tags: List[str]                    # freeform tags for search
    created_at: str                    # ISO timestamp
    confirmed_by_msl: bool = False     # True after MSL reviews and confirms

# Add to GTMState:
# raw_field_notes: Optional[str] = None
# interaction_date: Optional[str] = None
# interaction_type: Optional[str] = None   # "face_to_face" / "virtual" / "conference"
# captured_insights: List[FieldInsight] = field(default_factory=list)
```

---

## New Agent: `insight_extraction_agent`

### File
`src/agents/gtm_agents/insight_extraction_agent.py`

### Design Principles

- This agent runs **AFTER** a KOL meeting, not before. It is triggered from the Post-Call Capture UI tab, not from the main brief generation workflow.
- Temperature=0.2 — extraction must be deterministic and grounded in the actual notes
- The LLM must never invent insights. If no safety signal is present in the notes, no safety_signal insight should be returned
- All insights are marked `confirmed_by_msl=False` until the MSL reviews them in the UI

```python
async def insight_extraction_agent(state: GTMState) -> GTMState:
    """
    Post-call insight extraction from MSL field notes.
    Input:  state.raw_field_notes (set from Post-Call Capture UI)
            state.current_doctor, state.current_hospital
            state.drug_name, state.indication
            state.interaction_date, state.interaction_type
    Output: state.captured_insights (List[FieldInsight])
    """
    from src.core.llm import get_claude
    from src.core.logger import get_logger
    import uuid, json, re
    from datetime import datetime

    logger = get_logger(__name__)

    if not state.raw_field_notes or len(state.raw_field_notes.strip()) < 20:
        logger.warning("Insight extraction skipped: insufficient field notes")
        return state

    llm = get_claude(temperature=0.2)

    extraction_prompt = f"""
    You are a medical affairs intelligence analyst. Extract ALL meaningful insights
    from these MSL field notes from a KOL interaction.

    Context:
    - Drug: {state.drug_name}
    - Indication: {state.indication}
    - KOL: {state.current_doctor or "Unknown"}
    - Institution: {state.current_hospital or "Unknown"}
    - Date: {state.interaction_date or datetime.now().strftime("%Y-%m-%d")}
    - Meeting type: {state.interaction_type or "unspecified"}

    Field Notes:
    ---
    {state.raw_field_notes}
    ---

    Extract every distinct insight and return a JSON array.
    For each insight, use exactly this structure:

    {{
      "insight_category": one of [
        "unmet_medical_need", "competitive_intelligence", "data_gap",
        "safety_signal", "prescribing_barrier", "kol_sentiment",
        "payer_barrier", "clinical_question", "publication_request", "trial_interest"
      ],
      "insight_text": "Clear, actionable 1-2 sentence summary of what was learned",
      "sentiment": "positive|neutral|negative",
      "urgency": "high|medium|low",
      "action_required": true|false,
      "action_description": "Specific action for medical affairs (or empty string if none)",
      "source_verbatim": "Direct quote from KOL if present in notes, else empty string",
      "confidence": 0.0-1.0,
      "tags": ["tag1", "tag2"]
    }}

    Rules:
    - Only extract insights that are EXPLICITLY present in the notes
    - Do NOT invent insights or add context not in the notes
    - Safety signals (adverse events, unexpected toxicities) ALWAYS get urgency=high
    - A single meeting may produce 1–10 insights
    - If notes are brief and contain only 1 insight, return only 1
    - Return a JSON ARRAY (even if only 1 item). No prose. No explanation.
    """

    insights = []
    try:
        response = llm.invoke(extraction_prompt)
        raw_text = response.content

        # Extract JSON array
        array_match = re.search(r'\[.*\]', raw_text, re.DOTALL)
        if not array_match:
            # Try wrapped in object
            obj_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
            if obj_match:
                parsed = json.loads(obj_match.group())
                raw_insights = parsed.get("insights", [parsed])
            else:
                logger.error("No JSON found in insight extraction response")
                return state
        else:
            raw_insights = json.loads(array_match.group())

        kol_id = f"{state.current_doctor}_{state.current_hospital}".replace(" ", "_").lower()
        msl_id = getattr(state, "msl_id", "unknown")

        for raw in raw_insights:
            insight = FieldInsight(
                insight_id=str(uuid.uuid4()),
                kol_id=kol_id,
                msl_id=msl_id,
                drug_name=state.drug_name,
                indication=state.indication,
                interaction_date=state.interaction_date or datetime.now().strftime("%Y-%m-%d"),
                raw_notes=state.raw_field_notes,
                insight_category=raw.get("insight_category", "clinical_question"),
                insight_text=raw.get("insight_text", ""),
                sentiment=raw.get("sentiment", "neutral"),
                urgency=raw.get("urgency", "medium"),
                action_required=raw.get("action_required", False),
                action_description=raw.get("action_description", ""),
                source_verbatim=raw.get("source_verbatim", ""),
                confidence_score=float(raw.get("confidence", 0.7)),
                tags=raw.get("tags", []),
                created_at=datetime.now().isoformat(),
                confirmed_by_msl=False
            )
            insights.append(insight)

    except Exception as e:
        logger.error(f"Insight extraction failed: {e}")

    state.captured_insights = insights
    state.mark_agent_complete("Insight Extraction Agent")
    return state
```

---

## UI: Post-Call Capture Tab

### Add to `src/ui/app.py`

Add a new tab (or Streamlit page) for post-call capture. This is triggered separately from the brief generation workflow — it does NOT require a pre-call brief to have been generated first.

```python
def display_post_call_capture_section():
    """Post-call insight capture UI — standalone section in the Streamlit app."""

    st.subheader("Post-Call Insight Capture")
    st.write("Enter your field notes. Evidentia will extract and structure the insights.")

    with st.form("post_call_form"):
        col1, col2 = st.columns(2)

        with col1:
            meeting_date = st.date_input("Meeting Date", value=datetime.now().date())
            meeting_type = st.selectbox(
                "Meeting Type",
                ["Face-to-face", "Virtual", "Conference / Congress", "Phone"]
            )
            duration_minutes = st.number_input("Duration (minutes)", min_value=5, max_value=180, value=30)

        with col2:
            kol_name = st.text_input("KOL Name", value=st.session_state.get("current_doctor", ""))
            institution = st.text_input("Institution", value=st.session_state.get("current_hospital", ""))
            drug_name = st.text_input("Drug", value=st.session_state.get("drug_name", ""))
            indication = st.text_input("Indication", value=st.session_state.get("indication", ""))

        field_notes = st.text_area(
            "Field Notes",
            height=250,
            placeholder=(
                "Example: Dr. Smith expressed interest in the Phase 3 KEYNOTE data but raised "
                "concerns about the PD-L1 cutoff used. He mentioned that pembrolizumab is now "
                "standard of care at his institution. He asked whether we have RWE data for "
                "patients with ECOG PS 2. He also noted that one of his patients on the drug "
                "experienced grade 2 pneumonitis — not sure if related. Would be interested in "
                "joining an advisory board if invited."
            )
        )

        submitted = st.form_submit_button("Extract Insights", type="primary")

    if submitted:
        if len(field_notes.strip()) < 20:
            st.error("Please enter at least 20 characters of field notes.")
            return

        # Build minimal state for insight extraction
        from src.schema.gtm_state import GTMState
        from src.agents.gtm_agents.insight_extraction_agent import insight_extraction_agent
        import asyncio

        state = GTMState(
            drug_name=drug_name,
            indication=indication,
            current_doctor=kol_name,
            current_hospital=institution,
            raw_field_notes=field_notes,
            interaction_date=meeting_date.isoformat(),
            interaction_type=meeting_type.lower().replace(" ", "_").replace("/", "_")
        )

        with st.spinner("Extracting insights..."):
            loop = asyncio.new_event_loop()
            state = loop.run_until_complete(insight_extraction_agent(state))
            loop.close()

        if not state.captured_insights:
            st.warning("No insights could be extracted. Check that your notes contain meaningful observations.")
            return

        st.success(f"Extracted {len(state.captured_insights)} insights")
        st.session_state["pending_insights"] = state.captured_insights
        st.session_state["pending_raw_notes"] = field_notes

    # Display extracted insights for MSL review
    if "pending_insights" in st.session_state:
        display_insight_review_ui(st.session_state["pending_insights"])


def display_insight_review_ui(insights: List):
    """Allow MSL to review, edit, and confirm extracted insights before saving."""

    st.subheader("Review Extracted Insights")
    st.write("Review each insight below. Edit if needed, then confirm to save.")

    # Urgency color coding
    urgency_colors = {"high": "red", "medium": "orange", "low": "blue"}
    category_icons = {
        "unmet_medical_need": "🔴",
        "competitive_intelligence": "🟡",
        "data_gap": "🔵",
        "safety_signal": "⚠️",
        "prescribing_barrier": "🚧",
        "kol_sentiment": "💬",
        "payer_barrier": "💰",
        "clinical_question": "❓",
        "publication_request": "📄",
        "trial_interest": "🧪"
    }

    confirmed_insights = []
    for i, insight in enumerate(insights):
        icon = category_icons.get(insight.insight_category, "📌")
        urgency_color = urgency_colors.get(insight.urgency, "gray")

        with st.expander(
            f"{icon} {insight.insight_category.replace('_', ' ').title()} "
            f"— :{urgency_color}[{insight.urgency.upper()}]",
            expanded=(insight.urgency == "high")
        ):
            # Editable insight text
            edited_text = st.text_area(
                "Insight", value=insight.insight_text, key=f"insight_text_{i}"
            )

            col1, col2, col3 = st.columns(3)
            edited_category = col1.selectbox(
                "Category", options=[c.value for c in InsightCategory],
                index=[c.value for c in InsightCategory].index(insight.insight_category),
                key=f"cat_{i}"
            )
            edited_urgency = col2.selectbox(
                "Urgency", options=["high", "medium", "low"],
                index=["high", "medium", "low"].index(insight.urgency),
                key=f"urgency_{i}"
            )
            action_req = col3.checkbox(
                "Action Required", value=insight.action_required, key=f"action_{i}"
            )

            if insight.source_verbatim:
                st.info(f"KOL Quote: \"{insight.source_verbatim}\"")

            if action_req:
                action_desc = st.text_input(
                    "Action Description", value=insight.action_description, key=f"adesc_{i}"
                )
            else:
                action_desc = ""

            confirm = st.checkbox(f"Confirm this insight", key=f"confirm_{i}", value=True)

            if confirm:
                from dataclasses import replace
                confirmed_insights.append(replace(
                    insight,
                    insight_text=edited_text,
                    insight_category=edited_category,
                    urgency=edited_urgency,
                    action_required=action_req,
                    action_description=action_desc,
                    confirmed_by_msl=True
                ))

    if st.button("Save Confirmed Insights", type="primary"):
        if not confirmed_insights:
            st.warning("No insights confirmed. Check at least one insight to save.")
            return

        # Save to persistence layer (SKILL_06 InsightStore)
        try:
            from src.service.persistence.insight_store import InsightStore
            store = InsightStore()
            for insight in confirmed_insights:
                store.save_insight(insight)
            st.success(f"Saved {len(confirmed_insights)} insights.")
            del st.session_state["pending_insights"]
        except ImportError:
            # SKILL_06 not yet implemented — save to session state as fallback
            st.session_state["saved_insights"] = confirmed_insights
            st.success(f"Insights confirmed ({len(confirmed_insights)}). Persistence not yet active — saved to session.")
```

---

## Insight Analytics Service

### File: `src/service/insight_analytics.py`

```python
class InsightAnalytics:
    """
    Analyzes aggregated field insights across calls, KOLs, and time periods.
    Requires SKILL_06 InsightStore for persistence.
    """

    def get_trend_insights(
        self,
        drug_name: str,
        category: str,
        days_back: int = 90
    ) -> Dict:
        """
        Returns emerging themes for a specific category.
        Uses frequency counting + LLM cluster labeling.
        """
        ...

    def get_unmet_needs_summary(self, indication: str, days_back: int = 90) -> List[Dict]:
        """
        Aggregates unmet_medical_need insights across all KOLs.
        Returns ranked list: [{theme, frequency, representative_quotes}]
        """
        ...

    def get_competitive_alerts(self, drug_name: str, days_back: int = 30) -> List[Dict]:
        """
        Surfaces competitive_intelligence insights from the last N days.
        Flags any new competitor mentions not seen in prior period.
        Returns: [{competitor_name, mention_count, key_signal, urgency}]
        """
        ...

    def get_safety_signals(self, drug_name: str) -> List[Dict]:
        """
        Returns all safety_signal insights, sorted by urgency and date.
        These ALWAYS require escalation review regardless of age.
        """
        ...

    def get_insight_velocity(
        self,
        drug_name: str,
        category: str,
        days_back: int = 90
    ) -> Dict:
        """
        Returns week-by-week insight count for trend visualization.
        Used in Field Intelligence Dashboard (SKILL_04).
        """
        ...
```

---

## Safety Signal Escalation Rule

**Any insight with `insight_category = "safety_signal"` must:**
1. Be displayed with a ⚠️ warning banner regardless of confirmation status
2. Show an "Escalate to Medical Affairs" button that creates an email draft
3. Never be silently discarded — even if the MSL unchecks "confirm"

```python
# In display_insight_review_ui(), after the loop:
safety_signals = [i for i in insights if i.insight_category == "safety_signal"]
if safety_signals:
    st.error(f"⚠️ {len(safety_signals)} potential safety signal(s) detected. These require escalation.")
    for sig in safety_signals:
        st.write(f"**Signal:** {sig.insight_text}")
        if st.button(f"Draft Escalation Email — {sig.insight_id[:8]}", key=f"esc_{sig.insight_id}"):
            draft = generate_escalation_email(sig)
            st.text_area("Email Draft (copy and send to your Medical Affairs team)", value=draft, height=200)

def generate_escalation_email(insight: FieldInsight) -> str:
    return f"""Subject: Safety Signal — {insight.drug_name} / {insight.indication}

Dear Medical Affairs,

I am escalating a potential safety observation from a KOL interaction.

Date: {insight.interaction_date}
KOL: {insight.kol_id}
Drug: {insight.drug_name}
Indication: {insight.indication}

Observation:
{insight.insight_text}

{"Source verbatim: \"" + insight.source_verbatim + "\"" if insight.source_verbatim else ""}

Please review and initiate pharmacovigilance procedures if appropriate.

[MSL Name]
"""
```

---

## Files Modified

| File | Change |
|------|--------|
| `src/schema/gtm_state.py` | Add `FieldInsight`, `InsightCategory`; add `raw_field_notes`, `interaction_date`, `interaction_type`, `captured_insights` to `GTMState` |
| `src/ui/app.py` | Add Post-Call Capture tab with `display_post_call_capture_section()` and `display_insight_review_ui()` |

## Files Created

| File | Purpose |
|------|---------|
| `src/agents/gtm_agents/insight_extraction_agent.py` | LLM-powered freeform notes → structured insights |
| `src/service/insight_analytics.py` | Trend surfacing, unmet needs aggregation, competitive alerts |
