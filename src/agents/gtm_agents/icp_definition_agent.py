"""
ICP Definition Agent
Defines Ideal Customer Profile based on market and competitive data
"""

from typing import Dict, Any
from src.schema.gtm_state import GTMState, ICPProfile
from src.service.tools.tavily_tools import tavily_search
from src.core.llm import get_claude
from src.core.logger import get_logger
from src.utils.formatters import safe_join, safe_format_list
from src.service.validators.json_validator import extract_json_from_text

logger = get_logger(__name__)


async def icp_definition_agent(state: GTMState) -> GTMState:
    """
    ICP Definition Agent Node
    
    Defines Ideal Customer Profile (buying personas, company size, geography, etc.)
    
    Args:
        state: Current GTM state (with market_data and competitor_data populated)
        
    Returns:
        Updated GTM state with icp_profile populated
    """
    
    logger.info(f"👥 ICP Definition Agent starting for: {state.drug_name}")
    state.current_agent = "ICP Definition Agent"
    state.agent_status = "running"
    
    try:
        # Validate we have prerequisite data
        if not state.market_data or not state.competitor_data:
            logger.warning("⚠️ Market or competitor data missing. Using defaults.")
        
        # Extract key data for ICP analysis
        market_context = {
            "tam": state.market_data.tam_estimate if state.market_data else 0,
            "patient_population": state.market_data.patient_population if state.market_data else 0,
            "epidemiology": state.market_data.epidemiology if state.market_data else {}
        }
        
        competitor_context = {
            "competitor_count": len(state.competitor_data.competitors) if state.competitor_data else 0,
            "gaps": state.competitor_data.competitive_gaps if state.competitor_data else {},
            "opportunities": state.competitor_data.competitive_opportunities if state.competitor_data else []
        }
        
        payer_context = {
            "hta_status": state.payer_data.hta_status if state.payer_data else "Unknown",
            "qaly_threshold": state.payer_data.qaly_threshold if state.payer_data else 30000
        }
        
        # Step 1: Use LLM to define ICP
        logger.info("🧠 Defining ICP with Claude...")
        llm = get_claude()
        
        icp_prompt = f"""
You are a pharma GTM strategist. Based on the market analysis, define the Ideal Customer Profile (ICP) for sales and market access teams:

Drug: {state.drug_name}
Indication: {state.indication}

Market Context:
- TAM: ${market_context['tam']:,.0f}M
- Patient Population: {market_context['patient_population']:,}
- Market Drivers: {safe_join(market_context['epidemiology'].get('market_drivers', []))}

Competitive Context:
- Competitor Count: {competitor_context['competitor_count']}
- Market Gaps: {competitor_context['gaps']}
- Opportunities: {safe_join(competitor_context['opportunities'])}

Payer Context:
- HTA Status: {payer_context['hta_status']}
- QALY Threshold: £{payer_context['qaly_threshold']:,.0f}

Please define:

1. Primary ICP:
   - Company size (revenue range)
   - Company type (integrated pharma, biotech, CRO, etc.)
   - Therapeutic area focus
   - Geographic focus
   - Key decision-makers (roles)
   
2. Secondary ICP:
   - Alternative company profiles
   - Expansion opportunities
   
3. Buying Committee:
   - Chief Commercial Officer (influence: 0-100)
   - Head of Market Access (influence: 0-100)
   - HEOR Director (influence: 0-100)
   - Medical Affairs Lead (influence: 0-100)
   - Payer Relations Manager (influence: 0-100)
   
4. Urgency Triggers:
   - What makes them buy NOW vs later?
   - Regulatory milestones
   - Competitive threats
   - Clinical evidence needs
   
5. Geography Prioritization:
   - Rank: US, EU, UK, APAC, Rest of World
   - Rationale for each
   
6. TAM by Segment:
   - Estimate addressable market by primary segment
   - Estimate by secondary segment

Respond with ONLY valid JSON. No markdown, no explanation, no backticks. Raw JSON only.

Keys required:
- primary_icp (object)
- secondary_icp (object)
- buying_committee (object with role names as keys and influence scores as string values)
- urgency_triggers (list of strings)
- geography_priority (list of strings)
- tam_by_segment (object with segment names as keys and USD values as floats)
- icp_summary (string)
"""
        
        try:
            response = llm.invoke(icp_prompt)
            response_text = response.content
            try:
                icp_data_dict = extract_json_from_text(response_text)
                logger.info("✅ ICP definition synthesized successfully")
            except ValueError:
                logger.warning("⚠️ Could not extract JSON from LLM response")
                icp_data_dict = get_default_icp_data()
        except Exception as e:
            logger.error(f"❌ LLM synthesis error: {str(e)}")
            icp_data_dict = get_default_icp_data()
        
        # Step 4: Build ICP profile object
        primary_icp = icp_data_dict.get("primary_icp", {})
        secondary_icp = icp_data_dict.get("secondary_icp", {})
        
        icp_profile = ICPProfile(
            primary_icp=format_icp_description(primary_icp),
            secondary_icp=format_icp_description(secondary_icp),
            company_size_range=primary_icp.get("company_size", "Large pharma (>$5B revenue)"),
            therapeutic_areas_focus=safe_format_list(primary_icp.get("therapeutic_areas", [state.indication])),
            key_personas=[
                "Chief Commercial Officer",
                "Head of Market Access",
                "HEOR Director",
                "Medical Affairs Lead"
            ],
            buying_committee=icp_data_dict.get("buying_committee", get_default_buying_committee()),
            urgency_triggers=safe_format_list(icp_data_dict.get("urgency_triggers", [])),
            geography_priority=safe_format_list(icp_data_dict.get("geography_priority", ["US", "EU", "UK"])),
            estimated_tam_by_segment=icp_data_dict.get("tam_by_segment", {}),
            icp_notes=icp_data_dict.get("icp_summary", "")
        )
        
        # Update state
        state.icp_profile = icp_profile
        state.mark_agent_complete("ICP Definition Agent")
        state.agent_status = "completed"
        
        logger.info("✅ ICP Definition Agent completed successfully")
        logger.info(f"👥 Primary ICP: {icp_profile.primary_icp}")
        logger.info(f"🌍 Geography Priority: {safe_join(icp_profile.geography_priority)}")
        logger.info(f"📊 Key Personas: {safe_join(icp_profile.key_personas)}")
        
        return state
        
    except Exception as e:
        logger.error(f"❌ ICP Definition Agent failed: {str(e)}")
        state.add_error("ICP Definition Agent", str(e))
        state.agent_status = "error"
        return state


