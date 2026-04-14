# Evidentia — MSL Pre-Call Intelligence Platform

[Live Demo](https://evidentia-production-73a5.up.railway.app)

Production-grade LangGraph multi-agent system that generates pharmaceutical Medical Science Liaison (MSL) pre-call briefs in 90 seconds using publicly available clinical data.

---

## Overview

Evidentia automates the research phase of MSL physician calls. Instead of spending 30-45 minutes gathering trial data, competitive intelligence, and physician profiles, MSLs generate a complete, personalized brief in 90 seconds.

**Current State:** Phase 1 clinical brief generator using public APIs (ClinicalTrials.gov, PubMed, Tavily search).

**Future State:** Enterprise intelligence platform with CRM, payer feeds, and claims data integration.

---

## What This Actually Does (Honest Assessment)

### Real Data Sources
- Clinical trial data from ClinicalTrials.gov API
- Journal publications from PubMed Entrez API
- Physician profiles via user input and web search
- Market news from Tavily search API

### Templated Components
- Personalized conversation openers (tailored to physician specialty and indication)
- Tiered discovery questions (structure + clinical context)
- Objection response strategies (bridge format: acknowledge → pivot to drug strengths)
- "Do Not Say" compliance guardrails (regulatory language guardrails)

### Phase 1 Limitations (Not Built Yet)
- No CRM/EHR integration (no real prescribing patterns or patient volumes)
- No payer formulary feeds (no real access barrier data)
- No real-time competitor tracking (news-based only)
- No claims data integration (no patient journey mapping)

**Bottom Line:** Evidentia generates high-quality clinical briefs for MSLs. It personalizes well-structured templates. It is not (yet) an enterprise intelligence platform with proprietary data access.

---

## Business Impact

At a pharma company with 150 MSLs:

```
150 MSLs × 5 calls/week × 45 min/call = 562.5 hours/week of research
562.5 hours × $100/hour (loaded cost) = $56,250/week saved
Annually: $2.9M+ in research time recovered
```

**Per MSL:** ~8 hours saved per week = $9,600/year in productivity value.

---

## Quick Start

### Try the Live Demo
1. Visit [evidentia-production-73a5.up.railway.app](https://evidentia-production-73a5.up.railway.app)
2. Select: Hospital → Physician → Drug Name → Indication
3. Click "Generate MSL Brief"
4. Review 7 intelligence tabs + Download PDF

**Demo Data:** Try ivonescimab + Dr. Syedain Gulrez (Mayo Clinic) + Non-Small Cell Lung Cancer

### Local Development

**Prerequisites:**
- Python 3.11+
- ANTHROPIC_API_KEY (from Claude API)
- TAVILY_API_KEY (from Tavily)

**Installation:**
```bash
git clone https://github.com/LifeSciForge/Evidentia.git
cd Evidentia

cp .env.example .env
# Add ANTHROPIC_API_KEY and TAVILY_API_KEY to .env

pip install -r requirements.txt
streamlit run streamlit_app.py
```

Access: http://localhost:8501

---

## Core Features

### 7 Interactive Output Tabs

| Tab | Purpose |
|-----|---------|
| Talking Points | 3 clinical pillars, positioning statement, conversation opener, "Do Not Say" compliance rules |
| Objections & Questions | Pre-loaded responses to 8-10 anticipated objections with evidence and follow-up points |
| Discovery Questions | Tiered questions: Tier 1 (must-ask), Tier 2 (context-dependent), Tier 3 (nice-to-have) |
| Clinical Evidence | Active trials (table), key publications (with PMIDs), market sizing (TAM/SAM/SOM), patient population |
| Competitive Position | Affirmative positioning statements vs. 3 main competitors, competitor overview table |
| Final Brief | Executive summary formatted for 5-minute pre-call review |
| Download Brief | Export as professional PDF (mobile-friendly, printable) |

### Real US Hospital Database
- 8 major cancer centers (MD Anderson, MSK, Mayo Clinic, Cleveland Clinic, Dana-Farber, UCSF, Johns Hopkins, Stanford)
- Real oncologist names, specialties, and practice focuses
- Dynamic selection for realistic scenarios

### Ask Evidentia Q&A
Ask follow-up questions in plain English:
- "What if the doctor asks about side effects vs. pembro?"
- "What's our unique value in PD-L1 negative patients?"
- "How should I handle the cost objection?"

Claude responds in real-time, referencing the generated brief.

---

## Standout Features (Validated by Field)

### "Do Not Say" Compliance Section
MSLs get explicit guardrails for what NOT to claim:
- ❌ "Superior to standard of care" (without head-to-head data)
- ❌ "Breakthrough therapy" or "First-in-class" (marketing language)
- ✅ Instead: "Early signals suggest potential activity in acquired resistance settings"

**Why it matters:** Pharma compliance teams care deeply about non-promotional language. This prevents regulatory risk.

### Tiered Discovery Questions
Instead of 20 unstructured questions, Evidentia structures them:
- **Tier 1 (Must-Ask):** Every call. Foundation questions about patient population fit.
- **Tier 2 (Context-Dependent):** Follow-ups based on Tier 1 answers.
- **Tier 3 (Nice-to-Have):** Bonus questions if time permits.

**Why it matters:** MSLs know when to ask what. This is practical, not theoretical.

### Physician-Specific Conversation Opener
Not generic NSCLC talking points. The opener is personalized to the specific physician's focus area (e.g., resistance mechanisms, combination therapy approach, complex case management).

---

## System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                     (Streamlit Web App)                          │
│  Hospital Selection → Physician → Drug Name → Indication         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────┐
        │   GTM Workflow Orchestrator  │
        │      (LangGraph State)       │
        └────────────────┬─────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
    ┌─────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Agent 1   │ │   Agent 2    │ │   Agent 3    │
    │   Market    │ │    Payer     │ │  Competitor  │
    │  Research   │ │ Intelligence │ │   Analysis   │
    └─────┬───────┘ └──────┬───────┘ └──────┬───────┘
          │                │                │
          ▼                ▼                ▼
    ┌──────────────────────────────────────────────┐
    │  Data Sources (APIs)                         │
    │  • ClinicalTrials.gov (trials)              │
    │  • PubMed Entrez (publications)             │
    │  • Tavily Search (market news)              │
    └──────────────────────────────────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
          ┌─────────────┐      ┌─────────────┐
          │   Agent 4   │      │   Agent 5   │
          │     ICP     │      │  Messaging  │
          │ Definition  │      │ & Position  │
          └─────┬───────┘      └──────┬──────┘
                │                     │
                └──────────┬──────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
          ┌──────────────────────────────┐
          │   Shared GTMState Object     │
          │  (Single Source of Truth)    │
          │  • market_data               │
          │  • payer_data                │
          │  • competitor_data           │
          │  • icp_profile               │
          │  • messaging_data            │
          │  • agents_completed          │
          │  • progress_percentage       │
          └──────────────┬───────────────┘
                         │
                         ▼
                  ┌────────────────┐
                  │   Agent 6      │
                  │  GTM Synthesis │
                  │  (Final Brief) │
                  └────────┬───────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
           ┌─────────────────┐  ┌──────────────┐
           │  Streamlit UI   │  │ PDF Generator│
           │  (7 Tabs + Q&A) │  │ (ReportLab) │
           └─────────────────┘  └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ MSL Brief    │
                    │ (Download)   │
                    └──────────────┘
```

### 6-Agent Parallel Orchestration

```
Agent 1: Market Research        ──┐
Agent 2: Payer Intelligence     ──┼→ Shared GTMState ──→ Agent 6: GTM Synthesis
Agent 3: Competitor Analysis    ──┤
Agent 4: ICP Definition         ──┤
Agent 5: Messaging & Positioning──┘

Execution: Concurrent (not sequential)
Duration: ~90 seconds total
State Management: Immutable single source of truth
```

### Agent Responsibilities

| Agent | Input | Output | Tools Used |
|-------|-------|--------|-----------|
| **Market Research** | Drug name, indication | TAM/SAM/SOM, trials, publications, patient population | ClinicalTrials.gov API, PubMed Entrez, Tavily |
| **Payer Intelligence** | Drug name, indication | HTA status, QALY thresholds, reimbursement criteria | Tavily search, regulatory databases |
| **Competitor Analysis** | Drug name, indication | Competitor positioning, market share, pricing | ClinicalTrials.gov, Tavily, competitive research |
| **ICP Definition** | Market data, competitor data | Buyer personas, decision-makers, urgency triggers | Synthesis from previous agents |
| **Messaging & Positioning** | Competitor data, ICP, market data | Positioning statements, objection responses, "Do Not Say" guardrails | Claude synthesis |
| **GTM Synthesis** | All previous agent outputs | Executive summary, strategy, timeline, success metrics | Claude synthesis |

### State Machine (GTMState)

```python
class GTMState:
    # User Input
    drug_name: str
    indication: str
    
    # Agent Outputs
    market_data: MarketResearchData
    payer_data: PayerIntelligenceData
    competitor_data: CompetitorAnalysisData
    icp_profile: ICPProfile
    messaging_data: MessagingData
    final_gtm_strategy: GTMStrategy
    
    # Metadata
    workflow_id: str
    started_at: str
    completed_at: Optional[str]
    agents_completed: List[str]
    current_agent: Optional[str]
    agent_status: str
    progress_percentage: int
    errors: List[Dict]
```

**Key Design Principle:** All agents read from and write to this single object. No data duplication, hallucination prevention, single source of truth.

### Data Sources Integration

```
┌────────────────────────────────┐
│   ClinicalTrials.gov API v2    │
│  • Phase 2/3 active trials     │
│  • Enrollment status           │
│  • Primary endpoints           │
└────────────────────────────────┘
              │
              ▼
┌────────────────────────────────┐
│      PubMed Entrez API         │
│  • Recent publications         │
│  • Citation metadata           │
│  • Abstract text               │
└────────────────────────────────┘
              │
              ▼
┌────────────────────────────────┐
│    Tavily Search API           │
│  • Market news                 │
│  • FDA updates                 │
│  • Company announcements       │
└────────────────────────────────┘
              │
              ▼
        ┌─────────────┐
        │   Agents    │
        │  Process &  │
        │   Synthesize│
        └─────────────┘
```

### Real-Time Streaming & UI Updates

```
Agent 1 Completes (17%)
    ↓ Write to GTMState
    ↓ Callback fires
    ↓ Streamlit progress_bar updated
    ↓ status_text shows "✅ Market Research complete (17%)"

Agent 2 Completes (33%)
    ↓ Same flow
    ...
Agent 6 Completes (100%)
    ↓ Final brief rendered in 7 tabs
```

**Technology:** Streamlit's real-time WebSocket layer decouples from the blocking event loop, enabling live UI updates during concurrent agent execution.

### Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│          GitHub Repository (Main Branch)        │
│  (Automatically triggers Railway deployment)    │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   Railway.app        │
          │  (Production Server) │
          └──────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌────────┐  ┌────────┐  ┌─────────────┐
   │Streamlit│  │LangGraph│  │API Clients  │
   │Frontend │  │Backend  │  │(Anthropic,  │
   │         │  │         │  │ Tavily)     │
   └────────┘  └────────┘  └─────────────┘
        │            │
        └────────────┼────────────┐
                     │            │
                     ▼            ▼
            ┌──────────────┐  ┌──────────┐
            │  .env Secrets│  │ Logs     │
            │ (API Keys)   │  │          │
            └──────────────┘  └──────────┘
```

### Error Handling & Resilience

```
Agent Execution
    │
    ├─→ Success → Write to GTMState
    │
    ├─→ API Timeout → Fallback data + Log error
    │
    ├─→ Invalid JSON → Extract + Parse + Log warning
    │
    ├─→ Callback Error → Log (doesn't stop workflow)
    │
    └─→ Agent Error → Add to state.errors, continue
```

All agents are fail-safe. Failures don't crash the pipeline.

---

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Agent Framework | LangGraph | 1.1.3 |
| LLM Chain | LangChain | 1.2.13 |
| LLM | Claude Sonnet 4 (Anthropic API) | latest |
| Frontend | Streamlit | 1.55.0 |
| State Management | Pydantic | 2.12.5 |
| PDF Generation | ReportLab | 4.4.10 |
| Data Sources | ClinicalTrials.gov, PubMed, Tavily | APIs |
| Deployment | Railway.app + Docker | - |

---

## Performance

| Metric | Value |
|--------|-------|
| Brief generation time | ~90 seconds |
| Agents processing in parallel | 6/6 (100%) |
| Output tabs | 7 interactive + Q&A |
| Data sources queried | 3 (Trials, Publications, News) |
| PDF export | Mobile-friendly, printable |
| Production deployment | Live on Railway.app |

---

## Target Users

### Primary
- Medical Science Liaisons at large pharma companies
- Field-based clinical experts requiring pre-call prep

### Target Companies
- Large pharma (Roche, Merck, AstraZeneca, Novartis, Amgen, BMS, Eli Lilly)
- Specialty pharma with oncology/immunology focus
- Commercial teams requiring consistent messaging

### Use Cases
- Pre-call physician intelligence (primary)
- New MSL onboarding (day-1 productivity, no ramp-up)
- Field team consistency (standardized talking points)
- Compliance training (Do Not Say guardrails)

---

## Phase 2 Roadmap

### Current Gaps (Honest)
The product pitch often includes "prescribing patterns," "formulary restrictions," and "competitor moves," but these require enterprise data integrations not yet built.

### Phase 2 (Planned, Not Built)
- CRM integration (Salesforce API) — real prescribing patterns, patient volumes
- Payer formulary feeds (NICE, EMA, ICER) — real access barrier data
- Real-time competitor tracking — clinical event triggers, FDA decisions
- Claims data integration — patient journey mapping

---

## Deployment

### Production
**[Live App: evidentia-production-73a5.up.railway.app](https://evidentia-production-73a5.up.railway.app)**

Fully functional, live updates on every GitHub push.

### Local
```bash
streamlit run streamlit_app.py --server.port 8501
```

### Docker
```bash
docker build -t evidentia .
docker run -p 8501:8501 evidentia
```

---

## Why LangGraph

### Problem with Sequential APIs
- Search PubMed (30s) + wait
- Search trials (20s) + wait
- Search news (15s) + wait
- Synthesize (20s)
- **Total:** 85+ seconds of mostly waiting

### Solution: Parallel Orchestration
6 agents run concurrently. Each queries its specialized API. Single shared state prevents hallucinations.
**Total:** 90 seconds, end-to-end.

This pattern is applicable to any pharma workflow requiring multi-domain synthesis: GTM strategy, clinical trial tracking, Market Access automation.

---

## Key Design Decisions

### Decision 1: LangGraph Over Simple Prompting
One large prompt to Claude produces inconsistent, hallucinated output. Multiple specialized agents with a shared state machine produce reliable, repeatable results.

### Decision 2: Parallel Execution Over Sequential
Sequential would require 45+ minutes. Parallel brings it to 90 seconds. Complexity is managed via immutable shared state.

### Decision 3: Streamlit Over React
Rapid prototyping, beautiful UI, real-time streaming. Production could migrate to React + FastAPI for higher throughput.

### Decision 4: Railway.app Deployment
Free tier, GitHub integration, easy for recruiters to click and test live.

---

## Contributing

This is a portfolio project showcasing:
- LangGraph multi-agent orchestration (production patterns)
- Pharma domain expertise (11+ years in clinical development, regulatory, commercial)
- Full-stack AI development (Streamlit frontend → LangGraph backend → Docker deployment)
- State machine architecture (prevention of hallucinations)
- Production deployment (not just notebooks)

Contributions welcome:
- Fork the repo
- Submit PRs
- Open issues with feature requests
- Suggest new data sources

---

## Author

**Pranjal Das** —  Agentic AI Builder
- GitHub: [@LifeSciForge](https://github.com/LifeSciForge)
- LinkedIn: [pranjal-das1](https://linkedin.com/in/pranjal-das1)
- 11+ years pharma | $2M+ pipeline influenced | 6+ production AI systems

---

## License

MIT License — See LICENSE file for details

---

Let's build the future of pharmaceutical AI.