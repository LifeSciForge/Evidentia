"""
Tests for ICP and Synthesis agent JSON validation wiring.

Verifies that:
- ICPResponse and StrategyResponse schemas validate well-formed dicts
- Structurally-broken / empty dicts still produce a ValidationResult without raising
- When LLM returns junk, icp_definition_agent and synthesis_agent fall back gracefully
  (no raise, state fields populated with sensible defaults)

No live API or LLM calls are made.
"""

import asyncio
import os
from unittest.mock import MagicMock, patch

import pytest

# Ensure dummy keys before any src import
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("TAVILY_API_KEY", "test-key")

from src.schema.gtm_state import GTMState
from src.service.validators.json_validator import (
    ICPResponse,
    StrategyResponse,
    validate_with_pydantic,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def demo_state():
    """Standard working demo case used across the suite."""
    return GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")


# ---------------------------------------------------------------------------
# Schema-level tests (direct validate_with_pydantic)
# ---------------------------------------------------------------------------


class TestICPResponseSchema:
    def test_empty_dict_is_valid_with_defaults(self):
        """All fields are Optional / have defaults — empty dict must pass."""
        result = validate_with_pydantic({}, ICPResponse)
        assert result.valid is True
        assert result.data is not None

    def test_well_formed_dict_validates_true(self):
        well_formed = {
            "primary_icp": {"company_type": "Pharma", "company_size": ">$5B"},
            "secondary_icp": {"company_type": "Biotech"},
            "buying_committee": {"CCO": "90", "Head of Market Access": "85"},
            "urgency_triggers": ["Regulatory milestone", "Competitive threat"],
            "geography_priority": ["US", "EU", "UK"],
            "tam_by_segment": {"large_pharma": 75000000},
            "icp_summary": "Large integrated pharma",
        }
        result = validate_with_pydantic(well_formed, ICPResponse)
        assert result.valid is True
        data = result.data.model_dump()
        assert data["icp_summary"] == "Large integrated pharma"
        assert data["geography_priority"] == ["US", "EU", "UK"]

    def test_structurally_broken_list_field_coerces_or_returns_invalid(self):
        """A non-list value for a list field should either coerce or return valid=False.
        Either outcome is acceptable as long as validate_with_pydantic never raises."""
        broken = {"urgency_triggers": "not-a-list"}
        # Must not raise
        result = validate_with_pydantic(broken, ICPResponse)
        assert isinstance(result.valid, bool)


class TestStrategyResponseSchema:
    def test_empty_dict_is_valid_with_defaults(self):
        """All fields are Optional / have defaults — empty dict must pass."""
        result = validate_with_pydantic({}, StrategyResponse)
        assert result.valid is True
        assert result.data is not None

    def test_well_formed_dict_validates_true(self):
        well_formed = {
            "executive_summary": {"summary": "Comprehensive strategy"},
            "market_opportunity": {"overview": "Large opportunity"},
            "target_segment": {"segment": "Large pharma"},
            "positioning": {"statement": "First-in-class"},
            "channel_strategy": {"primary": "Direct"},
            "pricing_strategy": {"approach": "Value-based", "price_low": 40000, "price_high": 60000},
            "reimbursement_strategy": {"approach": "HTA submission"},
            "timeline": {"pre_launch": "6 months"},
            "resources": {"sales_team": 50},
            "success_metrics": ["Market share target", "Revenue target"],
            "risks_and_mitigations": {"Competitive threat": "Differentiation"},
            "competitive_moat": "Patent protection",
        }
        result = validate_with_pydantic(well_formed, StrategyResponse)
        assert result.valid is True
        data = result.data.model_dump()
        assert data["competitive_moat"] == "Patent protection"
        assert data["success_metrics"] == ["Market share target", "Revenue target"]

    def test_structurally_broken_list_field_never_raises(self):
        """Non-list value for success_metrics — must not raise."""
        broken = {"success_metrics": "not-a-list"}
        result = validate_with_pydantic(broken, StrategyResponse)
        assert isinstance(result.valid, bool)


# ---------------------------------------------------------------------------
# Agent-level tests — mock LLM, confirm no raise + fallback shape
# ---------------------------------------------------------------------------


class TestICPAgentWithJunkLLMOutput:
    """icp_definition_agent must not raise when LLM returns non-JSON."""

    def test_junk_llm_output_no_raise_state_populated(self, demo_state):
        from src.agents.gtm_agents.icp_definition_agent import icp_definition_agent

        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "not json at all — garbage output"

        with patch("src.agents.gtm_agents.icp_definition_agent.get_claude", return_value=mock_llm):
            result_state = asyncio.run(icp_definition_agent(demo_state))

        # Must not raise; icp_profile must be populated (fallback data applied)
        assert result_state.icp_profile is not None
        assert result_state.icp_profile.primary_icp != ""
        assert result_state.icp_profile.geography_priority  # non-empty list

    def test_valid_json_llm_output_populates_state(self, demo_state):
        from src.agents.gtm_agents.icp_definition_agent import icp_definition_agent

        valid_json_response = """{
            "primary_icp": {"company_type": "Pharma", "company_size": ">$5B", "therapeutic_areas": ["Oncology"]},
            "secondary_icp": {"company_type": "Biotech"},
            "buying_committee": {"CCO": "90"},
            "urgency_triggers": ["Regulatory milestone"],
            "geography_priority": ["US", "EU"],
            "tam_by_segment": {"large_pharma": 75000000},
            "icp_summary": "Large integrated pharma with scale"
        }"""

        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = valid_json_response

        with patch("src.agents.gtm_agents.icp_definition_agent.get_claude", return_value=mock_llm):
            result_state = asyncio.run(icp_definition_agent(demo_state))

        assert result_state.icp_profile is not None
        assert "Pharma" in result_state.icp_profile.primary_icp
        assert result_state.icp_profile.icp_notes == "Large integrated pharma with scale"


class TestSynthesisAgentWithJunkLLMOutput:
    """synthesis_agent must not raise when LLM returns non-JSON."""

    def test_junk_llm_output_no_raise_state_populated(self, demo_state):
        from src.agents.gtm_agents.synthesis_agent import synthesis_agent

        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = "not json at all — garbage output"

        with patch("src.agents.gtm_agents.synthesis_agent.get_claude", return_value=mock_llm):
            result_state = asyncio.run(synthesis_agent(demo_state))

        # Must not raise; final_gtm_strategy must be populated (fallback data applied)
        assert result_state.final_gtm_strategy is not None
        assert result_state.final_gtm_strategy.competitive_moat != ""

    def test_valid_json_llm_output_populates_strategy(self, demo_state):
        from src.agents.gtm_agents.synthesis_agent import synthesis_agent

        valid_json_response = """{
            "executive_summary": {"summary": "Strong market entry strategy"},
            "market_opportunity": {"overview": "$2B addressable market"},
            "target_segment": {"segment": "Top 20 oncology centers"},
            "positioning": {"statement": "First oral KRAS inhibitor"},
            "channel_strategy": {"primary": "Direct MSL engagement"},
            "pricing_strategy": {"approach": "Value-based", "price_low": 150000, "price_high": 200000},
            "reimbursement_strategy": {"approach": "Parallel HTA submissions"},
            "timeline": {"pre_launch": {"duration": "6 months", "activities": ["KOL mapping"]}},
            "resources": {"sales_team": 30, "marketing_budget": 5000000},
            "success_metrics": ["20% market share in year 1", "80% payer coverage"],
            "risks_and_mitigations": {"Competitive threat": "Differentiated efficacy data"},
            "competitive_moat": "First-mover advantage and patent protection"
        }"""

        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = valid_json_response

        with patch("src.agents.gtm_agents.synthesis_agent.get_claude", return_value=mock_llm):
            result_state = asyncio.run(synthesis_agent(demo_state))

        assert result_state.final_gtm_strategy is not None
        assert result_state.final_gtm_strategy.competitive_moat == "First-mover advantage and patent protection"
        assert result_state.final_gtm_strategy.executive_summary == "Strong market entry strategy"
