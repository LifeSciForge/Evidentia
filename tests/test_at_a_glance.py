"""Tests for the glance_lead_points helper."""

from types import SimpleNamespace
from src.ui.app import glance_lead_points


def test_returns_none_or_str_when_state_empty(demo_state):
    lead, objection = glance_lead_points(demo_state)
    assert lead is None or isinstance(lead, str)
    assert objection is None or isinstance(objection, str)


def test_picks_strings_when_present():
    state = SimpleNamespace(
        msl_talking_points=SimpleNamespace(talking_points=["Lead point about efficacy"]),
        messaging_data=SimpleNamespace(positioning_statement="pos"),
        objections=[{"objection": "OS not significant", "response": "reframe"}],
    )
    lead, objection = glance_lead_points(state)
    assert isinstance(lead, str) and lead
    assert isinstance(objection, str) and objection
