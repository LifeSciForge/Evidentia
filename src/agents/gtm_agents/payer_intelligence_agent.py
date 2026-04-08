"""
Payer Intelligence Agent
Searches for HTA decisions, reimbursement criteria, and payer feedback
"""

from typing import Dict, Any
from src.schema.gtm_state import GTMState, PayerIntelligenceData
from src.service.tools.pubmed_tools import search_hta_pubs
from src.service.tools.tavily_tools import tavily_search, search_payer_coverage, search_pricing_information
from src.core.llm import get_claude
from src.core.logger import get_logger
from src.service.validators.json_validator import extract_json_from_text, validate_with_pydantic, PayerResponse

logger = get_logger(__name__)


async def payer_intelligence_agent(state: GTMState) -> GTMState:
    """
    Payer Intelligence Agent Node
    
    Gathers HTA decisions, reimbursement criteria, and payer feedback
    
    Args:
        state: Current GTM state
        
    Returns:
        Updated GTM state with payer_data populated
    """
    
    logger.info(f"💰 Payer Intelligence Agent starting for: {state.drug_name}")
    state.current_agent = "Payer Intelligence Agent"
    state.agent_status = "running"
    
    try:
        # Step 1: Search HTA publications
        logger.info("📋 Searching HTA publications...")
        hta_result = search_hta_pubs(
            drug_name=state.drug_name,
            max_results=10
        )
        
        hta_publications = []
        if hta_result.get("success"):
            hta_publications = hta_result.get("publications", [])
            logger.info(f"✅ Found {len(hta_publications)} HTA publications")
        else:
            logger.warning(f"⚠️ HTA search failed")
        
        # Step 2: Search payer coverage information
        logger.info("🏥 Searching payer coverage information...")
        payer_coverage = search_payer_coverage(
            drug_name=state.drug_name,
            region="US",
            max_results=5
        )
        
        coverage_insights = ""
        if payer_coverage.get("success"):
            coverage_insights = payer_coverage.get("answer", "")
            logger.info("✅ Payer coverage data retrieved")
        else:
            logger.warning("⚠️ Payer coverage search failed")
        
        # Step 3: Search pricing information
        logger.info("💵 Searching pricing information...")
        pricing_result = search_pricing_information(
            drug_name=state.drug_name,
            max_results=5
        )
        
        pricing_insights = ""
        if pricing_result.get("success"):
            pricing_insights = pricing_result.get("answer", "")
            logger.info("✅ Pricing data retrieved")
        else:
            logger.warning("⚠️ Pricing search failed")
        
        # Step 4: Search for NICE/EMA/ICER decisions
        logger.info("🔍 Searching regulatory payer decisions...")
        regulatory_search = tavily_search(
            query=f"{state.drug_name} NICE EMA ICER decision reimbursement 2025 2026",
            max_results=5
        )
        
        regulatory_insights = ""
        if regulatory_search.get("success"):
            regulatory_insights = regulatory_search.get("answer", "")
            logger.info("✅ Regulatory payer data retrieved")
        else:
            logger.warning("⚠️ Regulatory search failed")
        
        # Step 5: Use LLM to synthesize payer strategy
        logger.info("🧠 Synthesizing payer intelligence with Claude...")
        llm = get_claude()
        
        payer_prompt = f"""
You are a pharma reimbursement and market access strategist. Based on the following data, provide payer intelligence:

Drug: {state.drug_name}
Indication: {state.indication}

HTA Publications Found: {len(hta_publications)}
Key HTA Insights:
{format_hta_summary(hta_publications)}

Payer Coverage Insights:
{coverage_insights}

Pricing Information:
{pricing_insights}

Regulatory Payer Decisions:
{regulatory_insights}

Please provide reimbursement strategy recommendations:
1. Current HTA status (NICE, EMA, ICER if available)
2. Likely QALY threshold for reimbursement
3. Pricing ceiling based on market comparisons
4. Key reimbursement barriers
5. Reimbursement solutions and access programs
6. Geographic prioritization for payer targeting
7. Managed access program recommendations

Respond with ONLY valid JSON. No markdown, no explanation, no backticks. Raw JSON only.

Keys required:
- hta_status (string: e.g., "Recommended", "Not recommended", "Under review")
- qaly_threshold (float, in pounds/euros per QALY)
- pricing_ceiling (float, in USD)
- reimbursement_barriers (list of strings)
- reimbursement_solutions (list of strings)
- geography_priority (list of strings: e.g., ["US", "EU", "UK"])
- managed_access_programs (list of strings)
- payer_feedback_summary (string)
"""
        
        try:
            response = llm.invoke(payer_prompt)
            response_text = response.content
            try:
                raw = extract_json_from_text(response_text)
                result = validate_with_pydantic(raw, PayerResponse)
                if result.valid:
                    payer_data_dict = result.data.model_dump()
                    logger.info("✅ Payer intelligence synthesized successfully")
                else:
                    logger.warning(f"⚠️ Validation errors: {result.errors}")
                    payer_data_dict = get_default_payer_data()
            except ValueError:
                logger.warning("⚠️ Could not extract JSON from LLM response")
                payer_data_dict = get_default_payer_data()
        except Exception as e:
            logger.error(f"❌ LLM synthesis error: {str(e)}")
            payer_data_dict = get_default_payer_data()
        
        # Step 6: Create PayerIntelligenceData object
        payer_intelligence_data = PayerIntelligenceData(
            hta_status=payer_data_dict.get("hta_status"),
            reimbursement_criteria=payer_data_dict.get("reimbursement_solutions", []),
            qaly_threshold=payer_data_dict.get("qaly_threshold"),
            pricing_ceiling=payer_data_dict.get("pricing_ceiling"),
            access_restrictions=payer_data_dict.get("reimbursement_barriers", []),
            comparator_drugs=[],  # Would require more detailed search
            payer_feedback={
                "us": "Research ongoing",
                "eu": "Research ongoing",
                "uk": "Research ongoing"
            },
            pricing_signals={
                "us_market_price": payer_data_dict.get("pricing_ceiling"),
                "geography_priority": payer_data_dict.get("geography_priority", [])
            },
            payer_notes=payer_data_dict.get("payer_feedback_summary", "")
        )
        
        # Update state
        state.payer_data = payer_intelligence_data
        state.mark_agent_complete("Payer Intelligence Agent")
        state.agent_status = "completed"
        
        logger.info("✅ Payer Intelligence Agent completed successfully")
        logger.info(f"💰 HTA Status: {payer_intelligence_data.hta_status} | QALY Threshold: £{payer_intelligence_data.qaly_threshold:,.0f}")
        
        return state
        
    except Exception as e:
        logger.error(f"❌ Payer Intelligence Agent failed: {str(e)}")
        state.add_error("Payer Intelligence Agent", str(e))
        state.agent_status = "error"
        return state


def format_hta_summary(publications: list) -> str:
    """Format HTA publication data for LLM prompt"""
    if not publications:
        return "No HTA publications found"
    
    summary_parts = []
    for pub in publications[:5]:  # Top 5
        summary_parts.append(
            f"- {pub.get('title', 'N/A')} "
            f"({pub.get('publication_year', 'N/A')})"
        )
    
    return "\n".join(summary_parts)


def get_default_payer_data() -> Dict[str, Any]:
    """Return default payer data when synthesis fails"""
    return {
        "hta_status": "Under review",
        "qaly_threshold": 30000,
        "pricing_ceiling": 0,
        "reimbursement_barriers": ["Insufficient data"],
        "reimbursement_solutions": ["Requires additional HTA submission"],
        "geography_priority": ["US", "EU", "UK"],
        "managed_access_programs": ["Risk-sharing agreement"],
        "payer_feedback_summary": "Requires additional research"
    }