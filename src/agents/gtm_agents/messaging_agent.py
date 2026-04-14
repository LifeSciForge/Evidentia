"""
Messaging & Positioning Agent
Creates positioning framework and persona-specific messaging
"""

from typing import Dict, Any, Optional
from src.schema.gtm_state import (
    GTMState, MessagingData, PersonaMessaging,
    MSLTalkingPoints, ClinicalPillar, ClinicalEvidence,
    KeyDifferentiator, AnticipatedObjection, Guardrail,
)
from src.core.llm import get_claude
from src.core.logger import get_logger
from src.service.validators.json_validator import (
    extract_json_from_text, validate_with_pydantic,
    PositioningResponse, PersonaResponse,
)

logger = get_logger(__name__)


async def generate_msl_talking_points(state: GTMState) -> Optional[MSLTalkingPoints]:
    """
    Generate KOL-specific, clinically-grounded MSL talking points.
    Only runs when state.current_doctor is populated.
    Returns None gracefully if LLM fails — caller shows fallback content.
    """
    if not state.current_doctor:
        return None

    publications = []
    if state.market_data and state.market_data.key_publications:
        publications = state.market_data.key_publications[:5]

    trials = []
    if state.market_data and state.market_data.clinical_trials:
        trials = state.market_data.clinical_trials[:3]

    llm = get_claude(temperature=0.3)

    prompt = f"""You are a clinical communication strategist for Medical Science Liaisons (MSLs).
Generate a clinically-grounded, MSL-conversational talking points guide.

KOL: {state.current_doctor}
Institution: {state.current_hospital or "Not specified"}
Drug: {state.drug_name}
Indication: {state.indication}

Clinical Data Available:
Trials: {trials}
Key Publications: {publications}

CRITICAL CONSTRAINTS:
1. Conversational — sounds like two doctors talking, NOT a pitch
2. Data-backed — every claim cites a trial or clinical observation; if data is unavailable, say so honestly
3. Actionable — MSL can say it naturally in under 60 seconds
4. KOL-relevant — addresses this specific doctor's likely patient population
5. Non-promotional — no "first-in-class", "breakthrough", "game-changing", "next evolution"

Return ONLY valid JSON:
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
    "delivery_tips": "Tone and pacing guidance for the MSL"
  }},
  "three_clinical_pillars": [
    {{
      "pillar_title": "2-4 word clinical fact",
      "evidence": {{
        "trial_name": "Trial name or NCT ID if available, else empty string",
        "key_data_point": "Response rate, safety metric, or clinical observation",
        "source": "Trial or publication reference"
      }},
      "msl_talking_point": "How MSL naturally says this to a doctor — peer-to-peer tone, not a pitch",
      "why_relevant_to_kol": "Why this matters for their specific patient population"
    }},
    {{
      "pillar_title": "Pillar 2 title",
      "evidence": {{"trial_name": "", "key_data_point": "", "source": ""}},
      "msl_talking_point": "",
      "why_relevant_to_kol": ""
    }},
    {{
      "pillar_title": "Pillar 3 title",
      "evidence": {{"trial_name": "", "key_data_point": "", "source": ""}},
      "msl_talking_point": "",
      "why_relevant_to_kol": ""
    }}
  ],
  "key_differentiators": [
    {{
      "vs_standard_of_care": "What this doctor is likely doing currently",
      "advantage": "How {state.drug_name} differs. Do NOT claim superiority without head-to-head data.",
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
}}"""

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


