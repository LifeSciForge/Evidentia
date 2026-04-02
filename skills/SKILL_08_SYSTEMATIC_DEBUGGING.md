# SKILL_08 — Systematic Debugging

**Source:** [obra/superpowers](https://github.com/obra/superpowers) — `skills/systematic-debugging`
**Applies to:** Any test failure, unexpected agent behaviour, or production bug in Evidentia

---

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose a fix. "Quick fixes" without root cause
analysis always create new bugs elsewhere.

---

## The Four Phases

### Phase 1 — Root Cause Investigation

**Before touching any code:**

1. **Read the error message completely** — don't skim past stack traces.
   Note: file path, line number, exception type, and the exact message.

2. **Reproduce it consistently** — trigger the bug reliably before attempting a fix.
   If it's intermittent, add logging until it becomes reproducible.

3. **Check what changed recently:**
   ```bash
   git diff HEAD~3 HEAD -- src/
   git log --oneline -10
   ```

4. **For multi-component systems (Evidentia has 6+ agents + 3 API tools + Streamlit UI):**
   Add diagnostic instrumentation at each layer boundary before proposing fixes.

   Example — debugging a brief generation failure:
   ```python
   # Add temporarily to each agent:
   logger.debug(f"[DIAG] {agent_name} input state keys: {[k for k,v in vars(state).items() if v is not None]}")
   logger.debug(f"[DIAG] {agent_name} LLM response length: {len(response.content)}")
   logger.debug(f"[DIAG] {agent_name} JSON extraction result: {json_result}")
   ```

   Run once to collect evidence, then determine which layer breaks.

5. **Trace data flow backward** — follow the bad value up the call stack to where it originated.
   Fix at the source, not at the symptom.

### Phase 2 — Pattern Analysis

1. Find working examples in the codebase similar to what is broken.
2. Compare line by line — identify every difference, however small.
3. Check all dependencies: environment variables, API keys, state fields that may be `None`.

### Phase 3 — Hypothesis and Testing

1. State a single, specific hypothesis in writing: "I think X is causing Y because Z."
2. Make the smallest possible change to test it — one variable at a time.
3. If it doesn't fix it: form a NEW hypothesis, do not stack more fixes on top.

### Phase 4 — Implementation

1. Write a failing test that reproduces the bug (see SKILL_07).
2. Implement ONE fix — the root cause, not the symptom.
3. Verify: test passes, no other tests break.
4. **If 3+ fixes have failed:** stop. Question the architecture, not the symptoms.

---

## Evidentia-Specific Debug Patterns

### Agent Produces Wrong Output
```
Suspect order:
1. LLM returned malformed JSON → json_validator fallback triggered silently?
2. API returned empty results (no PubMed hits, no trials) → default data used?
3. State field was None entering the agent (upstream agent failed silently)?
4. Temperature too high → non-deterministic output?
```

Add to agent temporarily:
```python
logger.debug(f"RAW LLM RESPONSE:\n{response.content[:500]}")
```

### JSON Parsing Failure (most common bug pre-SKILL_05)
Check:
- Does the LLM response contain a code fence (` ```json `)?
- Is there nested `{}` causing greedy regex to grab the wrong block?
- Did the LLM return a list `[...]` instead of an object `{...}`?

### Streamlit State Lost
Symptoms: brief disappears on page refresh, insights not showing.
Root cause: `st.session_state` is not initialised on page load.
Check: is `init_session_state()` called at the top of every page that reads state?

### API Tool Returning Empty
Before assuming the API is down:
```python
# Add to clinical_trials_tools.py temporarily:
logger.debug(f"Request URL: {response.url}")
logger.debug(f"Response status: {response.status_code}")
logger.debug(f"Response body (first 300): {response.text[:300]}")
```

### ChromaDB / SQLite Issues (SKILL_06)
```bash
# Check if DB file exists and has content:
ls -lh data/evidentia.db
sqlite3 data/evidentia.db ".tables"
sqlite3 data/evidentia.db "SELECT COUNT(*) FROM kol_profiles;"
```

---

## Red Flags — Stop and Return to Phase 1

- Proposing fix #3 before understanding why fixes #1 and #2 didn't work
- Adding logging to a different layer than where you traced the failure
- "Let me just try X and see if it helps"
- Fix works locally but not in production → you didn't fully understand the root cause
- Each fix reveals a new problem in a different component → architectural problem, not a bug

---

## When 3+ Fixes Have Failed

Stop attempting more fixes. Ask instead:

- Is the JSON extraction pattern fundamentally broken? → Replace with Pydantic (SKILL_05)
- Is the agent doing too much in one function? → Split it
- Is the state flowing correctly between agents? → Review `gtm_workflow.py` edge definitions
- Is the API client making assumptions about response format that aren't true?

Raise to architectural level before attempting fix #4.
