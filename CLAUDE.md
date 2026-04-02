# CLAUDE.md — Evidentia MSL Intelligence Platform

## What This Project Is

Evidentia is an AI-native intelligence platform for Medical Science Liaisons (MSLs) at
pharmaceutical companies. MSLs are field-based scientific experts (PhD/PharmD/MD) who engage
Key Opinion Leaders (KOLs) — physicians and researchers who influence prescribing behavior.
They are NOT sales reps. They do NOT promote. They exchange scientific information.

**The platform's core job:** Replace 45+ minutes of manual pre-call research with a 90-second
AI-generated intelligence package, and capture post-call insights that currently disappear into
freeform notes or are never written down at all.

---

## Pharma Domain Vocabulary

| Term | Definition |
|------|-----------|
| **KOL** | Key Opinion Leader — a physician, researcher, or payer decision-maker who influences clinical practice |
| **MSL** | Medical Science Liaison — field-based scientific expert; non-promotional |
| **HCP** | Healthcare Professional — any doctor, nurse, or clinician |
| **HTA** | Health Technology Assessment — NICE (UK), EMA (EU), ICER (US) reimbursement review |
| **QALY** | Quality-Adjusted Life Year — payer value metric; UK threshold ~£30K–£50K |
| **NCT ID** | ClinicalTrials.gov trial identifier (e.g., NCT04665128) |
| **PMID** | PubMed article identifier |
| **Indication** | The disease a drug is approved/studied for (e.g., "NSCLC", "KRAS G12C CRC") |
| **Pre-call brief** | Structured intelligence doc an MSL reviews before a KOL meeting |
| **IIT** | Investigator-Initiated Trial — sponsored by the KOL, not the company |
| **RWE** | Real-World Evidence — data from patient populations outside clinical trials |
| **HEOR** | Health Economics and Outcomes Research — value-based evidence |
| **Tier 1/2/3 KOL** | Influence classification: Tier 1 = top national/international KOLs |
| **Field insight** | Observation from a KOL interaction captured by the MSL post-meeting |
| **Territory** | Geographic/therapeutic area assigned to an MSL or MSL team |
| **DOL** | Digital Opinion Leader — influential via social media/online platforms |

---

## Architecture Overview

### Core Pattern: LangGraph StateGraph with Shared State

All agents read from and write to a single `GTMState` dataclass defined in
`src/schema/gtm_state.py`. **DO NOT pass data between agents via function arguments.**
The state object IS the message bus.

```
User Input
    │
    ▼
GTMState (initial: drug_name, indication, current_doctor, current_hospital)
    │
    ▼
LangGraph StateGraph
    ├── memory_retrieval_agent    (v2: runs first, loads prior KOL history)
    ├── kol_profiling_agent       (v2: KOL-specific research)
    ├── market_research_agent     (enhanced: RAG-based evidence)
    ├── payer_intelligence_agent  (enhanced: HTA + HEOR)
    ├── competitor_analysis_agent (fixed: FDA-verified, not hallucinated)
    ├── messaging_agent           (persona-specific talking points)
    └── synthesis_agent           (final brief + saved to brief_cache)
    │
    ▼
GTMState (final: all fields populated)
    │
    ▼
Streamlit UI (9 tabs + post-call capture)
```

### Agent Registration Pattern

New agents are registered in `src/agents/gtm_workflow.py`:

```python
graph.add_node("agent_name", agent_function)
graph.add_edge("upstream_agent", "agent_name")
```

All agent functions must have this exact signature:
```python
async def agent_name(state: GTMState) -> GTMState:
    ...
    state.mark_agent_complete("Agent Display Name")
    return state
```

---

## File Layout

