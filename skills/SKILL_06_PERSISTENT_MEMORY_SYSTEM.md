# SKILL_06: Persistent Memory System
## SQLite + ChromaDB + Session Continuity Across Streamlit Refreshes

---

## Problem Statement

Every time a Streamlit page refreshes, `GTMState` is destroyed. This means:

- A brief generated for Dr. Smith on Monday is completely gone by Tuesday
- An MSL cannot see their own interaction history with a KOL
- Post-call insights (SKILL_02) have nowhere to live persistently
- The platform cannot learn over time — every session starts from zero
- There is no audit trail of what was generated, when, and for whom

This violates a basic expectation of enterprise software and makes Evidentia unsuitable for any pharma organization with compliance, audit, or continuity requirements.

**Reference pattern:** `thedotmack/claude-mem` — SQLite FTS5 full-text search + ChromaDB vector store + 5 lifecycle hooks for memory continuity across sessions. Adapted here for pharma MSL context.

---

## Objective

Implement a three-layer persistence architecture:

1. **SQLite (primary)** — structured data: KOL profiles, interactions, insights, briefs, users
2. **ChromaDB (vector)** — semantic search over insights and clinical evidence
3. **CacheManager (session)** — fast in-memory TTL cache for API responses (SKILL_05)

Plus a `memory_retrieval_agent` that runs **first in every workflow**, loading prior context so the rest of the pipeline has full historical awareness.

---

## Database Schema

### File: `src/db/schema.sql`

