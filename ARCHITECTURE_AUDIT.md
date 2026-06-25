# Evidentia MSL Platform — Architectural Audit & Enhancement Plan

**Author:** Structural diagnosis in the style of Shirin Khosravi Jam (senior AI systems engineer)
**Date:** 2026-06-24
**Scope:** Full code/architecture QC of `project_9_gtm_simulator` (Evidentia)
**Status:** Findings captured for later planning + implementation. Nothing implemented yet.

> Audience note: this document is written for a non-coder owner. Explanations use plain language and
> analogies. The file:line references are included only so a developer can act on each item later.

---

## Executive Summary

Evidentia is a capable prototype with a real 6-agent workflow, but it currently behaves like a demo
that *looks* finished rather than a system that *is* reliable. **The dominant flaw cuts across every
phase: when something fails, the app silently substitutes invented data and reports "success."** For a
pharma tool that recruiters and medical teams will judge, that is the issue to fix before any feature work.

**Cross-cutting pattern — the "shadow layer":** the codebase contains finished infrastructure that
*nothing ever calls*:
- `src/service/tools/fda_tools.py` — full FDA API client, never imported.
- `src/service/validators/input_validator.py` — `InputValidator`, defined but never called.
- `src/service/cache_manager.py` — response cache (`CacheManager`), exists but not wired into the retrieval path.
- `src/schema/agent_messages.py` — message schema, defined but unused.

Much of the fix below is **connecting what was already built**, not writing new systems.

---

## Verified system facts (ground truth)

- **Pipeline:** 6 agents run strictly sequentially via LangGraph edges in `src/agents/gtm_workflow.py:42-47`:
  `market_research → payer_intelligence → competitor_analysis → icp_definition → messaging → synthesis`.
- **Shared state:** single `GTMState` dataclass (`src/schema/gtm_state.py`) is the message bus.
- **Model:** `claude-sonnet-4-20250514`, hardcoded in `src/core/settings.py:20` and `src/core/llm.py:23`.
- **Retrieval:** NO RAG. Live API calls (PubMed via Biopython Entrez, ClinicalTrials.gov v2, Tavily),
  results pasted into prompts. No embeddings, vector store, or relevance ranking.
- **UI:** `src/ui/app.py` ≈ 2,288 lines, 9 tabs, holds 7–9 responsibilities.
- **LLM calls per brief:** ~11–12 (not 6). Messaging fires 5×; synthesis re-injects all prior outputs.
- **Tokens per brief:** ~20,000–40,000.

---

## 🔍 Phase 1: Code Architecture & Design Pattern Flaws

### 1.1 Separation of concerns — the UI file does nine jobs
- `src/ui/app.py` (~2,288 lines) mixes: screen rendering, ~1,500 lines of inline HTML/CSS, workflow
  trigger (`run_workflow`, ~547-598), data formatting, hardcoded hospital/doctor list
  (`get_hospital_list()`, ~345-423), Q&A prompt construction (~2126-2146), session state (~19-33),
  9 tabs (~713-2100+), PDF export (~2210+).
- Prompts are written **inline inside agent functions**, tangled with API calls and parsing
  (e.g. `competitor_analysis_agent.py:62-112`, `market_research_agent.py:101-139`).
- **Impact:** every change is high-risk; one person is host + chef + accountant + electrician. Cannot
  test prompts in isolation; cannot add hospitals without a code edit; duplicate prompts drift apart.
- **Solution:** split into thin UI layer / service-orchestrator layer / `prompts/` folder of editable
  text templates. Move hospital list to a data file or DB table.

### 1.2 State & connection management — doors opened, never closed
- **AI client is correctly cached** as a singleton (`src/core/llm.py:38-45`). Good.
- **BUT subtle bug:** the singleton caches the *first* instance, so `temperature`/`max_tokens` passed on
  later `get_claude(...)` calls are **silently ignored** (`llm.py:38-45`). The per-agent temperature
  guidance in CLAUDE.md is not actually honored — whichever agent runs first sets the dial for all.
- **Data clients recreated per call** (no pooling, never closed):
  - Tavily: new `TavilySearchClient` per convenience-function call (`tavily_tools.py:92-135`) → 7+ clients per market-research run.
  - ClinicalTrials: `search_clinical_trials()` builds a new client+session per call (`clinical_trials_tools.py:191-192`).
  - FDA: new client per call (`fda_tools.py:183-186`).
  - PubMed: new client per call (`pubmed_tools.py:269,280,289`); mutates global `Entrez.email` repeatedly.
  - No `.session.close()` / context managers anywhere.
- **No session persistence:** a browser refresh wipes the entire brief (`app.py:19-33`).
- **Solution:** create each data client once and reuse (mirror the AI-client pattern); pass temperature
  explicitly; persist completed briefs so refresh restores them.

---

## ⚡ Phase 2: RAG & Context Injection Inefficiencies

