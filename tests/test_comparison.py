"""
tests/test_comparison.py

TDD tests for src/service/comparison.py

Design:
- NO live API or LLM calls — everything is mocked.
- Tests are grouped into four scenarios:
    1. highest_phase_trial selection logic
    2. build_comparison_row with retrieved_trials (happy path, LLM works)
    3. build_comparison_row on LLM failure (no-fabrication / graceful)
    4. build_comparison_row with no trials
    5. cache hit avoids repeated LLM/fetch
"""

import os
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("TAVILY_API_KEY", "test-key")

from unittest.mock import patch, MagicMock, call
import pytest

from src.service.comparison import highest_phase_trial, build_comparison_row
from src.service.cache.cache_manager import CacheManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _trial(nct_id: str, phase: str, status: str = "COMPLETED",
           primary_endpoint: str = "Overall Survival", enrollment: int = 500,
           url: str = "") -> dict:
    """Build a minimal parsed-trial dict matching _parse_trial output shape."""
    return {
        "nct_id": nct_id,
        "phase": phase,
        "status": status,
        "primary_endpoint": primary_endpoint,
        "enrollment": enrollment,
        "url": url or f"https://clinicaltrials.gov/study/{nct_id}",
        "title": f"Trial {nct_id}",
        "sponsor": "Test Pharma",
        "start_date": "2021-01",
        "completion_date": "2023-12",
        "key_insight": f"{phase} study, {status}. {primary_endpoint}",
    }


_MOCK_LLM_JSON = """{
  "mechanism": "KRAS G12C covalent inhibitor",
  "efficacy": "ORR 37.1%",
  "key_safety": "Hepatotoxicity (grade 3+: 2.7%)",
  "dosing": "960 mg QD"
}"""


# ---------------------------------------------------------------------------
# 1. highest_phase_trial: phase-ranking logic
# ---------------------------------------------------------------------------

class TestHighestPhaseTrial:
    def test_picks_phase3_over_phase2(self):
        trials = [
            _trial("NCT00000002", "PHASE2"),
            _trial("NCT00000003", "PHASE3"),
        ]
        result = highest_phase_trial(trials)
        assert result is not None
        assert result["nct_id"] == "NCT00000003"
        assert result["phase"] == "PHASE3"

    def test_picks_phase4_over_phase3(self):
        trials = [
            _trial("NCT00000003", "PHASE3"),
            _trial("NCT00000004", "PHASE4"),
        ]
        result = highest_phase_trial(trials)
        assert result["nct_id"] == "NCT00000004"

    def test_picks_phase3_over_phase1(self):
        trials = [
            _trial("NCT00000001", "PHASE1"),
            _trial("NCT00000003", "PHASE3"),
        ]
        result = highest_phase_trial(trials)
        assert result["nct_id"] == "NCT00000003"

    def test_unknown_phase_treated_as_lowest(self):
        trials = [
            _trial("NCT00000001", "N/A"),
            _trial("NCT00000002", "PHASE2"),
        ]
        result = highest_phase_trial(trials)
        assert result["nct_id"] == "NCT00000002"

    def test_empty_list_returns_none(self):
        assert highest_phase_trial([]) is None

    def test_single_trial_returned(self):
        t = _trial("NCT00000003", "PHASE3")
        assert highest_phase_trial([t]) == t

    def test_tiebreak_by_enrollment(self):
        """When phases are equal, pick the one with larger enrollment."""
        trials = [
            _trial("NCT00000003a", "PHASE3", enrollment=200),
            _trial("NCT00000003b", "PHASE3", enrollment=800),
        ]
        result = highest_phase_trial(trials)
        assert result["nct_id"] == "NCT00000003b"


# ---------------------------------------------------------------------------
# 2. build_comparison_row: happy path with retrieved_trials
# ---------------------------------------------------------------------------

