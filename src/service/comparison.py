"""
src/service/comparison.py

Highest-phase trial comparison service.

Given a drug name, returns a comparison row whose dimensions are sourced
exclusively from that drug's highest-phase clinical trial as registered on
ClinicalTrials.gov (no fabricated values).

Registry-backed dimensions (always traced to NCT id):
    nct_id            — NCT identifier of the selected trial
    nct_url           — canonical ClinicalTrials.gov URL
    phase             — trial phase (e.g. PHASE3)
    primary_endpoint  — first primary outcome measure (from registry)
    approval_status   — short human-readable label derived from overall status + phase

LLM-extracted dimensions (over the trial's own text; empty string if absent):
    mechanism         — MOA stated in the trial text
    efficacy          — key efficacy result / endpoint metric mentioned
    key_safety        — notable safety finding mentioned
    dosing            — dosing schedule mentioned

No-fabrication contract:
    - LLM is instructed to return "" for any dimension not stated in the trial text.
    - On any LLM failure the LLM dims are "" (registry dims are preserved).
    - On no trials available all dims are "" and NCT fields are "".
    - Never raises; always returns a well-formed row dict.
"""

from __future__ import annotations

from typing import Optional
import re

from src.core.logger import get_logger
from src.core.llm import get_claude
from src.service.tools.clinical_trials_tools import ClinicalTrialsClient, nct_url
from src.service.validators.json_validator import extract_json_from_text

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Phase ordering
# ---------------------------------------------------------------------------

_PHASE_ORDER = {
    "PHASE4": 4,
    "PHASE3": 3,
    "PHASE2": 2,
    "PHASE1": 1,
}


def _phase_rank(phase: str) -> int:
    """Return numeric rank for a phase string. Unknown / N/A → 0."""
    return _PHASE_ORDER.get((phase or "").upper().replace(" ", ""), 0)


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def highest_phase_trial(trials: list) -> dict | None:
    """Pick the trial with the highest phase (PHASE4 > PHASE3 > PHASE2 > PHASE1 > unknown).

    Tie-break: largest enrollment (then first encountered if still equal).
    Returns None if `trials` is empty.
    """
    if not trials:
        return None

    best = None
    best_rank = -1
    best_enrollment = -1

    for trial in trials:
        rank = _phase_rank(trial.get("phase", ""))
        enrollment = int(trial.get("enrollment") or 0)
        if rank > best_rank or (rank == best_rank and enrollment > best_enrollment):
            best = trial
            best_rank = rank
            best_enrollment = enrollment

    return best


def _derive_approval_status(phase: str, status: str) -> str:
    """Build a short registry-backed approval status label."""
    phase_clean = (phase or "").replace("_", " ").title()
    status_clean = (status or "").replace("_", " ").title()
    if phase_clean and status_clean:
        return f"{phase_clean}, {status_clean}"
    return phase_clean or status_clean or ""


def _empty_row(drug_name: str) -> dict:
    return {
        "drug": drug_name,
        "nct_id": "",
        "nct_url": "",
        "phase": "",
        "dimensions": {
            "mechanism": "",
            "efficacy": "",
            "key_safety": "",
            "primary_endpoint": "",
            "dosing": "",
            "approval_status": "",
        },
    }


