"""
Messaging & Positioning Agent
Creates positioning framework and persona-specific messaging
"""

from typing import Dict, Any
from src.schema.gtm_state import GTMState, MessagingData, PersonaMessaging
from src.core.llm import get_claude
from src.core.logger import get_logger

logger = get_logger(__name__)


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
            
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                positioning_dict = json.loads(json_match.group())
                logger.info("✅ Positioning framework created successfully")
            else:
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
                
                json_match = re.search(r'\{.*\}', persona_text, re.DOTALL)
                if json_match:
                    persona_data = json.loads(json_match.group())
                else:
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
        state.mark_agent_complete("Messaging & Positioning Agent")
        state.agent_status = "completed"
        
        logger.info("✅ Messaging & Positioning Agent completed successfully")
        logger.info(f"📢 Positioning: {messaging_data.positioning_statement[:80]}...")
        logger.info(f"👥 Created messaging for {len(persona_messaging)} personas")
        
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