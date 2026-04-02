# Evidentia v2.0 — Technical Architecture

---

## v1.0 vs v2.0: What Changes

| Dimension | v1.0 (Current) | v2.0 (Target) |
|-----------|---------------|--------------|
| **Core function** | Pre-call brief generator | Closed-loop MSL intelligence platform |
| **State persistence** | Lost on page refresh | SQLite + ChromaDB (permanent) |
| **KOL intelligence** | Generic personas, 7 hospitals | KOL-specific profiles, 50+ institutions |
| **Clinical evidence** | 20 PubMed results, unranked | RAG pipeline: hybrid BM25 + vector + reranking |
| **Competitor data** | 100% LLM-hallucinated | FDA-verified + Tavily-sourced + confidence badges |
| **Post-call capture** | None | Structured insight extraction in <2 minutes |
| **Quality measurement** | None | Quality score 0–10 per interaction |
| **Territory intelligence** | None | Territory-wide synthesis across all MSL insights |
| **FDA tools** | Implemented, never called | Wired into competitor + market agents |
| **JSON parsing** | Bare regex, ~20% failure rate | Pydantic validation with graceful fallbacks |
| **Caching** | None | 1-hour TTL for API calls, 24-hour for briefs |
| **Authentication** | None | Session-based auth (OAuth2 deferred to v2.1) |

---

## Two-Pipeline Architecture

### Pipeline A: Pre-Call Brief Generation (Enhanced)

```
User Action: Select KOL + Drug + Indication → Click "Generate Brief"
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  LangGraph StateGraph — Pipeline A                               │
│                                                                   │
│  1. memory_retrieval_agent (NEW)                                  │
│     └─ Check brief cache → if HIT, skip all below, return <3s   │
│     └─ Load prior KOL profile from SQLite                        │
│     └─ Load last 5 interactions for context                      │
│                │                                                  │
│                ▼                                                  │
│  2. kol_profiling_agent (NEW)                                     │
│     └─ PubMed author search (existing PubMedClient)              │
│     └─ ClinicalTrials PI lookup (existing ClinicalTrialsClient)  │
│     └─ Tavily KOL profile search                                 │
│     └─ LLM synthesis → KOLProfile (tier, research focus, etc.)  │
│     └─ Save to SQLite kol_profiles                               │
│                │                                                  │
│       ┌────────┴────────┬────────────────┐                        │
│       ▼                 ▼                ▼                        │
│  3a. market_research   3b. payer_intel  3c. competitor_analysis  │
│      [RAG pipeline]    [PubMed HTA      [FDA-verified names      │
│      ClinTrials        +Tavily]          +Tavily pricing]         │
│      PubMed            NICE/EMA/ICER    fda_tools.py (WIRED)     │
│      FDA adverse       QALY threshold   data_confidence badges   │
│       events           pricing ceiling                            │
│       └────────┬────────┴────────────────┘                        │
│                ▼                                                  │
│  4. messaging_agent                                               │
│     └─ MSL-oriented talking points (not commercial personas)     │
│     └─ KOL-specific objection responses                          │
│     └─ Discovery questions based on KOL research focus           │
│                │                                                  │
│                ▼                                                  │
│  5. synthesis_agent                                               │
│     └─ 10-tab MSL pre-call brief                                 │
│     └─ Save to brief_cache (24h TTL)                             │
│     └─ Emit AgentMessages for audit trail                        │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
Streamlit UI — 10 Tabs:
  KOL Profile | Talking Points | Objection Handling | Discovery Questions
  Clinical Evidence | Reimbursement | Competitive | Final Brief | Ask Evidentia | Download
```

### Pipeline B: Post-Call Capture + Territory Intelligence

