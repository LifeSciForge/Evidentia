# PLAN.md — MSL Talking Points: Clinically-Grounded Conversational Output

**Objective:** Replace the generic positioning/pillars output in the Talking Points tab with
KOL-specific, data-backed, MSL-conversational content — a conversation opener, 3 clinical
pillars with evidence, differentiators vs standard of care, anticipated objections with
responses, and guardrails on what NOT to say.

**Status:** Awaiting approval
**Test command:** `python3 -c "from src.agents.gtm_agents.messaging_agent import messaging_agent; print('ok')"`
**Smoke test:** `streamlit run streamlit_app.py` → generate brief → check Talking Points tab

---

## Files to Modify

### 1. `src/schema/gtm_state.py`

**Change:** Add 5 new dataclasses for the MSL talking points structure. Add
`msl_talking_points` field to `GTMState`. Existing `MessagingData` is kept unchanged —
the new field lives alongside it so nothing breaks.

**Add after the `MessagingData` dataclass (after line 108):**

```python
@dataclass
class ClinicalEvidence:
    """Evidence backing a clinical pillar"""
    trial_name: str = ""
    key_data_point: str = ""
    source: str = ""

@dataclass
class ClinicalPillar:
    """One of three MSL clinical talking pillars"""
    pillar_title: str = ""
    evidence: ClinicalEvidence = field(default_factory=ClinicalEvidence)
    msl_talking_point: str = ""
    why_relevant_to_kol: str = ""

@dataclass
class KeyDifferentiator:
    """Differentiator vs current standard of care"""
    vs_standard_of_care: str = ""
    advantage: str = ""
    evidence: str = ""
    msl_talking_point: str = ""

@dataclass
class AnticipatedObjection:
    """A clinical objection the KOL is likely to raise"""
    objection: str = ""
    why_they_ask: str = ""
    probability: str = ""
    evidence_response: str = ""
    msl_response: str = ""

@dataclass
class Guardrail:
    """A claim the MSL must NOT make"""
    avoid_claim: str = ""
    reason: str = ""
    alternative: str = ""

@dataclass
class MSLTalkingPoints:
    """
    KOL-specific, clinically-grounded MSL conversation guide.
    Replaces generic positioning statement + messaging pillars.
    Output from messaging_agent when current_doctor is set.
    """
    kol_name: str = ""
    kol_institution: str = ""
    patient_population: str = ""
    clinical_philosophy: str = ""

    conversation_opener: str = ""
    opener_why_it_works: str = ""
    opener_delivery_tips: str = ""

    three_pillars: List[ClinicalPillar] = field(default_factory=list)
    key_differentiators: List[KeyDifferentiator] = field(default_factory=list)
    anticipated_objections: List[AnticipatedObjection] = field(default_factory=list)
    guardrails: List[Guardrail] = field(default_factory=list)

    tone: str = "Peer-to-peer clinical discussion, not pitch"
    pace: str = "Deliverable in 2-3 minutes naturally"
    key_to_success: str = ""
```

**Add to `GTMState` class (after `messaging_data` field, line ~153):**
```python
msl_talking_points: Optional[MSLTalkingPoints] = None
current_doctor: Optional[str] = None
current_hospital: Optional[str] = None
agent_messages: List[Any] = field(default_factory=list)
```

**Test:** `python3 -c "from src.schema.gtm_state import GTMState, MSLTalkingPoints; print('ok')"`

---

### 2. `src/service/validators/json_validator.py`

**Change:** Add Pydantic schema for the new MSL talking points JSON output from the LLM.
Add after the existing `PositioningResponse` class.

