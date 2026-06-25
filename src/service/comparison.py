"""
src/service/comparison.py

Highest-phase trial comparison service.

Given a drug name, returns a comparison row whose dimensions are sourced from:
  1. The drug's highest-phase clinical trial as registered on ClinicalTrials.gov
     (registry-backed fields: phase, primary_endpoint, approval_status, nct_id, nct_url).
  2. The drug's top PubMed publication abstracts
     (publication-backed fields: efficacy as actual results, mechanism, key_safety, dosing).

The LLM extraction prompt explicitly requires efficacy to be an actual reported
result (e.g., "median PFS 11.1 mo, HR 0.51"), NOT the endpoint name — returning
"" if no numeric/qualitative result is stated in the retrieved text.

Registry-backed dimensions (always traced to NCT id):
    nct_id            — NCT identifier of the selected trial
    nct_url           — canonical ClinicalTrials.gov URL
    phase             — trial phase (e.g. PHASE3)
    primary_endpoint  — first primary outcome measure (from registry)
    approval_status   — short human-readable label derived from overall status + phase

LLM-extracted dimensions (over trial text + publication abstract(s); "" if absent):
    mechanism         — MOA as stated in the retrieved text
    efficacy          — actual reported result (median PFS/OS, HR, ORR etc.)
    key_safety        — notable AEs / safety signal stated in the text
    dosing            — dose/schedule if stated

Publication traceability:
    pmid              — PMID of the first used publication (or "")
    pmid_url          — canonical PubMed URL for the publication (or "")
    sources           — list of {pmid, pmid_url, title} for all used publications

No-fabrication contract:
    - LLM is instructed to return "" for any dimension not stated in the retrieved text.
    - efficacy MUST be a real result — NOT the endpoint name.
    - On any LLM failure the LLM dims are "" (registry dims are preserved).
    - On any PubMed failure, continues with trial-only text (graceful).
    - On no trials available all dims are "" and NCT/PMID fields are "".
    - Never raises; always returns a well-formed row dict.
"""

from __future__ import annotations

from typing import Optional

from src.core.logger import get_logger
from src.core.llm import get_claude
from src.service.tools.clinical_trials_tools import ClinicalTrialsClient, nct_url
from src.service.tools.pubmed_tools import search_pubmed
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
        "pmid": "",
        "pmid_url": "",
        "sources": [],
        "dimensions": {
            "mechanism": "",
            "efficacy": "",
            "key_safety": "",
            "primary_endpoint": "",
            "dosing": "",
            "approval_status": "",
        },
    }


def _fetch_pubmed_abstracts(drug_name: str, max_results: int = 3) -> tuple[str, list]:
    """Fetch top PubMed publications for drug_name and return (combined_abstract_text, sources).

    Returns ("", []) on any failure (graceful — never raises).

    sources is a list of dicts: [{pmid, pmid_url, title}, ...]
    """
    try:
        result = search_pubmed(drug_name=drug_name, max_results=max_results)
        if not result.get("success"):
            logger.warning(f"PubMed search failed for {drug_name}: {result.get('error')}")
            return "", []

        pubs = result.get("publications", [])
        if not pubs:
            return "", []

        # Build combined text from all retrieved abstracts (up to max_results)
        text_blocks = []
        sources = []
        for pub in pubs[:max_results]:
            pmid = str(pub.get("pmid", ""))
            title = str(pub.get("title", ""))
            abstract = str(pub.get("abstract", ""))
            pub_url = str(pub.get("url", ""))

            if not pub_url and pmid:
                from src.service.tools.pubmed_tools import pmid_url as _pmid_url
                pub_url = _pmid_url(pmid)

            if title or abstract:
                block_parts = []
                if title:
                    block_parts.append(f"Publication title: {title}")
                if abstract:
                    block_parts.append(f"Abstract: {abstract}")
                text_blocks.append("\n".join(block_parts))

            if pmid:
                sources.append({"pmid": pmid, "pmid_url": pub_url, "title": title})

        combined = "\n\n".join(text_blocks)
        return combined, sources

    except Exception as exc:
        logger.warning(f"PubMed fetch failed for {drug_name}: {exc}")
        return "", []


