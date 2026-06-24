"""
tests/test_cache.py
TDD tests for the brief-level cache in GTMWorkflow.run.

Tests prove that:
1. A repeat brief (same inputs) is served from cache — graph runs once.
2. Different inputs each run the graph independently.
3. Error states are NOT cached.
4. The progress_callback is still invoked on the live (non-cached) path.
"""

import asyncio
from unittest.mock import patch, MagicMock

from src.agents.gtm_workflow import GTMWorkflow
from src.schema.gtm_state import GTMState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_astream(state_factory=None):
    """Return an async-generator factory whose snapshots come from state_factory.

    state_factory(initial: GTMState) -> GTMState  defaults to returning
    a copy with drug_name / indication from initial.
    """
    def fake_astream(initial, stream_mode="values"):
        async def _gen():
            if state_factory is not None:
                yield state_factory(initial)
            else:
                yield GTMState(
                    drug_name=initial.drug_name,
                    indication=initial.indication,
                )
        return _gen()
    return fake_astream


# ---------------------------------------------------------------------------
# Test 1: identical inputs — graph runs only once
# ---------------------------------------------------------------------------

def test_repeat_brief_served_from_cache():
    """Second run with identical inputs must hit cache; graph not re-invoked."""
    wf = GTMWorkflow()
    # Use a fresh CacheManager so prior test state doesn't bleed through
    wf.cache.clear_all()

    fake_final = GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")

    async def fake_astream(initial, stream_mode="values"):
        yield fake_final

    with patch.object(wf.app, "astream", side_effect=fake_astream) as m:
        r1 = asyncio.run(wf.run("sotorasib", "KRAS G12C NSCLC"))
        r2 = asyncio.run(wf.run("sotorasib", "KRAS G12C NSCLC"))

    assert m.call_count == 1, (
        f"Expected graph to run exactly once; ran {m.call_count} times"
    )
    assert r1.drug_name == r2.drug_name
    assert r1.indication == r2.indication


# ---------------------------------------------------------------------------
# Test 2: different drug — both runs go through the graph
# ---------------------------------------------------------------------------

def test_different_inputs_not_cached_together():
    """Different drug names must each run the graph independently."""
    wf = GTMWorkflow()
    wf.cache.clear_all()

    async def fake_astream(initial, stream_mode="values"):
        yield GTMState(drug_name=initial.drug_name, indication=initial.indication)

    with patch.object(wf.app, "astream", side_effect=fake_astream) as m:
        asyncio.run(wf.run("sotorasib", "KRAS G12C NSCLC"))
        asyncio.run(wf.run("adagrasib", "KRAS G12C NSCLC"))

    assert m.call_count == 2, (
        f"Expected graph to run twice (different drugs); ran {m.call_count} times"
    )


# ---------------------------------------------------------------------------
# Test 3: different doctor — separate cache entries
# ---------------------------------------------------------------------------

def test_different_doctor_not_shared():
    """Different current_doctor must produce distinct cache entries."""
    wf = GTMWorkflow()
    wf.cache.clear_all()

    async def fake_astream(initial, stream_mode="values"):
        yield GTMState(drug_name=initial.drug_name, indication=initial.indication)

    with patch.object(wf.app, "astream", side_effect=fake_astream) as m:
        asyncio.run(wf.run("sotorasib", "KRAS G12C NSCLC", current_doctor="Dr Smith"))
        asyncio.run(wf.run("sotorasib", "KRAS G12C NSCLC", current_doctor="Dr Jones"))

    assert m.call_count == 2, (
        f"Expected two cache misses for different doctors; got {m.call_count}"
    )


# ---------------------------------------------------------------------------
# Test 4: error state is NOT cached
# ---------------------------------------------------------------------------

def test_error_state_not_cached():
    """An error from the graph should not be stored in cache so the next
    identical run retries the graph rather than returning the stale error."""
    wf = GTMWorkflow()
    wf.cache.clear_all()

    call_count = 0

    async def fake_astream_error(initial, stream_mode="values"):
        nonlocal call_count
        call_count += 1
        raise RuntimeError("Simulated agent failure")
        # pragma: no cover
        yield  # make it a generator

    with patch.object(wf.app, "astream", side_effect=fake_astream_error):
        r1 = asyncio.run(wf.run("sotorasib", "KRAS G12C NSCLC"))
        r2 = asyncio.run(wf.run("sotorasib", "KRAS G12C NSCLC"))

    assert call_count == 2, (
        f"Expected graph to be called twice when errors occur; called {call_count} times"
    )
    # Both should return error states but not from cache
    assert r1.agent_status == "error"
    assert r2.agent_status == "error"


# ---------------------------------------------------------------------------
# Test 5: progress_callback still fires on the live path
# ---------------------------------------------------------------------------

def test_progress_callback_fires_on_live_path():
    """progress_callback must still be called during a non-cached graph run."""
    wf = GTMWorkflow()
    wf.cache.clear_all()

    recorded_calls = []

    def my_callback(agent_name, agents_completed, pct):
        recorded_calls.append((agent_name, pct))

    fake_state = GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")
    # Simulate an agent completing
    fake_state.mark_agent_complete("Market Research")

    async def fake_astream(initial, stream_mode="values"):
        yield fake_state

    with patch.object(wf.app, "astream", side_effect=fake_astream):
        asyncio.run(wf.run(
            "sotorasib", "KRAS G12C NSCLC",
            progress_callback=my_callback
        ))

    assert len(recorded_calls) >= 1, "progress_callback should have been called at least once"
