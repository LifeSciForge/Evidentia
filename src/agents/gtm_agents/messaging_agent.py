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
You are a pharma brand positioning strategist. Create a comprehensive positioning framework:

Drug: {state.drug_name}
Indication: {state.indication}

Market Context:
{market_summary}

Competitive Context:
{competitor_summary}

ICP Context:
{icp_summary}

Payer Context:
{payer_summary}

Please create a positioning framework with:

1. Category Definition:
   - How do we define this therapeutic category?
   - What is the unmet need we address?
   
2. Positioning Statement:
   - Our unique position in the market
   - Why we matter to customers
   
3. Key Differentiators (vs competitors):
   - Clinical
   - Commercial
   - Economic/Payer value
   
4. Value Propositions by Persona:
   - For CCO: Commercial impact
   - For Market Access: Payer value
   - For HEOR: Health economics benefit
   - For Medical Affairs: Clinical evidence
   
5. Competitive Messaging:
   - "vs Competitor A" positioning
   - "vs Competitor B" positioning
   - "vs Competitor C" positioning
   
6. Messaging Pillars (3-5 core themes):
   - Pillar 1: ...
   - Pillar 2: ...
   
7. Common Objections & Responses:
   - Objection 1: Response strategy
   - Objection 2: Response strategy

Format response as JSON with keys:
- category_definition (string)
- positioning_statement (string)
- key_differentiators (list of strings)
- value_propositions (object with persona names as keys)
- competitive_vs_statements (list of strings)
- messaging_pillars (list of strings)
- common_objections (object with objection as key, response as value)
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

Format as JSON with keys:
- role_description
- pain_points (list)
- value_propositions (list)
- objection_responses (object)
- success_metrics (list)
- engagement_triggers (list)
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
        "category_definition": "First-in-class therapeutic solution",
        "positioning_statement": "The premium choice for clinical efficacy and payer value",
        "key_differentiators": [
            "Superior clinical efficacy",
            "Favorable safety profile",
            "Strong health economic value"
        ],
        "value_propositions": {
            "CCO": "Revenue upside opportunity",
            "Market Access": "Strong payer case",
            "HEOR": "Cost-effective solution"
        },
        "competitive_vs_statements": [
            "vs Competitor A: Better safety profile",
            "vs Competitor B: Superior efficacy"
        ],
        "messaging_pillars": [
            "Clinical leadership",
            "Payer value",
            "Patient impact"
        ],
        "common_objections": {
            "What about competitor X?": "Our differentiated mechanism provides superior outcomes"
        }
    }