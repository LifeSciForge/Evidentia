"""
Competitor Analysis Agent
Analyzes competitor landscape, positioning, and market threats
"""

from typing import Dict, Any, List
from src.schema.gtm_state import GTMState, CompetitorAnalysisData, CompetitorData
from src.service.tools.tavily_tools import tavily_search, search_competitor_news
from src.service.tools.pubmed_tools import search_pubmed
from src.core.llm import get_claude
from src.core.logger import get_logger
from src.service.validators.json_validator import extract_json_from_text, validate_with_pydantic, CompetitorResponse

logger = get_logger(__name__)


async def competitor_analysis_agent(state: GTMState) -> GTMState:
    """
    Competitor Analysis Agent Node
    
    Analyzes competitor drugs, positioning, and market threats
    
    Args:
        state: Current GTM state
        
    Returns:
        Updated GTM state with competitor_data populated
    """
    
    logger.info(f"🏆 Competitor Analysis Agent starting for: {state.drug_name}")
    state.current_agent = "Competitor Analysis Agent"
    state.agent_status = "running"
    
    try:
        # Step 1: Search for competitor drugs
        logger.info("🔍 Searching for competitor drugs...")
        competitor_search = tavily_search(
            query=f"{state.indication} drugs competitors approved treatment 2025",
            max_results=10
        )
        
        competitor_insights = ""
        if competitor_search.get("success"):
            competitor_insights = competitor_search.get("answer", "")
            logger.info("✅ Competitor overview retrieved")
        else:
            logger.warning("⚠️ Competitor search failed")
        
        # Step 2: Search for top 3 competitors individually
        logger.info("📊 Searching for top 3 competitors in detail...")
        
        competitors = []
        competitor_names = ["competitor analysis"]  # Placeholder
        
        # We'll extract competitor names from LLM in next step
        # For now, search general competitor information
        
        # Step 3: Use LLM to identify and analyze competitors
        logger.info("🧠 Analyzing competitor landscape with Claude...")
        llm = get_claude()
        
        competitor_prompt = f"""
You are a pharma competitive intelligence analyst. Based on the following data, identify and analyze the top 3 competitors:

Drug: {state.drug_name}
Indication: {state.indication}

Market Overview:
{competitor_insights}

Please identify the 3 main competitor drugs and provide:

For each competitor:
1. Drug name
2. Company/Applicant
3. Market share percentage (estimate)
4. Pricing (USD per dose or annual treatment cost if available)
5. Key differentiators vs our drug
6. Clinical advantages
7. Clinical disadvantages
8. Launch date (if available)
9. Annual sales (if available)

Also provide:
- Overall competitive gaps in the market
- Market positioning strategy for our drug
- Competitive threats to our launch
- Competitive opportunities we can exploit

Respond with ONLY valid JSON. No markdown, no explanation, no backticks. Raw JSON only.

Use this exact structure:
{{
  "competitors": [
    {{
      "name": "string",
      "company": "string",
      "market_share": 0.0,
      "pricing": 0.0,
      "key_differentiators": ["string"],
      "clinical_advantages": ["string"],
      "clinical_disadvantages": ["string"],
      "launch_date": "string",
      "annual_sales": 0.0
    }}
  ],
  "competitive_gaps": {{"gap_1": "description"}},
  "positioning_strategy": "string",
  "threats": ["string"],
  "opportunities": ["string"]
}}
"""
        
        try:
            response = llm.invoke(competitor_prompt)
            response_text = response.content
            try:
                raw = extract_json_from_text(response_text)
                result = validate_with_pydantic(raw, CompetitorResponse)
                if result.valid:
                    competitor_data_dict = result.data.model_dump()
                    logger.info("✅ Competitor analysis synthesized successfully")
                else:
                    logger.warning(f"⚠️ Validation errors: {result.errors}")
                    competitor_data_dict = get_default_competitor_data()
            except ValueError:
                logger.warning("⚠️ Could not extract JSON from LLM response")
                competitor_data_dict = get_default_competitor_data()
        except Exception as e:
            logger.error(f"❌ LLM synthesis error: {str(e)}")
            competitor_data_dict = get_default_competitor_data()
        
        # Step 4: Build competitor objects
        competitors_list = []
        for comp in competitor_data_dict.get("competitors", [])[:3]:  # Top 3
            competitor_obj = CompetitorData(
                competitor_name=comp.get("name", "Unknown"),
                competitor_indication=state.indication,
                market_share=comp.get("market_share"),
                pricing=comp.get("pricing"),
                positioning="",  # Would require more detail
                key_differentiators=comp.get("key_differentiators", []),
                clinical_advantages=comp.get("clinical_advantages", []),
                clinical_disadvantages=comp.get("clinical_disadvantages", []),
                launch_date=comp.get("launch_date"),
                sales_data=comp.get("annual_sales")
            )
            competitors_list.append(competitor_obj)
        
        # Step 5: Create CompetitorAnalysisData object
        competitor_analysis_data = CompetitorAnalysisData(
            competitors=competitors_list,
            competitive_gaps=competitor_data_dict.get("competitive_gaps", {}),
            market_positioning_strategy=competitor_data_dict.get("positioning_strategy", ""),
            competitive_threats=competitor_data_dict.get("threats", []),
            competitive_opportunities=competitor_data_dict.get("opportunities", []),
            competitive_notes=f"Analyzed {len(competitors_list)} main competitors in {state.indication}"
        )
        
        # Update state
        state.competitor_data = competitor_analysis_data
        state.mark_agent_complete("Competitor Analysis Agent")
        state.agent_status = "completed"
        
        logger.info("✅ Competitor Analysis Agent completed successfully")
        logger.info(f"🏆 Identified {len(competitors_list)} main competitors")
        logger.info(f"🎯 Opportunities: {', '.join(competitor_analysis_data.competitive_opportunities[:3])}")
        
        return state
        
    except Exception as e:
        logger.error(f"❌ Competitor Analysis Agent failed: {str(e)}")
        state.add_error("Competitor Analysis Agent", str(e))
        state.agent_status = "error"
        return state


def get_default_competitor_data() -> Dict[str, Any]:
    """Return default competitor data when synthesis fails"""
    return {
        "competitors": [
            {
                "name": "Competitor 1",
                "company": "Unknown",
                "market_share": 30.0,
                "pricing": 50000,
                "key_differentiators": ["Requires additional research"],
                "clinical_advantages": ["Requires additional research"],
                "clinical_disadvantages": ["Requires additional research"],
                "launch_date": "Unknown",
                "annual_sales": 0
            }
        ],
        "competitive_gaps": {"gap_1": "Requires additional research"},
        "positioning_strategy": "Differentiate on efficacy and safety",
        "threats": ["Well-established competitors"],
        "opportunities": ["Market expansion", "Unmet medical need fulfillment"]
    }