```python
class ClinicalEvidenceSchema(BaseModel):
    trial_name: str = ""
    key_data_point: str = ""
    source: str = ""

class ClinicalPillarSchema(BaseModel):
    pillar_title: str = ""
    evidence: ClinicalEvidenceSchema = ClinicalEvidenceSchema()
    msl_talking_point: str = ""
    why_relevant_to_kol: str = ""

class KeyDifferentiatorSchema(BaseModel):
    vs_standard_of_care: str = ""
    advantage: str = ""
    evidence: str = ""
    msl_talking_point: str = ""

class AnticipatedObjectionSchema(BaseModel):
    objection: str = ""
    why_they_ask: str = ""
    probability: str = "50%"
    evidence_response: str = ""
    msl_response: str = ""

class GuardrailSchema(BaseModel):
    avoid_claim: str = ""
    reason: str = ""
    alternative: str = ""

class MSLTalkingPointsSchema(BaseModel):
    doctor_profile: dict = {}
    conversation_opener: dict = {}
    three_clinical_pillars: list[ClinicalPillarSchema] = []
    key_differentiators: list[KeyDifferentiatorSchema] = []
    anticipated_objections: list[AnticipatedObjectionSchema] = []
    guardrails: dict = {}
    delivery_notes: dict = {}
```

**Test:** `python3 -c "from src.service.validators.json_validator import MSLTalkingPointsSchema; print('ok')"`

---

### 3. `src/agents/gtm_agents/messaging_agent.py`

**Change:** Add a new function `generate_msl_talking_points()` that runs the
clinically-grounded prompt when `state.current_doctor` is set. Call it at the end of
`messaging_agent()` and store output in `state.msl_talking_points`.

**Existing `messaging_agent()` function is NOT changed** — the positioning + persona
messaging still runs as before. The MSL talking points are additive.

**Add new function before `messaging_agent()`:**

