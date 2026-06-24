# Evidentia Stage 5 — Architecture Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`). This stage is BEHAVIOR-PRESERVING: every change is a move or rename, never a rewrite. The Task-1 safety net must be green before and after every later task.

**Goal:** Make the codebase maintainable: break up the 2,555-line `src/ui/app.py`, move inline agent prompts into editable templates, modernize the deprecated Pydantic settings config, and remove orphaned code — WITHOUT changing any behavior.

**Architecture:** Establish a characterization safety net first (render each section with a populated state, assert no crash). Then do the lowest-risk cleanups (settings config, dead code), then extract prompts, then decompose `app.py` into focused modules behind the net.

**Tech Stack:** Python, Streamlit, Pydantic v2, pytest. Builds on Stages 0–4 (111 tests).

**Branch:** `stage5-refactor` (stacked on `stage4-security`).

**Note from recon:** there is NO FastAPI code in `src/` to remove (it only appears in docker-compose infra) — drop that item. The Pydantic deprecation warning seen all along is `class Config` in `settings.py` — fixed in Task 2.

---

## Task 1: Characterization safety net (TDD-first, no production change)

**Files:** Create `tests/test_render_smoke.py`; create a shared `populated_state` fixture (in this test file or `conftest.py`).

> Streamlit render functions are no-ops in bare mode (they emit "missing ScriptRunContext" warnings but don't crash). So we can call each section with a fully-populated `GTMState` and assert it does not raise. This net guards the decomposition: if a move breaks a section, a smoke test fails.

- [ ] **Step 1:** Build a `populated_state` — a `GTMState` with `market_data`, `payer_data`, `competitor_data`, `icp_profile`, `messaging_data`, `msl_talking_points`, and a couple of `sources` entries filled with realistic values (read the dataclasses for required fields; use the `sotorasib` demo). Keep it in the test module.
- [ ] **Step 2:** For EACH public section function in `app.py` (`display_msl_results`, `display_talking_points_section`, `display_objection_handling_section`, `display_discovery_questions_section`, `display_clinical_evidence_section`, `display_competitive_section`, `display_final_brief_section`, `display_qa_chat_section`) write a test that calls it with `populated_state` (and any extra args) and asserts it returns without raising. Also a test that each renders with an EMPTY `GTMState` (honest-empty paths) without raising. Silence/ignore Streamlit warnings.
- [ ] **Step 3:** Run `pytest tests/test_render_smoke.py -v` → all pass (against the CURRENT, un-refactored code). This is the baseline.
- [ ] **Step 4:** Commit `test: characterization smoke tests for UI sections (refactor safety net)`.

---

## Task 2: Modernize settings config + remove orphaned code (TDD/verify)

**Files:** `src/core/settings.py`; `src/ui/app.py` (remove orphan).

- [ ] **Step 1:** In `settings.py`, replace the deprecated `class Config:` block with Pydantic v2 style:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
...
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="allow")
    # ... fields unchanged ...
```
Remove the old `class Config`. Run `pytest -q` and confirm the suite passes AND the Pydantic deprecation warning is gone (the run should show 0 warnings, or note it).
- [ ] **Step 2:** Remove the now-orphaned `display_download_section` from `app.py` (its buttons were moved to `_render_export_buttons` in Stage 1 and it is called nowhere — confirm with `grep -n "display_download_section(" src/ui/app.py` showing only the `def`). Delete the function. Re-run the Task-1 smoke tests + full suite → green.
- [ ] **Step 3:** Commit `chore: modernize Pydantic settings config; remove orphaned download section`.

---

## Task 3: Extract agent prompts to templates (per agent)

**Files:** Create `src/prompts/__init__.py` + a loader; create `src/prompts/<agent>.txt` files; modify the 6 agents. Test `tests/test_prompts.py`.

> 8 inline prompts: market/payer/icp/competitor/synthesis (1 each) + messaging (3). Move each prompt STRING into a template file; load it and `.format(...)`/f-substitute the same variables. Behavior identical — same prompt text reaches the LLM.

- [ ] **Step 1:** Add a tiny loader in `src/prompts/__init__.py`:
```python
from pathlib import Path
_DIR = Path(__file__).parent
def load_prompt(name: str) -> str:
    return (_DIR / f"{name}.txt").read_text(encoding="utf-8")
