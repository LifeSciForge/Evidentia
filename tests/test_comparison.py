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
    6. publication-sourced efficacy/mechanism/safety (new)
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

_PUBMED_EMPTY_RESULT = {"success": True, "total_results": 0, "publications": []}


class TestBuildRowHappyPath:
    """Pass retrieved_trials; mock LLM + PubMed; assert registry dims + LLM dims."""

    def test_registry_fields_populated(self):
        trials = [_trial("NCT12345678", "PHASE3",
                         status="COMPLETED",
                         primary_endpoint="Overall Survival at 12 months")]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = _MOCK_LLM_JSON

        with patch("src.service.comparison.get_claude", return_value=mock_llm), \
             patch("src.service.comparison.search_pubmed", return_value=_PUBMED_EMPTY_RESULT):
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

        with patch("src.service.comparison.get_claude", return_value=mock_llm), \
             patch("src.service.comparison.search_pubmed", return_value=_PUBMED_EMPTY_RESULT):
            row = build_comparison_row("sotorasib", retrieved_trials=trials)

        assert row["dimensions"]["primary_endpoint"] == "Progression-Free Survival"

    def test_approval_status_from_registry(self):
        """approval_status is derived from the trial's overallStatus field."""
        trials = [_trial("NCT12345678", "PHASE3", status="COMPLETED")]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = _MOCK_LLM_JSON

        with patch("src.service.comparison.get_claude", return_value=mock_llm), \
             patch("src.service.comparison.search_pubmed", return_value=_PUBMED_EMPTY_RESULT):
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

        with patch("src.service.comparison.get_claude", return_value=mock_llm), \
             patch("src.service.comparison.search_pubmed", return_value=_PUBMED_EMPTY_RESULT):
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

        with patch("src.service.comparison.get_claude", return_value=mock_llm), \
             patch("src.service.comparison.search_pubmed", return_value=_PUBMED_EMPTY_RESULT):
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

        with patch("src.service.comparison.get_claude", return_value=mock_llm), \
             patch("src.service.comparison.search_pubmed", return_value=_PUBMED_EMPTY_RESULT):
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

        with patch("src.service.comparison.get_claude", return_value=mock_llm), \
             patch("src.service.comparison.search_pubmed", return_value=_PUBMED_EMPTY_RESULT):
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

        with patch("src.service.comparison.get_claude", return_value=mock_llm), \
             patch("src.service.comparison.search_pubmed", return_value=_PUBMED_EMPTY_RESULT):
            build_comparison_row("sotorasib", retrieved_trials=trials_a, cache=cache)
            build_comparison_row("adagrasib", retrieved_trials=trials_b, cache=cache)

        assert mock_llm.invoke.call_count == 2, (
            f"Expected LLM invoke twice (different drugs), got {mock_llm.invoke.call_count}"
        )


# ---------------------------------------------------------------------------
# 6. Publication-sourced efficacy/mechanism/safety
# ---------------------------------------------------------------------------

# A fake PubMed result that looks like what PubMedClient.search_publications returns
_FAKE_PUBMED_RESULT = {
    "success": True,
    "total_results": 1,
    "returned_results": 1,
    "publications": [
        {
            "pmid": "12345678",
            "title": "Phase 3 trial of testdrug in NSCLC",
            "authors": ["Smith", "Jones"],
            "journal": "New England Journal of Medicine",
            "publication_year": "2023",
            "abstract": (
                "In this phase 3 trial, testdrug demonstrated median OS 17.2 months (HR 0.78, "
                "p=0.003) versus 12.4 months for chemotherapy. The mechanism involves selective "
                "KRAS G12C covalent inhibition. Dosing was 960 mg QD orally. Common adverse "
                "events included diarrhea (grade 3-4: 3%) and hepatotoxicity (grade 3-4: 2%)."
            ),
            "mesh_terms": [],
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
        }
    ],
    "query": '"testdrug"[Title/Abstract]',
}

_FAKE_PUBMED_EMPTY = {
    "success": True,
    "total_results": 0,
    "returned_results": 0,
    "publications": [],
    "query": '"testdrug"[Title/Abstract]',
}