async def messaging_agent(state: GTMState) -> GTMState:
    """
    Messaging & Positioning Agent Node
    
    Creates positioning framework, key messages, and persona-specific messaging
    
    Args:
        state: Current GTM state (with market, competitor, and ICP data)
        
    Returns:
        Updated GTM state with messaging_data populated
    """
    
    logger.info(f"📢 Messaging & Positioning Agent starting for: {state.drug_name}")
    state.current_agent = "Messaging & Positioning Agent"
    state.agent_status = "running"
    
    try:
        # Extract context from previous agents
        market_summary = extract_market_summary(state.market_data)
        competitor_summary = extract_competitor_summary(state.competitor_data)
        icp_summary = extract_icp_summary(state.icp_profile)
        payer_summary = extract_payer_summary(state.payer_data)
        
        # Step 1: Create overall positioning framework
        logger.info("🧠 Creating positioning framework with Claude...")
        llm = get_claude()
        
        positioning_prompt = f"""
You are a pharma Medical Science Liaison (MSL) communication strategist.
Your job is to help MSLs make the affirmative case for {state.drug_name} — not to criticise competitors.

RULE: Never lead with a competitor's weakness. Always lead with {state.drug_name}'s strengths.
RULE: When a competitor is well-established, acknowledge it, then pivot to what {state.drug_name} uniquely offers.
RULE: Competitive statements must end on {state.drug_name}'s benefit, not on a competitor's problem.

Drug: {state.drug_name}
Indication: {state.indication}

Market Context:
{market_summary}

Competitive Landscape (for context only — do NOT criticise these drugs):
{competitor_summary}

ICP Context:
{icp_summary}

Payer Context:
{payer_summary}

Create a positioning framework with:

1. Category Definition:
   - What unmet clinical need does {state.drug_name} address?
   - What patient population benefits most?

2. Positioning Statement (one sentence):
   - What {state.drug_name} uniquely does for patients
   - Must be affirmative — what we offer, not what others lack

3. Key Differentiators — affirmative framing only:
   - Mechanism of action advantage (what it uniquely targets or how)
   - Efficacy in specific patient sub-populations where {state.drug_name} has an edge
   - Safety or tolerability profile that benefits patients
   Each differentiator must be a complete sentence starting with "{state.drug_name}..."

4. Value Propositions by Persona:
   - For CCO: revenue and market access opportunity
   - For Market Access: payer value story
   - For HEOR: health economics evidence
   - For Medical Affairs: clinical evidence quality

5. Competitive Bridge Statements (one per major competitor):
   Format: "Yes, [competitor] is [acknowledged strength]. And {state.drug_name} [unique strength that adds value for [specific patient population]."
   - Acknowledge the competitor's legitimacy first
   - Pivot to {state.drug_name}'s complementary or additive advantage
   - End on the patient benefit, not on the competitor's limitation

6. Messaging Pillars (3 core clinical themes):
   - Each pillar: a short clinical fact about {state.drug_name}, evidence-backed if possible

7. Common Objection Responses:
   - Format: objection -> response that acknowledges the concern then pivots affirmatively
   - Include: "Why use {state.drug_name} when [established competitor] is proven?"
   - Response must start with acknowledgment ("That's a fair point..."), then pivot

Respond with ONLY valid JSON. No markdown, no explanation, no backticks. Raw JSON only.

Keys required:
- category_definition (string)
- positioning_statement (string)
- key_differentiators (list of strings, each starting with "{state.drug_name}")
- value_propositions (object with persona names as keys)
- competitive_vs_statements (list of strings, each in "Yes... And {state.drug_name}..." format)
- messaging_pillars (list of strings)
- common_objections (object: objection string -> response string that pivots affirmatively)
"""
        
        try:
            response = llm.invoke(positioning_prompt)
            response_text = response.content
            try:
                raw = extract_json_from_text(response_text)
                result = validate_with_pydantic(raw, PositioningResponse)
                if result.valid:
                    positioning_dict = result.data.model_dump()
                    logger.info("✅ Positioning framework created successfully")
                else:
                    logger.warning(f"⚠️ Validation errors: {result.errors}")
                    positioning_dict = get_default_positioning_data()
            except ValueError:
                logger.warning("⚠️ Could not extract JSON from LLM response")
                positioning_dict = get_default_positioning_data()
        except Exception as e:
            logger.error(f"❌ LLM positioning error: {str(e)}")
            positioning_dict = get_default_positioning_data()
        
        # Step 2: Generate persona-specific messaging
        logger.info("👥 Generating persona-specific messaging...")
        
        personas = ["Chief Commercial Officer", "Head of Market Access", "HEOR Director", "Medical Affairs Lead"]
        persona_messaging = {}
        
        for persona in personas:
            logger.info(f"  Creating messaging for {persona}...")
            
            persona_prompt = f"""
Create detailed messaging for a {persona} regarding {state.drug_name}:

Positioning: {positioning_dict.get('positioning_statement', '')}
Key Differentiators: {positioning_dict.get('key_differentiators', [])}

For this persona, provide:
1. Role description (2-3 sentences)
2. Top 3 pain points (from their perspective)
3. Top 3 value propositions (specific to their needs)
4. 3 objection-response pairs specific to their concerns
5. 3 success metrics they care about
6. 2-3 engagement triggers

Respond with ONLY valid JSON. No markdown, no explanation, no backticks. Raw JSON only.

Keys required:
- role_description (string)
- pain_points (list of strings)
- value_propositions (list of strings)
- objection_responses (object: objection -> response)
- success_metrics (list of strings)
- engagement_triggers (list of strings)
"""
            
            try:
                persona_response = llm.invoke(persona_prompt)
                persona_text = persona_response.content
                try:
                    raw = extract_json_from_text(persona_text)
                    presult = validate_with_pydantic(raw, PersonaResponse)
                    persona_data = presult.data.model_dump() if presult.valid else get_default_persona_data()
                except ValueError:
                    persona_data = get_default_persona_data()
            except Exception as e:
                logger.error(f"Error creating messaging for {persona}: {str(e)}")
                persona_data = get_default_persona_data()
            
            persona_messaging[persona] = PersonaMessaging(
                persona=persona,
                role_description=persona_data.get("role_description", ""),
                key_pain_points=persona_data.get("pain_points", []),
                value_propositions=persona_data.get("value_propositions", []),
                objection_responses=persona_data.get("objection_responses", {}),
                success_metrics=persona_data.get("success_metrics", []),
                engagement_triggers=persona_data.get("engagement_triggers", [])
            )
        
        # Step 3: Create MessagingData object
        messaging_data = MessagingData(
            category_definition=positioning_dict.get("category_definition", ""),
            positioning_statement=positioning_dict.get("positioning_statement", ""),
            key_differentiators=positioning_dict.get("key_differentiators", []),
            value_prop_by_persona=persona_messaging,
            competitive_vs_statements=positioning_dict.get("competitive_vs_statements", []),
            messaging_pillars=positioning_dict.get("messaging_pillars", []),
            common_objections=positioning_dict.get("common_objections", {}),
            messaging_notes=f"Positioning framework for {len(personas)} key personas"
        )
        
        # Update state
        state.messaging_data = messaging_data

        # Generate MSL-specific talking points if a KOL is selected
        state.msl_talking_points = await generate_msl_talking_points(state)
        if state.msl_talking_points:
            logger.info(f"MSL talking points generated for {state.current_doctor}")

        state.mark_agent_complete("Messaging & Positioning Agent")
        state.agent_status = "completed"

        logger.info("Messaging & Positioning Agent completed successfully")
        logger.info(f"Positioning: {messaging_data.positioning_statement[:80]}...")
        logger.info(f"Created messaging for {len(persona_messaging)} personas")

        return state
        
    except Exception as e:
        logger.error(f"❌ Messaging & Positioning Agent failed: {str(e)}")
        state.add_error("Messaging & Positioning Agent", str(e))
        state.agent_status = "error"
        return state