### 2.1 Honesty correction — there is no RAG
No embeddings, no ChromaDB, no sentence-transformers, no semantic ranking. requirements.txt has no vector
libs. "Retrieval" = live API calls pasted into prompts. Evaluate accordingly.

### 2.2 Chunking & retrieval integrity — fetch a library, read 5 pages
- Market research fetches **20** pubs/trials, stores **10**, injects only **5** into the prompt — and
  selects those 5 **by date, not relevance**:
  - retrieval cap: `market_research_agent.py:57` (`max_results=20`)
  - storage cap 10: `format_publications_for_storage()` ~`:229-240` (`publications[:10]`)
  - prompt cap 5: `format_publications_summary()` ~`:213-226` (`publications[:5]`), `format_trials_summary()` ~`:196-210` (`trials[:5]`)
- **75% of fetched evidence is discarded before the AI sees it.** Sorting by date drops landmark Phase 3
  trials in favor of minor recent abstracts — the opposite of what an MSL wants. The AI then "fills the
  gap" from training memory → invented citations.
- **Solution:** rank by combined relevance + study importance (phase, enrollment, recency); widen the
  injected set toward 10–15; label each piece so retrieved ≠ remembered.

### 2.3 Prompt & context bloat — paying to say the same thing repeatedly
- ~11–12 AI calls per brief. Messaging makes **5** (1 positioning + 4 near-identical persona calls that
  re-paste positioning each time): `messaging_agent.py` positioning ~`:316`, persona loop ~`:335-390`.
- Synthesis re-injects **all 5 prior agent outputs verbatim**: `synthesis_agent.py:42-71` + formatters
  `:231-304`.
- ~10,700 prompt tokens; 20,000–40,000 total per brief.
- **Solution:** collapse 4 persona calls into 1; pass compact summaries (not raw text) into synthesis;
  **wire up the existing `CacheManager`** so repeat drug/indication briefs are instant and free.

---

## 🛑 Phase 3: Error Handling & Resilience (the failure modes)

### 3.1 Silent failures — the app fabricates and smiles  ← TOP RISK
- Every agent has a catch-all that, on *any* failure, returns pre-written placeholder data then logs
  "completed successfully":
  - Competitor fallback invents **"Competitor 1", 30% share, $50,000** (`competitor_analysis_agent.py:178-198`).
  - ICP fallback always returns **$75M/$25M** segment split (`icp_definition_agent.py:210-234`).
  - Synthesis fallback always returns **$40k–$60k** pricing (`synthesis_agent.py:331-376`).
  - Market fallback returns TAM/SAM/SOM = **$0** with "Insufficient data" (`market_research_agent.py:243-252`).
- **Double fabrication path:** the competitor prompt *explicitly asks the AI to "estimate" market share
  and pricing* (`competitor_analysis_agent.py:71-83`). So the AI guesses, and when that fails, hardcoded
  fiction takes over. **No UI flag distinguishes real vs fallback data.**
- **Solution (highest-value design change):** per-data-point **provenance badges**
  (FDA-verified / Tavily-sourced / AI-estimated / Unavailable); honest empty states on fallback; never
  show invented numbers as facts. (CLAUDE.md already mandates this; code never implemented it.)

### 3.2 Rate limits & retries — the expensive call is the unprotected one
- Retry-with-backoff (tenacity) exists on data APIs: `clinical_trials_tools.py:25-34`,
  `tavily_tools.py:21-28`, most of `pubmed_tools.py:24-46`.
- **Zero retry on the AI calls** (the most expensive/critical): `.invoke()` at
  `market_research_agent.py:142`, `payer_intelligence_agent.py:138`, `competitor_analysis_agent.py:115`,
  `icp_definition_agent.py:128`, `messaging_agent.py:316,369`, `synthesis_agent.py:160`.
- **No 429 / RateLimitError handling anywhere** — a rate limit falls straight to fabricated defaults.
- Broad `except Exception` everywhere → cannot tell rate-limit from auth-failure from network blip.
- Two PubMed methods bypass retry entirely (`pubmed_tools.py:152-205`).
- JSON validation inconsistent: ICP and Synthesis skip Pydantic and use bare `extract_json_from_text()`
  (`icp_definition_agent.py:131`, `synthesis_agent.py:163`); others validate (`market_research_agent.py:146`,
  `competitor_analysis_agent.py:119`).
- **Solution:** add backoff+retry to AI calls; handle 429 specifically (wait/retry, surface "system busy");
  catch distinct error types; apply Pydantic validation consistently.

---

## 🔄 Phase 4: MCP & API Orchestration Bottlenecks

### 4.1 Chaining latency — single-file line where parallel is possible
- 6 agents strictly sequential (`gtm_workflow.py:42-47`).
- Inside each agent, 4–7 external lookups run sequentially with no `asyncio.gather`
  (e.g. `market_research_agent.py:39-96`).
