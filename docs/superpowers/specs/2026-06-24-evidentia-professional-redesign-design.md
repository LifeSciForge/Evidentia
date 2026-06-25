# Evidentia — Professional Redesign: Visual + Provenance + Speed

**Date:** 2026-06-24
**Status:** Design approved (verbal); spec under review
**Source audit:** `ARCHITECTURE_AUDIT.md` (repo root)
**Scope decision:** Full — operational foundation, visual polish, honest data provenance, concurrency,
security/compliance, and an architecture refactor. Delivered in **6 independently reviewable/pushable
stages (0–5)**, ordered so the safety net comes first and the riskiest change comes last.

**Stage map:**
- **Stage 0** — Foundation: CI + tests + graceful config failure (de-risks everything after).
- **Stage 1** — Visual redesign (UI only).
- **Stage 2** — Trustworthy data / provenance (+ consistent JSON validation).
- **Stage 3** — Speed & efficiency (+ response cache, retries, model-via-settings, refresh persistence).
- **Stage 4** — Security & compliance.
- **Stage 5** — Architecture refactor (`app.py` decomposition + prompt extraction + dead-code cleanup).

---

## Context

Evidentia is live on Streamlit Cloud (recruiter-facing). The earlier architecture audit found the app
*looks* like a finished demo but (1) presents an undistinguished, partly-templated UI, (2) **silently
fabricates data** on failure and shows unsourced numbers as fact, and (3) runs everything sequentially so
a brief takes ~60–120s. This effort makes the app look professional **and** be trustworthy and fast.

The guiding product principle, set by the owner: **no number is shown without a real, clickable source.**
"AI-estimated" language is removed — it destroys trust in pharma. Source URLs must come only from actual
retrieval (FDA / PubMed / ClinicalTrials / Tavily); the LLM is **never** asked to produce a URL.

## Goals
- A distinctive, professional "Modern SaaS / clinical" look (approved Direction C).
- Every displayed fact carries a truthful provenance chip linking to a real source, or an honest
  "unavailable" state. Zero fabricated numbers.
- Roughly halve brief generation time via concurrency, with resilient AI calls.

## Non-goals (this effort)
- Authentication, multi-user accounts, RBAC.
- Full SQLite/KOL-history persistence (v2). **Lightweight refresh persistence IS in scope** (Stage 3).
- Real RAG / vector store (separate; retrieval stays live-API).
- New FastAPI backend — the existing stub is **removed** (Stage 5), not built out.

---

## Approved visual decisions (reference)
- **Direction C**: light base `#f7f8fb`, white cards, indigo accent `#5b5bd6`, Inter, rounded 12–14px
  cards, soft shadows. Retire the purple-gradient metric card.
- **Provenance chips**, colored by trust tier: green = authoritative registry/API; blue = web source
  (domain shown); amber = company filing **or** modeled-from-sourced-inputs; gray = unavailable.
- **Market figure fallback** when no published number exists: a **modeled range** built from sourced
  inputs (patients × price × penetration), each input itself a real link.
- **Layout**: header with brand + "Export PDF" button; an **"At a glance"** band (key metrics + lead
  talking point + likely objection); then **6 tabs** in call-flow order:
  `Pre-Call Brief · Talking Points · Objections · Discovery Questions · Clinical Evidence · Competitive Position`.
  ("Final Brief" merges into "Pre-Call Brief"; "Download" becomes the header button.)

---

## Stage 0 — Foundation (do first; de-risks every later stage)

**What changes:** safety infrastructure only; no user-facing behavior change.

- **CI pipeline** (new `.github/workflows/ci.yml`): on push/PR, install the slim `requirements.txt` on the
  Streamlit-Cloud Python (3.13 **and** 3.14), run an **import smoke-test** (`import streamlit_app`
  succeeds with dummy env keys), and run `pytest`. This single check would have caught *both* recent
  outages (the langgraph wheel break and a missing import).
- **Test scaffolding** (new `tests/` + `conftest.py`): shared `sotorasib` / `KRAS G12C NSCLC` fixture,
  mocked LLM/API calls (no live calls). Establishes the harness all later stages add to.
- **Graceful config failure** (`src/core/settings.py` + entrypoint): on missing required key, show a clear
  "API keys not configured" message instead of a redacted white-screen crash.

**Ships alone, zero risk.** Everything after this is protected by CI + tests.

---

## Stage 1 — Visual redesign (UI only, low risk)

**What changes:** the look and structure of the results view; no agent/tool logic.

- **`src/ui/components.py`**: rewrite `metric_card()` to the Direction C card (no gradient); add a new
  `source_chip(source)` component that renders a tier-colored, clickable chip from a provenance object
  (and degrades gracefully when no source is present). Restyle `market_sizing_waterfall()` and
  `competitor_positioning_scatter()` to the new palette.
