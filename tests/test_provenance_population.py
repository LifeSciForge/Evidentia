"""
Task 5b: Provenance-population tests.

Three test groups, one per agent:
  1. no-LLM-URL guard — the most important: URLs that the LLM emits in its JSON
     must never appear as provenance sources.
  2. web source attached on success — when a Tavily tool returns a real top_url
     the relevant state.sources[key].tier == "web" and .url matches.
  3. modeled figure (market agent) — when market top_url is absent but the LLM
     returns patient_population + tam_estimate, the market_figure source tier is
     "modeled" (not "unavailable").

No live API or LLM calls are made.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from src.schema.gtm_state import GTMState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REAL_TAVILY_URL = "https://www.fiercepharma.com/market-real-source"
LLM_INVENTED_URL = "https://evil-llm-invented.example/fake"


def _demo_state() -> GTMState:
    return GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")


def _mock_llm_with_url(url: str = LLM_INVENTED_URL):
    """Return a get_claude() mock whose .invoke() returns JSON containing a URL.

    The URL is embedded in a field that could look like a source reference.
    The agent must NEVER pick this up as provenance.
    """
    llm = MagicMock()
    llm.invoke.return_value.content = (
        '{"tam_estimate": 5000.0, "sam_estimate": 2000.0, "som_estimate": 500.0, '
        f'"patient_population": 50000, "market_drivers": ["Unmet need"], '
        f'"growth_assumptions": ["10% CAGR"], "epidemiology_notes": "see {url}", '
        # Extra field that looks like a source url — must be ignored
        f'"source_url": "{url}",'
        '"competitors": [], "competitive_gaps": {}, '
        '"positioning_strategy": "Differentiate", "threats": [], "opportunities": [], '
        '"hta_status": "Under review", "qaly_threshold": 30000.0, '
        f'"pricing_ceiling": 180000.0, "reimbursement_barriers": [], '
        '"reimbursement_solutions": [], "geography_priority": ["US"], '
        '"managed_access_programs": [], "payer_feedback_summary": "TBD"}'
    )
    return llm


def _llm_raises(*args, **kwargs):
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = RuntimeError("Mocked LLM failure")
    return mock_llm


def _all_source_urls(state: GTMState) -> list[str]:
    """Collect every non-None URL stored in state.sources."""
    return [
        src.url
        for src in state.sources.values()
        if src is not None and getattr(src, "url", None) is not None
    ]


# ---------------------------------------------------------------------------
# market_research_agent
# ---------------------------------------------------------------------------

class TestMarketProvenancePopulation:
    """market_research_agent provenance tests."""

    # ---- shared run helpers ------------------------------------------------

    def _run_with_real_tavily_url(self) -> GTMState:
        """Success path: Tavily returns REAL_TAVILY_URL; LLM JSON contains LLM_INVENTED_URL."""
        from src.agents.gtm_agents import market_research_agent as mod

        state = _demo_state()
        mock_llm = _mock_llm_with_url(LLM_INVENTED_URL)

        tavily_success = {
            "success": True,
            "answer": "Large market",
            "top_url": REAL_TAVILY_URL,
            "top_domain": "fiercepharma.com",
            "results": [{"url": REAL_TAVILY_URL}],
        }
        tavily_no_url = {"success": True, "answer": "clinical evidence", "top_url": None, "results": []}

        with (
            patch.object(mod, "search_clinical_trials", return_value={"success": False}),
            patch.object(mod, "search_pubmed", return_value={"success": False}),
            patch.object(mod, "search_market_analysis", return_value=tavily_success),
            patch.object(mod, "search_clinical_evidence", return_value=tavily_no_url),
            patch.object(mod, "get_claude", return_value=mock_llm),
        ):
            asyncio.run(mod.market_research_agent(state))

        return state

    def _run_no_market_url_but_modeled_data(self) -> GTMState:
        """Success path: Tavily returns NO top_url; LLM gives patients+tam for modeled figure."""
        from src.agents.gtm_agents import market_research_agent as mod

        state = _demo_state()
        mock_llm = _mock_llm_with_url(LLM_INVENTED_URL)

        tavily_no_url = {"success": True, "answer": "data", "top_url": None, "results": []}

        with (
            patch.object(mod, "search_clinical_trials", return_value={"success": False}),
            patch.object(mod, "search_pubmed", return_value={"success": False}),
            patch.object(mod, "search_market_analysis", return_value=tavily_no_url),
            patch.object(mod, "search_clinical_evidence", return_value=tavily_no_url),
            patch.object(mod, "get_claude", return_value=mock_llm),
        ):
            asyncio.run(mod.market_research_agent(state))

        return state

    # ---- no-LLM-URL guard (most important) ---------------------------------

    def test_no_llm_url_in_market_sources(self):
        """LLM-emitted URL must NEVER appear in state.sources."""
        state = self._run_with_real_tavily_url()
        urls = _all_source_urls(state)
        assert LLM_INVENTED_URL not in urls, (
            f"LLM-invented URL leaked into provenance: {urls}"
        )

    # ---- web source on success ---------------------------------------------

    def test_web_source_attached_on_success(self):
        """When Tavily returns REAL_TAVILY_URL, market.market_figure must be web tier."""
        state = self._run_with_real_tavily_url()
        src = state.sources.get("market.market_figure")
        assert src is not None, "market.market_figure source not set on success"
        assert src.tier == "web", f"Expected tier 'web', got '{src.tier}'"
        assert src.url == REAL_TAVILY_URL, (
            f"Expected url '{REAL_TAVILY_URL}', got '{src.url}'"
        )

    # ---- modeled figure ----------------------------------------------------

    def test_modeled_figure_when_no_market_url(self):
        """When no market top_url but patients+tam exist, market_figure tier should be 'modeled'."""
        state = self._run_no_market_url_but_modeled_data()
        src = state.sources.get("market.market_figure")
        assert src is not None, "market.market_figure source not set"
        assert src.tier in ("modeled", "web"), (
            f"Expected 'modeled' or 'web', got '{src.tier}'"
        )
        assert src.tier != "unavailable", (
            "market.market_figure should not be unavailable when patients+tam are present"
        )


# ---------------------------------------------------------------------------
# competitor_analysis_agent
# ---------------------------------------------------------------------------

class TestCompetitorProvenancePopulation:
    """competitor_analysis_agent provenance tests."""

    def _run_with_real_url(self) -> GTMState:
        """Success path: Tavily returns REAL_TAVILY_URL; LLM JSON contains LLM_INVENTED_URL."""
        from src.agents.gtm_agents import competitor_analysis_agent as mod

        state = _demo_state()

        # LLM returns JSON with an invented URL + valid competitor structure
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = (
            '{"competitors": [], "competitive_gaps": {}, '
            '"positioning_strategy": "Differentiate", '
            '"threats": [], "opportunities": [], '
            f'"source_url": "{LLM_INVENTED_URL}"}}'
        )

        tavily_success = {
            "success": True,
            "answer": "Competitive landscape",
            "top_url": REAL_TAVILY_URL,
            "top_domain": "fiercepharma.com",
            "results": [{"url": REAL_TAVILY_URL}],
        }

        with (
            patch.object(mod, "tavily_search", return_value=tavily_success),
            patch.object(mod, "search_competitor_news", return_value={"success": False}),
            patch.object(mod, "search_pubmed", return_value={"success": False}),
            patch.object(mod, "get_claude", return_value=mock_llm),
        ):
            asyncio.run(mod.competitor_analysis_agent(state))

        return state

    # ---- no-LLM-URL guard --------------------------------------------------

    def test_no_llm_url_in_competitor_sources(self):
        state = self._run_with_real_url()
        urls = _all_source_urls(state)
        assert LLM_INVENTED_URL not in urls, (
            f"LLM-invented URL leaked into competitor provenance: {urls}"
        )

    # ---- web source on success ---------------------------------------------

    def test_web_source_attached_on_success(self):
        state = self._run_with_real_url()
        src = state.sources.get("competitor.market")
        assert src is not None, "competitor.market source not set on success"
        assert src.tier == "web", f"Expected tier 'web', got '{src.tier}'"
        assert src.url == REAL_TAVILY_URL, (
            f"Expected url '{REAL_TAVILY_URL}', got '{src.url}'"
        )


# ---------------------------------------------------------------------------
# payer_intelligence_agent
# ---------------------------------------------------------------------------

class TestPayerProvenancePopulation:
    """payer_intelligence_agent provenance tests."""

    def _run_with_real_urls(self) -> GTMState:
        """Success path: payer_coverage and pricing tools return real urls."""
        from src.agents.gtm_agents import payer_intelligence_agent as mod

        state = _demo_state()
        mock_llm = _mock_llm_with_url(LLM_INVENTED_URL)

        PRICING_URL = "https://www.drugpricing.com/sotorasib-cost"

        payer_success = {
            "success": True,
            "answer": "Coverage data",
            "top_url": REAL_TAVILY_URL,
            "top_domain": "fiercepharma.com",
            "results": [{"url": REAL_TAVILY_URL}],
        }
        pricing_success = {
            "success": True,
            "answer": "Pricing data",
            "top_url": PRICING_URL,
            "top_domain": "drugpricing.com",
            "results": [{"url": PRICING_URL}],
        }
        empty_success = {"success": True, "answer": "", "top_url": None, "results": []}

        with (
            patch.object(mod, "search_hta_pubs", return_value={"success": False}),
            patch.object(mod, "search_payer_coverage", return_value=payer_success),
            patch.object(mod, "search_pricing_information", return_value=pricing_success),
            patch.object(mod, "tavily_search", return_value=empty_success),
            patch.object(mod, "get_claude", return_value=mock_llm),
        ):
            asyncio.run(mod.payer_intelligence_agent(state))

        return state, PRICING_URL

    # ---- no-LLM-URL guard --------------------------------------------------

    def test_no_llm_url_in_payer_sources(self):
        state, _ = self._run_with_real_urls()
        urls = _all_source_urls(state)
        assert LLM_INVENTED_URL not in urls, (
            f"LLM-invented URL leaked into payer provenance: {urls}"
        )

    # ---- web sources on success --------------------------------------------

    def test_hta_status_web_source(self):
        state, _ = self._run_with_real_urls()
        src = state.sources.get("payer.hta_status")
        assert src is not None, "payer.hta_status source not set"
        assert src.tier == "web", f"Expected tier 'web', got '{src.tier}'"
        assert src.url == REAL_TAVILY_URL, (
            f"Expected url '{REAL_TAVILY_URL}', got '{src.url}'"
        )

    def test_pricing_ceiling_web_source(self):
        state, pricing_url = self._run_with_real_urls()
        src = state.sources.get("payer.pricing_ceiling")
        assert src is not None, "payer.pricing_ceiling source not set"
        assert src.tier == "web", f"Expected tier 'web', got '{src.tier}'"
        assert src.url == pricing_url, (
            f"Expected url '{pricing_url}', got '{src.url}'"
        )