```python
async def generate_msl_talking_points(state: GTMState) -> Optional[MSLTalkingPoints]:
    """
    Generate KOL-specific, clinically-grounded MSL talking points.
    Only runs when state.current_doctor is populated.
    Returns None gracefully if LLM fails.
    """
    if not state.current_doctor:
        return None

    # Build context from prior agents
    publications = []
    if state.market_data and state.market_data.key_publications:
        publications = state.market_data.key_publications[:5]

    trials = []
    if state.market_data and state.market_data.clinical_trials:
        trials = state.market_data.clinical_trials[:3]

    llm = get_claude(temperature=0.3)

    prompt = f"""
You are a clinical communication strategist for Medical Science Liaisons (MSLs).
Generate a clinically-grounded, MSL-conversational talking points guide for:

KOL: {state.current_doctor}
Institution: {state.current_hospital or "Not specified"}
Drug: {state.drug_name}
Indication: {state.indication}

Clinical Data Available:
Trials: {trials}
Key Publications: {publications}

CRITICAL CONSTRAINTS — every output must be:
1. Conversational (sounds like two doctors talking, NOT a pitch)
2. Data-backed (every claim cites a trial or clinical observation; if data is unavailable, say so honestly)
3. Actionable (MSL can say it in their own words in under 60 seconds)
4. KOL-relevant (addresses this specific doctor's likely patient population)
5. Non-promotional (no "first-in-class", "breakthrough", "game-changing" language)

Return ONLY valid JSON with this exact structure:
{{
  "doctor_profile": {{
    "name": "{state.current_doctor}",
    "institution": "{state.current_hospital or 'Not specified'}",
    "patient_population": "Inferred from indication: {state.indication}",
    "clinical_philosophy": "Evidence-driven"
  }},
  "conversation_opener": {{
    "text": "2-3 sentence clinical hook. Mentions patient population, clinical reason for engagement, opens dialogue. NO marketing language.",
    "why_this_works": "Why this doctor will engage based on their practice",
    "delivery_tips": "Tone and pacing guidance for MSL"
  }},
  "three_clinical_pillars": [
    {{
      "pillar_title": "2-4 word clinical fact",
      "evidence": {{
        "trial_name": "Trial name or NCT ID if available",
        "key_data_point": "Response rate %, safety metric, or clinical observation",
        "source": "Trial or publication"
      }},
      "msl_talking_point": "How MSL naturally says this to a doctor — peer-to-peer tone, not a pitch",
      "why_relevant_to_kol": "Why this matters for their specific patient population"
    }},
    {{
      "pillar_title": "Pillar 2",
      "evidence": {{"trial_name": "", "key_data_point": "", "source": ""}},
      "msl_talking_point": "",
      "why_relevant_to_kol": ""
    }},
    {{
      "pillar_title": "Pillar 3",
      "evidence": {{"trial_name": "", "key_data_point": "", "source": ""}},
      "msl_talking_point": "",
      "why_relevant_to_kol": ""
    }}
  ],
  "key_differentiators": [
    {{
      "vs_standard_of_care": "What this doctor is likely doing currently",
      "advantage": "How {state.drug_name} differs — do NOT claim superiority without head-to-head data",
      "evidence": "Data supporting this framing",
      "msl_talking_point": "Natural peer-to-peer way to say this"
    }}
  ],
  "anticipated_objections": [
    {{
      "objection": "Specific clinical concern this KOL would raise",
      "why_they_ask": "Root cause based on their patient population and practice",
      "probability": "XX%",
      "evidence_response": "Trial data or mechanism rationale that addresses it",
      "msl_response": "How to respond — acknowledge concern, cite data, not defensive"
    }},
    {{
      "objection": "Second likely objection",
      "why_they_ask": "",
      "probability": "XX%",
      "evidence_response": "",
      "msl_response": ""
    }},
    {{
      "objection": "Third likely objection",
      "why_they_ask": "",
      "probability": "XX%",
      "evidence_response": "",
      "msl_response": ""
    }}
  ],
  "guardrails": {{
    "avoid_claims": [
      {{
        "claim": "Specific phrase MSL must NOT use",
        "reason": "Why — unsupported, marketing language, defensive, etc.",
        "alternative": "Better way to frame it"
      }}
    ]
  }},
  "delivery_notes": {{
    "tone": "Peer-to-peer clinical discussion, not pitch",
    "pace": "Deliverable in 2-3 minutes naturally",
    "key_to_success": "What will make this specific doctor engage"
  }}
}}
"""

    try:
        response = llm.invoke(prompt)
        raw = extract_json_from_text(response.content)

        dp = raw.get("doctor_profile", {})
        opener = raw.get("conversation_opener", {})
        notes = raw.get("delivery_notes", {})
        guardrail_items = raw.get("guardrails", {}).get("avoid_claims", [])

        pillars = []
        for p in raw.get("three_clinical_pillars", [])[:3]:
            ev = p.get("evidence", {})
            pillars.append(ClinicalPillar(
                pillar_title=p.get("pillar_title", ""),
                evidence=ClinicalEvidence(
                    trial_name=ev.get("trial_name", ""),
                    key_data_point=ev.get("key_data_point", ""),
                    source=ev.get("source", ""),
                ),
                msl_talking_point=p.get("msl_talking_point", ""),
                why_relevant_to_kol=p.get("why_relevant_to_kol", ""),
            ))

        differentiators = []
        for d in raw.get("key_differentiators", [])[:3]:
            differentiators.append(KeyDifferentiator(
                vs_standard_of_care=d.get("vs_standard_of_care", ""),
                advantage=d.get("advantage", ""),
                evidence=d.get("evidence", ""),
                msl_talking_point=d.get("msl_talking_point", ""),
            ))

        objections = []
        for o in raw.get("anticipated_objections", [])[:5]:
            objections.append(AnticipatedObjection(
                objection=o.get("objection", ""),
                why_they_ask=o.get("why_they_ask", ""),
                probability=o.get("probability", ""),
                evidence_response=o.get("evidence_response", ""),
                msl_response=o.get("msl_response", ""),
            ))

        guardrails = []
        for g in guardrail_items[:5]:
            guardrails.append(Guardrail(
                avoid_claim=g.get("claim", ""),
                reason=g.get("reason", ""),
                alternative=g.get("alternative", ""),
            ))

        return MSLTalkingPoints(
            kol_name=dp.get("name", state.current_doctor),
            kol_institution=dp.get("institution", state.current_hospital or ""),
            patient_population=dp.get("patient_population", ""),
            clinical_philosophy=dp.get("clinical_philosophy", ""),
            conversation_opener=opener.get("text", ""),
            opener_why_it_works=opener.get("why_this_works", ""),
            opener_delivery_tips=opener.get("delivery_tips", ""),
            three_pillars=pillars,
            key_differentiators=differentiators,
            anticipated_objections=objections,
            guardrails=guardrails,
            tone=notes.get("tone", "Peer-to-peer clinical discussion"),
            pace=notes.get("pace", "2-3 minutes"),
            key_to_success=notes.get("key_to_success", ""),
        )

    except Exception as e:
        logger.error(f"MSL talking points generation failed: {e}")
        return None
```