class TestPublicationSourcedDims:
    """Publication abstracts supply efficacy results, mechanism, and safety.
    All PubMed calls are mocked — no live network traffic.
    """

    def _run_with_pub(self, mock_llm_json: str, pubmed_result=None):
        """Helper: run build_comparison_row with one trial + a mocked PubMed result."""
        if pubmed_result is None:
            pubmed_result = _FAKE_PUBMED_RESULT
        trials = [
            _trial(
                "NCT99001122",
                "PHASE3",
                status="COMPLETED",
                primary_endpoint="Overall Survival (OS)",
            )
        ]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = mock_llm_json

        with patch("src.service.comparison.get_claude", return_value=mock_llm), \
             patch(
                 "src.service.comparison.search_pubmed",
                 return_value=pubmed_result,
             ):
            row = build_comparison_row("testdrug", retrieved_trials=trials)
        return row

    def test_efficacy_is_result_not_endpoint(self):
        """efficacy must be the numeric result from the abstract, not the endpoint name."""
        llm_json = """{
          "mechanism": "KRAS G12C covalent inhibitor",
          "efficacy": "median OS 17.2 mo, HR 0.78",
          "key_safety": "diarrhea grade 3-4: 3%, hepatotoxicity grade 3-4: 2%",
          "dosing": "960 mg QD"
        }"""
        row = self._run_with_pub(llm_json)
        dims = row["dimensions"]
        # Efficacy must be the result, not the endpoint label
        assert dims["efficacy"] == "median OS 17.2 mo, HR 0.78"
        # Must NOT equal the primary_endpoint string
        assert dims["efficacy"] != dims["primary_endpoint"]
        assert dims["primary_endpoint"] == "Overall Survival (OS)"

    def test_dims_filled_from_publication(self):
        """mechanism and key_safety should be populated when present in the publication."""
        llm_json = """{
          "mechanism": "selective KRAS G12C covalent inhibitor",
          "efficacy": "median OS 17.2 mo, HR 0.78",
          "key_safety": "hepatotoxicity grade 3-4: 2%",
          "dosing": "960 mg QD"
        }"""
        row = self._run_with_pub(llm_json)
        dims = row["dimensions"]
        assert dims["mechanism"] != "", "mechanism should be filled from publication"
        assert dims["key_safety"] != "", "key_safety should be filled from publication"

    def test_no_publication_efficacy_empty(self):
        """When no publication abstract is available, LLM returns "" for efficacy.
        The row must carry "" — NOT the primary_endpoint string.
        """
        llm_json = """{
          "mechanism": "",
          "efficacy": "",
          "key_safety": "",
          "dosing": ""
        }"""
        row = self._run_with_pub(llm_json, pubmed_result=_FAKE_PUBMED_EMPTY)
        dims = row["dimensions"]
        assert dims["efficacy"] == "", (
            f"efficacy should be '' when no result in text, got {dims['efficacy']!r}"
        )
        # Must NOT have silently fallen back to the endpoint name
        assert dims["efficacy"] != dims["primary_endpoint"]

    def test_publication_source_returned(self):
        """Row must carry pmid + pmid_url (or a 'sources' list) when a publication was found."""
        llm_json = """{
          "mechanism": "KRAS G12C covalent inhibitor",
          "efficacy": "median OS 17.2 mo, HR 0.78",
          "key_safety": "diarrhea 3%",
          "dosing": "960 mg QD"
        }"""
        row = self._run_with_pub(llm_json)
        # The row must expose publication provenance in some form
        has_pmid = row.get("pmid") or (
            any(s.get("pmid") for s in row.get("sources", []))
        )
        has_pmid_url = row.get("pmid_url") or (
            any(s.get("pmid_url") for s in row.get("sources", []))
        )
        assert has_pmid, f"Row should carry pmid; row keys: {list(row.keys())}"
        assert has_pmid_url, f"Row should carry pmid_url; row keys: {list(row.keys())}"

    def test_pubmed_fetch_is_called_with_drug_name(self):
        """build_comparison_row must call search_pubmed with the drug name."""
        llm_json = """{
          "mechanism": "",
          "efficacy": "",
          "key_safety": "",
          "dosing": ""
        }"""
        trials = [_trial("NCT00001111", "PHASE3")]
        mock_llm = MagicMock()
        mock_llm.invoke.return_value.content = llm_json

        with patch("src.service.comparison.get_claude", return_value=mock_llm), \
             patch(
                 "src.service.comparison.search_pubmed",
                 return_value=_FAKE_PUBMED_EMPTY,
             ) as mock_pubmed:
            build_comparison_row("sotorasib", retrieved_trials=trials)

        mock_pubmed.assert_called_once()
        call_args = mock_pubmed.call_args
        # drug_name may be positional or keyword — check both
        positional_match = bool(call_args.args) and call_args.args[0] == "sotorasib"
        keyword_match = call_args.kwargs.get("drug_name") == "sotorasib"
        assert positional_match or keyword_match, (
            f"search_pubmed not called with drug_name='sotorasib'; call_args={call_args}"
        )

    def test_pubmed_failure_graceful(self):
        """If PubMed search raises, build_comparison_row must not raise; LLM dims default to ""."""
        trials = [_trial("NCT00001111", "PHASE3", primary_endpoint="PFS")]
        mock_llm = MagicMock()
        # LLM returns empty dims (simulating no text to extract from)
        mock_llm.invoke.return_value.content = (
            '{"mechanism": "", "efficacy": "", "key_safety": "", "dosing": ""}'
        )

        with patch("src.service.comparison.get_claude", return_value=mock_llm), \
             patch(
                 "src.service.comparison.search_pubmed",
                 side_effect=RuntimeError("PubMed is down"),
             ):
            try:
                row = build_comparison_row("sotorasib", retrieved_trials=trials)
            except Exception as exc:
                pytest.fail(f"build_comparison_row raised on PubMed failure: {exc}")

        # Registry dims must still be present
        assert row["nct_id"] == "NCT00001111"
        assert row["dimensions"]["primary_endpoint"] == "PFS"