- **`src/ui/app.py`**: introduce the "At a glance" band in `display_msl_results()`; reorder/rename tabs
  7→6; merge `display_final_brief_section()` into the lead "Pre-Call Brief" tab; move
  `display_download_section()` to a header Export button. Consolidate the duplicated "no data" guard
  (currently repeated at the top of `display_msl_results`). Extract the large inline CSS into one
  coherent Direction-C stylesheet block.
- **Honest empty states (UI portion):** where a section has no real data, render a clear "unavailable"
  state instead of empty/placeholder cards. (Full truth requires Stage 2's flags; Stage 1 lays the
  rendering groundwork.)

**Ships alone.** Chips light up immediately where real links already exist (NCT, PMID).

**Interface (new, stable):** `source_chip(source: Source) -> None` and a metric renderer that accepts an
optional `Source`. UI reads provenance; it never computes it.

---

## Stage 2 — Trustworthy data (provenance engine)

**Core data model** (new, in `src/schema/gtm_state.py`):

- `Source`: `tier` ("verified"|"web"|"filing"|"modeled"|"unavailable"), `label` (e.g. "ClinicalTrials.gov",
  "drugs.com", "Amgen FY23 10-K"), `url` (real, from retrieval; `None` for modeled/unavailable),
  `note` (short context).
- `SourcedValue`: `value` (or `None`), `display` (formatted string), `source: Source`,
  `modeled_from: List[SourcedValue]` (inputs when tier = "modeled").

Key fields on the existing dataclasses (`MarketResearchData`, `PayerIntelligenceData`,
`CompetitorAnalysisData`/`CompetitorData`, etc.) gain `SourcedValue` wrappers for user-facing numbers
(patients, price, market figure, market share, etc.). Free-text claims gain an attached `Source` where one
exists.

**Tools return URLs** (`src/service/tools/`):
- `clinical_trials_tools.py`: attach canonical `https://clinicaltrials.gov/study/<NCT>` per trial.
- `pubmed_tools.py`: attach `https://pubmed.ncbi.nlm.nih.gov/<PMID>/` per publication.
- `fda_tools.py`: **wire it in** (currently unused) for verified drug-approval/label facts + label URL.
- `tavily_tools.py`: stop discarding the result list — capture the top result `url`(s) and domain, not
  just the `answer` blob, and pass them through so a web fact can cite its real source.

**Agents stop fabricating** (`src/agents/gtm_agents/*.py`):
- Remove invented values from `get_default_*` paths. On LLM/API failure, set the affected
  `SourcedValue.source.tier = "unavailable"` (value `None`) — never "Competitor 1 / $50k / 30%",
  never hardcoded `$75M/$25M` or `$40–60k`.
- **Market figure:** prefer a real published source (company filing / web). If none is found, construct a
  `modeled` `SourcedValue` from sourced inputs (patient `SourcedValue` × price `SourcedValue` ×
  penetration assumption), populating `modeled_from`. Never a bare unsourced number.
- **Hard rule enforced in code:** `Source.url` is only ever set from a real retrieval result object. No
  prompt asks the LLM for URLs; any URL-looking string in LLM output is ignored for sourcing.

**UI:** render chips from `SourcedValue.source`; "unavailable" → honest empty state; "modeled" → expandable
"how this is sourced" showing the linked inputs.

**Also in this stage — consistent JSON validation (#5):** `icp_definition_agent` and `synthesis_agent`
currently skip Pydantic validation (the other four validate). Bring them in line so all six validate
LLM output the same way before it becomes a `SourcedValue`.

**Touches:** schema, 4 tool files, 6 agents, UI render functions.

---

## Stage 3 — Speed (concurrency + resilience, highest surface area)

- **`src/agents/gtm_workflow.py`**: fan-out the three independent agents (`market_research`,
  `payer_intelligence`, `competitor_analysis`) to run concurrently from the entry point, then fan-in to
  `icp_definition → messaging → synthesis` (which depend on the first three). Preserve `GTMState` merge
  semantics (each agent writes distinct fields).
- **Within agents:** gather each agent's multiple external lookups concurrently (`asyncio.gather`, with
  `asyncio.to_thread` for blocking `requests`/`Entrez`/Tavily clients).
- **AI calls non-blocking:** use `.ainvoke()` (or `to_thread` around `.invoke()`); add tenacity
  retry+exponential backoff and explicit handling for rate-limit (429) errors, surfacing a "system busy,
  retrying" state rather than falling to unavailable on the first hiccup.