def extract_market_summary(market_data) -> str:
    """Extract market data summary"""
    if not market_data:
        return "Market data not available"
    
    return f"""
TAM: ${market_data.tam_estimate:,.0f}M
SAM: ${market_data.sam_estimate:,.0f}M
SOM: ${market_data.som_estimate:,.0f}M
Patient Population: {market_data.patient_population:,}
Market Drivers: {market_data.epidemiology.get('market_drivers', [])}
"""


def extract_competitor_summary(competitor_data) -> str:
    """Extract competitor summary"""
    if not competitor_data:
        return "Competitor data not available"
    
    comp_names = [c.competitor_name for c in competitor_data.competitors]
    return f"""
Main Competitors: {', '.join(comp_names)}
Competitive Gaps: {competitor_data.competitive_gaps}
Opportunities: {competitor_data.competitive_opportunities}
"""


def extract_icp_summary(icp_profile) -> str:
    """Extract ICP summary"""
    if not icp_profile:
        return "ICP data not available"
    
    return f"""
Primary ICP: {icp_profile.primary_icp}
Key Personas: {', '.join(icp_profile.key_personas)}
Geography: {', '.join(icp_profile.geography_priority)}
"""


def extract_payer_summary(payer_data) -> str:
    """Extract payer summary"""
    if not payer_data:
        return "Payer data not available"
    
    return f"""
HTA Status: {payer_data.hta_status}
QALY Threshold: £{payer_data.qaly_threshold:,.0f}
Pricing Ceiling: ${payer_data.pricing_ceiling:,.0f}
"""