- AI calls use blocking `.invoke()` inside `async def` functions → the async design provides no real
  concurrency; the event loop freezes per call.
- **market_research / payer_intelligence / competitor_analysis are mutually independent** and could run
  concurrently.
- **Estimated impact:** ~60–120s today vs ~20–40s achievable. Biggest perceived-quality win available.
- **Solution:** run the 3 independent agents concurrently (fan-out → fan-in); fire each agent's internal
  lookups together; make AI calls non-blocking (`.ainvoke()` or `asyncio.to_thread`).

### 4.2 Tool-calling vulnerabilities — a lock that was never installed
- `InputValidator` exists but is **never called** (`input_validator.py`; UI passes raw input at
  `app.py:547-564`).
- Raw user text flows directly into Tavily queries (`tavily_tools.py:58-86`) and into AI prompts.
- Q&A box pastes user text straight into an AI instruction (`app.py:2126-2146`) → **prompt injection**.
- **No PHI de-identification before external calls** despite CLAUDE.md requiring it → HIPAA/GDPR exposure.
- **Solution:** call the existing validator at input; separate user text from system instructions
  (treat input as data, not commands); add a de-identification pass before anything leaves the server.

---

## 🛠️ Phase 5: Enhancement Blueprint (prioritized roadmap)

### Critical fixes (do first — stop the app from breaking trust)
1. **End silent fabrication; make provenance visible.** Stop inventing competitor/pricing/market data;
   add data-source badges + honest empty states. *(Touches: 6 agents' fallbacks + results UI.)*
2. **Fix orchestration + resilience together.** Concurrent independent agents + non-blocking AI calls +
   retry/429 handling. Cuts wait ~50% and removes freeze-under-load and fabricate-on-rate-limit.
   *(Touches: workflow def, each agent's call pattern, an AI-call wrapper.)*

### Efficiency optimizations (target 30–50% lower cost & latency)
- Collapse 4 persona AI calls into 1.
- Stop re-pasting full prior outputs into synthesis (use summaries).
- Wire up the existing response cache → repeat briefs instant & free.
- Reuse data-client connections instead of recreating per call.
- Expected: ~40% fewer tokens, ~50% less wall-clock. Mostly wiring/removal, not new systems.

### Production checklist (hand to a developer next)
1. **Provenance & outcome logging** — record per agent whether output was real synthesis / verified
   source / fallback, plus the exact error type. (Today logs say "success" even when data is invented.)
2. **Data-integrity guardrail in UI** — banner when any part of a brief is unverified; per-field source
   badges; hard rule that unverified numbers are never shown as facts.
3. **Monitoring/alerting on 3 signals** — fallback rate, token cost per brief, end-to-end latency; alert
   when fallback rate climbs (early warning of silent quality degradation).

---

## Design ideas (implementable, ordered by recruiter-facing impact)
1. **Provenance/confidence badges** per data point (Verified ✓ / Web-sourced / AI-estimated / Unavailable).
2. **Honest empty states** replacing fabricated cards.
3. **Live source-count strip** during generation ("Reviewed 18 publications · 12 trials · 4 web sources").
4. **Information-hierarchy cleanup** of the 9 tabs — lead with brief + talking points; demote the rest.
5. **Accessibility & polish** — contrast, loading skeletons, consistent typography ("production" vs "prototype").

---

## Recommended sequencing
While the deploy stabilizes, start with **Critical Fix #1 + Design #1–2 (provenance / no fabrication)** —
most visible to recruiters, lowest risk, converts the biggest liability into a selling point. Stage the
concurrency rewrite (**Critical Fix #2**) second — bigger speed win but larger surface area. Fold the
efficiency wins in alongside #2. Security (validator + PHI) before any real pilot with patient-adjacent data.

---

## Appendix: known bugs cross-reference (from CLAUDE.md, confirmed in code)
| Bug | Confirmed location | Status |
|-----|--------------------|--------|
| Competitor hallucination | `competitor_analysis_agent.py:71-83` (prompt asks for estimates) + `:178-198` (fabricated fallback) | Confirmed |
| `fda_tools.py` never called | no imports anywhere | Confirmed |
| `agent_messages.py` unused | no agent imports it | Confirmed |
| Hardcoded hospital list | `app.py` `get_hospital_list()` ~`:345-423` | Confirmed |
| No session persistence | `app.py:19-33` | Confirmed |
| Fragile JSON parsing | improved via `json_validator.py` but applied inconsistently (`icp`, `synthesis` skip it) | Partially fixed |
| Max 20 publications cap | `market_research_agent.py:57` (and only 5 reach the prompt) | Confirmed + worse than documented |
| InputValidator unused | `input_validator.py` defined, 0 call sites | New finding |
| CacheManager unused in retrieval path | `cache_manager.py` exists, not wired | New finding |
| LLM singleton ignores per-call temperature | `llm.py:38-45` | New finding |
