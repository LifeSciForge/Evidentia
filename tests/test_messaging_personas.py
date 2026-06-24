"""
TDD — Task 4 (Stage 3A Speed): Persona messaging collapses 4 LLM calls → 1

Asserts:
  (a) The agent does NOT raise.
  (b) All 4 expected personas are populated in state.messaging_data.value_prop_by_persona.
  (c) Exactly 1 LLM call was made for persona generation (not 4).

We count calls to invoke_with_retry. The messaging agent makes:
  - 1 call for the positioning framework
  - 1 call for all personas  (this is what we changed from 4 → 1)
  - 0 or 1 call for MSL talking points (only when current_doctor is set)

Because current_doctor is NOT set on our demo_state, total expected calls = 2.
The test asserts total_calls == 2 AND that personas are all present, which together
prove persona generation used exactly 1 call (total - 1 positioning = 1 persona call).
"""

import asyncio
import json
import os

import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("TAVILY_API_KEY", "test-key")

from src.schema.gtm_state import (
    GTMState,
    MarketResearchData,
    CompetitorAnalysisData,
    CompetitorData,
    ICPProfile,
    PayerIntelligenceData,
)

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

PERSONAS = [
    "Chief Commercial Officer",
    "Head of Market Access",
    "HEOR Director",
    "Medical Affairs Lead",
]


def _make_persona_dict(persona: str) -> dict:
    """Return a minimal valid persona dict for one persona."""
    return {
        "role_description": f"Role for {persona}",
        "pain_points": ["Pain A", "Pain B"],
        "value_propositions": ["Value A", "Value B"],
        "objection_responses": {"Objection?": "Response."},
        "success_metrics": ["Metric A"],
        "engagement_triggers": ["Trigger A"],
    }


def _all_personas_json() -> str:
    """Return the JSON string the LLM would produce for the single personas call."""
    payload = {p: _make_persona_dict(p) for p in PERSONAS}
    return json.dumps(payload)


def _positioning_json() -> str:
    """Return a minimal valid positioning JSON."""
    return json.dumps({
        "category_definition": "Addresses unmet need",
        "positioning_statement": "A distinct approach for KRAS G12C NSCLC",
        "key_differentiators": ["Sotorasib targets KRAS G12C directly"],
        "value_propositions": {"CCO": "Strong pipeline", "Market Access": "Value story"},
        "competitive_vs_statements": ["Yes, competitor is established. And sotorasib offers X."],
        "messaging_pillars": ["Pillar 1", "Pillar 2"],
        "common_objections": {"Why sotorasib?": "Because it uniquely targets KRAS G12C."},
    })