def _llm_extract_dims(trial: dict, combined_text: str) -> dict:
    """Call the LLM once over trial + publication text; return mechanism/efficacy/key_safety/dosing.

    Key contract enforced by prompt:
    - efficacy = actual reported RESULT (e.g. "median OS 17.2 mo, HR 0.78"), NOT the endpoint name.
    - Return "" for any dimension not explicitly stated in the provided text.
    - Never invent or infer beyond what the text states.

    Returns empty-string dict on any failure (no fabrication).
    """
    empty = {"mechanism": "", "efficacy": "", "key_safety": "", "dosing": ""}

    prompt = f"""You are a medical information extraction assistant with strict no-fabrication rules.

Below is text from a clinical trial registry entry and/or published clinical trial abstracts.
Extract ONLY the following four dimensions using ONLY facts explicitly stated in the text below.
If a dimension is NOT mentioned in the text, return an empty string "" — do NOT invent, infer, or guess.

DIMENSIONS TO EXTRACT:
- mechanism: The drug's mechanism of action (MOA) as literally described in the text
  (e.g. "PD-1/VEGF bispecific antibody", "KRAS G12C covalent inhibitor").
  Return "" if not stated.

- efficacy: The actual REPORTED RESULT — a real numeric or qualitative clinical outcome
  as stated in the text (e.g., "median PFS 11.1 months, HR 0.51", "ORR 37.1%",
  "median OS 17.2 mo vs 12.4 mo, HR 0.78").
  IMPORTANT: Do NOT return the endpoint NAME (e.g. do NOT return "Overall Survival (OS)"
  or "Progression-Free Survival"). Only return a result with numbers/data.
  Return "" if no actual result/data is stated in the text.

- key_safety: The most notable adverse event or safety signal explicitly stated
  (e.g., "hepatotoxicity grade 3+: 2.7%", "diarrhea grade 3-4: 3%").
  Return "" if not stated.

- dosing: The dosing schedule (dose + frequency) as explicitly stated in the text
  (e.g., "960 mg orally once daily", "200 mg IV Q3W").
  Return "" if not stated.

Respond with ONLY valid JSON, no explanation, no markdown:
{{
  "mechanism": "...",
  "efficacy": "...",
  "key_safety": "...",
  "dosing": "..."
}}

Retrieved text (trial registry + publication abstracts):
---
{combined_text}
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
        "pmid": "<PMID>" or "",          # first used publication
        "pmid_url": "<url>" or "",        # PubMed canonical URL
        "sources": [                       # all used publications
            {"pmid": "...", "pmid_url": "...", "title": "..."},
            ...
        ],
        "dimensions": {
            "mechanism": str, "efficacy": str, "key_safety": str,
            "primary_endpoint": str, "dosing": str, "approval_status": str,
        },
    }

    Provenance:
    - nct_id, nct_url, phase, primary_endpoint, approval_status — from trial registry.
    - mechanism, efficacy, key_safety, dosing — LLM-extracted from trial text
      PLUS top PubMed publication abstracts; "" if not stated or on LLM failure.
    - efficacy is always a real reported result, never just an endpoint name.
    - pmid / pmid_url / sources — from PubMed; "" / [] if no publications found.

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

    # ---------- Assemble trial text ----------
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

    # ---------- Fetch PubMed abstracts (graceful on failure) ----------
    pub_text, pub_sources = _fetch_pubmed_abstracts(drug_name, max_results=3)

    # ---------- Combine trial + publication text for LLM ----------
    combined_parts = [trial_text]
    if pub_text:
        combined_parts.append(pub_text)
    combined_text = "\n\n".join(combined_parts)

    # ---------- LLM extraction (graceful on failure) ----------
    llm_dims = _llm_extract_dims(best, combined_text)

    # ---------- Publication traceability ----------
    first_pmid = pub_sources[0]["pmid"] if pub_sources else ""
    first_pmid_url = pub_sources[0]["pmid_url"] if pub_sources else ""

    # ---------- Assemble row ----------
    row = {
        "drug": drug_name,
        "nct_id": nct_id,
        "nct_url": trial_url,
        "phase": phase,
        "pmid": first_pmid,
        "pmid_url": first_pmid_url,
        "sources": pub_sources,
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
