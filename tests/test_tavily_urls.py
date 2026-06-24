"""
Tests for Tavily top-source URL extraction and FDA verified-source helper.
No network calls — both functions are pure over dicts.
"""

from src.service.tools.tavily_tools import extract_top_source


def test_extract_top_source_with_results():
    raw = {"answer": "...", "results": [
        {"url": "https://www.fiercepharma.com/x", "title": "t"},
        {"url": "https://b.com"},
    ]}
    url, domain = extract_top_source(raw)
    assert url == "https://www.fiercepharma.com/x"
    assert domain == "fiercepharma.com"


def test_extract_top_source_empty_or_missing():
    assert extract_top_source({"answer": "x", "results": []}) == (None, None)
    assert extract_top_source({}) == (None, None)


from src.service.tools.fda_tools import source_from_fda_approval


def test_source_from_fda_approval_builds_verified_source():
    approval = {"brand_name": "LUMAKRAS", "application_number": "NDA214665"}
    s = source_from_fda_approval(approval)
    assert s is not None
    assert s.tier == "verified"
    assert "LUMAKRAS" in s.label or "FDA" in s.label
    assert s.url and "214665" in s.url


def test_source_from_fda_approval_none_when_empty():
    assert source_from_fda_approval({}) is None
