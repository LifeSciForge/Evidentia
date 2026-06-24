"""Tests for src/core/llm.py — per-call config cache, settings model, retry wrapper.

All tests are fast: no real network calls, no real sleeps.
"""
from unittest.mock import MagicMock
import pytest
from src.core.llm import get_claude, invoke_with_retry, LLMManager


def test_get_claude_caches_per_config():
    LLMManager._claude_instances = {}
    a = get_claude(temperature=0.2)
    b = get_claude(temperature=0.2)
    c = get_claude(temperature=0.7)
    assert a is b           # same config -> cached
    assert a is not c       # different temperature -> different instance


def test_get_claude_uses_settings_default_model(monkeypatch):
    from src.core import settings as settings_mod
    LLMManager._claude_instances = {}
    monkeypatch.setattr(settings_mod.settings, "DEFAULT_MODEL", "claude-test-xyz")
    inst = get_claude(temperature=0.1)
    assert inst.model == "claude-test-xyz"   # ChatAnthropic exposes .model


def test_invoke_with_retry_succeeds_after_transient(monkeypatch):
    monkeypatch.setattr("tenacity.nap.sleep", lambda *_: None)  # no real backoff sleep
    llm = MagicMock()
    ok = MagicMock(); ok.content = "ok"
    llm.invoke.side_effect = [Exception("rate limit"), ok]
    out = invoke_with_retry(llm, "p")
    assert out.content == "ok"
    assert llm.invoke.call_count == 2


def test_invoke_with_retry_reraises_after_exhaustion(monkeypatch):
    monkeypatch.setattr("tenacity.nap.sleep", lambda *_: None)
    llm = MagicMock(); llm.invoke.side_effect = Exception("boom")
    with pytest.raises(Exception):
        invoke_with_retry(llm, "p")
    assert llm.invoke.call_count == 3
