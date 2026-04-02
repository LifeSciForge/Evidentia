"""
JSON Validator — SKILL_05
Replaces bare re.search(r'\{.*\}') used in all 5 agents with:
  1. Balanced-brace JSON extraction (handles nested objects correctly)
  2. Pydantic v2 validation with per-agent schemas and graceful fallbacks
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional, Type

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

def extract_json_from_text(text: str) -> dict:
    """
    Find and parse the first well-formed JSON object in text.

    Handles:
    - Markdown code fences (```json ... ```)
    - Nested braces (the greedy-regex bug)
    - Leading/trailing whitespace

    Raises ValueError if no valid JSON object is found.
    """
    if not text:
        raise ValueError("Empty text — no JSON to extract")

    # Strip markdown code fences
    cleaned = text.strip()
    if "```" in cleaned:
        # Extract content between first ``` and last ```
        start = cleaned.find("```")
        end = cleaned.rfind("```")
        if start != end:
            block = cleaned[start + 3: end].strip()
            if block.startswith("json"):
                block = block[4:].strip()
            cleaned = block

    # Find outermost balanced { ... } block
    brace_start = cleaned.find("{")
    if brace_start == -1:
        raise ValueError("No JSON object found in text")

    depth = 0
    in_string = False
    escape_next = False

    for i, ch in enumerate(cleaned[brace_start:], start=brace_start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = cleaned[brace_start: i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Found balanced braces but JSON is invalid: {exc}") from exc

    raise ValueError("Unbalanced braces — could not extract valid JSON object")


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    valid: bool
    data: Optional[Any] = None
    errors: list[str] = field(default_factory=list)


def validate_with_pydantic(data: dict, schema_class: Type[BaseModel]) -> ValidationResult:
    """
    Try to instantiate schema_class from data dict.
    Returns ValidationResult(valid=True, data=instance) on success.
    Returns ValidationResult(valid=False, errors=[...]) on failure.
    Never raises.
    """
    try:
        instance = schema_class(**data)
        return ValidationResult(valid=True, data=instance)
    except Exception as exc:
        errors = [str(e) for e in exc.errors()] if hasattr(exc, "errors") else [str(exc)]
        return ValidationResult(valid=False, errors=errors)


# ---------------------------------------------------------------------------
# Per-agent Pydantic schemas
# ---------------------------------------------------------------------------

class CompetitorItem(BaseModel):
    name: str = "Unknown"
    company: str = "Unknown"
    market_share: float = Field(default=0.0, ge=0, le=100)
    pricing: float = Field(default=0.0, ge=0)
    key_differentiators: list[str] = []
    clinical_advantages: list[str] = []
    clinical_disadvantages: list[str] = []
    launch_date: str = "Unknown"
    annual_sales: float = 0.0

    @field_validator("market_share", "pricing", "annual_sales", mode="before")
    @classmethod
    def coerce_none_to_zero(cls, v):
        return v if v is not None else 0.0


class CompetitorResponse(BaseModel):
    competitors: list[CompetitorItem] = []
    competitive_gaps: dict = {}
    positioning_strategy: str = ""
    threats: list[str] = []
    opportunities: list[str] = []


class MarketResearchResponse(BaseModel):
    tam_estimate: float = Field(default=0.0, ge=0)
    sam_estimate: float = Field(default=0.0, ge=0)
    som_estimate: float = Field(default=0.0, ge=0)
    patient_population: int = Field(default=0, ge=0)
    market_drivers: list[str] = []
    growth_assumptions: list[str] = []
    epidemiology_notes: str = ""

    @field_validator("tam_estimate", "sam_estimate", "som_estimate", mode="before")
    @classmethod
    def coerce_none_to_zero(cls, v):
        return v if v is not None else 0.0

    @field_validator("patient_population", mode="before")
    @classmethod
    def coerce_population(cls, v):
        return int(v) if v is not None else 0


class PayerResponse(BaseModel):
    hta_status: str = "Under review"
    qaly_threshold: float = Field(default=30000.0, ge=0)
    pricing_ceiling: float = Field(default=0.0, ge=0)
    reimbursement_barriers: list[str] = []
    reimbursement_solutions: list[str] = []
    geography_priority: list[str] = ["US", "EU", "UK"]
    managed_access_programs: list[str] = []
    payer_feedback_summary: str = ""

    @field_validator("qaly_threshold", "pricing_ceiling", mode="before")
    @classmethod
    def coerce_none_to_zero(cls, v):
        return v if v is not None else 0.0


class PersonaResponse(BaseModel):
    role_description: str = ""
    pain_points: list[str] = []
    value_propositions: list[str] = []
    objection_responses: dict = {}
    success_metrics: list[str] = []
    engagement_triggers: list[str] = []


class PositioningResponse(BaseModel):
    category_definition: str = ""
    positioning_statement: str = ""
    key_differentiators: list[str] = []
    value_propositions: dict = {}
    competitive_vs_statements: list[str] = []
    messaging_pillars: list[str] = []
    common_objections: dict = {}


class ClinicalEvidenceSchema(BaseModel):
    trial_name: str = ""
    key_data_point: str = ""
    source: str = ""


class ClinicalPillarSchema(BaseModel):
    pillar_title: str = ""
    evidence: ClinicalEvidenceSchema = Field(default_factory=ClinicalEvidenceSchema)
    msl_talking_point: str = ""
    why_relevant_to_kol: str = ""


class KeyDifferentiatorSchema(BaseModel):
    vs_standard_of_care: str = ""
    advantage: str = ""
    evidence: str = ""
    msl_talking_point: str = ""


class AnticipatedObjectionSchema(BaseModel):
    objection: str = ""
    why_they_ask: str = ""
    probability: str = "50%"
    evidence_response: str = ""
    msl_response: str = ""


class GuardrailSchema(BaseModel):
    avoid_claim: str = ""
    reason: str = ""
    alternative: str = ""


class MSLTalkingPointsSchema(BaseModel):
    doctor_profile: dict = {}
    conversation_opener: dict = {}
    three_clinical_pillars: list[ClinicalPillarSchema] = []
    key_differentiators: list[KeyDifferentiatorSchema] = []
    anticipated_objections: list[AnticipatedObjectionSchema] = []
    guardrails: dict = {}
    delivery_notes: dict = {}