@pytest.fixture
def state_with_upstream() -> GTMState:
    """GTMState with enough upstream data for messaging_agent to run."""
    state = GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")

    state.market_data = MarketResearchData(
        drug_name="sotorasib",
        indication="KRAS G12C NSCLC",
        tam_estimate=1000.0,
        sam_estimate=500.0,
        som_estimate=100.0,
        patient_population=30000,
        epidemiology={"market_drivers": ["Unmet need in KRAS G12C"]},
    )

    state.competitor_data = CompetitorAnalysisData(
        competitors=[
            CompetitorData(
                competitor_name="adagrasib",
                competitor_indication="KRAS G12C NSCLC",
                market_share=40.0,
            )
        ],
        competitive_gaps={"gap": "No other KRAS G12C agents available"},
        competitive_opportunities=["First-mover advantage"],
    )

    state.icp_profile = ICPProfile(
        primary_icp="Large pharma oncology",
        key_personas=PERSONAS,
        geography_priority=["US"],
    )

    state.payer_data = PayerIntelligenceData(
        hta_status="Under review",
        qaly_threshold=50000.0,
        pricing_ceiling=200000.0,
    )

    return state


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMessagingPersonasSingleCall:
    """All persona messaging now comes from a single LLM round-trip."""

    def test_personas_populated_with_single_llm_call(self, state_with_upstream):
        """
        (a) Agent does not raise.
        (b) All 4 personas present in value_prop_by_persona.
        (c) Only 1 LLM call made for personas (2 total: positioning + all-personas).
        """
        call_count = {"n": 0}
        call_responses = [_positioning_json(), _all_personas_json()]

        def fake_invoke_with_retry(llm, prompt, **kwargs):
            idx = call_count["n"]
            call_count["n"] += 1
            mock_resp = MagicMock()
            mock_resp.content = call_responses[idx] if idx < len(call_responses) else "{}"
            return mock_resp

        with patch("src.agents.gtm_agents.messaging_agent.invoke_with_retry", side_effect=fake_invoke_with_retry):
            result = asyncio.run(
                __import__("src.agents.gtm_agents.messaging_agent", fromlist=["messaging_agent"]).messaging_agent(
                    state_with_upstream
                )
            )

        # (a) No exception — agent ran to completion
        assert result.messaging_data is not None, "messaging_data should be populated"

        # (b) All 4 personas present
        vp = result.messaging_data.value_prop_by_persona
        for persona in PERSONAS:
            assert persona in vp, f"Persona '{persona}' missing from value_prop_by_persona"
            pm = vp[persona]
            assert pm.persona == persona
            assert pm.role_description == f"Role for {persona}"
            assert len(pm.key_pain_points) == 2
            assert len(pm.value_propositions) == 2

        # (c) Exactly 2 total calls: 1 positioning + 1 all-personas (no MSL talking-points
        #     because current_doctor is not set on the fixture)
        assert call_count["n"] == 2, (
            f"Expected 2 total LLM calls (positioning + all-personas), got {call_count['n']}. "
            "The persona loop should make exactly 1 call, not 4."
        )

    def test_fallback_on_invalid_personas_json(self, state_with_upstream):
        """
        When the single personas call returns garbage JSON, each persona falls back
        to the default persona data — agent still does not raise.
        """
        call_count = {"n": 0}

        def fake_invoke_with_retry(llm, prompt, **kwargs):
            call_count["n"] += 1
            mock_resp = MagicMock()
            if call_count["n"] == 1:
                mock_resp.content = _positioning_json()
            else:
                mock_resp.content = "NOT VALID JSON AT ALL"
            return mock_resp

        with patch("src.agents.gtm_agents.messaging_agent.invoke_with_retry", side_effect=fake_invoke_with_retry):
            result = asyncio.run(
                __import__("src.agents.gtm_agents.messaging_agent", fromlist=["messaging_agent"]).messaging_agent(
                    state_with_upstream
                )
            )

        # Agent did not raise — messaging_data present
        assert result.messaging_data is not None

        # All 4 personas still exist (populated from fallback defaults)
        vp = result.messaging_data.value_prop_by_persona
        for persona in PERSONAS:
            assert persona in vp, f"Persona '{persona}' missing even after fallback"

        # Still only 2 LLM calls total
        assert call_count["n"] == 2, (
            f"Even on failure, only 2 LLM calls expected (positioning + one failed personas call), got {call_count['n']}"
        )

    def test_agent_status_completed(self, state_with_upstream):
        """Agent marks itself complete even when it runs the optimised single-call path."""
        def fake_invoke_with_retry(llm, prompt, **kwargs):
            mock_resp = MagicMock()
            # Return positioning JSON for first call, all-personas JSON for second
            if not hasattr(fake_invoke_with_retry, "_called"):
                fake_invoke_with_retry._called = 0
            fake_invoke_with_retry._called += 1
            mock_resp.content = _positioning_json() if fake_invoke_with_retry._called == 1 else _all_personas_json()
            return mock_resp

        with patch("src.agents.gtm_agents.messaging_agent.invoke_with_retry", side_effect=fake_invoke_with_retry):
            result = asyncio.run(
                __import__("src.agents.gtm_agents.messaging_agent", fromlist=["messaging_agent"]).messaging_agent(
                    state_with_upstream
                )
            )

        assert result.agent_status == "completed"
        assert "Messaging & Positioning Agent" in result.agents_completed
