# SKILL_05: Data Quality & Reliability
## Pydantic Validation + Retry Logic + Caching + Data Confidence Annotations

---

## Problem Statement

Every agent in the current codebase has the same fragile pattern:

```python
# Current pattern in ALL 6 agents — will fail ~20-30% of the time
json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
data = json.loads(json_match.group())
```

This fails when:
- LLM response has trailing text after the JSON object
- JSON contains nested braces that confuse the outer `\{.*\}` match
- LLM adds a code block wrapper (```json ... ```)
- Response is truncated due to token limits

Additionally:
- No retry logic: a single Tavily timeout = silent empty result
- No caching: the same drug is searched 10 times in a session at API cost
- Competitor data has zero provenance — an MSL sees numbers with no confidence indicator
- `agent_messages.py` defines 11 message schema classes — none are used anywhere
- Input validation is absent: `drug_name=""` flows through the entire 6-agent pipeline

For a pharmaceutical company using this tool to inform HCP engagement strategy, this is a compliance risk. Data presented without provenance is a regulatory exposure.

---

## Objective

Harden every agent and service layer so that:
1. LLM JSON parsing never silently fails — always validates against schema
2. Every API call retries 3 times with exponential backoff
3. Identical API requests are cached for 1 hour
4. Every data point carries a `data_confidence` flag visible in the UI
5. Invalid user inputs are rejected before the workflow starts

---

## Phase 1: Robust JSON Parsing with Pydantic Validation

### File: `src/service/validators/json_validator.py`

```python
import json
import re
from typing import Any, List, Optional, Type
from pydantic import BaseModel, ValidationError, field_validator
from dataclasses import dataclass

@dataclass
class ValidationResult:
    valid: bool
    data: Any
    errors: List[str]

def extract_json_from_text(text: str) -> Optional[str]:
    """
    Robust JSON extraction that handles:
    - Trailing text after JSON
    - Code block wrappers (```json ... ```)
    - Leading prose before JSON
    """
    # Remove code block wrapper if present
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)

    # Try array first (insight extraction returns arrays)
    array_match = re.search(r'\[.*\]', text, re.DOTALL)
    if array_match:
        try:
            json.loads(array_match.group())
            return array_match.group()
        except json.JSONDecodeError:
            pass

    # Try object
    # Use a balanced brace finder instead of greedy regex
    start = text.find('{')
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                candidate = text[start:i+1]
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    break
    return None


def validate_with_pydantic(
    raw_text: str,
    model_class: Type[BaseModel]
) -> ValidationResult:
    """
    Generic validator: extract JSON from LLM text, validate against Pydantic model.
    """
    json_str = extract_json_from_text(raw_text)
    if not json_str:
        return ValidationResult(False, None, ["No valid JSON found in response"])

    try:
        raw_dict = json.loads(json_str)
    except json.JSONDecodeError as e:
        return ValidationResult(False, None, [f"JSON decode error: {str(e)}"])

    try:
        validated = model_class(**raw_dict)
        return ValidationResult(True, validated.model_dump(), [])
    except ValidationError as e:
        errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
        # Return partial data — don't fail completely on missing optional fields
        # Try to construct with only valid fields
        valid_fields = {
            k: v for k, v in raw_dict.items()
            if k in model_class.model_fields
        }
        try:
            partial = model_class(**valid_fields)
            return ValidationResult(True, partial.model_dump(), errors)  # valid=True with warnings
        except ValidationError:
            return ValidationResult(False, raw_dict, errors)  # raw_dict as fallback


# --- Per-Agent Pydantic Models ---

class CompetitorItemSchema(BaseModel):
    name: str
    company: str = ""
    market_share: Optional[float] = None      # None = unknown, don't fabricate
    pricing: Optional[float] = None           # None = unknown
    key_differentiators: List[str] = []
    clinical_advantages: List[str] = []
    clinical_disadvantages: List[str] = []
    launch_date: Optional[str] = None
    data_confidence: str = "LLM-estimated"

    @field_validator('market_share')
    @classmethod
    def validate_market_share(cls, v):
        if v is not None and (v < 0 or v > 100):
            return None  # reject invalid, don't raise
        return v

    @field_validator('pricing')
    @classmethod
    def validate_pricing(cls, v):
        if v is not None and v < 0:
            return None
        return v


class CompetitorResponseSchema(BaseModel):
    competitor_names: List[str] = []
    competitors: List[CompetitorItemSchema] = []
    competitive_gaps: dict = {}
    positioning_strategy: str = ""
    threats: List[str] = []
    opportunities: List[str] = []


class MarketResearchSchema(BaseModel):
    tam_estimate: Optional[float] = None
    sam_estimate: Optional[float] = None
    som_estimate: Optional[float] = None
    patient_population: Optional[int] = None
    market_drivers: List[str] = []
    growth_assumptions: List[str] = []

    @field_validator('tam_estimate', 'sam_estimate', 'som_estimate')
    @classmethod
    def validate_market_size(cls, v):
        if v is not None and v < 0:
            return None
        return v


class PayerSchema(BaseModel):
    hta_status: str = "Unknown"
    qaly_threshold: Optional[float] = None
    pricing_ceiling: Optional[float] = None
    reimbursement_criteria: List[str] = []
    access_restrictions: List[str] = []
    reimbursement_barriers: List[str] = []


class InsightSchema(BaseModel):
    insight_category: str
    insight_text: str
    sentiment: str = "neutral"
    urgency: str = "medium"
    action_required: bool = False
    action_description: str = ""
    source_verbatim: str = ""
    confidence: float = 0.7
    tags: List[str] = []

    @field_validator('sentiment')
    @classmethod
    def validate_sentiment(cls, v):
        return v if v in ["positive", "neutral", "negative"] else "neutral"

    @field_validator('urgency')
    @classmethod
    def validate_urgency(cls, v):
        return v if v in ["high", "medium", "low"] else "medium"

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        return max(0.0, min(1.0, float(v)))


# Convenience functions for each agent
def validate_competitor_response(raw_text: str) -> ValidationResult:
    return validate_with_pydantic(raw_text, CompetitorResponseSchema)

def validate_market_research(raw_text: str) -> ValidationResult:
    return validate_with_pydantic(raw_text, MarketResearchSchema)

def validate_payer_response(raw_text: str) -> ValidationResult:
    return validate_with_pydantic(raw_text, PayerSchema)
```