```
Test (`tests/test_prompts.py`): `load_prompt` returns the file text; a known placeholder (e.g. `{drug_name}`) is present in the relevant template.
- [ ] **Step 2 (per agent):** move the inline prompt text into `src/prompts/<agent>.txt` using named `{placeholders}`; in the agent, `prompt = load_prompt("<agent>").format(drug_name=..., indication=..., ...)`. Keep the exact wording. The placeholders must match the variables previously interpolated. Run the agent's existing tests (Stage 2/3 mocked tests) → still green. Commit per agent (`refactor(<agent>): load prompt from template`).
- [ ] **Step 3:** After all agents, `pytest -q` green.

CAUTION: f-strings vs `.format()` — many prompts contain literal `{` `}` (JSON examples). When moving to `.format()`, literal braces must be doubled `{{ }}`. SAFER: keep them as f-strings by storing the template and using a small explicit substitution, OR escape braces carefully. The implementer must verify the rendered prompt is character-identical to before (write a quick assertion comparing a rendered sample to the old inline text for one agent).

---

## Task 4: Decompose `app.py` into modules (behind the safety net)

**Files:** Create `src/ui/styles.py`, `src/ui/helpers.py`, `src/ui/sections/` (one module per section); move the hospital list to `src/ui/data/hospitals.py` (or a JSON). Slim `src/ui/app.py` to entry + tab wiring.

> Move, don't rewrite. After EACH move, run the Task-1 smoke tests + full suite. Commit per move so any regression is bisectable.

- [ ] **Step 1:** Extract the big global CSS `<style>` string into `src/ui/styles.py` as a constant + an `inject_styles()` that does the `st.markdown`. Call it from `app.py`. Run net → green. Commit.
- [ ] **Step 2:** Extract helpers (`chip_for`, `glance_lead_points`, `_tab_heading`, `_section_label`) into `src/ui/helpers.py`; update imports. Net → green. Commit.
- [ ] **Step 3:** Move `get_hospital_list()`'s data into `src/ui/data/hospitals.py` (a plain dict/JSON) and have the function read from it. Net → green. Commit.
- [ ] **Step 4 (per section):** move each `display_*_section` (and its private `_render_*`/`_obj_content_html` helpers) into `src/ui/sections/<name>.py`, importing what it needs (helpers, components, deidentify, etc.). Update `app.py` to import and call them. Run the smoke tests + full suite after EACH section move. Commit per section.
- [ ] **Step 5:** Move `generate_qa_answer`/`fallback_qa_answer` business logic into `src/service/qa_service.py` (keep the Streamlit wrapper thin). Net → green. Commit.
- [ ] **Step 6:** `app.py` should now be a thin entry point (page config, preflight already in `streamlit_app.py`, `main()`, tab wiring). Confirm final `wc -l src/ui/app.py` is much smaller; full suite + smoke tests green.

---

## Task 5: Verification (human checkpoint)
- [ ] Run the app; generate the `sotorasib` brief; click through ALL tabs + Q&A + Export. Confirm everything looks and behaves EXACTLY as before the refactor (this stage changed structure, not behavior).
- [ ] Controller shows the user; explicit approval before Stage 5 is complete.

---

## Self-Review
**Spec coverage:** decompose `app.py` (T4) · extract prompts (T3) · modernize settings + remove dead code (T2) · (FastAPI stub: N/A — not in src). ✓
**Risk control:** characterization net first (T1); behavior-preserving moves only; per-move commits + net re-run; prompt extraction guarded against brace-escaping pitfalls. ✓
**Placeholder scan:** loader + settings snippets concrete; the moves are directive (read-then-move) with the net as the contract — appropriate for a large mechanical refactor. ✓
**Design note:** this stage must not change behavior. If any task tempts a behavior change, STOP and defer it — refactor and feature-change don't mix.
