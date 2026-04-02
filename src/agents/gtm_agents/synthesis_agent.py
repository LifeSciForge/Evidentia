"""
Synthesis Agent
Assembles all agent outputs into final GTM strategy
"""

from typing import Dict, Any
from src.schema.gtm_state import GTMState, GTMStrategy
from src.schema.gtm_output import GTMOutputDocument
from src.core.llm import get_claude
from src.core.logger import get_logger
from src.service.validators.json_validator import extract_json_from_text
from src.schema.agent_messages import create_agent_message, MESSAGE_TYPES
from datetime import datetime

logger = get_logger(__name__)


async def synthesis_agent(state: GTMState) -> GTMState:
    """
    Synthesis Agent Node
    
    Assembles all outputs from 5 agents into final GTM strategy
    
    Args:
        state: Current GTM state (with all agent outputs populated)
        
    Returns:
        Updated GTM state with final_gtm_strategy populated
    """
    
    logger.info(f"🎯 Synthesis Agent starting for: {state.drug_name}")
    state.current_agent = "Synthesis Agent"
    state.agent_status = "running"
    
    try:
        # Validate all agents completed
        if not all([state.market_data, state.payer_data, state.competitor_data, 
                   state.icp_profile, state.messaging_data]):
            logger.warning("⚠️ Some agent outputs missing. Proceeding with available data.")
        
        # Extract summaries from all agents
        market_context = format_market_context(state.market_data)
        payer_context = format_payer_context(state.payer_data)
        competitor_context = format_competitor_context(state.competitor_data)
        icp_context = format_icp_context(state.icp_profile)
        messaging_context = format_messaging_context(state.messaging_data)
        
        # Step 1: Generate final GTM strategy with Claude
        logger.info("🧠 Generating final GTM strategy with Claude...")
        llm = get_claude()
        
        strategy_prompt = f"""
You are a senior pharma GTM strategist. Synthesize all research into a comprehensive GTM strategy:

DRUG: {state.drug_name}
INDICATION: {state.indication}

=== MARKET RESEARCH ===
{market_context}

=== PAYER INTELLIGENCE ===
{payer_context}

=== COMPETITIVE ANALYSIS ===
{competitor_context}

=== ICP DEFINITION ===
{icp_context}

=== POSITIONING & MESSAGING ===
{messaging_context}

Now create a complete GTM strategy with:

1. Executive Summary:
   - Strategy title
   - Key insight
   - Recommended approach
   - Expected launch window
   
2. Market Opportunity:
   - TAM/SAM/SOM sizing
   - Market growth drivers
   - Key assumptions
   
3. Target Segment Definition:
   - Primary segment profile
   - Segment sizing
   - Penetration opportunity
   
4. Positioning Framework:
   - Category positioning
   - Key differentiators
   - Brand personality
   
5. Channel Strategy (multi-channel mix):
   - Primary channel
   - Secondary channels
   - Channel allocation %
   - Success metrics per channel
   
6. Pricing Strategy:
   - Recommended price point
   - Rationale
   - Competitive pricing analysis
   - Patient access programs
   
7. Reimbursement Strategy:
   - HTA approach
   - Payer targeting
   - Value story
   - Managed access programs
   
8. Commercial Timeline:
   - Pre-launch (months)
   - Hard launch (activities)
   - Scaling phase (6-12 months post-launch)
   - Mature market phase
   
9. Resource Requirements:
   - Sales team size needed
   - Marketing budget
   - Market access investment
   - Key partnerships
   
10. Success Metrics & KPIs:
    - Market share targets
    - Revenue targets
    - Payer coverage targets
    - Key regional metrics
    
11. Key Risks & Mitigation:
    - Market risk: mitigation
    - Competitive risk: mitigation
    - Regulatory risk: mitigation
    - Payer risk: mitigation
    - Commercial risk: mitigation
    
12. Competitive Moat:
    - How we sustain advantage long-term

Format response as JSON with keys:
- executive_summary (object)
- market_opportunity (object)
- target_segment (object)
- positioning (object)
- channel_strategy (object)
- pricing_strategy (object)
- reimbursement_strategy (object)
- timeline (object)
- resources (object)
- success_metrics (list)
- risks_and_mitigations (object)
- competitive_moat (string)
"""
        
        try:
            response = llm.invoke(strategy_prompt)
            response_text = response.content
            try:
                strategy_dict = extract_json_from_text(response_text)
                logger.info("✅ GTM strategy synthesized successfully")
            except ValueError:
                logger.warning("⚠️ Could not extract JSON from LLM response")
                strategy_dict = get_default_strategy_data()
        except Exception as e:
            logger.error(f"❌ LLM strategy synthesis error: {str(e)}")
            strategy_dict = get_default_strategy_data()
        
        # Step 2: Build GTMStrategy object
        gtm_strategy = GTMStrategy(
            executive_summary=format_string(strategy_dict.get("executive_summary", {}).get("summary", "")),
            market_overview=format_string(strategy_dict.get("market_opportunity", {}).get("overview", "")),
            market_sizing={
                "tam": state.market_data.tam_estimate if state.market_data else 0,
                "sam": state.market_data.sam_estimate if state.market_data else 0,
                "som": state.market_data.som_estimate if state.market_data else 0
            },
            target_segment=format_string(strategy_dict.get("target_segment", {}).get("segment", "")),
            positioning_framework=state.messaging_data.positioning_statement if state.messaging_data else "",
            key_messages=state.messaging_data.messaging_pillars if state.messaging_data else [],
            channel_strategy=strategy_dict.get("channel_strategy", {}),
            pricing_strategy=format_string(strategy_dict.get("pricing_strategy", {}).get("approach", "")),
            pricing_range={
                "min": strategy_dict.get("pricing_strategy", {}).get("price_low", 0),
                "max": strategy_dict.get("pricing_strategy", {}).get("price_high", 0)
            },
            reimbursement_strategy=format_string(strategy_dict.get("reimbursement_strategy", {}).get("approach", "")),
            commercial_timeline=format_timeline(strategy_dict.get("timeline", {})),
            resource_requirements=strategy_dict.get("resources", {}),
            success_metrics=strategy_dict.get("success_metrics", []),
            key_risks=list(strategy_dict.get("risks_and_mitigations", {}).keys()),
            risk_mitigation=strategy_dict.get("risks_and_mitigations", {}),
            competitive_moat=strategy_dict.get("competitive_moat", "Differentiated clinical profile"),
            synthesis_notes=f"Synthesis of 6-agent analysis: Market Research, Payer Intelligence, Competitor Analysis, ICP Definition, Messaging, and GTM Strategy"
        )
        
        # Update state
        state.final_gtm_strategy = gtm_strategy
        state.completed_at = datetime.now().isoformat()
        state.mark_agent_complete("Synthesis Agent")
        state.agent_status = "completed"

        # Audit trail (activates agent_messages.py schemas — SKILL_05)
        msg = create_agent_message(
            agent_name="Synthesis Agent",
            message_type=MESSAGE_TYPES["SYNTHESIS_COMPLETE"],
            content={"drug": state.drug_name, "indication": state.indication},
            confidence_score=0.9,
        )
        if not hasattr(state, "agent_messages") or state.agent_messages is None:
            state.agent_messages = []
        state.agent_messages.append(msg)
        
        logger.info("✅ Synthesis Agent completed successfully")
        logger.info(f"🎯 Final GTM Strategy Generated")
        logger.info(f"📊 Market Opportunity: ${state.final_gtm_strategy.market_sizing.get('tam', 0):,.0f}M TAM")
        logger.info(f"👥 All 6 agents completed: {state.agents_completed}")
        
        return state
        
    except Exception as e:
        logger.error(f"❌ Synthesis Agent failed: {str(e)}")
        state.add_error("Synthesis Agent", str(e))
        state.agent_status = "error"
        return state