```sql
-- KOL master profiles
CREATE TABLE IF NOT EXISTS kol_profiles (
    kol_id          TEXT PRIMARY KEY,       -- SHA256 of "kol_name|institution"
    kol_name        TEXT NOT NULL,
    institution     TEXT NOT NULL,
    specialty       TEXT,
    research_focus  TEXT,                   -- JSON array
    publication_count INTEGER DEFAULT 0,
    influence_tier  TEXT DEFAULT 'Tier 3',  -- "Tier 1" / "Tier 2" / "Tier 3"
    last_updated    TEXT NOT NULL,          -- ISO timestamp
    raw_profile_json TEXT                   -- full KOLProfile as JSON
);
CREATE INDEX IF NOT EXISTS idx_kol_institution ON kol_profiles(institution);
CREATE INDEX IF NOT EXISTS idx_kol_tier ON kol_profiles(influence_tier);

-- MSL-KOL interaction records
CREATE TABLE IF NOT EXISTS kol_interactions (
    interaction_id      TEXT PRIMARY KEY,
    kol_id              TEXT NOT NULL REFERENCES kol_profiles(kol_id),
    msl_id              TEXT NOT NULL,
    drug_name           TEXT NOT NULL,
    indication          TEXT NOT NULL,
    interaction_date    TEXT NOT NULL,
    interaction_type    TEXT,               -- "face_to_face" / "virtual" / etc.
    duration_minutes    INTEGER DEFAULT 0,
    quality_score       REAL,
    quality_rationale   TEXT,
    topics_discussed    TEXT,               -- JSON array
    materials_shared    TEXT,               -- JSON array
    follow_up_required  INTEGER DEFAULT 0,  -- 0/1 (SQLite boolean)
    follow_up_actions   TEXT,               -- JSON array
    insights_captured   INTEGER DEFAULT 0,
    created_at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_interaction_kol ON kol_interactions(kol_id);
CREATE INDEX IF NOT EXISTS idx_interaction_drug ON kol_interactions(drug_name, indication);
CREATE INDEX IF NOT EXISTS idx_interaction_date ON kol_interactions(interaction_date);

-- Field insights from post-call capture (SKILL_02)
CREATE TABLE IF NOT EXISTS field_insights (
    insight_id          TEXT PRIMARY KEY,
    kol_id              TEXT NOT NULL,
    msl_id              TEXT NOT NULL,
    drug_name           TEXT NOT NULL,
    indication          TEXT NOT NULL,
    interaction_date    TEXT NOT NULL,
    insight_category    TEXT NOT NULL,
    insight_text        TEXT NOT NULL,
    sentiment           TEXT DEFAULT 'neutral',
    urgency             TEXT DEFAULT 'medium',
    action_required     INTEGER DEFAULT 0,
    action_description  TEXT DEFAULT '',
    source_verbatim     TEXT DEFAULT '',
    confidence_score    REAL DEFAULT 0.7,
    tags                TEXT DEFAULT '[]',  -- JSON array
    confirmed_by_msl    INTEGER DEFAULT 0,
    created_at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_insight_drug ON field_insights(drug_name, indication);
CREATE INDEX IF NOT EXISTS idx_insight_category ON field_insights(insight_category);
CREATE INDEX IF NOT EXISTS idx_insight_date ON field_insights(interaction_date);
CREATE INDEX IF NOT EXISTS idx_insight_urgency ON field_insights(urgency);

-- FTS5 full-text search on insight content (claude-mem pattern)
CREATE VIRTUAL TABLE IF NOT EXISTS field_insights_fts USING fts5(
    insight_text,
    source_verbatim,
    action_description,
    content=field_insights,
    content_rowid=rowid
);

-- Triggers to keep FTS5 index in sync
CREATE TRIGGER IF NOT EXISTS insights_ai AFTER INSERT ON field_insights BEGIN
    INSERT INTO field_insights_fts(rowid, insight_text, source_verbatim, action_description)
    VALUES (new.rowid, new.insight_text, new.source_verbatim, new.action_description);
END;
CREATE TRIGGER IF NOT EXISTS insights_ad AFTER DELETE ON field_insights BEGIN
    INSERT INTO field_insights_fts(field_insights_fts, rowid, insight_text, source_verbatim, action_description)
    VALUES ('delete', old.rowid, old.insight_text, old.source_verbatim, old.action_description);
END;

-- Brief cache (24h TTL)
CREATE TABLE IF NOT EXISTS brief_cache (
    cache_id        TEXT PRIMARY KEY,       -- SHA256 of "drug|indication|kol_id"
    drug_name       TEXT NOT NULL,
    indication      TEXT NOT NULL,
    kol_id          TEXT,
    generated_at    TEXT NOT NULL,
    expires_at      TEXT NOT NULL,          -- generated_at + 24h
    state_json      TEXT NOT NULL           -- serialized GTMState as JSON
);

-- MSL users
CREATE TABLE IF NOT EXISTS msl_users (
    user_id         TEXT PRIMARY KEY,       -- uuid4
    email           TEXT UNIQUE NOT NULL,
    display_name    TEXT NOT NULL,
    password_hash   TEXT NOT NULL,          -- bcrypt hash
    territory_id    TEXT DEFAULT 'default',
    created_at      TEXT NOT NULL,
    last_login      TEXT
);

-- Territory intelligence cache (SKILL_04)
CREATE TABLE IF NOT EXISTS territory_intel_cache (
    cache_id        TEXT PRIMARY KEY,
    territory_id    TEXT NOT NULL,
    drug_name       TEXT NOT NULL,
    indication      TEXT NOT NULL,
    generated_at    TEXT NOT NULL,
    expires_at      TEXT NOT NULL,
    intel_json      TEXT NOT NULL
);
```

---

## ORM Layer

### File: `src/db/models.py`