class TestBuildRowHappyPath:
    """Pass retrieved_trials; mock LLM; assert registry dims + LLM dims."""

    def test_registry_fields_populated(self):
        trials = [_trial("NCT12345678", "PHASE3",
                         status="COMPLETED",
                         primary_endpoint="Overall Survival at 12 months")]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = _MOCK_LLM_JSON

        with patch("src.service.comparison.get_claude", return_value=mock_llm):
            row = build_comparison_row("sotorasib", retrieved_trials=trials)

        assert row["drug"] == "sotorasib"
        assert row["nct_id"] == "NCT12345678"
        assert row["nct_url"] == "https://clinicaltrials.gov/study/NCT12345678"
        assert row["phase"] == "PHASE3"

    def test_primary_endpoint_from_registry(self):
        """primary_endpoint comes from the trial record, not the LLM."""
        trials = [_trial("NCT12345678", "PHASE3",
                         primary_endpoint="Progression-Free Survival")]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = _MOCK_LLM_JSON

        with patch("src.service.comparison.get_claude", return_value=mock_llm):
            row = build_comparison_row("sotorasib", retrieved_trials=trials)

        assert row["dimensions"]["primary_endpoint"] == "Progression-Free Survival"

    def test_approval_status_from_registry(self):
        """approval_status is derived from the trial's overallStatus field."""
        trials = [_trial("NCT12345678", "PHASE3", status="COMPLETED")]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = _MOCK_LLM_JSON

        with patch("src.service.comparison.get_claude", return_value=mock_llm):
            row = build_comparison_row("sotorasib", retrieved_trials=trials)

        # approval_status is registry-derived: should mention COMPLETED / phase
        assert row["dimensions"]["approval_status"] != ""
        assert "PHASE3" in row["dimensions"]["approval_status"].upper() \
               or "COMPLETED" in row["dimensions"]["approval_status"].upper()

    def test_llm_extracted_dims_present(self):
        """mechanism, efficacy, key_safety, dosing come from LLM over trial text."""
        trials = [_trial("NCT12345678", "PHASE3")]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = _MOCK_LLM_JSON

        with patch("src.service.comparison.get_claude", return_value=mock_llm):
            row = build_comparison_row("sotorasib", retrieved_trials=trials)

        dims = row["dimensions"]
        assert dims["mechanism"] == "KRAS G12C covalent inhibitor"
        assert dims["efficacy"] == "ORR 37.1%"
        assert dims["key_safety"] == "Hepatotoxicity (grade 3+: 2.7%)"
        assert dims["dosing"] == "960 mg QD"

    def test_picks_highest_phase_from_retrieved(self):
        """When multiple trials passed, the PHASE3 beats PHASE2."""
        trials = [
            _trial("NCT00000002", "PHASE2"),
            _trial("NCT00000003", "PHASE3"),
        ]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = _MOCK_LLM_JSON

        with patch("src.service.comparison.get_claude", return_value=mock_llm):
            row = build_comparison_row("testdrug", retrieved_trials=trials)

        assert row["nct_id"] == "NCT00000003"


# ---------------------------------------------------------------------------
# 3. build_comparison_row: LLM failure → graceful, no invention
# ---------------------------------------------------------------------------

class TestBuildRowLLMFailure:
    """LLM raises → LLM-extracted dims are "", registry fields still present."""

    def _run(self, status: str = "COMPLETED"):
        trials = [_trial("NCT99999999", "PHASE3", status=status,
                         primary_endpoint="PFS")]
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = RuntimeError("LLM exploded")

        with patch("src.service.comparison.get_claude", return_value=mock_llm):
            row = build_comparison_row("testdrug", retrieved_trials=trials)
        return row

    def test_no_exception_raised(self):
        try:
            self._run()
        except Exception as exc:
            pytest.fail(f"build_comparison_row should not raise on LLM failure: {exc}")

    def test_mechanism_empty_on_llm_failure(self):
        row = self._run()
        assert row["dimensions"]["mechanism"] == ""

    def test_efficacy_empty_on_llm_failure(self):
        row = self._run()
        assert row["dimensions"]["efficacy"] == ""

    def test_key_safety_empty_on_llm_failure(self):
        row = self._run()
        assert row["dimensions"]["key_safety"] == ""

    def test_dosing_empty_on_llm_failure(self):
        row = self._run()
        assert row["dimensions"]["dosing"] == ""

    def test_registry_fields_still_populated_on_llm_failure(self):
        """NCT id, url, phase, primary_endpoint still come from the trial record."""
        row = self._run()
        assert row["nct_id"] == "NCT99999999"
        assert row["nct_url"] == "https://clinicaltrials.gov/study/NCT99999999"
        assert row["phase"] == "PHASE3"
        assert row["dimensions"]["primary_endpoint"] == "PFS"

    def test_approval_status_still_set_on_llm_failure(self):
        row = self._run(status="COMPLETED")
        # approval_status is registry-only; must survive LLM failure
        assert row["dimensions"]["approval_status"] != ""