**In `messaging_agent()` function, add at the end before `return state` (after the existing MessagingData is built):**
```python
# Generate MSL-specific talking points if KOL is selected
state.msl_talking_points = await generate_msl_talking_points(state)
if state.msl_talking_points:
    logger.info(f"✅ MSL talking points generated for {state.current_doctor}")
```

**Imports to add at top of file:**
```python
from src.schema.gtm_state import (GTMState, MessagingData, PersonaMessaging,
    MSLTalkingPoints, ClinicalPillar, ClinicalEvidence,
    KeyDifferentiator, AnticipatedObjection, Guardrail)
from src.service.validators.json_validator import extract_json_from_text
from typing import Optional
```

**Test:** `python3 -c "from src.agents.gtm_agents.messaging_agent import messaging_agent, generate_msl_talking_points; print('ok')"`

---

### 4. `src/ui/app.py`

**Two changes:**

**Change A — Pass doctor/hospital from sidebar into GTMState.**
Find where `GTMState` is instantiated (around line 360–390). Add the two new fields:
```python
state = GTMState(
    drug_name=drug_name,
    indication=indication,
    current_doctor=selected_doctor,    # ADD
    current_hospital=selected_hospital, # ADD
)
```

**Change B — Replace `display_talking_points_section()` function (lines 515–569).**
Replace entirely with new function that renders the structured MSL output.

New function renders in this order:
1. **KOL context banner** — name, institution, patient population (only if msl_talking_points populated)
2. **Conversation Opener** — blue callout box with the opener text + delivery tips expander
3. **Three Clinical Pillars** — 3 cards side by side, each showing: pillar title, evidence badge (trial name + data point), MSL talking point, why relevant
4. **Key Differentiators** — vs standard of care table
5. **Anticipated Objections** — expanders, each showing: probability badge, root cause, evidence, MSL response
6. **Guardrails** — red-bordered "Do NOT say" section
7. **Fallback** — if `msl_talking_points` is None, render the existing generic content (positioning statement + pillars) so it never shows blank

**Also update `display_objection_handling_section()`:** If `msl_talking_points` is set, show those objections instead of the generic ones. If not, keep existing behaviour.

**Test:** App loads → select a doctor → generate brief → Talking Points tab shows structured content.

---

## Execution Order

1. Modify `src/schema/gtm_state.py` → test import
2. Modify `src/service/validators/json_validator.py` → test import
3. Modify `src/agents/gtm_agents/messaging_agent.py` → test import
4. Modify `src/ui/app.py` → Change A (GTMState instantiation)
5. Modify `src/ui/app.py` → Change B (display_talking_points_section replacement)
6. Final smoke test: `streamlit run streamlit_app.py`

## Rollback
If any step fails: `git checkout -- <file>`. Stop, report error.

## Out of Scope
- No changes to market_research_agent, competitor_analysis_agent, payer_intelligence_agent, synthesis_agent
- No changes to gtm_workflow.py
- No database work
- No changes to other UI tabs (clinical evidence, reimbursement, etc.)
- Existing MessagingData and generic positioning output is preserved as fallback