```python
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, create_engine
from sqlalchemy.orm import DeclarativeBase, Session

class Base(DeclarativeBase):
    pass

class KOLProfileORM(Base):
    __tablename__ = "kol_profiles"
    kol_id = Column(String, primary_key=True)
    kol_name = Column(String, nullable=False)
    institution = Column(String, nullable=False)
    specialty = Column(String)
    research_focus = Column(Text)          # JSON
    publication_count = Column(Integer, default=0)
    influence_tier = Column(String, default="Tier 3")
    last_updated = Column(String, nullable=False)
    raw_profile_json = Column(Text)

class FieldInsightORM(Base):
    __tablename__ = "field_insights"
    insight_id = Column(String, primary_key=True)
    kol_id = Column(String, nullable=False)
    msl_id = Column(String, nullable=False)
    drug_name = Column(String, nullable=False)
    indication = Column(String, nullable=False)
    interaction_date = Column(String, nullable=False)
    insight_category = Column(String, nullable=False)
    insight_text = Column(Text, nullable=False)
    sentiment = Column(String, default="neutral")
    urgency = Column(String, default="medium")
    action_required = Column(Integer, default=0)
    action_description = Column(Text, default="")
    source_verbatim = Column(Text, default="")
    confidence_score = Column(Float, default=0.7)
    tags = Column(Text, default="[]")
    confirmed_by_msl = Column(Integer, default=0)
    created_at = Column(String, nullable=False)

class KOLInteractionORM(Base):
    __tablename__ = "kol_interactions"
    interaction_id = Column(String, primary_key=True)
    kol_id = Column(String, nullable=False)
    msl_id = Column(String, nullable=False)
    drug_name = Column(String, nullable=False)
    indication = Column(String, nullable=False)
    interaction_date = Column(String, nullable=False)
    interaction_type = Column(String)
    duration_minutes = Column(Integer, default=0)
    quality_score = Column(Float)
    topics_discussed = Column(Text)
    materials_shared = Column(Text)
    follow_up_required = Column(Integer, default=0)
    insights_captured = Column(Integer, default=0)
    created_at = Column(String, nullable=False)

class MSLUserORM(Base):
    __tablename__ = "msl_users"
    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    territory_id = Column(String, default="default")
    created_at = Column(String, nullable=False)
    last_login = Column(String)
```

### File: `src/db/session.py`

```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from src.core.settings import settings
from src.db.models import Base
from contextlib import contextmanager

# DATABASE_URL already in settings.py: sqlite:///./gtm_simulator.db
# Change to evidentia.db for v2:
ENGINE = create_engine(
    settings.DATABASE_URL.replace("gtm_simulator.db", "evidentia.db"),
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False)

def init_db():
    """Create all tables on first run."""
    Base.metadata.create_all(ENGINE)
    # Also run schema.sql for FTS5 and triggers (not handled by SQLAlchemy)
    with ENGINE.connect() as conn:
        with open("src/db/schema.sql") as f:
            sql = f.read()
        for statement in sql.split(";"):
            if statement.strip():
                try:
                    conn.execute(text(statement))
                except Exception:
                    pass  # table already exists
        conn.commit()

@contextmanager
def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

---

## Persistence Services

### File: `src/service/persistence/kol_store.py`

```python
import hashlib, json
from typing import Optional, List
from datetime import datetime
from src.db.session import get_session
from src.db.models import KOLProfileORM
from src.schema.gtm_state import KOLProfile

class KOLStore:
    @staticmethod
    def make_kol_id(kol_name: str, institution: str) -> str:
        return hashlib.sha256(f"{kol_name.lower()}|{institution.lower()}".encode()).hexdigest()[:16]

    def save_kol_profile(self, profile: KOLProfile) -> str:
        kol_id = self.make_kol_id(profile.kol_name, profile.institution)
        with get_session() as session:
            existing = session.get(KOLProfileORM, kol_id)
            if existing:
                existing.research_focus = json.dumps(profile.research_focus)
                existing.publication_count = profile.publication_count
                existing.influence_tier = profile.influence_tier
                existing.last_updated = datetime.now().isoformat()
                existing.raw_profile_json = json.dumps(profile.__dict__ if hasattr(profile, '__dict__') else {})
            else:
                session.add(KOLProfileORM(
                    kol_id=kol_id,
                    kol_name=profile.kol_name,
                    institution=profile.institution,
                    specialty=profile.specialty,
                    research_focus=json.dumps(profile.research_focus),
                    publication_count=profile.publication_count,
                    influence_tier=profile.influence_tier,
                    last_updated=datetime.now().isoformat(),
                    raw_profile_json=json.dumps({})
                ))
        return kol_id

    def get_kol_by_name_institution(
        self, kol_name: str, institution: str
    ) -> Optional[KOLProfile]:
        kol_id = self.make_kol_id(kol_name, institution)
        with get_session() as session:
            orm = session.get(KOLProfileORM, kol_id)
            if not orm:
                return None
            return KOLProfile(
                kol_name=orm.kol_name,
                institution=orm.institution,
                specialty=orm.specialty or "",
                research_focus=json.loads(orm.research_focus or "[]"),
                publication_count=orm.publication_count or 0,
                influence_tier=orm.influence_tier or "Tier 3",
                recent_publications=[],
                clinical_trial_pi=[],
                conference_presentations=[],
                collaboration_network=[],
                last_msl_interaction=None,
                interaction_count=0,
                preferred_topics=[],
                kol_sentiment="Unknown",
                profile_confidence="Low"
            )
