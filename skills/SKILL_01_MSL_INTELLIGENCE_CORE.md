# SKILL_01: MSL Intelligence Core
## KOL Profiling + RAG-Based Clinical Evidence + Fix Competitor Hallucination

---

## Problem Statement

The current pre-call brief is a generic GTM document with three critical failures:

1. **No KOL-specific profile.** The brief knows nothing about the specific doctor the MSL is meeting. There is no research focus, publication history, trial PI record, or interaction history for the individual KOL.

2. **Competitor data is entirely hallucinated.** `competitor_analysis_agent.py` asks the LLM to identify competitors and return pricing, market share, and clinical data — with no external source of truth. Every number is fabricated. An MSL using this data in front of a KOL risks embarrassment or compliance exposure.

3. **Clinical evidence is shallow and unranked.** PubMed results are capped at 20, retrieved in chronological order, and dumped into the brief without relevance ranking. The most clinically significant publications for a specific KOL conversation may not appear.

4. **`fda_tools.py` exists and works but is never called.** 197 lines of FDA OpenFDA API code — drug approvals, recalls, adverse events — completely unused.

---

## Objective

Transform the pre-call brief from a generic GTM summary into a KOL-specific, evidence-grounded intelligence package that takes 8–10 minutes to review (down from 45+ minutes of manual prep).

**Success criteria:**
- KOL profile section populated with research focus, publication count, trial PI roles
- Competitor data grounded in FDA approval records, not LLM imagination
- Top 5 most clinically relevant publications ranked by relevance to the specific KOL conversation
- `fda_tools.py` called from at least 2 agents

---

## Phase 1: KOL Profile Agent (New Agent)

### New File
`src/agents/gtm_agents/kol_profiling_agent.py`

### New Dataclass (add to `src/schema/gtm_state.py`)

```python
@dataclass
class KOLProfile:
    kol_name: str
    institution: str
    specialty: str
    research_focus: List[str]           # extracted from publications + Tavily
    publication_count: int              # from PubMed author search
    recent_publications: List[Dict]     # last 3 years: pmid, title, journal, year
    clinical_trial_pi: List[str]        # NCT IDs where this KOL is PI or co-PI
    conference_presentations: List[str] # congress abstracts/presentations
    collaboration_network: List[str]    # co-authors at other institutions (top 5)
    influence_tier: str                 # "Tier 1" / "Tier 2" / "Tier 3"
    last_msl_interaction: Optional[str] # ISO date, loaded from memory (SKILL_06)
    interaction_count: int              # total prior interactions
    preferred_topics: List[str]         # inferred from research focus
    kol_sentiment: str                  # "Favorable" / "Neutral" / "Skeptical" / "Unknown"
    profile_confidence: str             # "High" / "Medium" / "Low" (based on data found)

# Add to GTMState class:
# kol_profile: Optional[KOLProfile] = None
# current_doctor: Optional[str] = None
# current_hospital: Optional[str] = None
```

### Agent Implementation Pattern