---

## Phase 2: Retry Logic with Tenacity

`tenacity==9.1.4` is already in `requirements.txt`. Use it everywhere.

### Wrap All API Tool Clients

```python
# Pattern to apply to: tavily_tools.py, pubmed_tools.py, clinical_trials_tools.py, fda_tools.py

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

logger = logging.getLogger(__name__)

class TavilySearchClient:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=False
    )
    def search(self, query: str, search_depth: str = "advanced", max_results: int = 5) -> Dict:
        try:
            result = self.client.search(query=query, search_depth=search_depth, max_results=max_results)
            return {"success": True, "answer": result.get("answer", ""), "results": result.get("results", [])}
        except Exception as e:
            logger.warning(f"Tavily search failed (will retry): {e}")
            raise
```

Apply the same pattern to:
- `PubMedClient.search_publications()` in `pubmed_tools.py`
- `ClinicalTrialsClient.search_trials()` in `clinical_trials_tools.py`
- `FDAClient.search_drug_approvals()` in `fda_tools.py`

**Fallback return value** if all 3 attempts fail:
```python
# Each client's search method should have an outer try/except after the retry decorator
# to return a safe empty result rather than propagating the exception
def search(self, ...):
    try:
        return self._search_with_retry(...)
    except Exception as e:
        logger.error(f"All retry attempts failed: {e}")
        return {"success": False, "answer": "", "results": [], "error": str(e)}
```

---

## Phase 3: In-Memory TTL Cache

### File: `src/service/cache/cache_manager.py`