def format_market_context(market_data) -> str:
    """Format market data for synthesis prompt"""
    if not market_data:
        return "Market data not available"
    
    return f"""
TAM: ${market_data.tam_estimate:,.0f}M
SAM: ${market_data.sam_estimate:,.0f}M
SOM: ${market_data.som_estimate:,.0f}M
Patient Population: {market_data.patient_population:,}
Clinical Trials Analyzed: {len(market_data.clinical_trials)}
Key Publications: {len(market_data.key_publications)}
Market Drivers: {market_data.epidemiology.get('market_drivers', [])}
"""


def format_payer_context(payer_data) -> str:
    """Format payer data for synthesis prompt"""
    if not payer_data:
        return "Payer data not available"
    
    return f"""
HTA Status: {payer_data.hta_status}
QALY Threshold: £{payer_data.qaly_threshold:,.0f}
Pricing Ceiling: ${payer_data.pricing_ceiling:,.0f}
Reimbursement Criteria: {payer_data.reimbursement_criteria}
Access Restrictions: {payer_data.access_restrictions}
"""


def format_competitor_context(competitor_data) -> str:
    """Format competitor data for synthesis prompt"""
    if not competitor_data:
        return "Competitor data not available"
    
    comp_summary = "\n".join([
        f"- {c.competitor_name} (${c.pricing:,.0f}, {c.market_share}% share)"
        for c in competitor_data.competitors[:3]
    ])
    
    return f"""
Main Competitors:
{comp_summary}

Competitive Gaps: {competitor_data.competitive_gaps}
Market Opportunities: {competitor_data.competitive_opportunities}
"""