```python
async def kol_profiling_agent(state: GTMState) -> GTMState:
    """
    Builds a KOL-specific intelligence profile before the pre-call brief.
    Uses: PubMedClient (existing), ClinicalTrialsClient (existing), Tavily (existing).
    Input:  state.current_doctor, state.current_hospital, state.indication
    Output: state.kol_profile (KOLProfile)
    """
    from src.service.tools.pubmed_tools import PubMedClient
    from src.service.tools.clinical_trials_tools import ClinicalTrialsClient
    from src.service.tools.tavily_tools import TavilySearchClient
    from src.core.llm import get_claude

    kol_name = state.current_doctor
    institution = state.current_hospital
    indication = state.indication

    # Step 1: PubMed author search (use existing PubMedClient)
    pubmed = PubMedClient()
    author_pubs = pubmed.search_publications(
        drug_name=kol_name,       # PubMed treats this as a text search — works for author names
        condition=indication,
        max_results=30
    )
    publication_count = len(author_pubs)
    recent_pubs = [p for p in author_pubs if int(p.get("publication_year", 0)) >= 2022]

    # Step 2: ClinicalTrials — find NCTs where KOL is PI
    trials_client = ClinicalTrialsClient()
    kol_trials = trials_client.search_trials(
        drug_name=kol_name,
        condition=indication,
        max_results=20
    )
    pi_trials = [t["nct_id"] for t in kol_trials if kol_name.lower() in
                 str(t.get("sponsor", "")).lower()]  # approximate PI detection

    # Step 3: Tavily — KOL profile, research focus, conference activity
    tavily = TavilySearchClient()
    profile_search = tavily.search(
        f"{kol_name} {institution} {indication} research publications clinical trials"
    )
    congress_search = tavily.search(
        f"{kol_name} {institution} congress presentation ASCO ESMO ASH 2023 2024 2025"
    )

    # Step 4: LLM synthesis of KOL profile
    llm = get_claude(temperature=0.3)
    synthesis_prompt = f"""
    Build a KOL intelligence profile for an MSL pre-call brief.

    KOL Name: {kol_name}
    Institution: {institution}
    Indication of Interest: {indication}

    PubMed Publications Found: {len(author_pubs)} total, {len(recent_pubs)} in last 3 years
    Recent Publication Titles: {[p.get('title', '') for p in recent_pubs[:5]]}

    Clinical Trials Data: {kol_trials[:5]}
    Web Profile Data: {profile_search.get('answer', '')}
    Congress Activity: {congress_search.get('answer', '')}

    Extract and return JSON:
    {{
      "research_focus": ["list of 3-5 specific research areas"],
      "preferred_topics": ["topics this KOL most cares about scientifically"],
      "collaboration_network": ["institution names of frequent co-authors"],
      "conference_presentations": ["recent congress/symposium appearances"],
      "kol_sentiment": "Favorable|Neutral|Skeptical|Unknown",
      "influence_tier": "Tier 1|Tier 2|Tier 3",
      "profile_confidence": "High|Medium|Low",
      "specialty": "primary medical specialty"
    }}

    Tier 1 = national/international KOL, >50 publications or major trial PI.
    Tier 2 = regional KOL, 20-50 publications or 1-3 trial PI roles.
    Tier 3 = local HCP, <20 publications.
    If data is insufficient, set profile_confidence to Low.
    Return JSON only.
    """

    # Parse + build KOLProfile (use SKILL_05 validation when available)
    ...

    state.kol_profile = kol_profile
    state.mark_agent_complete("KOL Profiling Agent")
    return state
```

### Register in Workflow (`src/agents/gtm_workflow.py`)

```python
# Add node
graph.add_node("kol_profiling", kol_profiling_agent)

# Insert after memory_retrieval (SKILL_06), before market_research
graph.add_edge("memory_retrieval", "kol_profiling")
graph.add_edge("kol_profiling", "market_research")
```

### Pass KOL Context from UI (`src/ui/app.py`)

The UI already has `current_hospital` and `current_doctor` in session state. Pass them to GTMState:

```python
# In run_workflow() function in src/ui/app.py
initial_state = GTMState(
    drug_name=drug_name,
    indication=indication,
    current_doctor=st.session_state.get("current_doctor", ""),
    current_hospital=st.session_state.get("current_hospital", "")
)
```

### UI: Add KOL Profile Tab

Add a 10th tab "KOL Profile" to `display_msl_results()` in `src/ui/app.py`:

```python
tab_kol, tab_talking, tab_objections, ... = st.tabs([
    "KOL Profile", "Talking Points", "Objection Handling", ...
])

with tab_kol:
    display_kol_profile_section(state)

def display_kol_profile_section(state: GTMState):
    if not state.kol_profile:
        st.info("KOL profile not available.")
        return
    profile = state.kol_profile

    col1, col2, col3 = st.columns(3)
    col1.metric("Influence Tier", profile.influence_tier)
    col2.metric("Publications", profile.publication_count)
    col3.metric("Trial PI Roles", len(profile.clinical_trial_pi))

    st.subheader("Research Focus")
    for area in profile.research_focus:
        st.write(f"• {area}")

    st.subheader("Recent Publications (Last 3 Years)")
    for pub in profile.recent_publications[:5]:
        st.write(f"**{pub.get('title')}** — {pub.get('journal')}, {pub.get('year')}")

    # Data confidence badge
    confidence_color = {"High": "green", "Medium": "orange", "Low": "red"}
    color = confidence_color.get(profile.profile_confidence, "gray")
    st.markdown(f"Profile Confidence: :{color}[{profile.profile_confidence}]")
```

