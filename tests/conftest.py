"""Shared test fixtures.

Dummy secrets are set at import time so any module that constructs Settings
(src.core.settings) imports cleanly without real API keys. Tests never use
live keys and never make live API/LLM calls.
"""
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("TAVILY_API_KEY", "test-key")

import pytest
from src.schema.gtm_state import GTMState


@pytest.fixture(autouse=True)
def _no_retry_sleep(monkeypatch):
    """Neutralize tenacity's backoff sleep so retry paths don't slow the suite.

    The LLM/tool retry wrappers use real exponential backoff in production; tests
    that exercise failure/fallback paths would otherwise sleep seconds each. We
    only care that retries HAPPEN (asserted via call counts), not that they wait.
    """
    monkeypatch.setattr("tenacity.nap.time.sleep", lambda *_a, **_k: None)


@pytest.fixture
def demo_state():
    """Standard working demo case used across the suite."""
    return GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")