```
project_9_gtm_simulator/
├── CLAUDE.md                        ← YOU ARE HERE
├── EVIDENTIA_V2_ARCHITECTURE.md     ← Full v2 technical architecture
├── EVIDENTIA_PRODUCT_BRIEF.md       ← Commercial brief
├── streamlit_app.py                 ← Entry point (do not modify structure)
├── requirements.txt                 ← Dependencies
│
├── skills/                          ← Implementation guides (reference these when building)
│   ├── SKILL_01_MSL_INTELLIGENCE_CORE.md
│   ├── SKILL_02_INSIGHT_CAPTURE_ENGINE.md
│   ├── SKILL_03_KOL_ENGAGEMENT_TRACKER.md
│   ├── SKILL_04_FIELD_INTELLIGENCE_DASHBOARD.md
│   ├── SKILL_05_DATA_QUALITY_RELIABILITY.md
│   └── SKILL_06_PERSISTENT_MEMORY_SYSTEM.md
│
├── src/
│   ├── agents/
│   │   ├── gtm_workflow.py          ← LangGraph StateGraph definition (register agents here)
│   │   └── gtm_agents/              ← One file per agent
│   │       ├── market_research_agent.py
│   │       ├── payer_intelligence_agent.py
│   │       ├── competitor_analysis_agent.py   ← BUG: competitor data is hallucinated
│   │       ├── icp_definition_agent.py
│   │       ├── messaging_agent.py
│   │       └── synthesis_agent.py
│   │
│   ├── schema/
│   │   ├── gtm_state.py             ← GTMState + all sub-dataclasses (single source of truth)
│   │   ├── gtm_output.py            ← GTMOutputDocument (export format)
│   │   └── agent_messages.py        ← Agent message schemas (DEFINED BUT UNUSED — v2 activates)
│   │
│   ├── service/
│   │   └── tools/
│   │       ├── clinical_trials_tools.py  ← ClinicalTrials.gov API v2
│   │       ├── pubmed_tools.py            ← PubMed via Biopython Entrez
│   │       ├── tavily_tools.py            ← Tavily web search
│   │       └── fda_tools.py               ← FDA OpenFDA API (IMPLEMENTED BUT NEVER CALLED)
│   │
│   ├── core/
│   │   ├── llm.py                   ← LLMManager singleton: get_claude(), get_model()
│   │   ├── settings.py              ← Pydantic Settings from .env
│   │   └── logger.py                ← Structured JSON logger
│   │
│   ├── ui/
│   │   ├── app.py                   ← Main Streamlit app (1224 lines, 9 tabs)
│   │   └── components.py            ← Plotly charts + metric card components
│   │
│   └── utils/
│       └── formatters.py            ← safe_join(), safe_format_list()
│
└── data/                            ← Empty; v2 adds SQLite DB here
```

---

## LLM Usage Conventions

Always import from `src.core.llm`, never instantiate `ChatAnthropic` directly in agent files:

```python
from src.core.llm import get_claude

llm = get_claude(temperature=0.3)   # factual extraction tasks
llm = get_claude(temperature=0.7)   # synthesis and creative positioning
```

**Temperature guide:**
- `0.1–0.2`: Structured JSON extraction from field notes (must be deterministic)
- `0.3`: Market sizing, payer analysis, competitive data extraction
- `0.5–0.7`: Messaging, positioning, strategy synthesis

**Always wrap `llm.invoke()` in try/except with a default fallback:**
```python
try:
    response = llm.invoke(prompt)
    result = parse_json_response(response.content)
except Exception as e:
    logger.error(f"LLM call failed in {agent_name}: {e}")
    result = default_fallback_data()
```

**JSON parsing pattern (current — fragile):**
```python
json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
data = json.loads(json_match.group())
```

**JSON parsing pattern (v2 — use Pydantic validation from SKILL_05):**
```python
from src.service.validators.json_validator import validate_competitor_json
result = validate_competitor_json(response_text)
if not result.valid:
    logger.warning(f"Validation errors: {result.errors}")
    # use fallback
```

---

## State Extension Pattern

When adding new data to GTMState for v2 features:

1. Add a new `@dataclass` to `src/schema/gtm_state.py`
2. Add `Optional[NewDataClass] = None` field to `GTMState`
3. Call `state.mark_agent_complete("New Agent Name")` in the agent
4. Update `progress_percentage` denominator if adding a main pipeline agent

Example:
```python
# In src/schema/gtm_state.py
@dataclass
class KOLProfile:
    kol_name: str
    institution: str
    influence_tier: str
    publication_count: int
    recent_publications: List[Dict]
    clinical_trial_pi: List[str]
    ...

# In GTMState class
kol_profile: Optional[KOLProfile] = None
current_doctor: Optional[str] = None      # add these for KOL context
current_hospital: Optional[str] = None
```

---

## Known Critical Bugs (Fix These Before Adding Features)

| Bug | Location | Impact | Fix |
|-----|---------|--------|-----|
| **Competitor hallucination** | `competitor_analysis_agent.py` lines 59–128 | All competitor names, pricing, market share are LLM-fabricated | Wire `fda_tools.py` + Tavily fact-check pass (SKILL_01) |
| **fda_tools.py never called** | `src/service/tools/fda_tools.py` | 197 lines of working FDA API code, completely unused | Call from `competitor_analysis_agent.py` and `market_research_agent.py` |
| **agent_messages.py unused** | `src/schema/agent_messages.py` | Message schemas defined, no agent uses them | Activate in v2 for audit trail (SKILL_05) |
| **Hardcoded hospital list** | `src/ui/app.py` `get_hospital_list()` | Only 7 US cancer centers, all oncology | Move to SQLite table (SKILL_06) |
| **No session persistence** | `src/ui/app.py` | GTMState lost on Streamlit page refresh | Add brief_cache table (SKILL_06) |
| **Fragile JSON parsing** | All 6 agent files | `re.search(r'\{.*\}')` fails on nested JSON ~20–30% of responses | Replace with Pydantic validators (SKILL_05) |
| **Max 20 publications** | `market_research_agent.py` | Caps evidence at 20 PubMed results regardless of drug | Increase limit + use RAG ranking (SKILL_01) |

---

## v2 Feature Areas

Reference the skill files when implementing each area:

