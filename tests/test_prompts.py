"""
Tests for the src.prompts loader module.

Verifies:
1. load_prompt returns the file text for each known template.
2. Each template contains at least one expected placeholder.
3. load_prompt raises FileNotFoundError for an unknown template name.
"""

import pytest
from src.prompts import load_prompt


EXPECTED_PLACEHOLDERS = {
    "market_research":            "{drug_name}",
    "payer_intelligence":         "{drug_name}",
    "competitor_analysis":        "{drug_name}",
    "icp_definition":             "{drug_name}",
    "synthesis":                  "{drug_name}",
    "messaging_positioning":      "{drug_name}",
    "messaging_personas":         "{drug_name}",
    "messaging_talking_points":   "{current_doctor}",
}


class TestLoadPrompt:
    """load_prompt returns file text and it contains expected placeholders."""

    @pytest.mark.parametrize("name,placeholder", list(EXPECTED_PLACEHOLDERS.items()))
    def test_load_prompt_returns_text(self, name, placeholder):
        text = load_prompt(name)
        assert isinstance(text, str), f"{name}: expected str, got {type(text)}"
        assert len(text) > 50, f"{name}: suspiciously short — {len(text)} chars"

    @pytest.mark.parametrize("name,placeholder", list(EXPECTED_PLACEHOLDERS.items()))
    def test_placeholder_present(self, name, placeholder):
        text = load_prompt(name)
        assert placeholder in text, (
            f"{name}: expected placeholder {placeholder!r} not found in template"
        )

    def test_unknown_name_raises(self):
        with pytest.raises(FileNotFoundError):
            load_prompt("__nonexistent_template__")