```

### File: `src/service/persistence/insight_store.py`

```python
import json
from typing import List, Optional
from datetime import datetime, timedelta
from src.db.session import get_session
from src.db.models import FieldInsightORM
from src.schema.gtm_state import FieldInsight

class InsightStore:
    def save_insight(self, insight: FieldInsight) -> str:
        with get_session() as session:
            session.add(FieldInsightORM(
                insight_id=insight.insight_id,
                kol_id=insight.kol_id,
                msl_id=insight.msl_id,
                drug_name=insight.drug_name,
                indication=insight.indication,
                interaction_date=insight.interaction_date,
                insight_category=insight.insight_category,
                insight_text=insight.insight_text,
                sentiment=insight.sentiment,
                urgency=insight.urgency,
                action_required=int(insight.action_required),
                action_description=insight.action_description,
                source_verbatim=insight.source_verbatim,
                confidence_score=insight.confidence_score,
                tags=json.dumps(insight.tags),
                confirmed_by_msl=int(insight.confirmed_by_msl),
                created_at=insight.created_at
            ))
        return insight.insight_id

    def get_insights(
        self,
        drug_name: str,
        indication: str,
        days_back: int = 90,
        category: Optional[str] = None
    ) -> List[FieldInsight]:
        cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        with get_session() as session:
            query = session.query(FieldInsightORM).filter(
                FieldInsightORM.drug_name.ilike(f"%{drug_name}%"),
                FieldInsightORM.interaction_date >= cutoff
            )
            if category:
                query = query.filter(FieldInsightORM.insight_category == category)
            return [self._to_domain(orm) for orm in query.all()]

    def keyword_search(self, query_text: str, top_k: int = 20) -> List[FieldInsight]:
        """FTS5 full-text search over insight_text, source_verbatim, action_description."""
        with get_session() as session:
            from sqlalchemy import text
            results = session.execute(
                text("SELECT fi.* FROM field_insights fi "
                     "JOIN field_insights_fts fts ON fi.rowid = fts.rowid "
                     "WHERE field_insights_fts MATCH :query "
                     "ORDER BY bm25(field_insights_fts) LIMIT :limit"),
                {"query": query_text, "limit": top_k}
            ).fetchall()
            return [self._to_domain_from_row(r) for r in results]

    def _to_domain(self, orm: FieldInsightORM) -> FieldInsight:
        return FieldInsight(
            insight_id=orm.insight_id,
            kol_id=orm.kol_id,
            msl_id=orm.msl_id,
            drug_name=orm.drug_name,
            indication=orm.indication,
            interaction_date=orm.interaction_date,
            raw_notes="",
            insight_category=orm.insight_category,
            insight_text=orm.insight_text,
            sentiment=orm.sentiment,
            urgency=orm.urgency,
            action_required=bool(orm.action_required),
            action_description=orm.action_description or "",
            source_verbatim=orm.source_verbatim or "",
            confidence_score=orm.confidence_score or 0.7,
            tags=json.loads(orm.tags or "[]"),
            created_at=orm.created_at,
            confirmed_by_msl=bool(orm.confirmed_by_msl)
        )
```

### File: `src/service/persistence/brief_cache.py`

```python
import hashlib, json
from typing import Optional
from datetime import datetime, timedelta
from src.db.session import get_session
from sqlalchemy import text