```
User Action: Post-Call Tab → Enter Field Notes → Submit
         │
         ▼
┌───────────────────────────────────────────────────────────────┐
│  Pipeline B — Post-Call                                        │
│                                                                │
│  1. insight_extraction_agent (NEW)                             │
│     └─ LLM (temp=0.2) extracts structured insights           │
│     └─ 10 insight categories (unmet need, competitive, etc.) │
│     └─ MSL reviews + confirms in UI                           │
│                │                                               │
│                ▼                                               │
│  2. engagement_scoring_agent (NEW)                             │
│     └─ Quality score 0–10 across 4 dimensions                │
│     └─ Saved to kol_interactions table                        │
│                │                                               │
│                ▼                                               │
│  3. SQLite Persistence                                         │
│     └─ field_insights table (FTS5 indexed)                    │
│     └─ ChromaDB insight embeddings                            │
│     └─ Lifecycle hooks: on_insight_save → vector store        │
└───────────────────────────────────────────────────────────────┘

User Action (async, on-demand): Field Intelligence Dashboard → Run Analysis
         │
         ▼
┌───────────────────────────────────────────────────────────────┐
│  field_synthesis_agent (NEW)                                   │
│  └─ Queries last 90 days of field_insights from SQLite        │
│  └─ LLM synthesis → TerritoryIntelligence                     │
│     - Top unmet needs with frequency + representative quotes   │
│     - Competitive signals (new mentions, prescribing shifts)  │
│     - Data gaps with action recommendations                   │
│     - Content gaps (what KOLs ask for that doesn't exist)     │
│     - Medical strategy recommendations                         │
│     - Safety signal escalation flags                          │
│  └─ Cached in territory_intel_cache (24h TTL)                 │
└───────────────────────────────────────────────────────────────┘
```

---

## GTMState v2 — Complete Field Inventory

New fields added to `GTMState` in `src/schema/gtm_state.py`:

```python
# UI context (set from Streamlit session before workflow starts)
current_doctor:     Optional[str]          # KOL name from sidebar
current_hospital:   Optional[str]          # Institution from sidebar
msl_id:             Optional[str]          # Logged-in user ID
territory_id:       Optional[str]          # MSL territory assignment

# Memory layer (populated by memory_retrieval_agent)
from_cache:         bool = False           # True if brief loaded from cache
prior_interactions: List[FieldInsight] = [] # Last 5 insights for this drug/KOL

# KOL Intelligence (populated by kol_profiling_agent)
kol_profile:        Optional[KOLProfile]

# Post-call inputs (set from Post-Call Capture UI)
raw_field_notes:    Optional[str]
interaction_date:   Optional[str]
interaction_type:   Optional[str]

# Post-call outputs
captured_insights:  List[FieldInsight] = []
current_interaction: Optional[KOLInteraction]

# Territory intelligence (populated by field_synthesis_agent)
territory_intelligence: Optional[TerritoryIntelligence]

# Audit trail (populated by all agents via agent_messages.py)
agent_messages:     List[AgentMessage] = []
```

---

## Database Architecture

### Three-Layer Storage

```
Layer 1: SQLite (evidentia.db) — Structured Data
  ├── kol_profiles              KOL master records + tier assignments
  ├── kol_interactions          Every MSL-KOL interaction with quality scores
  ├── field_insights            Post-call structured insights (FTS5 indexed)
  ├── field_insights_fts        Virtual FTS5 table for keyword search
  ├── brief_cache               Serialized GTMState with 24h expiry
  ├── msl_users                 MSL user accounts (bcrypt passwords)
  └── territory_intel_cache     field_synthesis_agent output (24h expiry)

Layer 2: ChromaDB (data/chroma/) — Vector Search
  ├── evidentia_insights        Embeddings of field_insights.insight_text
  └── evidentia_evidence        Embeddings of PubMed abstracts + trial summaries
  Model: sentence-transformers/all-MiniLM-L6-v2 (384-dim, local, no API cost)

Layer 3: CacheManager (in-process dict) — API Response Cache
  └── TTL-based dict keyed by hash(api_type|drug|indication)
  TTL: 1h for API responses, 6h for RAG indexes, 24h for briefs
```

### Entity Relationships

```
msl_users ──┐
            │ msl_id
            ▼
kol_profiles ──── kol_interactions ──── field_insights
     kol_id              kol_id              kol_id
                         drug/ind            drug/ind
                             │
                             └──── brief_cache (drug/ind/kol)
```

---

## Streamlit Multi-Page Architecture