---

## Phase 2: RAG-Based Clinical Evidence

### Reference Pattern
From `andresrogers/ai-clinical-trials-rag`: semantic chunking + hybrid BM25/vector retrieval + cross-encoder reranking. Achieves 0.972 faithfulness score on RAGAS evaluation.

### New Files

```
src/service/rag/
├── clinical_evidence_rag.py    ← main RAG class
├── vector_store.py             ← ChromaDB wrapper
└── retriever.py                ← hybrid BM25 + vector + reranking
```

### Implementation

```python
# src/service/rag/clinical_evidence_rag.py

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder

class ClinicalEvidenceRAG:
    """
    RAG pipeline for clinical evidence retrieval.
    Ingests: ClinicalTrials.gov + PubMed + FDA labels
    Retrieval: BM25 (0.4 weight) + vector cosine (0.6 weight) + cross-encoder rerank
    """

    MODEL_NAME = "all-MiniLM-L6-v2"       # 384-dim, runs locally, no API
    RERANKER_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self, collection_name: str):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(collection_name)
        self.embedder = SentenceTransformer(self.MODEL_NAME)
        self.reranker = CrossEncoder(self.RERANKER_NAME)
        self.bm25 = None
        self.corpus = []

    def ingest(self, drug_name: str, indication: str) -> int:
        """
        Fetch documents from ClinicalTrials + PubMed + FDA, chunk, embed, store.
        Returns: number of chunks ingested
        """
        documents = []

        # Fetch from PubMed (existing tool)
        from src.service.tools.pubmed_tools import PubMedClient
        pubmed = PubMedClient()
        pubs = pubmed.search_publications(drug_name, indication, max_results=50)
        for pub in pubs:
            text = f"{pub.get('title', '')}. {pub.get('abstract', '')}"
            documents.append({
                "text": text,
                "source": "pubmed",
                "pmid": pub.get("pmid", ""),
                "title": pub.get("title", ""),
                "year": pub.get("publication_year", "")
            })

        # Fetch from ClinicalTrials (existing tool)
        from src.service.tools.clinical_trials_tools import ClinicalTrialsClient
        trials_client = ClinicalTrialsClient()
        trials = trials_client.search_trials(drug_name, indication, max_results=30)
        for trial in trials:
            text = f"{trial.get('title', '')}. Phase: {trial.get('phase', '')}. Status: {trial.get('status', '')}."
            documents.append({
                "text": text,
                "source": "clinical_trials",
                "nct_id": trial.get("nct_id", ""),
                "phase": trial.get("phase", "")
            })

        # Fetch from FDA (existing but unused tool — wire it here)
        from src.service.tools.fda_tools import FDAClient
        fda = FDAClient()
        approvals = fda.search_drug_approvals(drug_name, max_results=5)
        for approval in approvals:
            text = f"FDA approval: {approval.get('drug_name', '')} by {approval.get('applicant', '')}. Approved: {approval.get('approval_date', '')}."
            documents.append({
                "text": text,
                "source": "fda",
                "nda_number": approval.get("nda_number", "")
            })

        # Chunk into 512-token overlapping windows
        chunks = self._chunk_documents(documents, chunk_size=400, overlap=50)

        # Embed + store in ChromaDB
        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.encode(texts).tolist()
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        metadatas = [{k: v for k, v in c.items() if k != "text"} for c in chunks]

        self.collection.add(documents=texts, embeddings=embeddings, ids=ids, metadatas=metadatas)

        # Build BM25 index
        tokenized_corpus = [t.lower().split() for t in texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.corpus = texts

        return len(chunks)

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Hybrid retrieval: BM25 + vector search → cross-encoder reranking.
        Returns top_k most relevant chunks with source citations.
        """
        # Vector search
        query_embedding = self.embedder.encode([query]).tolist()
        vector_results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(20, self.collection.count())
        )

        # BM25 search
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        top_bm25_indices = bm25_scores.argsort()[-20:][::-1]

        # Merge candidates (deduplicate by text)
        candidates = {}
        for i, doc in enumerate(vector_results["documents"][0]):
            candidates[doc] = {
                "text": doc,
                "metadata": vector_results["metadatas"][0][i],
                "vector_score": 1 - vector_results["distances"][0][i]  # cosine similarity
            }
        for idx in top_bm25_indices:
            text = self.corpus[idx]
            if text not in candidates:
                candidates[text] = {"text": text, "metadata": {}, "bm25_score": bm25_scores[idx]}
            else:
                candidates[text]["bm25_score"] = bm25_scores[idx]

        # Cross-encoder reranking
        candidate_list = list(candidates.values())
        pairs = [(query, c["text"]) for c in candidate_list]
        rerank_scores = self.reranker.predict(pairs)

        for i, c in enumerate(candidate_list):
            c["final_score"] = rerank_scores[i]

        candidate_list.sort(key=lambda x: x["final_score"], reverse=True)
        return candidate_list[:top_k]

    def _chunk_documents(self, documents, chunk_size=400, overlap=50):
        """Split documents into overlapping chunks preserving metadata."""
        chunks = []
        for doc in documents:
            words = doc["text"].split()
            for i in range(0, len(words), chunk_size - overlap):
                chunk_text = " ".join(words[i:i + chunk_size])
                chunk = {"text": chunk_text}
                chunk.update({k: v for k, v in doc.items() if k != "text"})
                chunks.append(chunk)
        return chunks
```