```python
import time
import hashlib
from typing import Any, Optional, Dict

class CacheManager:
    """
    Two-tier in-memory TTL cache for API responses.
    Scope: Streamlit session (process lifetime).
    No Redis dependency for v2.0 MVP — pure Python dict.

    settings.py already has USE_MEMORY_CACHE: bool = True
    and REDIS_URL: Optional[str] — Redis upgrade deferred to v2.1.
    """

    _cache: Dict[str, Any] = {}
    _expiry: Dict[str, float] = {}
    DEFAULT_TTL = 3600      # 1 hour for API responses
    BRIEF_TTL = 3600 * 24   # 24 hours for generated briefs (SKILL_06)
    RAG_TTL = 3600 * 6      # 6 hours for RAG indexes

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        if key in cls._cache:
            if time.time() < cls._expiry.get(key, 0):
                return cls._cache[key]
            else:
                cls._invalidate(key)
        return None

    @classmethod
    def set(cls, key: str, value: Any, ttl: int = DEFAULT_TTL):
        cls._cache[key] = value
        cls._expiry[key] = time.time() + ttl

    @classmethod
    def _invalidate(cls, key: str):
        cls._cache.pop(key, None)
        cls._expiry.pop(key, None)

    @classmethod
    def clear_drug(cls, drug_name: str):
        """Invalidate all cache entries for a specific drug."""
        keys_to_remove = [k for k in cls._cache if drug_name.lower() in k.lower()]
        for k in keys_to_remove:
            cls._invalidate(k)

    @staticmethod
    def make_key(*args) -> str:
        """Create a deterministic cache key from any set of arguments."""
        combined = "|".join(str(a).lower().strip() for a in args)
        return hashlib.md5(combined.encode()).hexdigest()

    @classmethod
    def stats(cls) -> Dict:
        """Return cache stats for monitoring."""
        now = time.time()
        active = sum(1 for k in cls._expiry if cls._expiry[k] > now)
        expired = len(cls._expiry) - active
        return {"total_entries": len(cls._cache), "active": active, "expired": expired}
```

### Integration Pattern (apply to all API tool calls)

```python
# Example: in market_research_agent.py, wrap PubMed call with cache
from src.service.cache.cache_manager import CacheManager

cache_key = CacheManager.make_key("pubmed", drug_name, indication)
publications = CacheManager.get(cache_key)

if publications is None:
    publications = pubmed_client.search_publications(drug_name, indication, max_results=50)
    CacheManager.set(cache_key, publications, ttl=CacheManager.DEFAULT_TTL)

# Same pattern for: clinical_trials, tavily, fda, RAG indexes
```

---

## Phase 4: Input Validation

### File: `src/service/validators/input_validator.py`

```python
import re
from typing import Tuple

class InputValidator:
    """
    Validates user inputs before they enter the 6-agent workflow.
    Called from src/ui/app.py before run_workflow() is triggered.
    """

    # Known drug name patterns (FDA generic name format)
    DRUG_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-\(\)\/]+$')
    # Common indication abbreviations are allowed
    INDICATION_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-\(\)\/\,\.]+$')

    @classmethod
    def validate_drug_name(cls, name: str) -> Tuple[bool, str]:
        if not name or len(name.strip()) < 3:
            return False, "Drug name must be at least 3 characters."
        if len(name.strip()) > 100:
            return False, "Drug name is too long (max 100 characters)."
        if not cls.DRUG_NAME_PATTERN.match(name.strip()):
            return False, "Drug name contains invalid characters. Use letters, numbers, hyphens, and spaces only."
        return True, ""

    @classmethod
    def validate_indication(cls, indication: str) -> Tuple[bool, str]:
        if not indication or len(indication.strip()) < 3:
            return False, "Indication must be at least 3 characters."
        if len(indication.strip()) > 200:
            return False, "Indication is too long (max 200 characters)."
        if not cls.INDICATION_PATTERN.match(indication.strip()):
            return False, "Indication contains invalid characters."
        return True, ""

    @classmethod
    def validate_field_notes(cls, notes: str) -> Tuple[bool, str]:
        if not notes or len(notes.strip()) < 20:
            return False, "Field notes must be at least 20 characters to extract meaningful insights."
        if len(notes.strip()) > 10000:
            return False, "Field notes too long (max 10,000 characters). Split into multiple entries if needed."
        return True, ""
```

### Wire into `src/ui/app.py`

```python
# In the Generate Brief button handler (before run_workflow() is called):
from src.service.validators.input_validator import InputValidator

valid_drug, drug_error = InputValidator.validate_drug_name(drug_name)
valid_ind, ind_error = InputValidator.validate_indication(indication)

if not valid_drug:
    st.error(f"Invalid drug name: {drug_error}")
    return
if not valid_ind:
    st.error(f"Invalid indication: {ind_error}")
    return

# Proceed with workflow
run_workflow(drug_name, indication, hospital, doctor)
```

---

## Phase 5: Data Confidence Annotations

Every piece of data displayed to an MSL must show its provenance. MSLs use this information in front of KOLs — presenting LLM-estimated numbers as facts is a compliance risk.

### Confidence Levels

