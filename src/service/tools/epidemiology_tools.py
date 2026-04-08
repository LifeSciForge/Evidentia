"""
Epidemiology Tools
Collects disease epidemiology data for a given indication using
Tavily web search, PubMed literature, and ClinicalTrials.gov enrollment data.
"""

from typing import Dict, Any, List
from src.service.tools.tavily_tools import tavily_search
from src.service.tools.pubmed_tools import search_pubmed
from src.service.tools.clinical_trials_tools import search_clinical_trials
from src.core.logger import get_logger

logger = get_logger(__name__)


def _extract_enrollment_total(trials: List[Dict[str, Any]]) -> int:
    """Sum enrollment figures from trial records as a patient-population proxy."""
    total = 0
    for trial in trials:
        try:
            enrollment = trial.get("enrollment")
            if enrollment:
                total += int(enrollment)
        except (ValueError, TypeError):
            continue
    return total


def _format_pub_citations(publications: List[Dict[str, Any]], max_count: int = 5) -> List[str]:
    """Build citation strings from PubMed records."""
    citations = []
    for pub in publications[:max_count]:
        title = pub.get("title", "Unknown title")
        year = pub.get("publication_year") or pub.get("year", "")
        journal = pub.get("journal", "")
        pmid = pub.get("pmid", "")
        parts = [title]
        if journal:
            parts.append(journal)
        if year:
            parts.append(str(year))
        if pmid:
            parts.append(f"PMID:{pmid}")
        citations.append(". ".join(parts))
    return citations