- **`src/core/llm.py`**: keep the singleton but pass `temperature`/`max_tokens` per call (today the first
  call's settings are frozen for all). Reuse tool clients instead of recreating per call.
- **Messaging efficiency:** collapse the 4 per-persona LLM calls into 1 call returning all personas; stop
  re-injecting full prior outputs into synthesis (pass compact summaries).
- **Wire the response cache (#6):** activate the unused `CacheManager` in the tool/agent path so a repeat
  drug/indication brief is served from cache — instant and free.
- **Missing retries (#7):** add tenacity retry+backoff to the PubMed/epidemiology tool methods that
  currently call the API bare.
- **Model via settings (#8):** route agents through `settings.DEFAULT_MODEL` instead of the hardcoded
  `claude-sonnet-4-20250514` in three places; default it to the current Sonnet (4.6) for quality/cost.
- **Refresh persistence (#10, lightweight):** cache the last completed brief (session/on-disk) so a
  browser refresh restores it instead of wiping it. (Full SQLite history remains v2.)

**Target:** ~50% lower wall-clock; no fabricate-on-rate-limit; repeat briefs near-instant.

---

## Stage 4 — Security & compliance (#3, pharma-critical)

- **Wire `InputValidator`** (currently unused) at the UI input boundary in `app.py`: validate/clean
  `drug_name`, `indication`, and the Q&A question before they reach the workflow or any API. Reject or
  sanitize invalid input with a clear message.
- **Separate user text from instructions** in the Q&A prompt (`generate_qa_answer`) and any prompt that
  interpolates user input, so user text is treated as *data*, not as commands (prompt-injection defense).
- **PHI de-identification** (new `src/service/security/deidentify.py`): strip obvious patient identifiers
  (names, ages, MRN-like tokens) from any free text before it is sent to Tavily or the LLM. Applied at the
  Q&A path and anywhere user free-text leaves the server.
- **Touches:** `app.py` (input boundary), the Q&A prompt path, a new de-identification helper, agents that
  forward user text.

---

## Stage 5 — Architecture refactor (#4 + cleanup; highest risk, done last)

Sequenced last because it moves the most code and benefits from the Stage 0 test net + the now-cleaner
agents.

- **Decompose `app.py` (~2,288 lines):** extract a thin UI layer (`src/ui/` tab/section modules) from a
  service/orchestrator layer (`src/service/` — workflow invocation, state init, formatting). Move
  `get_hospital_list()` data out of code into a data file.
- **Extract prompts:** move every inline agent prompt into a `src/prompts/` directory of editable
  templates, loaded by the agents — so wording changes don't touch logic and prompts become testable.
- **Dead-code cleanup (#9):** remove the unwired FastAPI stub; either complete the `agent_messages` audit
  trail across all agents or simplify it to what synthesis actually uses.
- **Touches:** broad but mechanical; each extraction is behavior-preserving and covered by Stage 0 tests
  (characterization tests added before moving code).

---

## Error handling philosophy (applies to Stages 2–5)
- Failure → **honest absence**, never invented presence.
- Distinguish error types (rate-limit vs timeout vs auth vs malformed JSON) in logs; retry the
  transient ones.
- Log, per fact, whether it came from real synthesis/source vs unavailable — observability the audit
  flagged as missing.

## Testing
- **Stage 0** establishes `tests/` (pytest + pytest-asyncio) + CI. Demo fixture: `sotorasib` /
  `KRAS G12C NSCLC`. Mock all LLM/API calls — no live calls in unit tests. CI runs on Py 3.13 + 3.14.
- Stage 1: component render smoke tests for `source_chip` tiers and the metric card.
- Stage 2: provenance model unit tests; tool URL-capture tests; **agent no-fabrication tests** (failure
  path yields `unavailable`, not invented numbers); modeled-range construction test; **assert no
  LLM-originated URL is ever used as a source**; all six agents validate JSON.
- Stage 3: workflow fan-out/fan-in correctness (state merges; all fields populated); retry/429 behavior;
  temperature-per-call respected; cache hit on repeat brief.
- Stage 4: input validation rejects bad input; de-identification strips identifiers before external calls;
  a prompt-injection attempt in the Q&A box is treated as data, not instructions.
- Stage 5: **characterization tests written before each extraction** so refactors are provably
  behavior-preserving.

## Rollout / review
Six separate change sets, reviewed and pushed in order (0 → 5). Stage 0 ships first as the safety net;
later stages may overlap in review. All work local until per-stage go-ahead. Each stage is independently
revertible.

## Risks
- Stage 2 is the largest semantic change (schema + agents + tools + UI) — mitigated by the staged rollout
  and no-fabrication tests.
- Stage 3 fan-out must preserve `GTMState` field ownership to avoid concurrent-write clobbering — covered
  by workflow tests.
- **Stage 5 is the highest-risk (most code moved)** — mitigated by doing it last, behind Stage 0's CI and
  per-extraction characterization tests; each extraction is behavior-preserving, not a rewrite.
- Streamlit reruns: the new components must be render-only and cheap (no heavy work in the UI layer).