def get_default_persona_data() -> Dict[str, Any]:
    """Return default persona messaging data"""
    return {
        "role_description": "Senior commercial leader responsible for strategy",
        "pain_points": [
            "Need to differentiate in crowded market",
            "Pressure to maximize revenue",
            "Competition from established players"
        ],
        "value_propositions": [
            "Clear clinical differentiation",
            "Strong payer value proposition",
            "Addressable market opportunity"
        ],
        "objection_responses": {
            "Why you vs competitor?": "Unique mechanism of action with superior efficacy"
        },
        "success_metrics": [
            "Market share gains",
            "Revenue growth",
            "Payer coverage"
        ],
        "engagement_triggers": [
            "Clinical trial readouts",
            "Regulatory decisions",
            "Competitive announcements"
        ]
    }


def get_default_positioning_data() -> Dict[str, Any]:
    """Return default positioning data"""
    return {
        "category_definition": "Addresses an unmet clinical need with a differentiated mechanism of action",
        "positioning_statement": "Offers a distinct mechanism that provides clinical benefit in patient populations with limited current options",
        "key_differentiators": [
            "Targets a specific pathway that current standard-of-care agents do not address",
            "Demonstrates clinical activity in patient sub-populations where existing therapies show limited benefit",
            "Presents a tolerability profile that supports treatment adherence in the target population"
        ],
        "value_propositions": {
            "CCO": "Addresses a patient segment underserved by current options, creating a defensible commercial position",
            "Market Access": "Clinical differentiation in a defined sub-population supports a distinct value story for payers",
            "HEOR": "Efficacy in patients who progress on or are ineligible for current standard of care supports cost-effectiveness modelling",
            "Medical Affairs": "Mechanistic and clinical evidence supports scientific exchange on a clinically meaningful difference"
        },
        "competitive_vs_statements": [
            "Yes, current standard-of-care agents are well-established. And this drug offers a complementary mechanism that may benefit patients who do not respond adequately to existing options.",
            "Yes, established therapies have a strong evidence base. And this drug's distinct mode of action addresses a different biological driver, which may matter for specific patient sub-groups."
        ],
        "messaging_pillars": [
            "Differentiated mechanism of action targeting a clinically validated pathway",
            "Clinical activity in patient sub-populations with limited alternatives",
            "Tolerability data that supports sustained therapy"
        ],
        "common_objections": {
            "Why use this when established options are proven?": "That's a fair point — established therapies work well for many patients. And for the sub-population who don't respond or who are ineligible, this drug's distinct mechanism offers a clinically meaningful alternative worth discussing.",
            "What about the safety profile?": "The tolerability data from clinical studies is worth reviewing together — the adverse event profile is characterised and supports use in the intended patient population."
        }
    }