| Feature | Skill File | New Agents | Core Problem Solved |
|---------|-----------|-----------|-------------------|
| KOL profiling + RAG evidence | SKILL_01 | `kol_profiling_agent` | Generic briefs → KOL-specific intelligence |
| Post-call insight capture | SKILL_02 | `insight_extraction_agent` | Insights lost in freeform notes |
| Engagement quality tracking | SKILL_03 | `engagement_scoring_agent` | Activity counts ≠ quality |
| Territory intelligence | SKILL_04 | `field_synthesis_agent` | Insights never reach medical strategy |
| Data quality & reliability | SKILL_05 | none (service layer) | Fragile JSON, no retry, no caching |
| Persistent memory | SKILL_06 | `memory_retrieval_agent` | State lost on refresh, no history |
| Test-driven development | SKILL_07 | none (process) | No tests = regressions on every change |
| Systematic debugging | SKILL_08 | none (process) | Random fixes waste time, create new bugs |
| UI/UX standards | SKILL_09 | none (UI layer) | Confidence badges, accessibility, chart standards |
| Development workflow | SKILL_10 | none (process) | 3-phase local-first: explore → plan → implement |
| Territory intelligence | SKILL_04 | `field_synthesis_agent` | Insights never reach medical strategy |
| Data quality & reliability | SKILL_05 | none (service layer) | Fragile JSON, no retry, no caching |
| Persistent memory | SKILL_06 | `memory_retrieval_agent` | State lost on refresh, no history |

---

## New v2 Agent Naming Convention

```
memory_retrieval_agent     → runs first; loads prior KOL context from SQLite
kol_profiling_agent        → replaces icp_definition_agent for KOL-specific use
insight_extraction_agent   → post-call; extracts structured insights from field notes
engagement_scoring_agent   → scores interaction quality 0–10
field_synthesis_agent      → territory-wide insight aggregation (on-demand, not per-call)
```

---

## New Dependencies for v2

Add these to `requirements.txt`:

```
chromadb>=0.5.0                   # vector store for RAG (SKILL_01, SKILL_06)
rank-bm25>=0.2.2                  # BM25 hybrid retrieval (SKILL_01)
sentence-transformers>=2.2.0      # local embeddings, no extra API (SKILL_01, SKILL_06)
sqlalchemy>=2.0.0                 # ORM for SQLite persistence (SKILL_06)
alembic>=1.13.0                   # DB migrations (SKILL_06)
passlib[bcrypt]>=1.7.4            # password hashing for auth
python-jose[cryptography]>=3.3.0  # JWT tokens
slowapi>=0.1.9                    # FastAPI rate limiting
pytest>=8.0.0                     # testing
pytest-asyncio>=0.23.0            # async agent testing
```

Note: `tenacity>=9.1.4` is already in `requirements.txt` — use it for retry logic (SKILL_05).

---

## Testing Conventions

```
tests/                              (create this directory)
├── test_market_research_agent.py
├── test_competitor_analysis_agent.py
├── test_insight_extraction_agent.py
├── test_json_validator.py
├── test_cache_manager.py
└── conftest.py                     (shared fixtures)
```

**Standard test fixture** — use `sotorasib` + `KRAS G12C NSCLC` as the working demo case:
```python
# conftest.py
@pytest.fixture
def demo_state():
    return GTMState(drug_name="sotorasib", indication="KRAS G12C NSCLC")
```

**Mock LLM calls** — never make real API calls in unit tests:
```python
from unittest.mock import patch, MagicMock

@patch("src.core.llm.get_claude")
def test_agent(mock_llm, demo_state):
    mock_llm.return_value.invoke.return_value.content = '{"key": "value"}'
    ...
```

---

## FastAPI Backend (Stubbed — Wire in v2)

`FastAPI` is in `requirements.txt` and `settings.py` has `FASTAPI_HOST`/`FASTAPI_PORT` but
nothing is wired. In v2, expose a REST API at `src/api/main.py`:

```
POST   /api/v1/auth/login
GET    /api/v1/briefs/{drug_name}/{indication}
POST   /api/v1/briefs/generate
GET    /api/v1/kols/{kol_id}
GET    /api/v1/kols/search?q=...&institution=...
POST   /api/v1/insights
GET    /api/v1/insights?drug_name=...&days=90
GET    /api/v1/territory/{territory_id}/dashboard
GET    /api/v1/territory/{territory_id}/coverage-gaps
```

Auth via JWT Bearer tokens using `settings.AUTH_SECRET` (already in `settings.py`).

---

## Security Notes for Pharma Enterprise

1. **Never commit `evidentia.db`** — add to `.gitignore`. Contains KOL interaction PII.
2. **Data confidence flags** — always show whether data is `FDA-verified`, `Tavily-sourced`, or `LLM-estimated` in the UI. Never hide provenance from users.
3. **No PHI in Tavily queries** — de-identify field notes before web search calls.
4. **Audit trail** — all LLM outputs must be logged with `timestamp + user_id` (compliance requirement in pharma for actions influencing HCP engagement).
5. **API keys** — never commit `.env`. Rotate immediately if exposed.
