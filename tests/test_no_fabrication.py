"""
Task 5a: No-fabrication tests.

For each agent that previously emitted fabricated numbers in its fallback path,
verify that when the LLM fails the fallback values are honest empties (None /
empty list / empty dict) and that the relevant provenance key is marked
"unavailable" in state.sources.

No live API or LLM calls are made — the LLM is patched to raise an exception so
the fallback branch is always exercised.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from src.schema.gtm_state import GTMState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_demo_state() -> GTMState:
    """Fresh GTMState for each test — same values as conftest demo_state."""
    return GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")


def _llm_raises(*args, **kwargs):
    """Replacement for get_claude() that returns a mock whose .invoke() raises."""
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = RuntimeError("Mocked LLM failure")
    return mock_llm


# ---------------------------------------------------------------------------
# competitor_analysis_agent — no fabricated competitor name/share/pricing
# ---------------------------------------------------------------------------

class TestCompetitorNoFabrication:
    """Fallback must emit zero competitors, no sentinel values."""

    def _run(self) -> GTMState:
        from src.agents.gtm_agents import competitor_analysis_agent as mod

        state = _make_demo_state()

        # Patch both the Tavily search and the LLM so no network/LLM calls happen
        with (
            patch.object(mod, "tavily_search", return_value={"success": False}),
            patch.object(mod, "search_competitor_news", return_value={"success": False}),
            patch.object(mod, "search_pubmed", return_value={"success": False}),
            patch.object(mod, "get_claude", side_effect=_llm_raises),
        ):
            asyncio.run(mod.competitor_analysis_agent(state))

        return state

    def test_no_competitor_named_competitor_1(self):
        state = self._run()
        if state.competitor_data:
            names = [c.competitor_name for c in state.competitor_data.competitors]
            assert "Competitor 1" not in names, (
                f"Fabricated 'Competitor 1' found in fallback: {names}"
            )

    def test_no_fabricated_market_share(self):
        state = self._run()
        if state.competitor_data:
            shares = [c.market_share for c in state.competitor_data.competitors]
            assert 30.0 not in shares, (
                f"Fabricated market_share 30.0 found in fallback: {shares}"
            )

    def test_no_fabricated_pricing(self):
        state = self._run()
        if state.competitor_data:
            prices = [c.pricing for c in state.competitor_data.competitors]
            assert 50000 not in prices, (
                f"Fabricated pricing 50000 found in fallback: {prices}"
            )

    def test_empty_competitors_list(self):
        state = self._run()
        if state.competitor_data:
            assert state.competitor_data.competitors == [], (
                f"Expected empty competitors on fallback, got: {state.competitor_data.competitors}"
            )

    def test_competitor_market_source_unavailable(self):
        state = self._run()
        assert "competitor.market" in state.sources, (
            "state.sources['competitor.market'] not set on fallback"
        )
        assert state.sources["competitor.market"].tier == "unavailable", (
            f"Expected tier='unavailable', got: {state.sources['competitor.market'].tier}"
        )


# ---------------------------------------------------------------------------
# market_research_agent — no fabricated 0 sentinel for patient_population
# ---------------------------------------------------------------------------

class TestMarketNoFabrication:
    """Fallback must use None (not 0) for numeric market figures."""

    def _run(self) -> GTMState:
        from src.agents.gtm_agents import market_research_agent as mod

        state = _make_demo_state()

        with (
            patch.object(mod, "search_clinical_trials", return_value={"success": False}),
            patch.object(mod, "get_sponsor_trials", return_value={"success": False}),
            patch.object(mod, "search_pubmed", return_value={"success": False}),
            patch.object(mod, "search_clinical_trials_pubs", return_value={"success": False}),
            patch.object(mod, "search_market_analysis", return_value={"success": False}),
            patch.object(mod, "search_clinical_evidence", return_value={"success": False}),
            patch.object(mod, "fetch_epidemiology_data", return_value={"success": False}),
            patch.object(mod, "get_claude", side_effect=_llm_raises),
        ):
            asyncio.run(mod.market_research_agent(state))

        return state

    def test_patient_population_is_none_not_zero(self):
        state = self._run()
        assert state.market_data is not None, "market_data should be set even on fallback"
        assert state.market_data.patient_population is None, (
            f"Expected patient_population=None on fallback, got: {state.market_data.patient_population}"
        )

    def test_tam_is_none_not_zero(self):
        state = self._run()
        assert state.market_data is not None
        assert state.market_data.tam_estimate is None, (
            f"Expected tam_estimate=None on fallback, got: {state.market_data.tam_estimate}"
        )

    def test_sam_is_none_not_zero(self):
        state = self._run()
        assert state.market_data is not None
        assert state.market_data.sam_estimate is None, (
            f"Expected sam_estimate=None on fallback, got: {state.market_data.sam_estimate}"
        )

    def test_market_patient_population_source_unavailable(self):
        state = self._run()
        assert "market.patient_population" in state.sources, (
            "state.sources['market.patient_population'] not set on fallback"
        )
        assert state.sources["market.patient_population"].tier == "unavailable", (
            f"Expected tier='unavailable', got: {state.sources['market.patient_population'].tier}"
        )

    def test_market_tam_source_unavailable(self):
        state = self._run()
        assert "market.tam" in state.sources
        assert state.sources["market.tam"].tier == "unavailable"

    def test_market_market_figure_source_unavailable(self):
        state = self._run()
        assert "market.market_figure" in state.sources
        assert state.sources["market.market_figure"].tier == "unavailable"


# ---------------------------------------------------------------------------
# icp_definition_agent — no fabricated tam_by_segment values
# ---------------------------------------------------------------------------

class TestICPNoFabrication:
    """Fallback must return empty tam_by_segment dict, not fabricated figures."""

    def _run(self) -> GTMState:
        from src.agents.gtm_agents import icp_definition_agent as mod

        state = _make_demo_state()

        with (
            patch.object(mod, "tavily_search", return_value={"success": False}),
            patch.object(mod, "get_claude", side_effect=_llm_raises),
        ):
            asyncio.run(mod.icp_definition_agent(state))

        return state

    def test_no_fabricated_large_pharma_tam(self):
        state = self._run()
        if state.icp_profile:
            segments = state.icp_profile.estimated_tam_by_segment
            assert 75000000 not in segments.values(), (
                f"Fabricated large_pharma TAM 75000000 found in fallback: {segments}"
            )

    def test_no_fabricated_mid_size_tam(self):
        state = self._run()
        if state.icp_profile:
            segments = state.icp_profile.estimated_tam_by_segment
            assert 25000000 not in segments.values(), (
                f"Fabricated mid_size TAM 25000000 found in fallback: {segments}"
            )

    def test_tam_by_segment_is_empty(self):
        state = self._run()
        if state.icp_profile:
            assert state.icp_profile.estimated_tam_by_segment == {}, (
                f"Expected empty tam_by_segment on fallback, got: {state.icp_profile.estimated_tam_by_segment}"
            )

    def test_icp_tam_by_segment_source_unavailable(self):
        state = self._run()
        assert "icp.tam_by_segment" in state.sources, (
            "state.sources['icp.tam_by_segment'] not set on fallback"
        )
        assert state.sources["icp.tam_by_segment"].tier == "unavailable", (
            f"Expected tier='unavailable', got: {state.sources['icp.tam_by_segment'].tier}"
        )


# ---------------------------------------------------------------------------
# synthesis_agent — no fabricated pricing (40000 / 60000)
# ---------------------------------------------------------------------------

class TestSynthesisNoFabrication:
    """Fallback must not emit the sentinel pricing figures 40000 / 60000."""

    def _run(self) -> GTMState:
        from src.agents.gtm_agents import synthesis_agent as mod

        state = _make_demo_state()

        with patch.object(mod, "get_claude", side_effect=_llm_raises):
            asyncio.run(mod.synthesis_agent(state))

        return state

    def test_no_fabricated_price_low(self):
        state = self._run()
        if state.final_gtm_strategy and state.final_gtm_strategy.pricing_range:
            low = state.final_gtm_strategy.pricing_range.get("min")
            assert low != 40000, (
                f"Fabricated price_low 40000 found in fallback: {low}"
            )

    def test_no_fabricated_price_high(self):
        state = self._run()
        if state.final_gtm_strategy and state.final_gtm_strategy.pricing_range:
            high = state.final_gtm_strategy.pricing_range.get("max")
            assert high != 60000, (
                f"Fabricated price_high 60000 found in fallback: {high}"
            )

    def test_pricing_range_values_are_none(self):
        state = self._run()
        if state.final_gtm_strategy and state.final_gtm_strategy.pricing_range:
            low = state.final_gtm_strategy.pricing_range.get("min")
            high = state.final_gtm_strategy.pricing_range.get("max")
            assert low is None and high is None, (
                f"Expected None pricing values on fallback, got: min={low}, max={high}"
            )

    def test_strategy_pricing_source_unavailable(self):
        state = self._run()
        assert "strategy.pricing" in state.sources, (
            "state.sources['strategy.pricing'] not set on fallback"
        )
        assert state.sources["strategy.pricing"].tier == "unavailable", (
            f"Expected tier='unavailable', got: {state.sources['strategy.pricing'].tier}"
        )


# ---------------------------------------------------------------------------
# messaging_agent — confirm no fabricated numeric figures in defaults
# ---------------------------------------------------------------------------

class TestMessagingNoFabrication:
    """messaging_agent defaults are text-only; confirm no numeric fabrication."""

    def test_default_positioning_data_has_no_numbers(self):
        from src.agents.gtm_agents.messaging_agent import get_default_positioning_data
        data = get_default_positioning_data()
        # Walk all leaf values; none should be a raw integer or float
        def _leaves(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    yield from _leaves(v)
            elif isinstance(obj, list):
                for item in obj:
                    yield from _leaves(item)
            else:
                yield obj
        for v in _leaves(data):
            assert not isinstance(v, (int, float)), (
                f"Found numeric value {v!r} in get_default_positioning_data() — "
                "check whether it is a fabricated number"
            )

    def test_default_persona_data_has_no_numbers(self):
        from src.agents.gtm_agents.messaging_agent import get_default_persona_data
        data = get_default_persona_data()
        def _leaves(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    yield from _leaves(v)
            elif isinstance(obj, list):
                for item in obj:
                    yield from _leaves(item)
            else:
                yield obj
        for v in _leaves(data):
            assert not isinstance(v, (int, float)), (
                f"Found numeric value {v!r} in get_default_persona_data() — "
                "check whether it is a fabricated number"
            )


# ---------------------------------------------------------------------------
# payer_intelligence_agent — no fabricated qaly_threshold / pricing_ceiling
# ---------------------------------------------------------------------------

class TestPayerNoFabrication:
    """Fallback must use None (not 30000 / 0) for payer numeric fields."""

    def _run(self) -> GTMState:
        from src.agents.gtm_agents import payer_intelligence_agent as mod

        state = _make_demo_state()

        with (
            patch.object(mod, "search_hta_pubs", return_value={"success": False}),
            patch.object(mod, "search_payer_coverage", return_value={"success": False}),
            patch.object(mod, "search_pricing_information", return_value={"success": False}),
            patch.object(mod, "tavily_search", return_value={"success": False}),
            patch.object(mod, "get_claude", side_effect=_llm_raises),
        ):
            asyncio.run(mod.payer_intelligence_agent(state))

        return state

    def test_qaly_threshold_is_none_not_30000(self):
        state = self._run()
        assert state.payer_data is not None
        assert state.payer_data.qaly_threshold is None, (
            f"Expected qaly_threshold=None on fallback, got: {state.payer_data.qaly_threshold}"
        )

    def test_pricing_ceiling_is_none_not_zero(self):
        state = self._run()
        assert state.payer_data is not None
        assert state.payer_data.pricing_ceiling is None, (
            f"Expected pricing_ceiling=None on fallback, got: {state.payer_data.pricing_ceiling}"
        )

    def test_hta_status_is_none_not_under_review(self):
        state = self._run()
        assert state.payer_data is not None
        assert state.payer_data.hta_status is None, (
            f"Expected hta_status=None on fallback, got: {state.payer_data.hta_status}"
        )

    def test_payer_pricing_ceiling_source_unavailable(self):
        state = self._run()
        assert "payer.pricing_ceiling" in state.sources, (
            "state.sources['payer.pricing_ceiling'] not set on fallback"
        )
        assert state.sources["payer.pricing_ceiling"].tier == "unavailable"

    def test_payer_hta_status_source_unavailable(self):
        state = self._run()
        assert "payer.hta_status" in state.sources, (
            "state.sources['payer.hta_status'] not set on fallback"
        )
        assert state.sources["payer.hta_status"].tier == "unavailable"
