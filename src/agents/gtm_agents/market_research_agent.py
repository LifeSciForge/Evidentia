"""
Market Research Agent
Searches for market sizing, clinical trials, and epidemiology data
"""

from typing import Dict, Any
from src.schema.gtm_state import GTMState, MarketResearchData
from src.service.tools.clinical_trials_tools import search_clinical_trials, get_sponsor_trials
from src.service.tools.pubmed_tools import search_pubmed, search_clinical_trials_pubs
from src.service.tools.tavily_tools import tavily_search, search_market_analysis, search_clinical_evidence
from src.service.tools.who_epidemiology_tools import WHOEpidemiologyClient
from src.core.llm import get_claude
from src.core.logger import get_logger
from src.service.validators.json_validator import extract_json_from_text, validate_with_pydantic, MarketResearchResponse

logger = get_logger(__name__)


async def market_research_agent(state: GTMState) -> GTMState:
    """
    Market Research Agent Node
    
    Gathers market sizing, trial data, and epidemiology information
    
    Args:
        state: Current GTM state
        
    Returns:
        Updated GTM state with market_data populated
    """
    
    logger.info(f"🔬 Market Research Agent starting for: {state.drug_name} in {state.indication}")
    state.current_agent = "Market Research Agent"
    state.agent_status = "running"
    
    try:
        # Step 1: Search clinical trials
        logger.info("📋 Searching clinical trials...")
        trials_result = search_clinical_trials(
            drug_name=state.drug_name,
            condition=state.indication,
            max_results=20
        )
        
        trials_data = []
        if trials_result.get("success"):
            trials_data = trials_result.get("trials", [])
            logger.info(f"✅ Found {len(trials_data)} clinical trials")
        else:
            logger.warning(f"⚠️ Clinical trials search failed: {trials_result.get('error')}")
        
        # Step 2: Search PubMed for publications
        logger.info("📚 Searching PubMed publications...")
        pubmed_result = search_pubmed(
            drug_name=state.drug_name,
            condition=state.indication,
            max_results=20
        )
        
        publications = []
        if pubmed_result.get("success"):
            publications = pubmed_result.get("publications", [])
            logger.info(f"✅ Found {len(publications)} publications")
        else:
            logger.warning(f"⚠️ PubMed search failed: {pubmed_result.get('error')}")
        
        
        # Step 2.5: Fetch WHO epidemiology data
        logger.info("🌍 Fetching WHO epidemiology data...")
        who_client = WHOEpidemiologyClient()
        who_data = who_client.get_cancer_data(state.indication)
        who_epidemiology = {}
        if who_data.get("status") == "success":
            who_epidemiology = who_data.get("data", {})
            logger.info(f"✅ WHO epidemiology data retrieved: {who_epidemiology.get('cancer_type')}")
        else:
            logger.warning("⚠️ WHO epidemiology data not available")
        # Step 3: Search for market analysis
        logger.info("📊 Searching market analysis...")
        market_analysis = search_market_analysis(
            indication=state.indication,
            max_results=5
        )
        
        market_insights = ""
        if market_analysis.get("success"):
            market_insights = market_analysis.get("answer", "")
            logger.info("✅ Market analysis data retrieved")
        else:
            logger.warning(f"⚠️ Market analysis search failed")
        
        # Step 4: Search for clinical evidence
        logger.info("🔬 Searching clinical evidence...")
        evidence_result = search_clinical_evidence(
            drug_name=state.drug_name,
            indication=state.indication,
            max_results=5
        )
        
        clinical_evidence = ""
        if evidence_result.get("success"):
            clinical_evidence = evidence_result.get("answer", "")
            logger.info("✅ Clinical evidence retrieved")
        else:
            logger.warning(f"⚠️ Clinical evidence search failed")
        
        # Step 5: Use LLM to synthesize market sizing
        logger.info("🧠 Synthesizing market data with Claude...")
        llm = get_claude()
        
        market_sizing_prompt = f"""
You are a pharma market research analyst. Based on the following data, provide market sizing estimates:

Drug: {state.drug_name}
Indication: {state.indication}

Clinical Trials Found: {len(trials_data)}
Key Trial Data:
{format_trials_summary(trials_data)}

Publications Found: {len(publications)}
Key Publications:
{format_publications_summary(publications)}

Market Analysis Insights:
{market_insights}

Clinical Evidence:
{clinical_evidence}

Please provide:
1. Total Addressable Market (TAM) estimate in USD
2. Serviceable Available Market (SAM) estimate
3. Serviceable Obtainable Market (SOM) estimate
4. Estimated patient population
5. Key market drivers
6. Growth assumptions

Format your response as JSON with these exact keys:
- tam_estimate (float, in millions USD)
- sam_estimate (float, in millions USD)
- som_estimate (float, in millions USD)
- patient_population (int)
- market_drivers (list of strings)
- growth_assumptions (list of strings)
- epidemiology_notes (string)
"""
        
        try:
            response = llm.invoke(market_sizing_prompt)
            response_text = response.content
            try:
                raw = extract_json_from_text(response_text)
                result = validate_with_pydantic(raw, MarketResearchResponse)
                if result.valid:
                    market_data_dict = result.data.model_dump()
                    logger.info("✅ Market data synthesized successfully")
                else:
                    logger.warning(f"⚠️ Validation errors: {result.errors}")
                    market_data_dict = get_default_market_data()
            except ValueError:
                logger.warning("⚠️ Could not extract JSON from LLM response")
                market_data_dict = get_default_market_data()
        except Exception as e:
            logger.error(f"❌ LLM synthesis error: {str(e)}")
            market_data_dict = get_default_market_data()
        
        # Step 6: Create MarketResearchData object
        market_research_data = MarketResearchData(
            drug_name=state.drug_name,
            indication=state.indication,
            tam_estimate=market_data_dict.get("tam_estimate"),
            sam_estimate=market_data_dict.get("sam_estimate"),
            som_estimate=market_data_dict.get("som_estimate"),
            patient_population=market_data_dict.get("patient_population"),
            clinical_trials=trials_data,
            key_publications=format_publications_for_storage(publications),
            market_drivers=market_data_dict.get("market_drivers", []),
            epidemiology={
                "market_drivers": market_data_dict.get("market_drivers", []),
                "growth_assumptions": market_data_dict.get("growth_assumptions", []),
                "notes": market_data_dict.get("epidemiology_notes", "")
            },
            research_notes=f"Analyzed {len(trials_data)} trials and {len(publications)} publications"
        )
        
        # Update state
        state.market_data = market_research_data
        state.mark_agent_complete("Market Research Agent")
        state.agent_status = "completed"
        
        logger.info("✅ Market Research Agent completed successfully")
        logger.info(f"📊 TAM: ${market_research_data.tam_estimate:,.0f}M | SAM: ${market_research_data.sam_estimate:,.0f}M | Patients: {market_research_data.patient_population:,}")
        
        return state
        
    except Exception as e:
        logger.error(f"❌ Market Research Agent failed: {str(e)}")
        state.add_error("Market Research Agent", str(e))
        state.agent_status = "error"
        return state


