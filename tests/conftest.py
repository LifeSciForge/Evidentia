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


@pytest.fixture
def demo_state():
    """Standard working demo case used across the suite."""
    return GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")