def format_icp_description(icp_dict: Dict[str, Any]) -> str:
    """Format ICP dictionary into readable description"""
    if not icp_dict:
        return "Large pharma with >$5B revenue"
    
    parts = []
    if "company_type" in icp_dict:
        parts.append(str(icp_dict["company_type"]))
    if "company_size" in icp_dict:
        parts.append(str(icp_dict["company_size"]))
    if "therapeutic_areas" in icp_dict:
        therapeutic_areas = safe_format_list(icp_dict['therapeutic_areas'])
        if therapeutic_areas:
            parts.append(f"focused on {', '.join(therapeutic_areas)}")
    
    return " | ".join(parts) if parts else "Pharma/Biotech company"


def get_default_buying_committee() -> Dict[str, str]:
    """Return default buying committee structure"""
    return {
        "Chief Commercial Officer": "90",
        "Head of Market Access": "85",
        "HEOR Director": "80",
        "Medical Affairs Lead": "75",
        "Payer Relations Manager": "70"
    }


def get_default_icp_data() -> Dict[str, Any]:
    """Return default ICP data when synthesis fails"""
    return {
        "primary_icp": {
            "company_type": "Integrated Pharma",
            "company_size": "Large (>$5B revenue)",
            "therapeutic_areas": ["Oncology", "Respiratory"]
        },
        "secondary_icp": {
            "company_type": "Mid-size Biotech",
            "company_size": "$1B-$5B revenue"
        },
        "buying_committee": get_default_buying_committee(),
        "urgency_triggers": [
            "Upcoming clinical readout",
            "Competitive threat",
            "Payer feedback requiring solution"
        ],
        "geography_priority": ["US", "EU", "UK", "APAC"],
        "tam_by_segment": {
            "large_pharma": 75000000,
            "mid_size": 25000000
        },
        "icp_summary": "Large integrated pharma with commercial scale and payer relationships"
    }
