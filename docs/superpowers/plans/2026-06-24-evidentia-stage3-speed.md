# Evidentia Stage 3 — Speed & Efficiency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Cut brief-generation wall-clock roughly in half and stop fabricate-on-rate-limit, without changing what the brief says. Plus efficiency wins (cache, fewer LLM calls) and the LLM-config + model-routing fixes from the audit.

**Architecture:** Two phases by risk. **Phase A (low risk, most of the win):** make each agent's multiple tool calls run concurrently and its LLM call non-blocking + retried; fix the LLM singleton so per-call temperature works; route the model through settings; wire the existing cache; collapse the 4 persona LLM calls into 1; add lightweight refresh persistence. **Phase B (higher risk, done last):** run the three independent agents (market/payer/competitor) concurrently via a **custom async orchestrator** that gathers them on copies of the state and merges distinct outputs + shared lists/dicts — chosen because `GTMState` is a plain dataclass with no LangGraph reducer channels, so a naive fan-out would clobber `agents_completed`/`sources`/`errors`.

**Tech Stack:** Python asyncio, tenacity, LangGraph, pytest. Builds on Stages 0–2.

**Branch:** `stage3-speed` (stacked on `stage2-provenance`).

---

## PHASE A — safe, high-value (do first)

### Task 1: LLM config + retry/429 + model-via-settings (TDD)
**Files:** `src/core/llm.py`; `tests/test_llm.py`.
- **Per-call config:** `get_claude(model, temperature, max_tokens)` currently caches the FIRST instance and ignores later params. Change the cache to key on `(model, temperature, max_tokens)` so each distinct config gets its own cached `ChatAnthropic`. Test: two different temperatures return two different instances; same config returns the same instance.
- **Model via settings:** default `model` to `settings.DEFAULT_MODEL` instead of the hardcoded id (3 hardcoded sites). Test: with `DEFAULT_MODEL` patched, `get_claude()` uses it.
- **Retry/429 wrapper:** add `invoke_with_retry(llm, prompt)` using tenacity (`stop_after_attempt(3)`, `wait_exponential`), retrying on transient/rate-limit errors and re-raising others; it calls `llm.invoke` (sync) — callers will wrap it in `asyncio.to_thread`. Test with a mock llm that raises once then succeeds → returns the success; raises a non-retryable → propagates.
- Commit `feat(llm): per-call config cache, settings-driven model, retry/429 wrapper`.

### Task 2: Non-blocking + within-agent concurrency (per agent, TDD-light)
**Files:** the 6 agents in `src/agents/gtm_agents/`.
> Implementer reads each agent. Two changes per agent:
- **Non-blocking LLM:** replace `response = llm.invoke(prompt)` with `response = await asyncio.to_thread(invoke_with_retry, llm, prompt)` (frees the event loop + adds retry).
- **Concurrent tool calls:** where an agent makes ≥2 independent blocking tool calls in sequence (e.g. market_research does clinical_trials + pubmed + 2 Tavily searches), run them concurrently: `a, b, c = await asyncio.gather(asyncio.to_thread(call_a), asyncio.to_thread(call_b), asyncio.to_thread(call_c))`. Preserve each result's downstream use. Keep behavior identical; only timing changes.
- Per-agent commit. Test: a per-agent test (mock tools + LLM) asserting the agent still populates its state field and does not raise. Confirm full suite green.

### Task 3: Wire the response cache (TDD)
**Files:** `src/service/cache_manager.py` (exists, unused), the tool layer or `GTMWorkflow.run`; `tests/test_cache.py`.
- Use the existing `CacheManager` to cache by a stable key (drug_name + indication, or per-tool api+args via its `make_key`). Simplest high-value: cache the completed brief / per-tool responses so a repeat run is served from cache. Test: two calls with same args hit the cache the second time (underlying fn called once).
- Commit `feat: wire response cache for repeat briefs`.

### Task 4: Collapse messaging 4 persona calls → 1 (TDD)
**Files:** `src/agents/gtm_agents/messaging_agent.py`; test.
- Replace the 4 per-persona `llm.invoke` calls with ONE call whose prompt asks for all personas in a single JSON object, validated with a Pydantic schema. Test: mock the single LLM call returns all personas; assert the agent builds the same persona structure and makes exactly one persona LLM call.
- Commit `perf(messaging): one LLM call for all personas`.

### Task 5: Lightweight refresh persistence
**Files:** `src/ui/app.py`.
- Cache the last completed brief in `st.session_state` keyed by `(drug, indication, hospital, doctor)`; on rerun/refresh, if a matching brief exists, restore it instead of regenerating. Keep it simple (session-scoped). No test required (Streamlit UI); verify by reading the code path.
- Commit `feat(ui): restore last brief on refresh`.

---

## PHASE B — higher risk (do last, thorough tests)

### Task 6: Concurrent independent agents via custom orchestrator (TDD)
**Files:** `src/agents/gtm_workflow.py`; `tests/test_parallel_merge.py`.
> The three independent agents — `market_research`, `payer_intelligence`, `competitor_analysis` — have no data dependency on each other; `icp → messaging → synthesis` depend on them.
- Implement a `run` path that:
  1. Runs the 3 independent agents concurrently with `asyncio.gather`, EACH on its own `copy.deepcopy(state)` (so they don't race on shared mutable fields).
  2. **Merges** the three results into one state: copy each agent's DISTINCT output field (`market_data`, `payer_data`, `competitor_data`); and merge the SHARED fields by union — `agents_completed` (dedup union), `errors` (concatenate), `sources` (dict update). Recompute `progress_percentage`.
  3. Then runs `icp_definition → messaging → synthesis` sequentially on the merged state.
- Keep the existing LangGraph app as a fallback/secondary path if helpful, but the orchestrator is the active path. Preserve the `progress_callback` so the UI still updates per agent.
- **Tests (the safety net):** construct three states where each independent agent sets its own field + appends to `agents_completed`/`sources`; assert the merge keeps ALL three fields, the union of `agents_completed` (no dupes, no loss), merged `sources`, and concatenated `errors`. Assert no field is clobbered. Also assert the dependent agents then see all three upstream outputs.
- Commit `perf(workflow): run independent agents concurrently with safe merge`.

### Task 7: Integration + performance verification (human checkpoint)
- Run the app locally, generate the `sotorasib` brief, confirm: same content quality as before, visibly faster, no crashes, brief still shows real values/chips. Optionally time before/after.
- Controller shows the user; explicit approval before Stage 3 is complete.

---

## Self-Review
**Spec coverage:** parallel independent agents (T6) · within-agent concurrency + non-blocking AI (T2) · retry/429 (T1,T2) · per-call temperature fix (T1) · model-via-settings (T1) · wire cache (T3) · messaging collapse (T4) · refresh persistence (T5). ✓
**Risk:** T6 is the only state-merge change — isolated to the orchestrator, deep-copies inputs, explicit union merge, dedicated no-clobber tests; everything else is behavior-preserving timing/config. ✓
**Placeholder scan:** new code (llm config, merge) is concrete; per-agent edits are directive against existing code with one complete pattern shown. ✓
**Design decision for reviewer:** custom async orchestrator for fan-out (not LangGraph reducer channels) — chosen because `GTMState` has no reducer annotations; least-risk, fully testable. Phase A delivers most of the speed win at low risk; Phase B adds cross-agent parallelism last.
