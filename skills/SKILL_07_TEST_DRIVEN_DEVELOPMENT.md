# SKILL_07 — Test-Driven Development

**Source:** [obra/superpowers](https://github.com/obra/superpowers) — `skills/test-driven-development`
**Applies to:** Every feature, bug fix, or behaviour change in Evidentia codebase

---

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over. No exceptions.

---

## The RED-GREEN-REFACTOR Cycle

### RED — Write a Failing Test
Write one minimal test that describes what the new behaviour should be.

```python
# Example: testing insight extraction fallback
def test_insight_extraction_returns_default_on_llm_failure(demo_state):
    demo_state.raw_field_notes = "KOL expressed interest in KRAS data"
    with patch("src.core.llm.get_claude") as mock_llm:
        mock_llm.side_effect = Exception("API timeout")
        result = asyncio.run(insight_extraction_agent(demo_state))
    assert result.captured_insights == []   # graceful fallback
    assert result.agent_status == "error"
```

Requirements:
- One behaviour per test
- Name clearly describes the behaviour being tested
- Uses real code, not mocks, wherever possible

### Verify RED — Watch It Fail (MANDATORY. Never skip.)
```bash
python3 -m pytest tests/test_insight_extraction_agent.py::test_insight_extraction_returns_default_on_llm_failure -v
```
Confirm:
- Test fails (not errors out with an import problem)
- Failure message is what you expected
- It fails because the feature is missing, not because of a typo

### GREEN — Write Minimal Code to Pass
Write the smallest possible implementation that makes the test pass.
Do not add features, do not refactor other code, do not "improve" anything outside the test scope.

### Verify GREEN (MANDATORY)
```bash
python3 -m pytest tests/ -v
```
Confirm: test passes AND no previously passing tests broke.

### REFACTOR — Clean Up
After green only: remove duplication, improve names, extract helpers.
Keep tests green. Do not add new behaviour.

---

## Evidentia-Specific Test Conventions

### Standard Demo Fixture
Always use `sotorasib` + `KRAS G12C NSCLC` as the canonical demo drug/indication:

```python
# tests/conftest.py
import pytest
from src.schema.gtm_state import GTMState

@pytest.fixture
def demo_state():
    return GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")
```

### Mock LLM Calls — Never Hit Real APIs in Unit Tests
```python
from unittest.mock import patch, MagicMock

@patch("src.core.llm.get_claude")
def test_competitor_agent_uses_fallback(mock_llm, demo_state):
    mock_llm.return_value.invoke.return_value.content = '{"competitors": []}'
    result = asyncio.run(competitor_analysis_agent(demo_state))
    assert result.competitor_data is not None
```

### Test File Locations
```
tests/
├── conftest.py                          # shared fixtures
├── test_market_research_agent.py
├── test_competitor_analysis_agent.py
├── test_payer_intelligence_agent.py
├── test_messaging_agent.py
├── test_synthesis_agent.py
├── test_insight_extraction_agent.py     # SKILL_02
├── test_engagement_scoring_agent.py     # SKILL_03
├── test_field_synthesis_agent.py        # SKILL_04
├── test_json_validator.py               # SKILL_05
├── test_cache_manager.py                # SKILL_05
├── test_input_validator.py              # SKILL_05
├── test_kol_store.py                    # SKILL_06
└── test_insight_store.py                # SKILL_06
```

### What to Test Per Agent
For every agent file, write tests for:
1. Happy path — valid input, LLM returns valid JSON
2. LLM failure — API exception → graceful fallback, `agent_status == "error"`
3. Malformed JSON from LLM — falls back to default data, does not crash
4. Empty API results (no trials found, no publications) — handles gracefully
5. State propagation — output is written to the correct `GTMState` field

### What to Test for Validators (SKILL_05)
```python
# test_json_validator.py
def test_extract_json_handles_nested_braces():
    text = '{"competitors": [{"name": "X", "pricing": {"us": 50000}}]}'
    result = extract_json_from_text(text)
    assert result["competitors"][0]["pricing"]["us"] == 50000

def test_extract_json_handles_code_fence():
    text = '```json\n{"key": "value"}\n```'
    result = extract_json_from_text(text)
    assert result["key"] == "value"

def test_extract_json_raises_on_no_json():
    with pytest.raises(ValueError):
        extract_json_from_text("No JSON here at all")

def test_competitor_response_coerces_market_share_out_of_range():
    data = {"competitors": [{"name": "X", "market_share": 150}]}
    result = validate_with_pydantic(data, CompetitorResponse)
    assert not result.valid  # 150 > 100, fails ge=0,le=100 validator
```

---

## Run Commands

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run single file
python3 -m pytest tests/test_json_validator.py -v

# Run with coverage
python3 -m pytest tests/ --cov=src --cov-report=term-missing

# Run only fast unit tests (skip integration)
python3 -m pytest tests/ -v -m "not integration"
```

---

## Red Flags — Stop and Start Over

- You wrote agent code before writing a test
- The test passed immediately on first run
- You're not sure why the test failed
- You added `# will add test later` anywhere
- You ran the app manually to verify instead of writing an automated test

---

## Rationalizations to Reject

| Excuse | Reality |
|--------|---------|
| "It's a simple change" | Simple changes break things. Test takes 2 minutes. |
| "I'll write tests after" | Tests that pass immediately prove nothing. |
| "Already tested it manually" | Manual testing can't be re-run after refactor. |
| "The agent is hard to test" | Hard to test = hard to reason about. Simplify the agent. |
| "Mocking the LLM is complex" | Use `unittest.mock.patch`. One decorator. |