# ---------------------------------------------------------------------------
# 4. build_comparison_row: no trials → empty row
# ---------------------------------------------------------------------------

class TestBuildRowNoTrials:
    """retrieved_trials=[] → empty nct_id/url, all dims ""."""

    def test_empty_nct_id(self):
        row = build_comparison_row("unknowndrug", retrieved_trials=[])
        assert row["nct_id"] == ""

    def test_empty_nct_url(self):
        row = build_comparison_row("unknowndrug", retrieved_trials=[])
        assert row["nct_url"] == ""

    def test_empty_phase(self):
        row = build_comparison_row("unknowndrug", retrieved_trials=[])
        assert row["phase"] == ""

    def test_all_dimensions_empty(self):
        row = build_comparison_row("unknowndrug", retrieved_trials=[])
        dims = row["dimensions"]
        for key in ("mechanism", "efficacy", "key_safety", "primary_endpoint",
                    "dosing", "approval_status"):
            assert dims[key] == "", f"Expected '' for {key}, got {dims[key]!r}"

    def test_drug_name_preserved(self):
        row = build_comparison_row("unknowndrug", retrieved_trials=[])
        assert row["drug"] == "unknowndrug"

    def test_no_live_search_when_retrieved_provided(self):
        """If retrieved_trials=[] is explicitly passed, no search should fire."""
        with patch("src.service.comparison.ClinicalTrialsClient") as mock_client:
            build_comparison_row("anydrug", retrieved_trials=[])
            mock_client.assert_not_called()


# ---------------------------------------------------------------------------
# 5. Cache hit: second call for same drug skips LLM
# ---------------------------------------------------------------------------

class TestCacheHit:
    def test_second_call_hits_cache_not_llm(self):
        """With a CacheManager, two calls for the same drug invoke LLM only once."""
        trials = [_trial("NCT11111111", "PHASE3")]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = _MOCK_LLM_JSON
        cache = CacheManager()

        with patch("src.service.comparison.get_claude", return_value=mock_llm):
            row1 = build_comparison_row("sotorasib", retrieved_trials=trials, cache=cache)
            row2 = build_comparison_row("sotorasib", retrieved_trials=trials, cache=cache)

        # LLM should only be called once (cache hit on second call)
        assert mock_llm.invoke.call_count == 1, (
            f"Expected LLM invoke once (cached), got {mock_llm.invoke.call_count}"
        )
        assert row1["nct_id"] == row2["nct_id"]
        assert row1["dimensions"] == row2["dimensions"]

    def test_different_drugs_each_call_llm(self):
        """Different drug names have separate cache entries."""
        trials_a = [_trial("NCT11111111", "PHASE3")]
        trials_b = [_trial("NCT22222222", "PHASE3")]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = _MOCK_LLM_JSON
        cache = CacheManager()

        with patch("src.service.comparison.get_claude", return_value=mock_llm):
            build_comparison_row("sotorasib", retrieved_trials=trials_a, cache=cache)
            build_comparison_row("adagrasib", retrieved_trials=trials_b, cache=cache)

        assert mock_llm.invoke.call_count == 2, (
            f"Expected LLM invoke twice (different drugs), got {mock_llm.invoke.call_count}"
        )