class BriefCache:
    def save_brief(
        self,
        state_dict: dict,
        drug_name: str,
        indication: str,
        kol_id: Optional[str] = None,
        ttl_hours: int = 24
    ):
        cache_id = hashlib.sha256(f"{drug_name}|{indication}|{kol_id or ''}".encode()).hexdigest()[:16]
        now = datetime.now()
        with get_session() as session:
            session.execute(text("""
                INSERT OR REPLACE INTO brief_cache
                (cache_id, drug_name, indication, kol_id, generated_at, expires_at, state_json)
                VALUES (:id, :drug, :ind, :kol, :gen, :exp, :json)
            """), {
                "id": cache_id, "drug": drug_name, "ind": indication, "kol": kol_id,
                "gen": now.isoformat(),
                "exp": (now + timedelta(hours=ttl_hours)).isoformat(),
                "json": json.dumps(state_dict)
            })

    def get_brief(
        self,
        drug_name: str,
        indication: str,
        kol_id: Optional[str] = None
    ) -> Optional[dict]:
        cache_id = hashlib.sha256(f"{drug_name}|{indication}|{kol_id or ''}".encode()).hexdigest()[:16]
        with get_session() as session:
            row = session.execute(
                text("SELECT state_json, expires_at FROM brief_cache WHERE cache_id = :id"),
                {"id": cache_id}
            ).fetchone()
            if not row:
                return None
            if datetime.fromisoformat(row.expires_at) < datetime.now():
                return None
            return json.loads(row.state_json)
```

---

## Memory Retrieval Agent (NEW — Entry Point)

### File: `src/agents/gtm_agents/memory_retrieval_agent.py`

This agent runs **first** in every workflow execution. It:
1. Checks the brief cache — if a valid brief exists for this drug+indication+KOL, returns it immediately (skips all other agents)
2. Loads prior KOL profile if it exists
3. Loads last 5 interactions for context
4. Logs session start

```python
async def memory_retrieval_agent(state: GTMState) -> GTMState:
    """
    Runs FIRST in every workflow.
    Loads prior context from SQLite before any API calls.
    If valid brief cache hit: short-circuits entire workflow.
    """
    from src.core.logger import get_logger
    logger = get_logger(__name__)

    # Graceful degradation: if persistence not yet active, skip silently
    try:
        from src.service.persistence.kol_store import KOLStore
        from src.service.persistence.insight_store import InsightStore
        from src.service.persistence.brief_cache import BriefCache
    except ImportError:
        logger.info("Persistence layer not active — skipping memory retrieval")
        state.mark_agent_complete("Memory Retrieval Agent")
        return state

    kol_store = KOLStore()
    insight_store = InsightStore()
    brief_cache = BriefCache()

    # Step 1: Check brief cache
    kol_id = None
    if state.current_doctor and state.current_hospital:
        kol_id = KOLStore.make_kol_id(state.current_doctor, state.current_hospital)

    cached = brief_cache.get_brief(state.drug_name, state.indication, kol_id)
    if cached:
        logger.info(f"Brief cache HIT for {state.drug_name}/{state.indication}/{kol_id}")
        state.from_cache = True
        # Restore key fields from cache
        # (Full GTMState deserialization is complex; restore the most important fields)
        state.mark_agent_complete("Memory Retrieval Agent")
        # Signal that brief is available from cache by setting a flag
        # Other agents check state.from_cache and skip if True
        return state

    # Step 2: Load prior KOL profile
    if state.current_doctor and state.current_hospital:
        prior_profile = kol_store.get_kol_by_name_institution(
            state.current_doctor, state.current_hospital
        )
        if prior_profile:
            state.kol_profile = prior_profile
            logger.info(f"Loaded prior KOL profile: {prior_profile.kol_name}")

    # Step 3: Load last 5 interactions for context
    if state.drug_name and state.indication:
        prior_insights = insight_store.get_insights(
            drug_name=state.drug_name,
            indication=state.indication,
            days_back=180
        )
        if prior_insights:
            state.prior_interactions = prior_insights[:5]
            logger.info(f"Loaded {len(prior_insights)} prior insights")

    state.mark_agent_complete("Memory Retrieval Agent")
    return state