### Integration in `market_research_agent.py`

Replace the raw PubMed dump with RAG-ranked evidence:

```python
# In market_research_agent.py — replace direct PubMed call with RAG
from src.service.rag.clinical_evidence_rag import ClinicalEvidenceRAG
from src.service.cache.cache_manager import CacheManager  # SKILL_05

cache_key = CacheManager.make_key("rag", drug_name, indication)
rag = CacheManager.get(cache_key)
if not rag:
    rag = ClinicalEvidenceRAG(f"{drug_name}_{indication}".replace(" ", "_"))
    rag.ingest(drug_name, indication)
    CacheManager.set(cache_key, rag, ttl=3600)

# Query for most relevant evidence for this KOL's research focus
kol_topics = state.kol_profile.research_focus if state.kol_profile else [indication]
query = f"efficacy safety {drug_name} {indication} " + " ".join(kol_topics[:2])
top_evidence = rag.retrieve(query, top_k=5)

# Feed ranked evidence into the LLM prompt instead of raw PubMed list
```

---

## Phase 3: Fix Competitor Hallucination

### The Bug

`src/agents/gtm_agents/competitor_analysis_agent.py` (lines ~59–128):
- LLM is asked to name competitors and provide pricing, market share, launch dates
- No external validation
- Results are presented to MSLs as facts

### Fix Strategy

**Step 1:** LLM extracts candidate competitor names only (not data) from Tavily overview.

**Step 2:** For each candidate name, call `FDAClient.search_drug_approvals()` from `fda_tools.py` — this is the authoritative source for approval status, applicant, and approval date.