def _llm_extract_dims(trial: dict, trial_detail_text: str) -> dict:
    """Call the LLM once over trial text; return dict with mechanism/efficacy/key_safety/dosing.

    Returns empty-string dict on any failure (no fabrication).
    """
    empty = {"mechanism": "", "efficacy": "", "key_safety": "", "dosing": ""}

    prompt = f"""You are a medical information extraction assistant.

Below is the available text from a clinical trial registry entry (ClinicalTrials.gov).
Extract ONLY the following four dimensions using ONLY facts explicitly stated in the text below.
If a dimension is NOT mentioned in the text, return an empty string "" for it — do NOT invent or infer.

Dimensions to extract:
- mechanism: The drug's mechanism of action (MOA) as described in the trial text.
- efficacy: A key efficacy result or primary endpoint metric mentioned (e.g., ORR %, OS, PFS).
- key_safety: The most notable safety finding or AE mentioned.
- dosing: The dosing schedule (dose + frequency) as described.

Respond with ONLY valid JSON, no explanation:
{{
  "mechanism": "...",
  "efficacy": "...",
  "key_safety": "...",
  "dosing": "..."
}}

Trial text:
---
{trial_detail_text}
---"""

    try:
        llm = get_claude(temperature=0.1)
        response = llm.invoke(prompt)
        data = extract_json_from_text(response.content)
        # Ensure all four keys exist; coerce missing/None to ""
        return {k: str(data.get(k) or "") for k in ("mechanism", "efficacy", "key_safety", "dosing")}
    except Exception as exc:
        logger.error(f"LLM extraction failed: {exc}")
        return empty


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_comparison_row(
    drug_name: str,
    retrieved_trials: list | None = None,
    cache=None,
) -> dict:
    """Return a comparison row for `drug_name`.

    Shape:
    {
        "drug": drug_name,
        "nct_id": "<NCT...>" or "",
        "nct_url": "<canonical url>" or "",
        "phase": "<PHASE3>" or "",
        "dimensions": {
            "mechanism": str, "efficacy": str, "key_safety": str,
            "primary_endpoint": str, "dosing": str, "approval_status": str,
        },
    }

    Provenance:
    - nct_id, nct_url, phase, primary_endpoint, approval_status — from trial registry.
    - mechanism, efficacy, key_safety, dosing — LLM-extracted from trial text;
      "" if not mentioned or on LLM failure.

    Args:
        drug_name: Name of the drug to profile.
        retrieved_trials: Pre-fetched trial list (parsed trial dicts). If supplied
            (even as []) the ClinicalTrials API is NOT called. Pass None to trigger
            an API search.
        cache: Optional CacheManager. If given, caches the result by drug_name so
            a second call for the same drug is instant.

    Never raises — returns empty row on any failure.
    """
    # ---------- Cache check ----------
    cache_key = None
    if cache is not None:
        cache_key = cache.make_key("comparison", drug_name)
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"Cache hit for comparison row: {drug_name}")
            return cached

    # ---------- Fetch trials if not provided ----------
    trials: list = []
    if retrieved_trials is not None:
        # Caller explicitly provided trials (may be empty list)
        trials = retrieved_trials
    else:
        # Need to search ClinicalTrials.gov
        try:
            client = ClinicalTrialsClient()
            result = client.search_trials(drug_name=drug_name, condition="")
            trials = result.get("trials", []) if result.get("success") else []
        except Exception as exc:
            logger.error(f"ClinicalTrials search failed for {drug_name}: {exc}")
            trials = []

    # ---------- No trials → empty row ----------
    if not trials:
        empty = _empty_row(drug_name)
        if cache is not None and cache_key:
            cache.set(cache_key, empty)
        return empty

    # ---------- Select highest-phase trial ----------
    best = highest_phase_trial(trials)
    if best is None:
        empty = _empty_row(drug_name)
        if cache is not None and cache_key:
            cache.set(cache_key, empty)
        return empty

    # ---------- Registry-backed fields ----------
    nct_id = best.get("nct_id") or ""
    phase = best.get("phase") or ""
    status = best.get("status") or ""
    primary_endpoint_raw = best.get("primary_endpoint") or ""
    # Normalise "N/A" sentinel from _parse_trial to ""
    primary_endpoint = "" if primary_endpoint_raw == "N/A" else primary_endpoint_raw
    trial_url = best.get("url") or (nct_url(nct_id) if nct_id else "")
    approval_status = _derive_approval_status(phase, status)

    # ---------- Assemble trial text for LLM ----------
    # Use whatever text is available from the parsed record
    text_parts = []
    if best.get("title") and best["title"] != "N/A":
        text_parts.append(f"Title: {best['title']}")
    if phase:
        text_parts.append(f"Phase: {phase}")
    if status:
        text_parts.append(f"Status: {status}")
    if primary_endpoint:
        text_parts.append(f"Primary Endpoint: {primary_endpoint}")
    if best.get("sponsor") and best["sponsor"] != "N/A":
        text_parts.append(f"Sponsor: {best['sponsor']}")
    if best.get("key_insight"):
        text_parts.append(f"Key Insight: {best['key_insight']}")

    # Optionally try to get richer detail text from the API
    if nct_id:
        try:
            client = ClinicalTrialsClient()
            detail = client.get_trial_details(nct_id)
            if detail.get("success") and detail.get("trial"):
                detail_trial = detail["trial"]
                for field in ("title", "primary_endpoint", "key_insight"):
                    val = detail_trial.get(field, "")
                    if val and val != "N/A":
                        text_parts.append(f"{field}: {val}")
        except Exception as exc:
            logger.warning(f"Could not fetch detail for {nct_id}: {exc}")

    trial_text = "\n".join(text_parts) if text_parts else f"Drug: {drug_name}"

    # ---------- LLM extraction (graceful on failure) ----------
    llm_dims = _llm_extract_dims(best, trial_text)

    # ---------- Assemble row ----------
    row = {
        "drug": drug_name,
        "nct_id": nct_id,
        "nct_url": trial_url,
        "phase": phase,
        "dimensions": {
            "mechanism": llm_dims["mechanism"],
            "efficacy": llm_dims["efficacy"],
            "key_safety": llm_dims["key_safety"],
            "primary_endpoint": primary_endpoint,
            "dosing": llm_dims["dosing"],
            "approval_status": approval_status,
        },
    }

    # ---------- Cache result ----------
    if cache is not None and cache_key:
        cache.set(cache_key, row)

    return row