def format_icp_context(icp_profile) -> str:
    """Format ICP data for synthesis prompt"""
    if not icp_profile:
        return "ICP data not available"
    
    return f"""
Primary ICP: {icp_profile.primary_icp}
Secondary ICP: {icp_profile.secondary_icp}
Key Personas: {', '.join(icp_profile.key_personas)}
Geography Priority: {', '.join(icp_profile.geography_priority)}
Urgency Triggers: {icp_profile.urgency_triggers}
"""


def format_messaging_context(messaging_data) -> str:
    """Format messaging data for synthesis prompt"""
    if not messaging_data:
        return "Messaging data not available"
    
    return f"""
Positioning: {messaging_data.positioning_statement}
Key Differentiators: {messaging_data.key_differentiators}
Messaging Pillars: {messaging_data.messaging_pillars}
Competitive Positioning: {messaging_data.competitive_vs_statements}
"""


def format_string(value: Any) -> str:
    """Safely format any value as string"""
    if isinstance(value, (dict, list)):
        return str(value)
    return str(value) if value else ""


def format_timeline(timeline_dict: Dict[str, Any]) -> list:
    """Format timeline data"""
    if not timeline_dict:
        return []
    
    phases = []
    for phase_name, phase_data in timeline_dict.items():
        if isinstance(phase_data, dict):
            phases.append({
                "phase": phase_name,
                "duration": phase_data.get("duration", ""),
                "key_activities": phase_data.get("activities", [])
            })
    
    return phases


def get_default_strategy_data() -> Dict[str, Any]:
    """Return default strategy data when synthesis fails"""
    return {
        "executive_summary": {
            "summary": "Comprehensive GTM strategy for market entry"
        },
        "market_opportunity": {
            "overview": "Significant market opportunity in target indication"
        },
        "target_segment": {
            "segment": "Large pharma and biotech companies"
        },
        "positioning": {
            "statement": "First-in-class solution"
        },
        "channel_strategy": {
            "primary": "Direct commercial",
            "secondary": ["Digital marketing", "Medical education"]
        },
        "pricing_strategy": {
            "approach": "Value-based pricing",
            "price_low": 40000,
            "price_high": 60000
        },
        "reimbursement_strategy": {
            "approach": "HTA submission with health economics"
        },
        "timeline": {
            "pre_launch": "6 months",
            "launch": "Month 7-9",
            "scaling": "Month 10-12"
        },
        "resources": {
            "sales_team": 50,
            "marketing_budget": 5000000
        },
        "success_metrics": [
            "Market share target",
            "Revenue target",
            "Payer coverage"
        ],
        "risks_and_mitigations": {
            "Competitive threat": "Differentiation strategy"
        },
        "competitive_moat": "Patent protection and clinical evidence"
    }