**Step 3:** Tavily fact-check for pricing signals only (FDA doesn't have pricing).

**Step 4:** Each `CompetitorData` object gets a `data_confidence` field.

```python
# Add data_confidence to CompetitorData in src/schema/gtm_state.py
@dataclass
class CompetitorData:
    competitor_name: str
    company: str
    indication: str
    market_share: Optional[float] = None      # None if not verifiable
    pricing: Optional[float] = None           # None if not verifiable
    key_differentiators: List[str] = field(default_factory=list)
    clinical_advantages: List[str] = field(default_factory=list)
    clinical_disadvantages: List[str] = field(default_factory=list)
    launch_date: Optional[str] = None
    annual_sales: Optional[float] = None
    data_confidence: str = "LLM-estimated"    # NEW: "FDA-verified" / "Tavily-sourced" / "LLM-estimated"
    fda_nda_number: Optional[str] = None      # NEW: from FDA if found
    approval_date: Optional[str] = None       # NEW: from FDA if found
```

```python
# In competitor_analysis_agent.py — new approach

from src.service.tools.fda_tools import FDAClient

async def competitor_analysis_agent(state: GTMState) -> GTMState:
    tavily = TavilySearchClient()
    fda = FDAClient()

    # Step 1: Get competitor landscape overview
    overview = tavily.search(
        f"{state.drug_name} {state.indication} competing drugs alternatives 2025"
    )

    # Step 2: LLM extracts ONLY candidate names (not data)
    llm = get_claude(temperature=0.2)
    name_extraction_prompt = f"""
    From this competitive landscape overview, extract only the drug names that compete
    with {state.drug_name} in {state.indication}.

    Overview: {overview.get('answer', '')}

    Return JSON: {{"competitor_names": ["name1", "name2", "name3"]}}
    Maximum 5 competitors. Return only drug names, not company names or descriptions.
    """
    # ... parse candidate names

    competitors = []
    for name in candidate_names[:5]:
        competitor = CompetitorData(competitor_name=name, company="", indication=state.indication)

        # Step 3: FDA verification
        fda_results = fda.search_drug_approvals(name, max_results=3)
        if fda_results:
            best_match = fda_results[0]
            competitor.company = best_match.get("applicant", "")
            competitor.approval_date = best_match.get("approval_date", "")
            competitor.fda_nda_number = best_match.get("nda_number", "")
            competitor.data_confidence = "FDA-verified"

        # Step 4: Tavily for pricing signals (explicitly not presented as fact)
        pricing_data = tavily.search_pricing_information(name)
        if pricing_data.get("success"):
            competitor.data_confidence = max(
                competitor.data_confidence,
                "Tavily-sourced"  # only upgrade if not already FDA-verified
            )

        # Step 5: LLM for clinical differentiation (clearly marked as synthesis)
        # ... populate key_differentiators, clinical_advantages, clinical_disadvantages

        competitors.append(competitor)

    state.competitor_data = CompetitorAnalysisData(competitors=competitors, ...)
    state.mark_agent_complete("Competitor Analysis Agent")
    return state
```

### UI: Data Confidence Badges (`src/ui/app.py`)

In `display_competitive_section()`, show confidence level for each competitor:

```python
def _confidence_badge(confidence: str) -> str:
    badges = {
        "FDA-verified": "🟢 FDA-verified",
        "Tavily-sourced": "🟡 Web-sourced",
        "LLM-estimated": "🟠 AI-estimated — verify before use"
    }
    return badges.get(confidence, "⚪ Unknown")

# In competitor display loop:
st.write(f"{competitor.competitor_name} {_confidence_badge(competitor.data_confidence)}")
```

---

## Phase 4: Wire FDA Tools

`src/service/tools/fda_tools.py` has 3 working methods. Wire them:

| Method | Call From | Purpose |
|--------|----------|---------|
| `FDAClient.search_drug_approvals()` | `competitor_analysis_agent.py` | Verify competitor names + get approval dates |
| `FDAClient.search_drug_approvals()` | `market_research_agent.py` | Get approval status for the target drug itself |
| `FDAClient.search_adverse_events()` | `market_research_agent.py` | Add safety signal context to clinical evidence |

---

## Phase 5: Expand KOL Database

`src/ui/app.py` `get_hospital_list()` currently returns 7 hardcoded oncology centers.

**MVP expansion (before moving to SQLite in SKILL_06):** Add 40+ institutions across 4 therapeutic areas:

```python
HOSPITAL_DATABASE = {
    "Oncology": {
        "MD Anderson Cancer Center": ["Dr. Vassiliki Papadimitrakopoulou", "Dr. John Heymach", "Dr. Funda Meric-Bernstam", "Dr. Adi Diab"],
        "Memorial Sloan Kettering": ["Dr. Charles Rudin", "Dr. Matthew Hellmann", "Dr. Marina Shcherba", "Dr. David Jones"],
        "Dana-Farber Cancer Institute": ["Dr. Pasi Janne", "Dr. Geoffrey Oxnard", "Dr. David Jackman", "Dr. Cloud Paweletz"],
        "UCSF Helen Diller": ["Dr. Trever Bivona", "Dr. Eric Collisson", "Dr. Collin Blakely", "Dr. Jonathan Weiner"],
        "Johns Hopkins Sidney Kimmel": ["Dr. Julie Brahmer", "Dr. Patrick Forde", "Dr. Josephine Feliciano", "Dr. Christine Hann"],
        "Stanford Cancer Institute": ["Dr. Heather Wakelee", "Dr. Joel Neal", "Dr. Sukhmani Padda", "Dr. Natalie Lui"],
    },
    "Cardiology": {
        "Cleveland Clinic": ["Dr. Steven Nissen", "Dr. Samir Kapadia", "Dr. Milind Desai", "Dr. Brian Griffin"],
        "Mayo Clinic": ["Dr. Paul Friedman", "Dr. Suraj Kapa", "Dr. Samuel Asirvatham", "Dr. Niyada Naksuk"],
        "Massachusetts General Hospital": ["Dr. James Januzzi", "Dr. Marc Sabatine", "Dr. David Morrow", "Dr. Eugene Braunwald"],
        "Cleveland Clinic Florida": ["Dr. Wael Jaber", "Dr. Amar Krishnaswamy", "Dr. Jose Navia", "Dr. Rishi Puri"],
    },
    "Neurology": {
        "UCSF Memory and Aging Center": ["Dr. Bruce Miller", "Dr. Adam Boxer", "Dr. Lea Grinberg", "Dr. Gil Rabinovici"],
        "Massachusetts General Hospital Neurology": ["Dr. Merit Cudkowicz", "Dr. Anne-Marie Wills", "Dr. Michael Schwarzschild", "Dr. Albert Hung"],
        "Johns Hopkins Neurology": ["Dr. Peter Calabresi", "Dr. Carlos Pardo", "Dr. John Griffin", "Dr. Justin McArthur"],
    },
    "Rare Disease": {
        "NIH Clinical Center": ["Dr. William Gahl", "Dr. Camilo Toro", "Dr. David Adams", "Dr. Cynthia Tifft"],
        "Boston Children's Hospital": ["Dr. Alan Beggs", "Dr. Timothy Yu", "Dr. Laurie Ozelius", "Dr. Basil Darras"],
        "University of Washington Medical Center": ["Dr. Michael Bamshad", "Dr. Deborah Nickerson", "Dr. Evan Eichler", "Dr. Jay Shendure"],
    }
}
```

---

## Files Modified

| File | Change |
|------|--------|
| `src/schema/gtm_state.py` | Add `KOLProfile` dataclass; add `data_confidence` + `fda_nda_number` + `approval_date` to `CompetitorData`; add `current_doctor`, `current_hospital`, `kol_profile` to `GTMState` |
| `src/agents/gtm_workflow.py` | Add `kol_profiling_agent` node; insert between `memory_retrieval` and `market_research` |
| `src/agents/gtm_agents/competitor_analysis_agent.py` | Replace hallucinated data with FDA-verified + Tavily-sourced approach |
| `src/agents/gtm_agents/market_research_agent.py` | Integrate `ClinicalEvidenceRAG`; wire `fda_tools.py` for drug approval + adverse events |
| `src/ui/app.py` | Add KOL Profile tab; add confidence badges in competitive section; expand hospital database; pass `current_doctor`/`current_hospital` into `GTMState` |

## Files Created

| File | Purpose |
|------|---------|
| `src/agents/gtm_agents/kol_profiling_agent.py` | KOL-specific intelligence profiling |
| `src/service/rag/clinical_evidence_rag.py` | RAG pipeline: ingest + hybrid retrieval |
| `src/service/rag/vector_store.py` | ChromaDB wrapper with collection management |
| `src/service/rag/retriever.py` | BM25 + vector hybrid retrieval + cross-encoder reranking |

## Dependencies Added

```
chromadb>=0.5.0
rank-bm25>=0.2.2
sentence-transformers>=2.2.0
```
