"""Tests for the chip_for helper in src/ui/app.py."""
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("TAVILY_API_KEY", "test-key")

from types import SimpleNamespace
from src.ui.app import chip_for
from src.schema.gtm_state import verified_source, unavailable


def test_chip_for_returns_chip_html_for_known_key():
    state = SimpleNamespace(
        sources={
            "market.patient_population": verified_source(
                "PubMed", "https://pubmed.ncbi.nlm.nih.gov/36546659/"
            )
        }
    )
    html = chip_for(state, "market.patient_population")
    assert "ev-chip-verified" in html
    assert "PubMed" in html
    assert "pubmed.ncbi.nlm.nih.gov" in html


def test_chip_for_unavailable_renders_unavailable_chip_no_link():
    state = SimpleNamespace(sources={"market.tam": unavailable("Not available")})
    html = chip_for(state, "market.tam")
    assert "ev-chip-unavailable" in html
    assert "<a " not in html


def test_chip_for_absent_key_returns_empty_string():
    state = SimpleNamespace(sources={})
    assert chip_for(state, "missing.key") == ""


def test_chip_for_no_sources_attr_returns_empty_string():
    """State with no sources attribute at all should return '' without raising."""
    state = SimpleNamespace()
    assert chip_for(state, "market.patient_population") == ""


def test_chip_for_web_source_renders_link():
    from src.schema.gtm_state import web_source
    state = SimpleNamespace(
        sources={"market.sam": web_source("https://statista.com/example")}
    )
    html = chip_for(state, "market.sam")
    assert "ev-chip-web" in html
    assert "<a " in html
    assert "statista.com" in html
