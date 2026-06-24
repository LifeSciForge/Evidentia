"""
Market Research Agent
Searches for market sizing, clinical trials, and epidemiology data
"""

from typing import Dict, Any
from src.schema.gtm_state import (
    GTMState, MarketResearchData, unavailable,
    web_source, verified_source, modeled, SourcedValue, Source,
)
from src.service.tools.clinical_trials_tools import search_clinical_trials, get_sponsor_trials
from src.service.tools.pubmed_tools import search_pubmed, search_clinical_trials_pubs
from src.service.tools.tavily_tools import tavily_search, search_market_analysis, search_clinical_evidence
from src.service.tools.epidemiology_tools import fetch_epidemiology_data
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
        _pubmed_top_url: str | None = None
        if pubmed_result.get("success"):
            publications = pubmed_result.get("publications", [])
            logger.info(f"✅ Found {len(publications)} publications")
            # Capture the URL of the first publication for provenance (comes from the tool, not LLM)
            if publications:
                _pubmed_top_url = publications[0].get("url")
        else:
            logger.warning(f"⚠️ PubMed search failed: {pubmed_result.get('error')}")


        # Step 3: Search for market analysis
        logger.info("📊 Searching market analysis...")
        market_analysis = search_market_analysis(
            indication=state.indication,
            max_results=5
        )

        market_insights = ""
        _market_top_url: str | None = None
        if market_analysis.get("success"):
            market_insights = market_analysis.get("answer", "")
            _market_top_url = market_analysis.get("top_url")  # from tool, never LLM
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

Respond with ONLY valid JSON. No markdown, no explanation, no backticks. Raw JSON only.

Keys required:
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
                    # --- Attach REAL provenance from tool results (never from LLM text) ---
                    _attach_market_sources(state, market_data_dict,
                                           _market_top_url, _pubmed_top_url)
                else:
                    logger.warning(f"⚠️ Validation errors: {result.errors}")
                    market_data_dict = get_default_market_data()
                    _mark_market_unavailable(state, "validation failed")
            except ValueError:
                logger.warning("⚠️ Could not extract JSON from LLM response")
                market_data_dict = get_default_market_data()
                _mark_market_unavailable(state, "JSON extraction failed")
        except Exception as e:
            logger.error(f"❌ LLM synthesis error: {str(e)}")
            market_data_dict = get_default_market_data()
            _mark_market_unavailable(state, f"LLM error: {str(e)}")
        
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
        tam_str = f"${market_research_data.tam_estimate:,.0f}M" if market_research_data.tam_estimate is not None else "N/A"
        sam_str = f"${market_research_data.sam_estimate:,.0f}M" if market_research_data.sam_estimate is not None else "N/A"
        pop_str = f"{market_research_data.patient_population:,}" if market_research_data.patient_population is not None else "N/A"
        logger.info(f"📊 TAM: {tam_str} | SAM: {sam_str} | Patients: {pop_str}")
        
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


def _attach_market_sources(
    state: GTMState,
    market_data_dict: Dict[str, Any],
    market_top_url: str | None,
    pubmed_top_url: str | None,
) -> None:
    """Attach provenance from REAL tool results only — never from LLM text.

    Rules:
    - market.market_figure: prefer Tavily market-analysis url (web_source).
      If absent but we have a patient_population and a tam_estimate, build a
      modeled SourcedValue and record its source.
    - market.patient_population: prefer PubMed url (verified_source); fall
      back to Tavily market url if no pubmed url; else leave unchanged (5a
      already set unavailable on the fallback path, so only reach here on
      success, meaning we may simply not have a url for this specific field).
    """
    try:
        pat_pop = market_data_dict.get("patient_population")
        tam = market_data_dict.get("tam_estimate")

        # --- market.patient_population ---
        if pubmed_top_url:
            state.sources["market.patient_population"] = verified_source(
                "PubMed", pubmed_top_url
            )
        elif market_top_url:
            state.sources["market.patient_population"] = web_source(market_top_url)
        # else: no url available for this field on this run; leave as-is

        # --- market.market_figure ---
        if market_top_url:
            # A real market-analysis URL was returned by the tool
            state.sources["market.market_figure"] = web_source(market_top_url)
        elif pat_pop and tam:
            # No published market figure URL, but we can model from sourced inputs
            pop_source_obj: Source = state.sources.get(
                "market.patient_population",
                unavailable("patient population source unknown"),
            )
            pop_sv = SourcedValue(value=pat_pop, source=pop_source_obj,
                                  display=str(pat_pop))
            # tam is in millions; build a rough annual-cost proxy label
            display_str = f"~${tam:,.0f}M (modeled)"
            mv = modeled(value=tam, display=display_str, inputs=[pop_sv])
            state.sources["market.market_figure"] = mv.source
        # else: leave unavailable (set by 5a fallback or not yet set)

    except Exception:
        # Never crash the agent due to provenance bookkeeping
        pass


def _mark_market_unavailable(state: GTMState, reason: str) -> None:
    """Record market numeric fields as unavailable in the provenance side-map."""
    note = f"Not available from sources — {reason}"
    state.sources["market.patient_population"] = unavailable(note)
    state.sources["market.tam"] = unavailable(note)
    state.sources["market.sam"] = unavailable(note)
    state.sources["market.market_figure"] = unavailable(note)


def get_default_market_data() -> Dict[str, Any]:
    """Return honest empty fallback when market synthesis fails.

    Numeric fields are None (not 0) so the UI can distinguish "no data" from
    a genuine zero value.  Text guidance fields are kept as-is.
    """
    return {
        "tam_estimate": None,
        "sam_estimate": None,
        "som_estimate": None,
        "patient_population": None,
        "market_drivers": ["Insufficient data"],
        "growth_assumptions": ["Conservative estimate"],
        "epidemiology_notes": "Requires additional research"
    }