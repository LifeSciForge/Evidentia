"""
Messaging & Positioning Agent
Creates positioning framework and persona-specific messaging
"""

import asyncio
from typing import Dict, Any, Optional
from src.schema.gtm_state import (
    GTMState, MessagingData, PersonaMessaging,
    MSLTalkingPoints, ClinicalPillar, ClinicalEvidence,
    KeyDifferentiator, AnticipatedObjection, Guardrail,
)
from src.core.llm import get_claude, invoke_with_retry
from src.core.logger import get_logger
from src.service.validators.json_validator import (
    extract_json_from_text, validate_with_pydantic,
    PositioningResponse, PersonaResponse, AllPersonasResponse,
)
from src.prompts import load_prompt

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

    hospital_or_default = state.current_hospital or "Not specified"
    prompt = load_prompt("messaging_talking_points").format(
        current_doctor=state.current_doctor,
        hospital_or_default=hospital_or_default,
        drug_name=state.drug_name,
        indication=state.indication,
        trials=trials,
        publications=publications,
    )

    try:
        response = await asyncio.to_thread(invoke_with_retry, llm, prompt)
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
        
        positioning_prompt = load_prompt("messaging_positioning").format(
            drug_name=state.drug_name,
            indication=state.indication,
            market_summary=market_summary,
            competitor_summary=competitor_summary,
            icp_summary=icp_summary,
            payer_summary=payer_summary,
        )
        
        try:
            response = await asyncio.to_thread(invoke_with_retry, llm, positioning_prompt)
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

        # Step 2: Generate persona-specific messaging — ONE call for all personas
        logger.info("👥 Generating messaging for all personas in a single LLM call...")

        personas = ["Chief Commercial Officer", "Head of Market Access", "HEOR Director", "Medical Affairs Lead"]

        personas_str = ', '.join(personas)
        positioning_statement = positioning_dict.get('positioning_statement', '')
        key_differentiators = positioning_dict.get('key_differentiators', [])
        all_personas_prompt = load_prompt("messaging_personas").format(
            drug_name=state.drug_name,
            personas_str=personas_str,
            positioning_statement=positioning_statement,
            key_differentiators=key_differentiators,
        )

        persona_messaging = {}
        try:
            personas_response = await asyncio.to_thread(invoke_with_retry, llm, all_personas_prompt)
            personas_text = personas_response.content
            try:
                raw = extract_json_from_text(personas_text)
                all_personas = AllPersonasResponse.from_flat_dict(raw)
                for persona in personas:
                    persona_model = all_personas.personas.get(persona, PersonaResponse())
                    persona_data = persona_model.model_dump()
                    persona_messaging[persona] = PersonaMessaging(
                        persona=persona,
                        role_description=persona_data.get("role_description", ""),
                        key_pain_points=persona_data.get("pain_points", []),
                        value_propositions=persona_data.get("value_propositions", []),
                        objection_responses=persona_data.get("objection_responses", {}),
                        success_metrics=persona_data.get("success_metrics", []),
                        engagement_triggers=persona_data.get("engagement_triggers", []),
                    )
                logger.info(f"✅ All-personas call succeeded — {len(all_personas.personas)} personas parsed")
            except (ValueError, Exception) as parse_err:
                logger.warning(f"⚠️ Could not parse all-personas JSON ({parse_err}); using defaults for all personas")
                for persona in personas:
                    persona_data = get_default_persona_data()
                    persona_messaging[persona] = PersonaMessaging(
                        persona=persona,
                        role_description=persona_data.get("role_description", ""),
                        key_pain_points=persona_data.get("pain_points", []),
                        value_propositions=persona_data.get("value_propositions", []),
                        objection_responses=persona_data.get("objection_responses", {}),
                        success_metrics=persona_data.get("success_metrics", []),
                        engagement_triggers=persona_data.get("engagement_triggers", []),
                    )
        except Exception as e:
            logger.error(f"❌ All-personas LLM call failed: {e}; using defaults for all personas")
            for persona in personas:
                persona_data = get_default_persona_data()
                persona_messaging[persona] = PersonaMessaging(
                    persona=persona,
                    role_description=persona_data.get("role_description", ""),
                    key_pain_points=persona_data.get("pain_points", []),
                    value_propositions=persona_data.get("value_propositions", []),
                    objection_responses=persona_data.get("objection_responses", {}),
                    success_metrics=persona_data.get("success_metrics", []),
                    engagement_triggers=persona_data.get("engagement_triggers", []),
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

    tam_str = f"${market_data.tam_estimate:,.0f}M" if market_data.tam_estimate is not None else "N/A"
    sam_str = f"${market_data.sam_estimate:,.0f}M" if market_data.sam_estimate is not None else "N/A"
    som_str = f"${market_data.som_estimate:,.0f}M" if market_data.som_estimate is not None else "N/A"
    pop_str = f"{market_data.patient_population:,}" if market_data.patient_population is not None else "N/A"
    return f"""
TAM: {tam_str}
SAM: {sam_str}
SOM: {som_str}
Patient Population: {pop_str}
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

    qaly_str = f"£{payer_data.qaly_threshold:,.0f}" if payer_data.qaly_threshold is not None else "N/A"
    ceiling_str = f"${payer_data.pricing_ceiling:,.0f}" if payer_data.pricing_ceiling is not None else "N/A"
    return f"""
HTA Status: {payer_data.hta_status}
QALY Threshold: {qaly_str}
Pricing Ceiling: {ceiling_str}
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