def fetch_epidemiology_data(indication: str) -> Dict[str, Any]:
    """
    Collect epidemiology data for a disease indication.

    Aggregates data from three sources:
    1. Tavily web search — prevalence, incidence, risk factors, demographics
    2. PubMed — peer-reviewed epidemiology literature (used for citations)
    3. ClinicalTrials.gov — total enrolled patients as patient-population proxy

    Args:
        indication: Disease or condition name (e.g. "KRAS G12C NSCLC")

    Returns:
        dict with keys:
            prevalence        str   e.g. "X per 100,000"
            incidence         str   e.g. "Y new cases per year"
            risk_factors      list  known risk factors
            demographics      dict  age_group, gender_distribution, geography
            treatment_patterns list current standard of care
            unmet_needs       list  gaps in current treatment
            patient_population_proxy int  sum of ClinicalTrials enrollment
            sources           list  citations from PubMed + Tavily answer
    """
    result: Dict[str, Any] = {
        "prevalence": "",
        "incidence": "",
        "risk_factors": [],
        "demographics": {},
        "treatment_patterns": [],
        "unmet_needs": [],
        "patient_population_proxy": 0,
        "sources": [],
    }

    # ── 1. Tavily: prevalence & incidence ────────────────────────────────────
    logger.info(f"🌍 Epidemiology search: prevalence/incidence for '{indication}'")
    prev_result = tavily_search(
        query=f"{indication} epidemiology statistics prevalence incidence",
        max_results=5,
    )
    prevalence_text = ""
    if prev_result.get("success"):
        prevalence_text = prev_result.get("answer", "")
        logger.info("✅ Prevalence/incidence data retrieved")
        if prevalence_text:
            result["sources"].append(f"Tavily web search: {indication} epidemiology prevalence incidence")
    else:
        logger.warning(f"⚠️ Prevalence search failed: {prev_result.get('error')}")

    # ── 2. Tavily: risk factors & demographics ───────────────────────────────
    logger.info(f"👥 Epidemiology search: demographics/risk factors for '{indication}'")
    demo_result = tavily_search(
        query=f"{indication} risk factors demographics age gender patient population",
        max_results=5,
    )
    demographics_text = ""
    if demo_result.get("success"):
        demographics_text = demo_result.get("answer", "")
        logger.info("✅ Demographics/risk factor data retrieved")
        if demographics_text:
            result["sources"].append(f"Tavily web search: {indication} demographics risk factors")
    else:
        logger.warning(f"⚠️ Demographics search failed: {demo_result.get('error')}")

    # ── 3. Tavily: treatment patterns & unmet needs ──────────────────────────
    logger.info(f"💊 Epidemiology search: treatment patterns for '{indication}'")
    tx_result = tavily_search(
        query=f"{indication} standard of care treatment patterns unmet medical need",
        max_results=5,
    )
    treatment_text = ""
    if tx_result.get("success"):
        treatment_text = tx_result.get("answer", "")
        logger.info("✅ Treatment pattern data retrieved")
        if treatment_text:
            result["sources"].append(f"Tavily web search: {indication} standard of care unmet need")
    else:
        logger.warning(f"⚠️ Treatment patterns search failed: {tx_result.get('error')}")

    # ── 4. PubMed: peer-reviewed epidemiology literature ────────────────────
    logger.info(f"📚 PubMed search: epidemiology literature for '{indication}'")
    pubmed_result = search_pubmed(
        drug_name="epidemiology",
        condition=indication,
        max_results=10,
    )
    publications: List[Dict[str, Any]] = []
    if pubmed_result.get("success"):
        publications = pubmed_result.get("publications", [])
        logger.info(f"✅ Found {len(publications)} PubMed epidemiology publications")
        result["sources"].extend(_format_pub_citations(publications))
    else:
        logger.warning(f"⚠️ PubMed search failed: {pubmed_result.get('error')}")

    # ── 5. ClinicalTrials.gov: enrollment as population proxy ────────────────
    logger.info(f"🏥 ClinicalTrials.gov: enrollment data for '{indication}'")
    trials_result = search_clinical_trials(
        drug_name="",
        condition=indication,
        max_results=20,
    )
    trials: List[Dict[str, Any]] = []
    if trials_result.get("success"):
        trials = trials_result.get("trials", [])
        logger.info(f"✅ Found {len(trials)} trials for enrollment proxy")
    else:
        logger.warning(f"⚠️ ClinicalTrials search failed: {trials_result.get('error')}")

    enrollment_total = _extract_enrollment_total(trials)

    # ── 6. Assemble structured result ────────────────────────────────────────
    # Populate text fields from Tavily answers; callers can refine further
    # with an LLM if they need structured extraction.
    result["prevalence"] = prevalence_text or f"Prevalence data not available for {indication}"
    result["incidence"] = prevalence_text or f"Incidence data not available for {indication}"

    # Parse risk factors from demographics text (best-effort line extraction)
    if demographics_text:
        lines = [ln.strip("- •*").strip() for ln in demographics_text.split("\n") if ln.strip()]
        risk_lines = [ln for ln in lines if any(
            kw in ln.lower() for kw in ("risk", "factor", "age", "gender", "male", "female", "smoker", "mutation")
        )]
        result["risk_factors"] = risk_lines[:6] if risk_lines else [demographics_text[:200]]
        result["demographics"] = {
            "summary": demographics_text[:500],
            "source": "Tavily web search",
        }
    else:
        result["demographics"] = {"summary": f"Demographics data not available for {indication}"}

    # Treatment patterns & unmet needs from Tavily answer
    if treatment_text:
        lines = [ln.strip("- •*").strip() for ln in treatment_text.split("\n") if ln.strip()]
        soc_lines = [ln for ln in lines if any(
            kw in ln.lower() for kw in ("treatment", "therapy", "chemotherapy", "surgery", "radiation",
                                         "standard", "care", "approved", "first-line", "second-line")
        )]
        unmet_lines = [ln for ln in lines if any(
            kw in ln.lower() for kw in ("unmet", "need", "gap", "limitation", "challenge", "lack", "resistance")
        )]
        result["treatment_patterns"] = soc_lines[:5] if soc_lines else [treatment_text[:200]]
        result["unmet_needs"] = unmet_lines[:5] if unmet_lines else [
            f"Unmet need data not specifically extracted for {indication}"
        ]
    else:
        result["treatment_patterns"] = [f"Treatment pattern data not available for {indication}"]
        result["unmet_needs"] = [f"Unmet need data not available for {indication}"]

    result["patient_population_proxy"] = enrollment_total

    logger.info(
        f"✅ Epidemiology data assembled for '{indication}': "
        f"{len(result['risk_factors'])} risk factors, "
        f"{len(result['treatment_patterns'])} treatment patterns, "
        f"{enrollment_total:,} enrolled patients (proxy), "
        f"{len(result['sources'])} sources"
    )

    return result