| Level | Meaning | UI Color | Source |
|-------|---------|---------|--------|
| `FDA-verified` | Data from FDA OpenFDA API | Green | `fda_tools.py` |
| `PubMed-sourced` | Data from PubMed with PMID | Green | `pubmed_tools.py` |
| `ClinicalTrials-sourced` | Data from ClinicalTrials.gov | Green | `clinical_trials_tools.py` |
| `Tavily-sourced` | Data from web search (URL cited) | Yellow | `tavily_tools.py` |
| `LLM-estimated` | No external source; LLM synthesis | Orange | Any agent |
| `User-provided` | Entered directly by MSL | Blue | UI input |

### UI Helper Functions (add to `src/ui/app.py` or `src/ui/components.py`)

```python
def confidence_badge(confidence: str) -> str:
    """Returns a Streamlit-compatible colored badge string."""
    badges = {
        "FDA-verified":            "🟢 FDA-verified",
        "PubMed-sourced":          "🟢 PubMed-cited",
        "ClinicalTrials-sourced":  "🟢 ClinicalTrials.gov",
        "Tavily-sourced":          "🟡 Web-sourced (verify URL)",
        "LLM-estimated":           "🟠 AI-estimated — verify before use",
        "User-provided":           "🔵 User-provided"
    }
    return badges.get(confidence, "⚪ Unknown source")

def confidence_warning(confidence: str) -> None:
    """Show Streamlit warning for low-confidence data."""
    if confidence == "LLM-estimated":
        st.warning(
            "This data is AI-estimated and has not been verified against an external source. "
            "Do not present this to a KOL without independent verification."
        )
```

### Apply to All Data Displays

Minimum: apply `confidence_badge()` to these sections:
- Competitor pricing and market share (`display_competitive_section()`)
- Market sizing estimates TAM/SAM/SOM (`display_final_brief_section()`)
- QALY threshold and pricing ceiling (`display_reimbursement_section()`)
- HTA status (`display_reimbursement_section()`)

---

## Phase 6: Activate `agent_messages.py`

`src/schema/agent_messages.py` defines 11 message schema classes — all unused. Activate for audit trail:

```python
# In each agent, after successful completion, emit an AgentMessage:
from src.schema.agent_messages import AgentMessage, create_agent_message, MESSAGE_TYPES

# At the end of each agent function:
message = create_agent_message(
    agent_name="Market Research Agent",
    message_type=MESSAGE_TYPES["RESEARCH_COMPLETE"],
    content={
        "drug_name": state.drug_name,
        "publications_found": len(state.market_data.key_publications),
        "trials_found": len(state.market_data.clinical_trials)
    },
    confidence_score=0.8
)

# Add to GTMState agent_messages list:
if not hasattr(state, "agent_messages") or state.agent_messages is None:
    state.agent_messages = []
state.agent_messages.append(message)
```

Add `agent_messages: List[AgentMessage] = field(default_factory=list)` to `GTMState` in `gtm_state.py`.

The audit trail is then visible in the Download tab:
```python
# In display_download_section():
if state.agent_messages:
    st.subheader("Audit Trail")
    for msg in state.agent_messages:
        st.write(f"**{msg.agent_name}** — {msg.message_type} at {msg.timestamp}")
```

---

## Files Modified

| File | Change |
|------|--------|
| `src/service/tools/tavily_tools.py` | Add tenacity `@retry` decorator to all search methods |
| `src/service/tools/pubmed_tools.py` | Add tenacity `@retry` decorator |
| `src/service/tools/clinical_trials_tools.py` | Add tenacity `@retry` decorator |
| `src/service/tools/fda_tools.py` | Add tenacity `@retry` decorator |
| `src/agents/gtm_agents/*.py` | Replace bare `re.search + json.loads` with `validate_with_pydantic()` calls; add cache lookups; emit `AgentMessage` at completion |
| `src/schema/gtm_state.py` | Add `agent_messages: List[AgentMessage]` to `GTMState` |
| `src/ui/app.py` | Add `InputValidator` calls before workflow trigger; add `confidence_badge()` to competitive + market + payer display sections |

## Files Created

| File | Purpose |
|------|---------|
| `src/service/validators/json_validator.py` | Pydantic-based LLM JSON parsing and validation |
| `src/service/validators/input_validator.py` | Drug name + indication + field notes validation |
| `src/service/cache/cache_manager.py` | In-memory TTL cache for API responses |