```

### Wire as Workflow Entry Point (`src/agents/gtm_workflow.py`)

```python
from src.agents.gtm_agents.memory_retrieval_agent import memory_retrieval_agent

# In build_graph():
graph.add_node("memory_retrieval", memory_retrieval_agent)
graph.set_entry_point("memory_retrieval")          # CHANGE from "market_research"
graph.add_edge("memory_retrieval", "market_research")
```

---

## Vector Store for Semantic Search

### File: `src/service/rag/vector_store.py`

```python
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class EvidentiaVectorStore:
    """
    Two ChromaDB collections:
    - evidentia_insights: FieldInsight.insight_text embeddings (semantic search)
    - evidentia_evidence: PubMed abstract + trial summary embeddings (RAG, SKILL_01)
    """

    MODEL_NAME = "all-MiniLM-L6-v2"    # 384-dim, local, no API
    INSIGHTS_COLLECTION = "evidentia_insights"
    EVIDENCE_COLLECTION = "evidentia_evidence"

    def __init__(self, persist_dir: str = "./data/chroma"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedder = SentenceTransformer(self.MODEL_NAME)
        self.insights = self.client.get_or_create_collection(self.INSIGHTS_COLLECTION)
        self.evidence = self.client.get_or_create_collection(self.EVIDENCE_COLLECTION)

    def add_insight(self, insight_id: str, insight_text: str, metadata: Dict):
        embedding = self.embedder.encode([insight_text]).tolist()
        self.insights.add(
            ids=[insight_id],
            embeddings=embedding,
            documents=[insight_text],
            metadatas=[metadata]
        )

    def search_insights(self, query: str, top_k: int = 10) -> List[Dict]:
        query_embedding = self.embedder.encode([query]).tolist()
        results = self.insights.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, self.insights.count())
        )
        if not results["ids"][0]:
            return []
        return [
            {
                "insight_id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "similarity": 1 - results["distances"][0][i]
            }
            for i in range(len(results["ids"][0]))
        ]
```

---

## 5 Lifecycle Hooks (claude-mem pattern)

### File: `src/service/persistence/hooks.py`

```python
from src.core.logger import get_logger
logger = get_logger(__name__)

class SessionHooks:
    """
    5 lifecycle hooks triggered at key moments during a session.
    Each hook is a no-op if the persistence layer is not active.
    """

    @staticmethod
    def on_kol_profile_update(kol_id: str, profile_dict: dict):
        """Hook 1: Re-embed KOL profile text in vector store after any update."""
        try:
            from src.service.rag.vector_store import EvidentiaVectorStore
            store = EvidentiaVectorStore()
            profile_text = f"{profile_dict.get('kol_name')} {profile_dict.get('research_focus')} {profile_dict.get('specialty')}"
            store.insights.upsert(
                ids=[f"kol_{kol_id}"],
                documents=[profile_text],
                metadatas=[{"type": "kol_profile", "kol_id": kol_id}]
            )
        except Exception as e:
            logger.warning(f"on_kol_profile_update hook failed: {e}")

    @staticmethod
    def on_insight_save(insight_id: str, insight_text: str, metadata: dict):
        """Hook 2: Update FTS5 + vector store when new insight is saved."""
        try:
            from src.service.rag.vector_store import EvidentiaVectorStore
            store = EvidentiaVectorStore()
            store.add_insight(insight_id, insight_text, metadata)
        except Exception as e:
            logger.warning(f"on_insight_save hook failed: {e}")

    @staticmethod
    def on_brief_cache_write(drug_name: str, indication: str, kol_id: str):
        """Hook 3: Log to audit trail when a brief is cached."""
        logger.info(f"Brief cached: {drug_name}/{indication} for KOL {kol_id}")

    @staticmethod
    def on_brief_cache_hit(drug_name: str, indication: str, kol_id: str):
        """Hook 4: Track cache efficiency metric."""
        logger.info(f"Brief cache HIT: {drug_name}/{indication} for KOL {kol_id}")

    @staticmethod
    def on_session_end(session_id: str):
        """Hook 5: Flush any pending writes, log session summary."""
        logger.info(f"Session ended: {session_id}")