Current: Single 1224-line `src/ui/app.py` handling everything.

v2.0 refactor to multi-page Streamlit app:

```
streamlit_app.py                     ← entry point (unchanged)
pages/
  01_Brief_Generator.py              ← current app.py refactored (10 tabs)
  02_Post_Call_Capture.py            ← SKILL_02: insight extraction UI
  03_KOL_Engagement.py               ← SKILL_03: coverage tracker
  04_Field_Intelligence.py           ← SKILL_04: territory dashboard
  05_Settings.py                     ← auth + territory config

src/ui/
  app.py                             ← Brief Generator (refactored, not deleted)
  components.py                      ← existing Plotly charts + metric cards
  components/                        ← new shared components
    kol_card.py                      ← KOL profile display card
    insight_card.py                  ← insight display with category badge
    confidence_badge.py              ← data confidence indicator
    quality_gauge.py                 ← quality score gauge (0–10)
```

---

## API Architecture (FastAPI — Wire in v2)

`FastAPI` is in `requirements.txt`. `settings.py` has `FASTAPI_HOST`/`FASTAPI_PORT`. Nothing is wired yet. v2.0 adds `src/api/main.py`:

```python
# REST API for CRM integration + mobile app access
POST   /api/v1/auth/login              → JWT token
GET    /api/v1/briefs/{drug}/{ind}     → get cached brief for drug+indication
POST   /api/v1/briefs/generate         → async trigger brief generation
GET    /api/v1/kols/{kol_id}           → KOL profile
GET    /api/v1/kols/search             → search by name/institution
POST   /api/v1/insights                → save post-call insight
GET    /api/v1/insights                → query insights (drug, days, category)
GET    /api/v1/territory/{id}/dashboard → territory intelligence
GET    /api/v1/territory/{id}/gaps     → coverage gap report
POST   /api/v1/content/{id}/usage      → record content use
```

Auth: JWT Bearer tokens via `settings.AUTH_SECRET`.
Middleware: CORS, slowapi rate limiting (100 req/min per user), request logging.

---

## Performance Targets

| Operation | Target | Mechanism |
|-----------|--------|-----------|
| Pre-call brief (full) | < 120 seconds | Sequential agents; RAG adds ~10s |
| Pre-call brief (cached) | < 3 seconds | brief_cache SQLite lookup |
| Post-call insight extraction | < 15 seconds | Single LLM call, temp=0.2 |
| Engagement scoring | < 10 seconds | Single LLM call, temp=0.2 |
| Territory synthesis (on-demand) | < 60 seconds | Single LLM call, 90-day insights |
| KOL profile lookup (cached) | < 1 second | SQLite kol_profiles index |
| API response cache hit rate | > 80% | CacheManager with 1h TTL |

---

## Authentication Architecture

**v2.0 MVP: Simple session auth (not OAuth)**
- Login page: email + bcrypt password stored in `msl_users` SQLite table
- Session token stored in `st.session_state`
- `msl_id` and `territory_id` propagated to `GTMState` from session

**v2.1 (deferred): Azure AD / Okta OAuth2**
- Most pharma companies use Azure AD for SSO
- SAML 2.0 integration via `python-saml` library
- `settings.AUTH_SECRET` already present for JWT signing

---

## Docker Compose v2.0

Additions to `docker-compose.yml`:

```yaml
services:
  app:
    # existing Streamlit service
    volumes:
      - ./data:/app/data    # mount data dir for SQLite + ChromaDB persistence
    environment:
      - DATABASE_URL=sqlite:////app/data/evidentia.db

  api:
    build: .
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8080
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
    depends_on:
      - app

volumes:
  data:
    driver: local
```

Note: ChromaDB runs embedded (no separate container needed for v2.0).
Separate ChromaDB container only needed at v2.1 scale (>10 concurrent users).

---

## Security Requirements for Enterprise Pharma

