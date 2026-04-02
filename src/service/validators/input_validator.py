"""
Input Validator — SKILL_05
Validates user-supplied inputs at Streamlit UI boundaries before
triggering the LangGraph workflow.
"""

import re


class InputValidator:
    """Validates drug name, indication, and field notes inputs."""

    @staticmethod
    def validate_drug_name(name: str) -> str:
        """
        Returns cleaned drug name or raises ValueError.
        Rules: non-empty, ≥2 chars, not all digits.
        """
        if not name:
            raise ValueError("Drug name is required")
        cleaned = name.strip()
        if len(cleaned) < 2:
            raise ValueError("Drug name must be at least 2 characters")
        if cleaned.isdigit():
            raise ValueError("Drug name cannot be all digits")
        # Allow letters, digits, hyphens, spaces (e.g. "sotorasib", "BNT111", "PD-1 inhibitor")
        if not re.match(r"^[A-Za-z0-9\s\-\.\/]+$", cleaned):
            raise ValueError("Drug name contains invalid characters")
        return cleaned

    @staticmethod
    def validate_indication(indication: str) -> str:
        """
        Returns cleaned indication or raises ValueError.
        Rules: non-empty, ≥3 chars.
        """
        if not indication:
            raise ValueError("Indication is required")
        cleaned = indication.strip()
        if len(cleaned) < 3:
            raise ValueError("Indication must be at least 3 characters")
        return cleaned

    @staticmethod
    def validate_field_notes(notes: str) -> str:
        """
        Returns cleaned field notes or raises ValueError.
        Rules: non-empty, 10–10000 chars.
        """
        if not notes:
            raise ValueError("Field notes are required")
        cleaned = notes.strip()
        if len(cleaned) < 10:
            raise ValueError("Field notes are too short (minimum 10 characters)")
        if len(cleaned) > 10000:
            raise ValueError("Field notes are too long (maximum 10,000 characters)")
        return cleaned