def format_trials_summary(trials: list) -> str:
    """Format trial data for LLM prompt"""
    if not trials:
        return "No trials found"
    
    summary_parts = []
    for trial in trials[:5]:  # Top 5 trials
        summary_parts.append(
            f"- NCT: {trial.get('nct_id', 'N/A')}, "
            f"Phase: {trial.get('phase', 'N/A')}, "
            f"Status: {trial.get('status', 'N/A')}, "
            f"Enrolled: {trial.get('enrollment', 'N/A')}"
        )
    
    return "\n".join(summary_parts)


def format_publications_summary(publications: list) -> str:
    """Format publication data for LLM prompt"""
    if not publications:
        return "No publications found"
    
    summary_parts = []
    for pub in publications[:5]:  # Top 5 publications
        summary_parts.append(
            f"- {pub.get('title', 'N/A')} "
            f"({pub.get('publication_year', 'N/A')}), "
            f"Journal: {pub.get('journal', 'N/A')}"
        )
    
    return "\n".join(summary_parts)


def format_publications_for_storage(publications: list) -> list:
    """Convert publications to storable format"""
    return [
        {
            "pmid": pub.get("pmid"),
            "title": pub.get("title"),
            "journal": pub.get("journal"),
            "year": pub.get("publication_year"),
            "url": pub.get("url")
        }
        for pub in publications[:10]
    ]


def get_default_market_data() -> Dict[str, Any]:
    """Return default market data when synthesis fails"""
    return {
        "tam_estimate": 0,
        "sam_estimate": 0,
        "som_estimate": 0,
        "patient_population": 0,
        "market_drivers": ["Insufficient data"],
        "growth_assumptions": ["Conservative estimate"],
        "epidemiology_notes": "Requires additional research"
    }