### Must-Have for Any Pilot
1. **`evidentia.db` never committed to git.** Add to `.gitignore` — contains KOL PII and interaction history.
2. **`data/chroma/` never committed to git.** Add to `.gitignore` — contains vector embeddings derived from proprietary field insights.
3. **Data confidence badges on all AI-generated data.** MSLs must know what they can rely on (SKILL_05).
4. **Audit trail for all brief generation.** `on_brief_cache_write` hook logs: user_id + drug + indication + timestamp.

### Required for Pharma Enterprise (beyond MVP)
5. **PHI de-identification.** Field notes may contain patient-identifiable information. De-identify before any Tavily web search queries.
6. **GxP audit logging.** All AI outputs used to inform HCP engagement must be logged with provenance for regulatory inspection.
7. **Data residency.** Enterprise pharma may require all data to remain in their cloud region (AWS/Azure deployment, not Railway.app).
8. **SOC 2 Type II.** Required for most pharma enterprise procurement. Target v2.2.

---

## 8-Week Implementation Sequence

```
Week 1: SKILL_05 — Data quality foundation
  ├── Pydantic validators for all 6 agents
  ├── Tenacity retry on all 4 API tools
  ├── CacheManager implementation
  └── Input validation in Streamlit UI

Week 2: SKILL_06 — Persistence foundation
  ├── SQLite schema + ORM models
  ├── Session setup + init_db()
  ├── BriefCache + KOLStore
  └── memory_retrieval_agent wired as entry point

Week 3: SKILL_01 Phase 1 — KOL profiling
  ├── kol_profiling_agent
  ├── KOLProfile dataclass
  ├── KOL Profile tab in UI
  └── Hospital database expanded (50+ institutions)

Week 4: SKILL_01 Phase 2–3 — Evidence + Competitor fix
  ├── ClinicalEvidenceRAG (ingest + retrieve)
  ├── RAG integrated into market_research_agent
  ├── fda_tools.py wired into competitor_analysis_agent
  └── Data confidence badges in UI

Week 5: SKILL_02 — Post-call insight capture
  ├── insight_extraction_agent
  ├── InsightStore (SQLite + FTS5)
  ├── Post-Call Capture tab in UI
  └── Safety signal escalation email

Week 6: SKILL_03 — Engagement tracking
  ├── engagement_scoring_agent
  ├── CoverageAnalytics service
  ├── KOL Engagement Tracker page
  └── Coverage gap detection

Week 7: SKILL_04 — Field intelligence dashboard
  ├── field_synthesis_agent
  ├── ContentAnalytics service
  └── Field Intelligence Dashboard page

Week 8: FastAPI + Integration testing
  ├── src/api/main.py with core endpoints
  ├── End-to-end test: full workflow + post-call + territory
  ├── Docker Compose with data volume mounts
  └── Verify: streamlit run streamlit_app.py still works unchanged
```

---

## New Dependencies Summary

Add to `requirements.txt`:

```
# SKILL_01 (RAG)
chromadb>=0.5.0
rank-bm25>=0.2.2
sentence-transformers>=2.2.0

# SKILL_06 (Persistence)
sqlalchemy>=2.0.0
alembic>=1.13.0
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0

# API layer
slowapi>=0.1.9

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0

# Already present — verify versions:
# tenacity>=9.1.4 (SKILL_05 retry logic)
# pydantic>=2.12.5 (SKILL_05 validators)
# fastapi>=0.135.1 (API layer)
```

---

## Verification Checklist

After completing implementation:

- [ ] `streamlit run streamlit_app.py` — existing app runs without errors
- [ ] Enter `sotorasib` + `KRAS G12C NSCLC` → brief generates in <120s
- [ ] Brief generation twice → second run uses cache (<3s)
- [ ] Post-call notes → insights extracted and displayed in UI
- [ ] KOL profile tab populated for any doctor in the hospital list
- [ ] Competitor data shows confidence badges (no bare numbers without source)
- [ ] `evidentia.db` created in project root (not committed to git)
- [ ] `data/chroma/` created for vector store (not committed to git)
- [ ] All 6 agent files use `validate_with_pydantic()` not bare `re.search + json.loads`
- [ ] `fda_tools.py` called from at least 2 agent files
- [ ] `pages/` directory contains at least 3 new Streamlit pages
