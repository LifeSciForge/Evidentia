"""Regression: synthesis must survive an LLM failure without crashing on
formatting None values (production model-404 cascade -> default strategy with
None market figures -> `:,.0f` on None). See settings model fix + line 229 guard.
"""
import asyncio
from unittest.mock import patch

from src.schema.gtm_state import GTMState
from src.agents.gtm_agents.synthesis_agent import synthesis_agent


def test_synthesis_survives_llm_failure_without_format_crash():
    state = GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")

    def boom(*_a, **_k):
        raise Exception("Error code: 404 - model: claude-sonnet-4-20250514")

    # Simulate every synthesis LLM call failing (as the retired model did in prod).
    with patch("src.agents.gtm_agents.synthesis_agent.invoke_with_retry", side_effect=boom):
        result = asyncio.run(synthesis_agent(state))

    # The bug raised `unsupported format string passed to NoneType.__format__`
    # before returning. It must now complete and hand back a state.
    assert result is not None