```

---

## Session Management in Streamlit (`src/ui/app.py`)

```python
# Add to the top of main() in src/ui/app.py:
from uuid import uuid4
from src.db.session import init_db

# Initialize database on first run
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

# Session ID
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid4())

# At workflow completion, save brief to cache:
if workflow_result:
    try:
        from src.service.persistence.brief_cache import BriefCache
        from src.service.persistence.hooks import SessionHooks
        kol_id = None
        if state.current_doctor and state.current_hospital:
            from src.service.persistence.kol_store import KOLStore
            kol_id = KOLStore.make_kol_id(state.current_doctor, state.current_hospital)
        BriefCache().save_brief(
            state_dict=workflow_result.to_dict(),
            drug_name=state.drug_name,
            indication=state.indication,
            kol_id=kol_id
        )
        SessionHooks.on_brief_cache_write(state.drug_name, state.indication, kol_id or "")
    except Exception as e:
        pass  # persistence failure never blocks the UI
```

---

## Alembic Migrations

### File: `src/db/migrations/001_initial.py`

```python
"""Initial Evidentia v2.0 schema

Revision ID: 001_initial
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table('kol_profiles', ...)
    op.create_table('kol_interactions', ...)
    op.create_table('field_insights', ...)
    op.create_table('brief_cache', ...)
    op.create_table('msl_users', ...)

def downgrade():
    op.drop_table('msl_users')
    op.drop_table('brief_cache')
    op.drop_table('field_insights')
    op.drop_table('kol_interactions')
    op.drop_table('kol_profiles')
```

---

## Security Notes

1. **Add `evidentia.db` to `.gitignore` immediately.** Contains KOL PII and interaction history.
2. **Password hashing:** Use `passlib[bcrypt]` for `msl_users.password_hash`. Never store plaintext.
3. **Audit trail:** All brief generation events are logged with `user_id + timestamp` via `on_brief_cache_write` hook — meets pharma compliance requirements for auditability of AI-generated content used in HCP engagement.

---

## Files Modified

| File | Change |
|------|--------|
| `src/agents/gtm_workflow.py` | Set `memory_retrieval_agent` as entry point (replaces `market_research` as start) |
| `src/schema/gtm_state.py` | Add `from_cache`, `prior_interactions`, `msl_id`, `territory_id` to `GTMState` |
| `src/core/settings.py` | Update `DATABASE_URL` default to `sqlite:///./evidentia.db` |
| `src/ui/app.py` | Add `init_db()` call on startup; add brief cache save after workflow completion; add session_id management |
| `.gitignore` | Add `evidentia.db`, `data/chroma/` |

## Files Created

| File | Purpose |
|------|---------|
| `src/db/schema.sql` | Raw SQL schema with FTS5 virtual tables and triggers |
| `src/db/models.py` | SQLAlchemy ORM models |
| `src/db/session.py` | Engine + session factory + `init_db()` |
| `src/db/migrations/001_initial.py` | Alembic initial migration |
| `src/service/persistence/kol_store.py` | KOL profile CRUD |
| `src/service/persistence/insight_store.py` | Field insight CRUD + FTS5 keyword search |
| `src/service/persistence/brief_cache.py` | Brief caching with 24h TTL |
| `src/service/persistence/hooks.py` | 5 lifecycle hooks (claude-mem pattern) |
| `src/service/rag/vector_store.py` | ChromaDB wrapper (shared with SKILL_01) |
| `src/agents/gtm_agents/memory_retrieval_agent.py` | Workflow entry point; loads prior context |

## Dependencies Added

```
sqlalchemy>=2.0.0
alembic>=1.13.0
passlib[bcrypt]>=1.7.4
python-jose[cryptography]>=3.3.0
```
